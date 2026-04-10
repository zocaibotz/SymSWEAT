import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


class _LinearStub:
    def list_project_issues(self, project_id: str, first: int = 50):
        return {
            "success": True,
            "issues": [
                {"id": "i1", "identifier": "ZOC-901", "priority": 3, "state": {"type": "unstarted"}},
                {"id": "i2", "identifier": "ZOC-900", "priority": 1, "state": {"type": "unstarted"}},
            ],
        }

    def transition_issue(self, identifier: str, to_state_type: str, team_id=None):
        return {"success": True, "identifier": identifier, "to": to_state_type}

    def close_issue(self, identifier: str, team_id=None):
        return {"success": True, "identifier": identifier}

    def comment_issue(self, issue_id: str, body: str):
        return {"success": True}


def test_sprint_executor_happy_path(monkeypatch):
    monkeypatch.setattr(workers, "linear", _LinearStub())
    monkeypatch.setenv("SWEAT_SPRINT_WIP_LIMIT", "1")
    monkeypatch.setenv("SWEAT_SPRINT_MAX_ISSUES_PER_RUN", "2")

    out = workers.sprint_executor_node({"linear_project_id": "p1"})
    assert out["sprint_executor_completed"] is True
    assert out["next_agent"] == "__end__"
    assert out["sprint_execution_log"][0]["identifier"] == "ZOC-900"  # priority-aware
    assert out["sprint_execution_log"][0]["action"] == "started"
    assert out["sprint_execution_log"][1]["action"] == "completed"


def test_sprint_executor_respects_wip_limit(monkeypatch):
    class _WipLinear(_LinearStub):
        def list_project_issues(self, project_id: str, first: int = 50):
            return {
                "success": True,
                "issues": [
                    {"id": "i3", "identifier": "ZOC-999", "priority": 1, "state": {"type": "started"}},
                    {"id": "i2", "identifier": "ZOC-900", "priority": 1, "state": {"type": "unstarted"}},
                ],
            }

    monkeypatch.setattr(workers, "linear", _WipLinear())
    monkeypatch.setenv("SWEAT_SPRINT_WIP_LIMIT", "1")
    out = workers.sprint_executor_node({"linear_project_id": "p1"})
    assert out["sprint_execution_log"] == []
    assert "WIP limit reached" in out["messages"][0].content
