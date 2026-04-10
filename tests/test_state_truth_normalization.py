import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.state_store import StateStore


def test_snapshot_normalizes_ci_and_deploy_truth(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = StateStore(project_id="p-truth", workspace_path="projects/p-truth")
    store.start_run("run_truth")

    store.write_snapshot(
        {
            "ci_pipeline_status": "PASSED",
            "deployment_url": "pending",
            "design_approval_status": "approved",
            "test_readiness_status": "ready",
        },
        run_id="run_truth",
    )

    snap = json.loads((tmp_path / "projects/p-truth/state/project_state.json").read_text())
    assert snap["gates"]["ci_passed"] is True
    assert snap["gates"]["deployment_approved"] is False
