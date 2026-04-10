import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.state_store import StateStore, VersionConflictError


def test_append_only_event_log_and_idempotency(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = StateStore(project_id="p1", workspace_path="projects/p1")
    run_id = "run_test_1"

    store.start_run(run_id)
    a = store.append_event(
        run_id=run_id,
        node="zocai",
        event_type="node_enter",
        payload={"x": 1},
        idempotency_key="k1",
    )
    b = store.append_event(
        run_id=run_id,
        node="zocai",
        event_type="node_enter",
        payload={"x": 1},
        idempotency_key="k1",
    )

    assert a.get("deduped") is False
    assert b.get("deduped") is True

    events_path = tmp_path / "projects/p1/state/run_events.jsonl"
    lines = events_path.read_text(encoding="utf-8").strip().splitlines()
    # run_start + one node_enter
    assert len(lines) == 2


def test_end_run_does_not_downgrade_failed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = StateStore(project_id="p3", workspace_path="projects/p3")
    run_id = "run_test_3"
    store.start_run(run_id)
    store.end_run(run_id, status="failed")
    store.end_run(run_id, status="completed")

    idx = store.load_index()
    assert idx["runs"][run_id]["status"] == "failed"

    events = (tmp_path / "projects/p3/state/run_events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    last = json.loads(events[-1])
    assert last["event_type"] == "run_end"
    assert last["payload"]["status"] == "failed"


def test_snapshot_version_conflict(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = StateStore(project_id="p2", workspace_path="projects/p2")
    run_id = "run_test_2"
    store.start_run(run_id)

    r1 = store.write_snapshot({"next_agent": "req_master"}, run_id=run_id)
    assert r1["state_version"] == 1

    try:
        store.write_snapshot({"next_agent": "architect"}, run_id=run_id, expected_version=0)
        assert False, "expected VersionConflictError"
    except VersionConflictError:
        pass

    r2 = store.write_snapshot({"next_agent": "architect"}, run_id=run_id, expected_version=1)
    assert r2["state_version"] == 2

    snap = json.loads((tmp_path / "projects/p2/state/project_state.json").read_text(encoding="utf-8"))
    assert snap["state_version"] == 2
