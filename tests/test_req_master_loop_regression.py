import os
import sys

from langchain_core.messages import AIMessage, HumanMessage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers_mod
from src.agents.workers import req_master_interview_node


def test_partial_requirements_do_not_route_to_sdd_specify():
    state = {
        "requirements": {"name": "demo"},
        "messages": [AIMessage(content="prior")],
        "requirements_revision_reasons": ["missing_required_fields"],
        "requirements_revision_count": 0,
    }

    out = req_master_interview_node(state)
    assert out.get("next_agent") == "req_master_interview"
    assert out.get("requirements_interview_status") in {"in_progress", "blocked"}


def test_revision_path_regenerates_only_on_human_message(monkeypatch):
    called = {"v": False}

    def fake_req_master_node(state):
        called["v"] = True
        return {"requirements": {"name": "demo"}}

    monkeypatch.setattr(workers_mod, "req_master_node", fake_req_master_node)

    # last message AI => no regeneration call
    state_ai = {
        "requirements": {"name": "demo"},
        "messages": [AIMessage(content="needs revision")],
        "requirements_revision_reasons": ["missing_required_fields"],
        "requirements_revision_count": 0,
    }
    out_ai = req_master_interview_node(state_ai)
    assert called["v"] is False
    assert out_ai.get("next_agent") == "req_master_interview"
    assert out_ai.get("requirements_revision_count") == 0

    # last message Human => regeneration call attempted
    state_h = {
        "requirements": {"name": "demo"},
        "messages": [HumanMessage(content="here are more details")],
        "requirements_revision_reasons": ["missing_required_fields"],
        "requirements_revision_count": 0,
    }
    _ = req_master_interview_node(state_h)
    assert called["v"] is True
