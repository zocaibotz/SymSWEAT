import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_community.chat_models import FakeListChatModel
import src.agents.workers as workers


class _LinearStub:
    def __init__(self):
        self.created_project = None

    def create_or_get_project(self, name, description="", team_id=None):
        self.created_project = {"id": "p-1", "name": name, "url": "https://linear.app/project/p-1"}
        return {"success": True, "created": True, "project": self.created_project}

    def create_issue(self, title, description, priority=0, project_id=None):
        ident = "ZOC-100" if "Task A" in title else "ZOC-101"
        return {
            "success": True,
            "issue": {
                "identifier": ident,
                "title": title,
                "url": f"https://linear.app/zocai/issue/{ident}/x",
            },
        }

    def transition_issue(self, identifier, to_state_type):
        return {"success": True, "identifier": identifier, "to": to_state_type}

    def assign_issue_by_identifier(self, identifier, assignee_id):
        return {"success": True, "identifier": identifier, "assignee_id": assignee_id}

    def close_issue(self, identifier):
        return {"success": True, "identifier": identifier, "closed": True}


def test_scrumlord_creates_and_syncs_updates(monkeypatch):
    workers.llm = FakeListChatModel(
        responses=['[{"title":"Task A","description":"d1","priority":1},{"title":"Task B","description":"d2","priority":2}]']
    )
    stub = _LinearStub()
    monkeypatch.setattr(workers, "linear", stub)

    state = {
        "requirements": {"goal": "demo"},
        "architecture_docs": "simple",
        "should_create_linear_project": True,
        "linear_project_name": "Zocai-test-auto",
        "scrum_updates": [
            {"identifier": "ZOC-100", "transition_to": "started"},
            {"identifier": "ZOC-101", "assignee_id": "user-1", "close": True},
        ],
    }

    out = workers.scrumlord_node(state)

    assert out["next_agent"] == "__end__"
    assert len(out["sprint_backlog"]) == 2
    assert len(out["scrum_sync_updates"]) == 2
    assert out["scrum_sync_updates"][0]["actions"][0]["type"] == "transition"
    assert out["scrum_sync_updates"][1]["actions"][0]["type"] == "assign"
    assert out["scrum_sync_updates"][1]["actions"][1]["type"] == "close"
    assert out["linear_project_id"] == "p-1"
    assert out["linear_project_created"] is True
    assert stub.created_project["name"] == "Zocai-test-auto"
