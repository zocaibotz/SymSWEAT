import json
import os
from typing import Dict, Any, Optional


RESUME_KEYS = {
    "project_id",
    "project_workspace_path",
    "requirements",
    "requirements_interview_status",
    "requirements_open_questions",
    "requirements_questions_asked",
    "requirements_revision_reasons",
    "requirements_revision_count",
    "next_agent",
    "last_agent",
    "run_id",
    "run_started",
    "project_state_version",
}


def write_resume_state(state_dir: str, state: Dict[str, Any]) -> str:
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, "resume_state.json")
    data = {k: state.get(k) for k in RESUME_KEYS if k in state}
    data["snapshot_kind"] = "resume"
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def load_resume_state(state_dir: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(state_dir, "resume_state.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            x = json.load(f)
        return x if isinstance(x, dict) else None
    except Exception:
        return None
