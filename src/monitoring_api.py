from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ACTIVE_WINDOW_SECONDS = 7 * 24 * 60 * 60
UI_AUTH_COOKIE = "sweat_ui_auth"
UI_AUTH_SALT = "sweat-monitor-ui-v1"

from pydantic import BaseModel
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse

from src.utils.state_store import StateStore

PROJECTS_ROOT = Path("projects")
PIPELINE_STAGES = [
    "requirement_master",
    "specify",
    "plan",
    "tasks",
    "architect",
    "pixel",
    "frontman",
    "code_smith",
    "review",
    "ci_deploy_automator",
]
NODE_TO_STAGE = {
    "zocai": "requirement_master",
    "req_master": "requirement_master",
    "req_master_interview": "requirement_master",
    "sdd_specify": "specify",
    "sdd_plan": "plan",
    "sdd_tasks": "tasks",
    "architect": "architect",
    "pixel": "pixel",
    "frontman": "frontman",
    "design_approval_gate": "frontman",
    "tdd_orchestrator": "code_smith",
    "unit_test_author": "code_smith",
    "integration_test_author": "code_smith",
    "playwright_test_author": "code_smith",
    "test_readiness_gate": "code_smith",
    "github_bootstrap": "code_smith",
    "codesmith": "code_smith",
    "bughunter": "review",
    "gatekeeper": "review",
    "pipeline": "ci_deploy_automator",
    "integrator": "ci_deploy_automator",
    "deployer": "ci_deploy_automator",
    "automator": "ci_deploy_automator",
    "scrumlord": "ci_deploy_automator",
    "sprint_executor": "ci_deploy_automator",
}

class NewProjectRequest(BaseModel):
    prompt: str
    project_id: Optional[str] = None


def _get_users() -> Dict[str, str]:
    users_env = os.getenv("SWEAT_USERS", "admin:change-me")
    users = {}
    for pair in users_env.split(","):
        if ":" in pair:
            u, p = pair.split(":", 1)
            users[u.strip()] = p.strip()
    return users


def _skip_auth() -> bool:
    """Return True when running under pytest's TestClient (no actual HTTP transport)."""
    return os.getenv("TESTING", "").lower() in ("1", "true", "yes")


def _create_auth_cookie(username: str) -> str:
    import base64
    return base64.b64encode(f"{username}:{UI_AUTH_SALT}".encode("utf-8")).decode("utf-8")


def _get_authenticated_user(request: Request) -> Optional[str]:
    cookie = request.cookies.get(UI_AUTH_COOKIE)
    if not cookie:
        return None
    import base64
    try:
        decoded = base64.b64decode(cookie).decode("utf-8")
        if decoded.endswith(f":{UI_AUTH_SALT}"):
            return decoded.split(":")[0]
    except Exception:
        pass
    return None


def _is_authenticated(request: Request) -> bool:
    return _get_authenticated_user(request) is not None


def _require_auth(request: Request) -> str:
    if _skip_auth():
        return "testuser"
    user = _get_authenticated_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def _json_load(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _project_dirs() -> List[Path]:
    if not PROJECTS_ROOT.exists():
        return []
    return sorted([p for p in PROJECTS_ROOT.iterdir() if p.is_dir()])


def _normalize_stage(raw: Optional[str]) -> str:
    return NODE_TO_STAGE.get((raw or "").strip(), "requirement_master")


def _project_paths(project_id: str, create: bool = False) -> Dict[str, Path]:
    root = PROJECTS_ROOT / project_id
    if not root.exists() or not root.is_dir():
        if create:
            root.mkdir(parents=True, exist_ok=True)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown project: {project_id}")
    state_dir = root / "state"
    if create:
        state_dir.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "state": state_dir,
        "state_file": state_dir / "project_state.json",
        "run_index": state_dir / "run_index.json",
        "run_events": state_dir / "run_events.jsonl",
        "resume": state_dir / "resume_state.json",
        "answers": state_dir / "req_master_answers.jsonl",
        "meta": state_dir / "project_meta.json",
    }


def _load_project_meta(project_id: str) -> Dict[str, Any]:
    return _json_load(_project_paths(project_id)["meta"], {})


def _save_project_meta(project_id: str, meta: Dict[str, Any]) -> None:
    _json_write(_project_paths(project_id)["meta"], meta)


def _parse_utc(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


def _is_active(latest_status: str, last_updated_utc: Optional[str]) -> bool:
    if latest_status not in {"running", "in_progress"}:
        return False
    last_ts = _parse_utc(last_updated_utc)
    if last_ts is None:
        return False
    return (datetime.now(timezone.utc) - last_ts).total_seconds() <= ACTIVE_WINDOW_SECONDS


def _collect_artifacts(root: Path, state_doc: Dict[str, Any], events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    artifacts: Dict[str, Dict[str, Any]] = {}

    def add_artifact(key: str, path_or_url: Any, source: str) -> None:
        if not path_or_url:
            return
        value = str(path_or_url).strip()
        if not value:
            return
        entry = artifacts.get(key, {"key": key, "source": source})
        entry["path"] = value
        entry["source"] = source
        if value.startswith("http://") or value.startswith("https://"):
            entry["kind"] = "url"
            entry["exists"] = True
        else:
            p = Path(value)
            if not p.is_absolute():
                p = Path.cwd() / p
            entry["kind"] = "file"
            entry["exists"] = p.exists()
        artifacts[key] = entry

    for key, value in (state_doc.get("artifacts") or {}).items():
        add_artifact(key, value, "state_snapshot")

    default_candidates = {
        "spec": root / "docs/spec/spec.md",
        "plan": root / "docs/spec/plan.md",
        "tasks": root / "docs/spec/tasks.md",
        "architecture": root / "docs/design/design.md",
        "ux_wireframes": root / "docs/ux/wireframes.md",
        "ui_handoff": root / "docs/ui/handoff_contract.json",
        "unit_test_plan": root / "docs/tests/unit_test_plan.md",
        "integration_test_plan": root / "docs/tests/integration_test_plan.md",
        "playwright_test_plan": root / "docs/tests/playwright_test_plan.md",
    }
    for key, path in default_candidates.items():
        if path.exists():
            add_artifact(key, str(path), "convention_scan")

    for event in events[-200:]:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        for key, value in payload.items():
            skey = str(key)
            if skey.endswith("_path") or skey.endswith("_url"):
                add_artifact(f"event:{event.get('event_id', 'unknown')}:{skey}", value, f"event:{event.get('event_type')}")

    return sorted(artifacts.values(), key=lambda x: x.get("key", ""))


def _extract_blockers(run_index: Dict[str, Any], events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blockers: List[Dict[str, Any]] = []
    runs = run_index.get("runs") if isinstance(run_index.get("runs"), dict) else {}
    for run_id, run in runs.items():
        status = str((run or {}).get("status") or "").lower()
        if status in {"failed", "blocked"}:
            blockers.append({
                "kind": "run_status",
                "run_id": run_id,
                "status": status,
                "ended_at_utc": run.get("ended_at_utc"),
            })

    for event in events[-300:]:
        if event.get("event_type") in {"validation_error", "retry_scheduled"}:
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            blockers.append({
                "kind": event.get("event_type"),
                "event_id": event.get("event_id"),
                "run_id": event.get("run_id"),
                "node": event.get("node"),
                "ts_utc": event.get("ts_utc"),
                "detail": payload.get("error") or payload.get("kind") or payload,
            })

    return blockers[-25:]


def _compute_kpis(state_doc: Dict[str, Any], run_index: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
    runs = run_index.get("runs") if isinstance(run_index.get("runs"), dict) else {}
    counts = {"running": 0, "completed": 0, "failed": 0, "blocked": 0}
    for run in runs.values():
        status = str((run or {}).get("status") or "running").lower()
        if status in counts:
            counts[status] += 1

    gate_doc = state_doc.get("gates") if isinstance(state_doc.get("gates"), dict) else {}
    gate_passed = sum(1 for _, v in gate_doc.items() if bool(v))

    latest_event_ts = events[-1].get("ts_utc") if events else None
    return {
        "runs_total": len(runs),
        "runs_running": counts["running"],
        "runs_completed": counts["completed"],
        "runs_failed": counts["failed"],
        "runs_blocked": counts["blocked"],
        "events_total": len(events),
        "gates_passed": gate_passed,
        "gates_total": len(gate_doc),
        "last_event_at_utc": latest_event_ts,
    }


def _latest_route_stage(events: List[Dict[str, Any]], fallback: str) -> str:
    for event in reversed(events):
        if event.get("event_type") == "route_decision":
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            next_node = payload.get("next_node")
            if next_node and next_node != "__end__":
                return _normalize_stage(str(next_node))
        node = event.get("node")
        if node and node != "__end__":
            return _normalize_stage(str(node))
    return fallback


def _project_summary(project_id: str) -> Dict[str, Any]:
    paths = _project_paths(project_id)
    state_doc = _json_load(paths["state_file"], {})
    run_index = _json_load(paths["run_index"], {})
    events = _read_jsonl(paths["run_events"])

    lifecycle = state_doc.get("lifecycle") if isinstance(state_doc.get("lifecycle"), dict) else {}
    phase = lifecycle.get("phase")
    current_stage = _normalize_stage(phase) if phase and phase != "__end__" else None
    if not current_stage:
        current_stage = _latest_route_stage(events, "requirement_master")

    runs = run_index.get("runs") if isinstance(run_index.get("runs"), dict) else {}
    latest_run_id = run_index.get("latest_run_id") or lifecycle.get("current_run_id")
    latest_run = runs.get(latest_run_id) if isinstance(runs, dict) else None
    latest_status = str((latest_run or {}).get("status") or lifecycle.get("status") or "unknown").lower()
    interview = _interview_view(project_id)
    meta = _load_project_meta(project_id)

    last_updated_utc = lifecycle.get("last_updated_utc") or (events[-1].get("ts_utc") if events else None)
    completed = current_stage == PIPELINE_STAGES[-1] and latest_status in {"completed", "success"}
    active = _is_active(latest_status, last_updated_utc)
    
    if interview.get("status") == "awaiting_human":
        active = True
        latest_status = "awaiting_human"
        
    lifecycle_bucket = "active" if active else "archived"

    return {
        "project_id": project_id,
        "project_slug": state_doc.get("project_slug") or project_id,
        "display_name": (state_doc.get("project_slug") or project_id).replace("-", " ").title(),
        "status": "completed" if completed else ("in_progress" if active else "archived"),
        "latest_run_id": latest_run_id,
        "latest_run_status": latest_status,
        "current_stage": current_stage,
        "lifecycle_bucket": lifecycle_bucket,
        "archived": bool(meta.get("archived")),
        "stage_order": PIPELINE_STAGES,
        "last_updated_utc": last_updated_utc,
        "kpis": _compute_kpis(state_doc, run_index, events),
        "blockers": _extract_blockers(run_index, events),
    }


def _interview_view(project_id: str) -> Dict[str, Any]:
    paths = _project_paths(project_id)
    resume = _json_load(paths["resume"], {})
    answers = _read_jsonl(paths["answers"])

    answered_questions = {str(r.get("question") or "").strip() for r in answers if r.get("question")}

    open_questions = resume.get("requirements_open_questions") or []
    asked_questions = resume.get("requirements_questions_asked") or []
    base_questions = [q for q in open_questions if isinstance(q, str)]
    if not base_questions:
        base_questions = [q for q in asked_questions if isinstance(q, str)]

    pending = [q for q in base_questions if q.strip() and q.strip() not in answered_questions]
    return {
        "project_id": project_id,
        "status": resume.get("requirements_interview_status") or "unknown",
        "pending_questions": pending,
        "answered_count": len(answers),
        "answers": answers[-30:],
    }


def _timeline(events: List[Dict[str, Any]], limit: int = 150) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for event in events[-limit:]:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        out.append({
            "event_id": event.get("event_id"),
            "ts_utc": event.get("ts_utc"),
            "run_id": event.get("run_id"),
            "node": event.get("node"),
            "event_type": event.get("event_type"),
            "summary": payload.get("error") or payload.get("kind") or payload.get("status") or payload.get("next_node") or "event",
            "payload": payload,
        })
    return out


def _project_details(project_id: str) -> Dict[str, Any]:
    paths = _project_paths(project_id)
    state_doc = _json_load(paths["state_file"], {})
    run_index = _json_load(paths["run_index"], {})
    events = _read_jsonl(paths["run_events"])
    summary = _project_summary(project_id)
    interview = _interview_view(project_id)

    current_stage = summary["current_stage"]
    stage_index = PIPELINE_STAGES.index(current_stage)

    stage_progress = []
    for idx, stage in enumerate(PIPELINE_STAGES):
        status = "pending"
        if idx < stage_index:
            status = "completed"
        elif idx == stage_index:
            status = "active"
        stage_progress.append({"stage": stage, "status": status})

    artifacts = _collect_artifacts(paths["root"], state_doc, events)

    stage_events = [e for e in events if _normalize_stage(str(e.get("node"))) == current_stage]
    stage_details = {
        "stage": current_stage,
        "latest_event": stage_events[-1] if stage_events else None,
        "event_count": len(stage_events),
        "interview": interview if current_stage == "requirement_master" else None,
    }

    return {
        "summary": summary,
        "project_state": state_doc,
        "run_index": run_index,
        "pipeline": stage_progress,
        "stage_details": stage_details,
        "timeline": _timeline(events, limit=250),
        "artifacts": artifacts,
        "interview": interview,
    }


def _run_project_background(prompt: str, project_id: str):
    try:
        from src.main import build_graph
        from langchain_core.messages import HumanMessage
        graph = build_graph()
        initial_state = {
            "messages": [HumanMessage(content=prompt)],
            "project_id": project_id,
            "next_agent": "req_master"
        }
        for _ in graph.stream(initial_state):
            pass
    except Exception as e:
        print(f"Background run failed for {project_id}: {e}")


def create_app() -> FastAPI:
    app = FastAPI(title="SWEAT Monitoring API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/ui")
    def ui(request: Request):
        if not _is_authenticated(request):
            return HTMLResponse(
                """
                <!doctype html><html><body style='font-family:Arial;background:#0a1120;color:#e7eefb;padding:40px'>
                <h2>SWEAT Command Center Login</h2>
                <form method='post' action='/ui/login'>
                  <input type='text' name='username' placeholder='Username' style='padding:10px;border-radius:8px;border:1px solid #31476a;background:#16233b;color:#e7eefb;margin-bottom:8px;display:block;' />
                  <input type='password' name='password' placeholder='Password' style='padding:10px;border-radius:8px;border:1px solid #31476a;background:#16233b;color:#e7eefb;margin-bottom:8px;display:block;' />
                  <button type='submit' style='padding:10px 14px;border:0;border-radius:8px;background:#5ea3ff;color:white;display:block;'>Enter</button>
                </form>
                </body></html>
                """
            )
        return FileResponse(Path(__file__).with_name("monitoring_ui.html"))

    @app.get("/ui/project/{project_id}")
    def ui_project(project_id: str, request: Request):
        _project_paths(project_id)
        if not _is_authenticated(request):
            return RedirectResponse(url="/ui", status_code=303)
        return FileResponse(Path(__file__).with_name("monitoring_ui.html"))

    @app.post("/ui/login")
    def ui_login(username: str = Form(...), password: str = Form(...)):
        users = _get_users()
        print(f"[LOGIN ATTEMPT] username: '{username}', password: '{password}'")
        username = username.strip()
        password = password.strip()
        if users.get(username) != password:
            print(f"[LOGIN FAILED] expected: '{users.get(username)}', got: '{password}'")
            return HTMLResponse("Invalid username or password", status_code=401)
        print(f"[LOGIN SUCCESS] username: '{username}'")
        response = RedirectResponse(url="/ui", status_code=303)
        response.set_cookie(UI_AUTH_COOKIE, _create_auth_cookie(username), httponly=True, samesite="lax", path="/")
        return response

    @app.post("/ui/logout")
    def ui_logout():
        response = RedirectResponse(url="/ui", status_code=303)
        response.delete_cookie(UI_AUTH_COOKIE, path="/")
        return response

    @app.post("/api/monitoring/projects/new")
    def new_project(payload: NewProjectRequest, request: Request) -> Dict[str, Any]:
        username = _require_auth(request)
        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
            
        project_id = payload.project_id
        if not project_id or not project_id.strip():
            project_id = f"proj-{uuid.uuid4().hex[:8]}"
            
        # Pre-create the directory so it shows up in UI immediately
        paths = _project_paths(project_id, create=True)
        
        threading.Thread(target=_run_project_background, args=(prompt, project_id), daemon=True).start()
        return {"ok": True, "project_id": project_id}

    @app.get("/api/monitoring/projects")
    def list_projects(request: Request) -> Dict[str, Any]:
        _require_auth(request)
        rows = []
        for path in _project_dirs():
            try:
                rows.append(_project_summary(path.name))
            except Exception:
                continue
        in_progress = [r for r in rows if r.get("status") == "in_progress"]
        completed = [r for r in rows if r.get("status") == "completed"]
        active = [r for r in rows if r.get("lifecycle_bucket") == "active"]
        idle = [r for r in rows if r.get("lifecycle_bucket") == "idle"]
        archived = [r for r in rows if r.get("lifecycle_bucket") == "archived"]
        return {
            "projects": rows,
            "in_progress_count": len(in_progress),
            "completed_count": len(completed),
            "active_count": len(active),
            "idle_count": len(idle),
            "archived_count": len(archived),
            "total_count": len(rows),
        }

    @app.get("/api/monitoring/projects/{project_id}")
    def project_details(project_id: str, request: Request) -> Dict[str, Any]:
        _require_auth(request)
        return _project_details(project_id)

    @app.post("/api/monitoring/projects/{project_id}/archive")
    def archive_project(project_id: str, request: Request) -> Dict[str, Any]:
        _require_auth(request)
        meta = _load_project_meta(project_id)
        meta["archived"] = True
        meta["archived_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _save_project_meta(project_id, meta)
        return {"ok": True, "project_id": project_id, "archived": True}

    @app.post("/api/monitoring/projects/{project_id}/unarchive")
    def unarchive_project(project_id: str, request: Request) -> Dict[str, Any]:
        _require_auth(request)
        meta = _load_project_meta(project_id)
        meta["archived"] = False
        meta["unarchived_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _save_project_meta(project_id, meta)
        return {"ok": True, "project_id": project_id, "archived": False}

    @app.get("/api/monitoring/projects/{project_id}/events")
    def project_events(project_id: str, request: Request, limit: int = Query(default=200, ge=1, le=2000)) -> Dict[str, Any]:
        _require_auth(request)
        paths = _project_paths(project_id)
        events = _read_jsonl(paths["run_events"])
        return {"project_id": project_id, "events": _timeline(events, limit=limit)}

    @app.get("/api/monitoring/projects/{project_id}/interview")
    def interview(project_id: str, request: Request) -> Dict[str, Any]:
        _require_auth(request)
        return _interview_view(project_id)

    @app.post("/api/monitoring/projects/{project_id}/interview/answer")
    def submit_interview_answer(project_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
        _require_auth(request)
        question = str(payload.get("question") or "").strip()
        answer = str(payload.get("answer") or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="question is required")
        if not answer:
            raise HTTPException(status_code=400, detail="answer is required")

        paths = _project_paths(project_id)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        entry = {
            "question": question,
            "answer": answer,
            "answered_at_utc": now,
            "author": _require_auth(request),
        }
        paths["answers"].parent.mkdir(parents=True, exist_ok=True)
        with paths["answers"].open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        resume = _json_load(paths["resume"], {})
        open_questions = [q for q in (resume.get("requirements_open_questions") or []) if isinstance(q, str)]
        open_questions = [q for q in open_questions if q.strip() != question]
        resume["requirements_open_questions"] = open_questions
        if open_questions:
            resume["requirements_interview_status"] = "in_progress"
        else:
            resume["requirements_interview_status"] = "complete"
        _json_write(paths["resume"], resume)

        state_doc = _json_load(paths["state_file"], {})
        run_id = (
            (state_doc.get("lifecycle") or {}).get("current_run_id")
            or f"ui_interview_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
        )
        store = StateStore(project_id=project_id, workspace_path=str(paths["root"]))
        store.append_event(
            run_id=run_id,
            node="req_master_interview",
            event_type="integration_call",
            payload={
                "integration": "ui_interview",
                "action": "answer_recorded",
                "question": question,
                "answered_at_utc": now,
            },
        )

        return {"ok": True, "entry": entry, "pending_questions": open_questions}

    @app.get("/api/monitoring/projects/{project_id}/artifacts/{artifact_key}")
    def artifact_view(project_id: str, artifact_key: str, request: Request) -> Dict[str, Any]:
        _require_auth(request)
        details = _project_details(project_id)
        artifact = next((a for a in details["artifacts"] if a.get("key") == artifact_key), None)
        if not artifact:
            raise HTTPException(status_code=404, detail=f"Unknown artifact: {artifact_key}")

        if artifact.get("kind") == "url":
            return {"artifact": artifact, "preview": None}

        path_value = str(artifact.get("path") or "")
        p = Path(path_value)
        if not p.is_absolute():
            p = Path.cwd() / p

        project_root = (PROJECTS_ROOT / project_id).resolve()
        try:
            resolved = p.resolve()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid artifact path: {e}")

        if not (str(resolved).startswith(str(project_root)) or str(resolved).startswith(str(Path.cwd().resolve()))):
            raise HTTPException(status_code=403, detail="Artifact path is outside allowed roots")

        if not resolved.exists():
            return {"artifact": artifact, "preview": None}

        text_preview = None
        if resolved.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".jsx", ".tsx", ".js"}:
            try:
                text_preview = resolved.read_text(encoding="utf-8")[:12000]
            except Exception:
                text_preview = None

        return {
            "artifact": artifact,
            "resolved_path": str(resolved),
            "preview": text_preview,
            "size_bytes": resolved.stat().st_size,
        }

    @app.get("/api/monitoring/stream")
    async def stream(
        request: Request,
        project_id: Optional[str] = Query(default=None),
        heartbeat_seconds: int = Query(default=8, ge=2, le=60),
        max_events: Optional[int] = Query(default=None, ge=1, le=10000),
    ):
        _require_auth(request)
        target_projects = [project_id] if project_id else [p.name for p in _project_dirs()]
        offsets: Dict[str, int] = {}

        async def event_gen() -> Iterable[str]:
            emitted = 0
            snapshot = {"projects": [_project_summary(pid) for pid in target_projects if (PROJECTS_ROOT / pid).exists()]}
            yield f"event: snapshot\ndata: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
            emitted += 1
            while not await request.is_disconnected():
                if max_events is not None and emitted >= max_events:
                    break
                sent = False
                for pid in target_projects:
                    try:
                        paths = _project_paths(pid)
                    except HTTPException:
                        continue
                    fpath = paths["run_events"]
                    if not fpath.exists():
                        continue

                    key = str(fpath)
                    current_size = fpath.stat().st_size
                    offset = offsets.get(key, 0)
                    if current_size < offset:
                        offset = 0

                    with fpath.open("r", encoding="utf-8") as f:
                        f.seek(offset)
                        chunk = f.read()
                        offsets[key] = f.tell()

                    if not chunk:
                        continue
                    for line in chunk.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except Exception:
                            continue
                        wrapped = {
                            "project_id": pid,
                            "event": event,
                            "current_stage": _normalize_stage(str(event.get("node"))),
                        }
                        sent = True
                        yield f"event: run_event\ndata: {json.dumps(wrapped, ensure_ascii=False)}\n\n"
                        emitted += 1
                        if max_events is not None and emitted >= max_events:
                            break

                if max_events is not None and emitted >= max_events:
                    break

                if not sent:
                    yield f"event: heartbeat\ndata: {json.dumps({'ts_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})}\n\n"
                    emitted += 1
                await asyncio.sleep(heartbeat_seconds)

        return StreamingResponse(
            event_gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return app


app = create_app()