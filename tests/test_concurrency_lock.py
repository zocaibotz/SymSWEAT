import os
import sys
import fcntl

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.state_store import StateStore, ConcurrencyLockError


def test_project_lock_blocks_competing_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = StateStore(project_id="p-lock", workspace_path="projects/p-lock")
    store.start_run("run-lock")

    lock_path = tmp_path / "projects/p-lock/state/locks/project.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    f = open(lock_path, "a+", encoding="utf-8")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            store.append_event(run_id="run-lock", node="zocai", event_type="node_enter", payload={})
            assert False, "expected lock contention"
        except ConcurrencyLockError:
            pass
    finally:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        f.close()
