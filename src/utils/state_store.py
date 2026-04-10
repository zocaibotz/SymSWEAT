import json
import os
import time
import uuid
import fcntl
from contextlib import contextmanager
from typing import Any, Dict, Optional


class VersionConflictError(Exception):
    pass


class ConcurrencyLockError(Exception):
    pass


class StateStore:
    """Durable state/event persistence for SWEAT runs.

    Files (per project workspace):
    - state/project_state.json
    - state/run_events.jsonl (append-only)
    - state/run_index.json
    """

    SCHEMA_VERSION = "1.0.0"

    def __init__(self, project_id: str, workspace_path: Optional[str] = None):
        self.project_id = (project_id or "unknown").strip() or "unknown"
        self.workspace_path = workspace_path or os.path.join("projects", self.project_id)
        self.state_dir = os.path.join(self.workspace_path, "state")
        self.events_path = os.path.join(self.state_dir, "run_events.jsonl")
        self.index_path = os.path.join(self.state_dir, "run_index.json")
        self.snapshot_path = os.path.join(self.state_dir, "project_state.json")
        self.locks_dir = os.path.join(self.state_dir, "locks")
        self.project_lock_path = os.path.join(self.locks_dir, "project.lock")
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.locks_dir, exist_ok=True)

    @staticmethod
    def new_run_id() -> str:
        return f"run_{time.strftime('%Y-%m-%dT%H-%M-%SZ', time.gmtime())}_{uuid.uuid4().hex[:6]}"

    def _read_json(self, path: str, default: Dict[str, Any]) -> Dict[str, Any]:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else default
        except Exception:
            return default

    def _write_json_atomic(self, path: str, data: Dict[str, Any]) -> None:
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    @contextmanager
    def _project_lock(self):
        f = open(self.project_lock_path, "a+", encoding="utf-8")
        try:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ConcurrencyLockError("project lock is already held")
            f.seek(0)
            f.truncate()
            f.write(str(os.getpid()))
            f.flush()
            yield
        finally:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            f.close()

    def load_index(self) -> Dict[str, Any]:
        return self._read_json(self.index_path, {
            "schema_version": self.SCHEMA_VERSION,
            "project_id": self.project_id,
            "runs": {},
            "latest_run_id": None,
            "updated_at_utc": None,
        })

    def save_index(self, index: Dict[str, Any]) -> None:
        self._write_json_atomic(self.index_path, index)

    def start_run(self, run_id: str) -> None:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        index = self.load_index()
        index.setdefault("runs", {})
        index["runs"][run_id] = {
            "status": "running",
            "started_at_utc": now,
            "ended_at_utc": None,
            "last_seq": 0,
            "last_event_id": None,
            "last_node": None,
            "idempotency_keys": {},
        }
        index["latest_run_id"] = run_id
        index["updated_at_utc"] = now
        self.save_index(index)
        self.append_event(run_id=run_id, node="zocai", event_type="run_start", payload={"status": "running"})

    def end_run(self, run_id: str, status: str = "completed") -> None:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        precedence = {"running": 0, "completed": 1, "blocked": 2, "failed": 3}

        # Compute effective terminal state first so run_end event and stored state agree.
        index0 = self.load_index()
        run0 = index0.get("runs", {}).get(run_id) if isinstance(index0, dict) else None
        current = str((run0 or {}).get("status") or "running")
        target = str(status or "completed")
        effective = target if precedence.get(target, 0) >= precedence.get(current, 0) else current

        self.append_event(run_id=run_id, node="zocai", event_type="run_end", payload={"status": effective})

        with self._project_lock():
            index = self.load_index()
            run = index.get("runs", {}).get(run_id)
            if isinstance(run, dict):
                run["status"] = effective
                run["ended_at_utc"] = now
                index["updated_at_utc"] = now
                self.save_index(index)

    def append_event(
        self,
        *,
        run_id: str,
        node: str,
        event_type: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._project_lock():
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            index = self.load_index()
            run = index.setdefault("runs", {}).setdefault(run_id, {
                "status": "running",
                "started_at_utc": now,
                "ended_at_utc": None,
                "last_seq": 0,
                "last_event_id": None,
                "last_node": None,
                "idempotency_keys": {},
            })

            if idempotency_key:
                keys = run.setdefault("idempotency_keys", {})
                existing = keys.get(idempotency_key)
                if existing:
                    return {"success": True, "deduped": True, "event_id": existing}

            seq = int(run.get("last_seq") or 0) + 1
            event_id = f"evt_{seq:06d}_{uuid.uuid4().hex[:4]}"
            event = {
                "schema_version": self.SCHEMA_VERSION,
                "event_id": event_id,
                "run_id": run_id,
                "project_id": self.project_id,
                "ts_utc": now,
                "node": node,
                "event_type": event_type,
                "seq": seq,
                "payload": payload or {},
            }
            with open(self.events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

            run["last_seq"] = seq
            run["last_event_id"] = event_id
            run["last_node"] = node
            if idempotency_key:
                run.setdefault("idempotency_keys", {})[idempotency_key] = event_id
            index["latest_run_id"] = run_id
            index["updated_at_utc"] = now
            self.save_index(index)
            return {"success": True, "event_id": event_id, "deduped": False}

    def write_snapshot(self, state: Dict[str, Any], run_id: str, expected_version: Optional[int] = None) -> Dict[str, Any]:
        with self._project_lock():
            existing = self._read_json(self.snapshot_path, {})
            current_version = int(existing.get("state_version") or 0)

            if expected_version is not None and expected_version != current_version:
                raise VersionConflictError(f"expected version {expected_version} but current is {current_version}")

            next_version = current_version + 1
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            req = state.get("requirements") if isinstance(state.get("requirements"), dict) else {}
            ci_status = str(state.get("ci_pipeline_status") or "").strip().lower()
            deploy_url = str(state.get("deployment_url") or "").strip()
            deployment_approved = bool(deploy_url) and deploy_url.lower() not in {"pending", "n/a", "none", "null"}

            snapshot = {
                "schema_version": self.SCHEMA_VERSION,
                "state_version": next_version,
                "project_id": self.project_id,
                "project_slug": (req.get("project_name") or self.project_id).lower().replace(" ", "-"),
                "lifecycle": {
                    "phase": state.get("next_agent") or state.get("last_agent") or "unknown",
                    "status": "in_progress",
                    "current_run_id": run_id,
                    "last_updated_utc": now,
                },
                "gates": {
                    "design_approved": state.get("design_approval_status") == "approved",
                    "tdd_ready": state.get("test_readiness_status") == "ready",
                    "ci_passed": ci_status in {"passed", "pass", "success", "succeeded"},
                    "deployment_approved": deployment_approved,
                },
                "artifacts": {
                    "spec": state.get("sdd_spec_path"),
                    "plan": state.get("sdd_plan_path"),
                    "tasks": state.get("sdd_tasks_path"),
                    "architecture": "docs/SWEAT_ARCHITECTURE_AS_BUILT.md",
                    "unit_tests_plan": state.get("unit_test_plan_path"),
                    "integration_tests_plan": state.get("integration_test_plan_path"),
                    "playwright_tests_plan": state.get("playwright_test_plan_path"),
                    "run_report": state.get("run_report_path"),
                },
                "integrations": {
                    "linear": {
                        "project_id": state.get("linear_project_id"),
                        "project_url": state.get("linear_project_url"),
                    },
                    "ci": {
                        "provider": "github_actions",
                        "last_result": state.get("ci_pipeline_status"),
                    },
                    "automation": {
                        "status": "completed" if state.get("automation_completed") else "pending",
                    },
                },
                "memory": {
                    "last_agent": state.get("last_agent"),
                    "last_20_run_ids": [run_id],
                },
            }
            self._write_json_atomic(self.snapshot_path, snapshot)
            return {"success": True, "state_version": next_version, "path": self.snapshot_path}
