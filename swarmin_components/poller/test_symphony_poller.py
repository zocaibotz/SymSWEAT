import json
from datetime import timedelta
from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).resolve().parent / "symphony_poller.py"
spec = importlib.util.spec_from_file_location("symphony_poller", MODULE_PATH)
poller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(poller)


def _issue(issue_id="issue-1", identifier="ZOC-1"):
    return {
        "id": issue_id,
        "identifier": identifier,
        "title": "Test issue",
        "description": "desc",
        "project": {"id": "p1", "name": "proj"},
        "inverseRelations": {"nodes": []},
    }


def test_active_run_registry_survives_reload(tmp_path, monkeypatch):
    monkeypatch.setattr(poller, "RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(poller, "ACTIVE_RUNS_DIR", str(tmp_path / "runs" / "active"))
    monkeypatch.setattr(poller, "ATTEMPT_RUNS_DIR", str(tmp_path / "runs" / "attempts"))
    monkeypatch.setattr(poller, "ISSUE_RUNS_DIR", str(tmp_path / "runs" / "issues"))

    issue = _issue()
    run = poller.build_active_run_record(issue, attempt_id="attempt-1", adapter_pid=4321, status="running")
    poller.persist_active_run(run)

    loaded = poller.load_active_runs()
    assert issue["id"] in loaded
    assert loaded[issue["id"]]["attempt_id"] == "attempt-1"
    assert loaded[issue["id"]]["adapter_pid"] == 4321
    assert loaded[issue["id"]]["current_phase"] == "poller_dispatch"
    assert loaded[issue["id"]]["last_event"] == "dispatch_created"
    assert loaded[issue["id"]]["phase_started_at"] == loaded[issue["id"]]["poller_dispatch_ts"]
    assert loaded[issue["id"]]["ledger_path"].endswith("runs/attempts/ZOC-1--attempt-1.json")
    assert loaded[issue["id"]]["issue_summary_path"].endswith("runs/issues/ZOC-1.json")


def test_reconcile_active_run_clears_registry_when_ledger_terminal(tmp_path, monkeypatch):
    monkeypatch.setattr(poller, "RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(poller, "ACTIVE_RUNS_DIR", str(tmp_path / "runs" / "active"))
    monkeypatch.setattr(poller, "ATTEMPT_RUNS_DIR", str(tmp_path / "runs" / "attempts"))
    monkeypatch.setattr(poller, "ISSUE_RUNS_DIR", str(tmp_path / "runs" / "issues"))

    issue = _issue()
    run = poller.build_active_run_record(issue, attempt_id="attempt-2", adapter_pid=9999, status="running")
    poller.persist_active_run(run)
    Path(run["ledger_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(run["ledger_path"]).write_text(json.dumps({"status": "success", "ended_at": "2026-04-03T07:00:00+00:00"}))

    reconciled = poller.reconcile_active_runs(poller.load_active_runs())
    assert reconciled == {}
    assert not Path(run["registry_path"]).exists()
    assert not Path(run["current_path"]).exists()


def test_handle_stalled_issues_skips_live_registered_run(monkeypatch):
    transitions = []
    comments = []
    now = poller._now_utc()
    stale_issue = {
        "id": "issue-1",
        "identifier": "ZOC-1",
        "title": "Stale in progress",
        "updatedAt": (now - timedelta(minutes=poller.STALL_MINUTES + 5)).isoformat(),
        "project": {"id": "p1", "name": "proj"},
    }
    active_run = {
        "issue_id": "issue-1",
        "issue_identifier": "ZOC-1",
        "attempt_id": "attempt-3",
        "status": "running",
        "adapter_pid": 1234,
        "last_heartbeat_ts": (now - timedelta(minutes=poller.STALL_MINUTES + 5)).isoformat(),
        "poller_dispatch_ts": (now - timedelta(minutes=poller.STALL_MINUTES + 5)).isoformat(),
    }

    monkeypatch.setattr(poller, "run_linear_graphql", lambda query, variables=None: {"data": {"issues": {"nodes": [stale_issue]}}})
    monkeypatch.setattr(poller, "_pid_is_running", lambda pid: True)
    monkeypatch.setattr(poller, "transition_issue", lambda issue_id, states: transitions.append((issue_id, tuple(states))) or True)
    monkeypatch.setattr(poller, "linear_comment", lambda issue_id, body: comments.append((issue_id, body)))

    retry_state = {"issues": {}, "processed": {}}
    poller.handle_stalled_issues(retry_state, {"issue-1": active_run})

    assert transitions == []
    assert comments == []
    assert retry_state["issues"] == {}


def test_get_candidate_issues_excludes_registry_owned_issue(monkeypatch):
    issue = _issue()
    monkeypatch.setattr(
        poller,
        "run_linear_graphql",
        lambda query, variables=None: {"data": {"issues": {"nodes": [issue]}}},
    )

    candidates = poller.get_candidate_issues({"issues": {}, "processed": {}}, active_issue_ids={"issue-1"})
    assert candidates == []


def test_reconcile_failed_attempts_reads_distinct_attempt_ledgers(tmp_path, monkeypatch):
    monkeypatch.setattr(poller, "RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(poller, "ATTEMPT_RUNS_DIR", str(tmp_path / "runs" / "attempts"))
    monkeypatch.setattr(poller, "ISSUE_RUNS_DIR", str(tmp_path / "runs" / "issues"))

    attempt_dir = Path(poller.ATTEMPT_RUNS_DIR)
    attempt_dir.mkdir(parents=True, exist_ok=True)
    first = attempt_dir / "ZOC-1--attempt-1.json"
    second = attempt_dir / "ZOC-1--attempt-2.json"
    first.write_text(json.dumps({
        "issue_id": "issue-1",
        "issue_identifier": "ZOC-1",
        "attempt_id": "attempt-1",
        "status": "failed",
        "reason": "agent_failed",
        "ended_at": "2026-04-03T07:00:00+00:00"
    }))
    second.write_text(json.dumps({
        "issue_id": "issue-1",
        "issue_identifier": "ZOC-1",
        "attempt_id": "attempt-2",
        "status": "failed",
        "reason": "clone_failed",
        "ended_at": "2026-04-03T07:05:00+00:00"
    }))

    retry_state = {"issues": {}, "processed": {}}
    poller.reconcile_failed_attempts(retry_state)

    meta = retry_state["issues"]["ZOC-1"]
    assert meta["attempts"] == 2
    assert [entry["attempt_id"] for entry in meta["history"]] == ["attempt-1", "attempt-2"]
    assert {entry["ledger_path"] for entry in meta["history"]} == {str(first), str(second)}
