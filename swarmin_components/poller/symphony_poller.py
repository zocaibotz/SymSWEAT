import atexit
import fcntl
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
LINEAR_API_URL = "https://api.linear.app/graphql"
POLL_INTERVAL_SEC = int(os.environ.get("POLL_INTERVAL_SEC", "30"))
MAX_CONCURRENT_AGENTS = int(os.environ.get("MAX_CONCURRENT_AGENTS", "3"))
PROJECT_ID_FILTER = (os.environ.get("PROJECT_ID_FILTER") or "").strip()
PROJECT_NAME_FILTER = (os.environ.get("PROJECT_NAME_FILTER") or "").strip().lower()
MAX_RETRY_ATTEMPTS = int(os.environ.get("MAX_RETRY_ATTEMPTS", "3"))
STALL_MINUTES = int(os.environ.get("STALL_MINUTES", "30"))

# Path to the swarm adapter
SWARM_ADAPTER_PATH = os.path.abspath(os.environ.get("SWARM_ADAPTER_PATH", os.path.join(os.path.dirname(__file__), "..", "swarm-adapter", "run_swarm.sh")))
RUNS_DIR = os.path.abspath(os.environ.get("RUNS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "symphony", "runs")))
RETRY_STATE_PATH = os.path.join(RUNS_DIR, "retry_state.json")
ACTIVE_RUNS_DIR = os.path.join(RUNS_DIR, "active")
ATTEMPT_RUNS_DIR = os.path.join(RUNS_DIR, "attempts")
ISSUE_RUNS_DIR = os.path.join(RUNS_DIR, "issues")
POLLER_LOCK_PATH = os.environ.get("POLLER_LOCK_PATH", "/tmp/swarminsym_poller.lock")
TERMINAL_RUN_STATUSES = {"success", "failed", "stalled", "abandoned", "completed"}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _allowed_state_names() -> List[str]:
    states = ["Todo"]
    if _env_flag("INCLUDE_BACKLOG", default=False):
        states.append("Backlog")
    return states


def _issue_matches_project_filter(issue: Dict) -> bool:
    project = issue.get("project") or {}
    project_id = (project.get("id") or "").strip()
    project_name = (project.get("name") or "").strip().lower()

    if PROJECT_ID_FILTER and project_id != PROJECT_ID_FILTER:
        return False
    if PROJECT_NAME_FILTER and project_name != PROJECT_NAME_FILTER:
        return False
    return True


def run_linear_graphql(query: str, variables: Dict = None) -> Dict:
    headers = {
        "Authorization": LINEAR_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(
        LINEAR_API_URL,
        headers=headers,
        json={"query": query, "variables": variables or {}}
    )
    response.raise_for_status()
    result = response.json()
    if "errors" in result:
        raise Exception(f"Linear API errors: {result['errors']}")
    return result


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _now_utc().isoformat()


def _parse_ts(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _write_json_atomic(path: str, data: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def _safe_unlink(path: str):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _active_attempt_path(issue_identifier: str, attempt_id: str) -> str:
    return os.path.join(ACTIVE_RUNS_DIR, f"{issue_identifier}--{attempt_id}.json")


def _active_current_path(issue_identifier: str) -> str:
    return os.path.join(ACTIVE_RUNS_DIR, f"{issue_identifier}.current.json")


def _attempt_ledger_path(issue_identifier: str, attempt_id: str) -> str:
    return os.path.join(ATTEMPT_RUNS_DIR, f"{issue_identifier}--{attempt_id}.json")


def _issue_summary_path(issue_identifier: str) -> str:
    return os.path.join(ISSUE_RUNS_DIR, f"{issue_identifier}.json")


def _legacy_ledger_path(issue_identifier: str) -> str:
    return os.path.join(RUNS_DIR, f"{issue_identifier}.json")


def _read_json(path: str) -> Optional[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _generate_attempt_id() -> str:
    return _now_utc().strftime("%Y%m%dT%H%M%S%fZ")


def _pid_is_running(pid: Optional[int]) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _run_last_activity_ts(run: Dict) -> Optional[datetime]:
    for key in ("last_heartbeat_ts", "poller_dispatch_ts"):
        parsed = _parse_ts(run.get(key))
        if parsed:
            return parsed
    return None


def _run_activity_age_minutes(run: Dict, now: Optional[datetime] = None) -> float:
    activity_ts = _run_last_activity_ts(run)
    if not activity_ts:
        return float("inf")
    ref = now or _now_utc()
    return (ref - activity_ts).total_seconds() / 60.0


def _run_is_terminal(run: Dict) -> bool:
    return (run.get("status") or "").lower() in TERMINAL_RUN_STATUSES


def _resolve_run_ledger_path(run: Dict) -> str:
    ledger_path = (run.get("ledger_path") or "").strip()
    if ledger_path:
        return ledger_path

    issue_identifier = (run.get("issue_identifier") or "").strip()
    attempt_id = (run.get("attempt_id") or "").strip()
    if issue_identifier and attempt_id:
        return _attempt_ledger_path(issue_identifier, attempt_id)
    if issue_identifier:
        return _legacy_ledger_path(issue_identifier)
    return ""


def _load_active_run_from_current_file(path: str) -> Optional[Dict]:
    data = _read_json(path)
    if not data:
        return None
    issue_identifier = data.get("issue_identifier")
    attempt_id = data.get("attempt_id")
    if not issue_identifier or not attempt_id:
        return None

    attempt_path = data.get("registry_path") or _active_attempt_path(issue_identifier, attempt_id)
    attempt_data = _read_json(attempt_path)
    if attempt_data:
        attempt_data.setdefault("registry_path", attempt_path)
        attempt_data.setdefault("current_path", path)
        return attempt_data

    data.setdefault("registry_path", attempt_path)
    data.setdefault("current_path", path)
    return data


def persist_active_run(run: Dict):
    issue_identifier = run["issue_identifier"]
    attempt_id = run["attempt_id"]
    attempt_path = run.get("registry_path") or _active_attempt_path(issue_identifier, attempt_id)
    current_path = run.get("current_path") or _active_current_path(issue_identifier)

    payload = dict(run)
    payload["registry_path"] = attempt_path
    payload["current_path"] = current_path
    _write_json_atomic(attempt_path, payload)

    current_payload = {
        "issue_id": payload.get("issue_id"),
        "issue_identifier": payload.get("issue_identifier"),
        "attempt_id": payload.get("attempt_id"),
        "status": payload.get("status"),
        "poller_dispatch_ts": payload.get("poller_dispatch_ts"),
        "last_heartbeat_ts": payload.get("last_heartbeat_ts"),
        "current_phase": payload.get("current_phase"),
        "phase_started_at": payload.get("phase_started_at"),
        "last_event": payload.get("last_event"),
        "ledger_path": payload.get("ledger_path"),
        "issue_summary_path": payload.get("issue_summary_path"),
        "branch": payload.get("branch"),
        "adapter_pid": payload.get("adapter_pid"),
        "registry_path": attempt_path,
        "current_path": current_path,
    }
    _write_json_atomic(current_path, current_payload)


def clear_active_run(run: Dict):
    _safe_unlink(run.get("registry_path") or _active_attempt_path(run.get("issue_identifier", ""), run.get("attempt_id", "")))
    _safe_unlink(run.get("current_path") or _active_current_path(run.get("issue_identifier", "")))


def build_active_run_record(issue: Dict, attempt_id: str, adapter_pid: Optional[int] = None, status: str = "dispatched") -> Dict:
    ts = _utc_now_iso()
    identifier = issue["identifier"]
    return {
        "issue_id": issue["id"],
        "issue_identifier": identifier,
        "attempt_id": attempt_id,
        "poller_dispatch_ts": ts,
        "last_heartbeat_ts": ts,
        "current_phase": "poller_dispatch",
        "phase_started_at": ts,
        "last_event": "dispatch_created",
        "adapter_pid": adapter_pid,
        "status": status,
        "ledger_path": _attempt_ledger_path(identifier, attempt_id),
        "issue_summary_path": _issue_summary_path(identifier),
        "branch": identifier,
        "registry_path": _active_attempt_path(identifier, attempt_id),
        "current_path": _active_current_path(identifier),
    }


def load_active_runs() -> Dict[str, Dict]:
    os.makedirs(ACTIVE_RUNS_DIR, exist_ok=True)
    active_runs: Dict[str, Dict] = {}
    for fn in os.listdir(ACTIVE_RUNS_DIR):
        if not fn.endswith(".current.json"):
            continue
        run = _load_active_run_from_current_file(os.path.join(ACTIVE_RUNS_DIR, fn))
        if not run:
            continue
        issue_id = run.get("issue_id")
        if issue_id:
            active_runs[issue_id] = run
    return active_runs


def reconcile_active_runs(active_runs: Dict[str, Dict]) -> Dict[str, Dict]:
    reconciled: Dict[str, Dict] = {}
    for issue_id, run in active_runs.items():
        ledger = _read_json(_resolve_run_ledger_path(run)) or {}
        ledger_status = (ledger.get("status") or "").lower()
        if ledger_status in TERMINAL_RUN_STATUSES:
            run = dict(run)
            run["status"] = ledger_status
            run["last_heartbeat_ts"] = ledger.get("ended_at") or run.get("last_heartbeat_ts")
            clear_active_run(run)
            continue

        if _pid_is_running(run.get("adapter_pid")):
            run = dict(run)
            run["status"] = "running"
            persist_active_run(run)
            reconciled[issue_id] = run
            continue

        # If adapter_pid is not running and we are not in terminal state
        # The run might have died unexpectedly or it's stalled.
        # We still keep it in reconciled so handle_stalled_issues can clean it up
        reconciled[issue_id] = run
    return reconciled


def load_retry_state() -> Dict:
    try:
        with open(RETRY_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"issues": {}, "processed": {}}


def save_retry_state(state: Dict):
    os.makedirs(RUNS_DIR, exist_ok=True)
    with open(RETRY_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def linear_comment(issue_id: str, body: str):
    if not LINEAR_API_KEY or not issue_id:
        return
    mutation = "mutation CommentCreate($issueId: String!, $body: String!) { commentCreate(input: { issueId: $issueId, body: $body }) { success } }"
    run_linear_graphql(mutation, {"issueId": issue_id, "body": body})


def transition_issue(issue_id: str, preferred_names: List[str]) -> bool:
    if not LINEAR_API_KEY or not issue_id:
        return False

    q = """
    query TeamStates($issueId: String!) {
      issue(id: $issueId) {
        team { states { nodes { id name type } } }
      }
    }
    """
    res = run_linear_graphql(q, {"issueId": issue_id})
    states = (((res.get("data") or {}).get("issue") or {}).get("team") or {}).get("states", {}).get("nodes", [])
    state_id = None
    for name in preferred_names:
        for s in states:
            if s.get("name") == name:
                state_id = s.get("id")
                break
        if state_id:
            break

    if not state_id and any(n.lower() in {"done", "review", "in review"} for n in preferred_names):
        for s in states:
            if (s.get("type") or "").lower() == "completed":
                state_id = s.get("id")
                break

    if not state_id:
        return False

    mut = "mutation UpdateIssue($id: String!, $stateId: String!) { issueUpdate(id: $id, input: { stateId: $stateId }) { success } }"
    out = run_linear_graphql(mut, {"id": issue_id, "stateId": state_id})
    return bool((((out.get("data") or {}).get("issueUpdate") or {}).get("success")))


def _iter_attempt_ledger_paths() -> List[str]:
    paths: List[str] = []
    if os.path.isdir(ATTEMPT_RUNS_DIR):
        for fn in sorted(os.listdir(ATTEMPT_RUNS_DIR)):
            if fn.endswith(".json"):
                paths.append(os.path.join(ATTEMPT_RUNS_DIR, fn))
    else:
        os.makedirs(ATTEMPT_RUNS_DIR, exist_ok=True)

    # Backward-compatible fallback for pre-Slice-2A ledgers.
    if os.path.isdir(RUNS_DIR):
        for fn in sorted(os.listdir(RUNS_DIR)):
            if not fn.endswith(".json") or fn == "retry_state.json":
                continue
            paths.append(os.path.join(RUNS_DIR, fn))
    return paths


def reconcile_failed_attempts(retry_state: Dict):
    os.makedirs(RUNS_DIR, exist_ok=True)
    for path in _iter_attempt_ledger_paths():
        data = _read_json(path)
        if not data:
            continue

        identifier = data.get("issue_identifier")
        issue_id = data.get("issue_id")
        attempt_id = data.get("attempt_id") or os.path.splitext(os.path.basename(path))[0]
        ended_at = data.get("ended_at")
        status = data.get("status")
        reason = data.get("reason") or "unknown"
        if not identifier or not ended_at or not status:
            continue

        key = f"{identifier}:{attempt_id}:{ended_at}:{status}"
        if retry_state.get("processed", {}).get(key):
            continue
        retry_state.setdefault("processed", {})[key] = True

        issue_meta = retry_state.setdefault("issues", {}).setdefault(identifier, {
            "attempts": 0,
            "last_reason": "",
            "terminal": False,
            "issue_id": issue_id,
            "history": []
        })
        if issue_id and not issue_meta.get("issue_id"):
            issue_meta["issue_id"] = issue_id

        history_entry = {
            "attempt_id": attempt_id,
            "ended_at": ended_at,
            "status": status,
            "reason": "success" if status == "success" else reason,
            "ledger_path": path,
        }

        if status == "failed":
            issue_meta["attempts"] = int(issue_meta.get("attempts", 0)) + 1
            issue_meta["last_reason"] = reason
            issue_meta.setdefault("history", []).append(history_entry)
        elif status == "success":
            issue_meta["attempts"] = 0
            issue_meta["last_reason"] = ""
            issue_meta["terminal"] = True
            issue_meta.setdefault("history", []).append(history_entry)
            if issue_id:
                transition_issue(issue_id, ["In Review", "Review", "Done"])
                linear_comment(issue_id, "Auto-monitor: successful run ledger detected; moved ticket to review/completed state.")


def handle_stalled_issues(retry_state: Dict, active_runs_by_issue: Dict[str, Dict]):
    query = """
    query {
      issues(filter: { state: { name: { eq: "In Progress" } } }) {
        nodes { id identifier title updatedAt project { id name } }
      }
    }
    """
    res = run_linear_graphql(query)
    issues = (res.get("data") or {}).get("issues", {}).get("nodes", [])
    now = _now_utc()

    for issue in issues:
        if not _issue_matches_project_filter(issue):
            continue

        active_run = active_runs_by_issue.get(issue.get("id"))
        if active_run and not _run_is_terminal(active_run):
            if _pid_is_running(active_run.get("adapter_pid")):
                continue
            if _run_activity_age_minutes(active_run, now=now) < STALL_MINUTES:
                continue

        updated = _parse_ts(issue.get("updatedAt"))
        if not updated:
            continue
        age_min = (now - updated).total_seconds() / 60.0
        if age_min < STALL_MINUTES:
            continue

        identifier = issue.get("identifier")
        meta = retry_state.setdefault("issues", {}).setdefault(identifier, {
            "attempts": 0,
            "last_reason": "stalled",
            "terminal": False,
            "issue_id": issue.get("id"),
            "history": []
        })

        if meta.get("terminal"):
            continue

        attempts = int(meta.get("attempts", 0))
        if attempts >= MAX_RETRY_ATTEMPTS:
            transition_issue(issue.get("id"), ["Canceled", "Cancelled", "Done"])
            linear_comment(issue.get("id"), f"Auto-monitor: Marking as terminal after {attempts} failed/stalled attempts. Last reason: {meta.get('last_reason')}.")
            meta["terminal"] = True
            continue

        meta["attempts"] = attempts + 1
        meta["last_reason"] = "stalled"
        meta.setdefault("history", []).append({"ended_at": _now_utc().isoformat(), "reason": "stalled"})
        transition_issue(issue.get("id"), ["Todo", "Backlog"])
        linear_comment(issue.get("id"), f"Auto-monitor: ticket appeared stalled for ~{int(age_min)}m; re-queued for retry (attempt {attempts + 1}/{MAX_RETRY_ATTEMPTS}).")


def get_candidate_issues(retry_state: Dict, active_issue_ids: Optional[set] = None) -> List[Dict]:
    active_issue_ids = active_issue_ids or set()
    allowed_states = _allowed_state_names()
    query = """
    query GetCandidateIssues($stateNames: [String!]) {
      issues(filter: { state: { name: { in: $stateNames } } }) {
        nodes {
          id
          identifier
          title
          description
          state { name }
          project {
            id
            name
          }
          inverseRelations {
            nodes {
              type
              issue {
                id
                state { name }
              }
            }
          }
        }
      }
    }
    """
    res = run_linear_graphql(query, {"stateNames": allowed_states})
    issues = res["data"]["issues"]["nodes"]

    candidates = []
    for issue in issues:
        if not _issue_matches_project_filter(issue):
            continue
        if issue.get("id") in active_issue_ids:
            continue

        meta = (retry_state.get("issues") or {}).get(issue.get("identifier") or "", {})
        attempts = int(meta.get("attempts", 0))
        if meta.get("terminal") or attempts >= MAX_RETRY_ATTEMPTS:
            if not meta.get("terminal") and issue.get("id"):
                transition_issue(issue.get("id"), ["Canceled", "Cancelled", "Done"])
                linear_comment(issue.get("id"), f"Auto-monitor: max retries reached ({attempts}). Marking ticket terminal. Last reason: {meta.get('last_reason', 'unknown')}.")
                meta["terminal"] = True
                retry_state.setdefault("issues", {})[issue.get("identifier")] = meta
            continue

        is_blocked = False
        for rel in issue["inverseRelations"]["nodes"]:
            if rel["type"] == "blocks":
                blocker_state = rel["issue"]["state"]["name"]
                if blocker_state not in ["Done", "In Review", "Review", "Canceled", "Closed"]:
                    is_blocked = True
                    break

        if not is_blocked:
            candidates.append(issue)

    return candidates


def mark_issue_in_progress(issue_id: str):
    query = """
    query { workflowStates { nodes { id name } } }
    """
    res = run_linear_graphql(query)
    states = res["data"]["workflowStates"]["nodes"]
    in_progress_state_id = next((s["id"] for s in states if s["name"] == "In Progress"), None)

    if in_progress_state_id:
        mut = """
        mutation UpdateIssue($id: String!, $stateId: String!) {
          issueUpdate(id: $id, input: { stateId: $stateId }) { success }
        }
        """
        run_linear_graphql(mut, {"id": issue_id, "stateId": in_progress_state_id})


def _slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def _repo_exists(owner: str, repo: str) -> bool:
    try:
        subprocess.check_output(["gh", "repo", "view", f"{owner}/{repo}"], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _expand_truncated_repo(owner: str, prefix: str) -> Optional[str]:
    """If prefix is like 'habit-tracker' from 'habit-tracker...', find first matching repo."""
    try:
        out = subprocess.check_output(
            ["gh", "repo", "list", owner, "--limit", "200", "--json", "name", "--jq", ".[].[\"name\"]"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        repos = [r.strip() for r in out.splitlines() if r.strip()]
        exact = [r for r in repos if r == prefix]
        if exact:
            return f"https://github.com/{owner}/{exact[0]}"
        matches = [r for r in repos if r.startswith(prefix)]
        if matches:
            return f"https://github.com/{owner}/{sorted(matches, key=len)[0]}"
    except Exception:
        pass
    return None


def get_repo_url_from_project(issue: Dict) -> str:
    issue_id = issue["id"]
    owner = os.environ.get("GITHUB_OWNER", "zocaibotz")
    query = """
    query GetProject($issueId: String!) {
      issue(id: $issueId) {
        project {
          name
          description
        }
      }
    }
    """
    try:
        res = run_linear_graphql(query, {"issueId": issue_id})
        project = res["data"]["issue"]["project"] or {}
        project_name = project.get("name") or ""
        desc = project.get("description") or ""

        m0 = re.search(r"REPO_URL\s*=\s*(https?://github\.com/[\w.-]+/[\w.-]+)", desc)
        if m0:
            return m0.group(1).strip()

        m = re.search(r"https?://github\.com/([\w.-]+)/([\w.-]+)", desc)
        if m:
            repo = m.group(2)
            if "..." not in repo:
                return f"https://github.com/{m.group(1)}/{repo}"

        m2 = re.search(r"https?://github\.com/([\w.-]+)/([\w.-]+)\.\.\.", desc)
        if m2:
            expanded = _expand_truncated_repo(m2.group(1), m2.group(2))
            if expanded:
                return expanded

        base_slug = _slugify(project_name)
        candidates = [
            base_slug,
            base_slug.replace("simple-", "", 1),
            base_slug.replace("-app", ""),
            base_slug.replace("simple-", "", 1).replace("-app", ""),
        ]
        seen = set()
        for repo in candidates:
            if not repo or repo in seen:
                continue
            seen.add(repo)
            if _repo_exists(owner, repo):
                return f"https://github.com/{owner}/{repo}"

        return ""
    except Exception:
        return ""


def dispatch_swarm_adapter(issue: Dict) -> subprocess.Popen:
    issue_id = issue["id"]
    identifier = issue["identifier"]
    title = issue["title"]
    description = issue["description"] or ""
    repo_url = get_repo_url_from_project(issue)
    attempt_id = _generate_attempt_id()

    print(f"Dispatching SWARM for {identifier}: {title}")
    mark_issue_in_progress(issue_id)

    env = os.environ.copy()
    env["ISSUE_ID"] = issue_id
    env["ISSUE_IDENTIFIER"] = identifier
    env["ISSUE_TITLE"] = title
    env["ISSUE_DESCRIPTION"] = description
    env["REPO_URL"] = repo_url
    env["SWARM_ATTEMPT_ID"] = attempt_id

    active_run = build_active_run_record(issue, attempt_id=attempt_id, status="dispatched")
    persist_active_run(active_run)

    try:
        process = subprocess.Popen(
            ["bash", SWARM_ADAPTER_PATH],
            env=env,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        clear_active_run(active_run)
        raise

    started_ts = _utc_now_iso()
    active_run["adapter_pid"] = process.pid
    active_run["status"] = "running"
    active_run["last_heartbeat_ts"] = started_ts
    active_run["current_phase"] = "adapter_bootstrap"
    active_run["phase_started_at"] = started_ts
    active_run["last_event"] = "adapter_spawned"
    persist_active_run(active_run)
    return process


def main():
    if not LINEAR_API_KEY:
        print("Missing LINEAR_API_KEY")
        return

    lock_fh = open(POLLER_LOCK_PATH, "w")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"Another poller instance is already running (lock: {POLLER_LOCK_PATH}). Exiting.")
        return
    atexit.register(lambda: lock_fh.close())

    scope = []
    if PROJECT_ID_FILTER:
        scope.append(f"project_id={PROJECT_ID_FILTER}")
    if PROJECT_NAME_FILTER:
        scope.append(f"project_name={PROJECT_NAME_FILTER}")
    scope_desc = ", ".join(scope) if scope else "all-projects"
    print(
        f"Starting SWARMINSYM Poller "
        f"(Interval: {POLL_INTERVAL_SEC}s, Max Concurrency: {MAX_CONCURRENT_AGENTS}, "
        f"States: {_allowed_state_names()}, Scope: {scope_desc}, "
        f"MaxRetries: {MAX_RETRY_ATTEMPTS}, StallMins: {STALL_MINUTES})"
    )

    active_by_issue = reconcile_active_runs(load_active_runs())

    while True:
        try:
            active_by_issue = reconcile_active_runs(load_active_runs())
            active_issue_ids = set(active_by_issue.keys())

            retry_state = load_retry_state()
            reconcile_failed_attempts(retry_state)
            handle_stalled_issues(retry_state, active_by_issue)
            save_retry_state(retry_state)

            available_slots = MAX_CONCURRENT_AGENTS - len(active_issue_ids)

            if available_slots > 0:
                candidates = get_candidate_issues(retry_state, active_issue_ids=active_issue_ids)
                if candidates:
                    print(f"Found {len(candidates)} unblocked candidate issues. Dispatching up to {available_slots}.")
                    for issue in candidates[:available_slots]:
                        dispatch_swarm_adapter(issue)
                else:
                    pass
            else:
                print(f"Max concurrency reached ({MAX_CONCURRENT_AGENTS}). Waiting for processes to finish...")

        except Exception as e:
            print(f"Poller error: {e}")

        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
