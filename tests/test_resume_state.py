import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.resume_state import write_resume_state, load_resume_state


def test_write_and_load_resume_state(tmp_path):
    state_dir = tmp_path / "projects/p1/state"
    state = {
        "project_id": "p1",
        "requirements": {"name": "demo", "acceptance_criteria": ["User can create task"]},
        "requirements_revision_count": 1,
        "next_agent": "sdd_specify",
        "extra": "ignore-me",
    }

    path = write_resume_state(str(state_dir), state)
    assert os.path.exists(path)
    data = load_resume_state(str(state_dir))
    assert data["project_id"] == "p1"
    assert data["requirements"]["name"] == "demo"
    assert data["next_agent"] == "sdd_specify"
    assert "extra" not in data
    assert data["snapshot_kind"] == "resume"
