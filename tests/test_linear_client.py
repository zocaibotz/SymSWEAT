import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.linear import LinearClient


def test_transition_issue_happy_path(monkeypatch):
    c = LinearClient(api_key="x")

    def fake_query(query, variables=None):
        if "query IssueByNumber" in query:
            return {"data": {"issues": {"nodes": [{"id": "issue-1", "identifier": "ZOC-1"}]}}}
        if "query TeamStates" in query:
            return {
                "data": {
                    "team": {
                        "states": {
                            "nodes": [
                                {"id": "s-start", "type": "started", "name": "In Progress"},
                                {"id": "s-done", "type": "completed", "name": "Done"},
                            ]
                        }
                    }
                }
            }
        if "mutation IssueUpdate" in query:
            return {"data": {"issueUpdate": {"success": True, "issue": {"id": "issue-1"}}}}
        return {"errors": ["unexpected query"]}

    monkeypatch.setattr(c, "_query", fake_query)
    out = c.transition_issue("ZOC-1", "completed", team_id="team-1")
    assert out.get("success") is True


def test_transition_issue_state_not_found(monkeypatch):
    c = LinearClient(api_key="x")

    def fake_query(query, variables=None):
        if "query IssueByNumber" in query:
            return {"data": {"issues": {"nodes": [{"id": "issue-1", "identifier": "ZOC-1"}]}}}
        if "query TeamStates" in query:
            return {"data": {"team": {"states": {"nodes": [{"id": "s-start", "type": "started", "name": "In Progress"}]}}}}
        return {"errors": ["unexpected query"]}

    monkeypatch.setattr(c, "_query", fake_query)
    out = c.transition_issue("ZOC-1", "completed", team_id="team-1")
    assert out.get("success") is False
    assert "not found" in str(out.get("error", "")).lower()


def test_assign_issue_by_identifier(monkeypatch):
    c = LinearClient(api_key="x")

    def fake_query(query, variables=None):
        if "query IssueByNumber" in query:
            return {"data": {"issues": {"nodes": [{"id": "issue-2", "identifier": "ZOC-2"}]}}}
        if "mutation IssueUpdate" in query:
            assert variables["input"]["assigneeId"] == "user-1"
            return {"data": {"issueUpdate": {"success": True, "issue": {"id": "issue-2"}}}}
        return {"errors": ["unexpected query"]}

    monkeypatch.setattr(c, "_query", fake_query)
    out = c.assign_issue_by_identifier("ZOC-2", "user-1")
    assert out.get("success") is True


def test_create_or_get_project_existing(monkeypatch):
    c = LinearClient(api_key="x")

    def fake_query(query, variables=None):
        if "query ProjectByName" in query:
            return {"data": {"projects": {"nodes": [{"id": "p1", "name": "Zocai-test", "url": "u", "state": "backlog"}]}}}
        return {"errors": ["unexpected query"]}

    monkeypatch.setattr(c, "_query", fake_query)
    out = c.create_or_get_project("Zocai-test")
    assert out.get("success") is True
    assert out.get("created") is False
    assert out["project"]["id"] == "p1"


def test_create_or_get_project_create_new(monkeypatch):
    c = LinearClient(api_key="x")

    def fake_query(query, variables=None):
        if "query ProjectByName" in query:
            return {"data": {"projects": {"nodes": []}}}
        if "mutation ProjectCreate" in query:
            return {"data": {"projectCreate": {"success": True, "project": {"id": "p2", "name": "New", "url": "u2", "state": "backlog"}}}}
        return {"errors": ["unexpected query"]}

    monkeypatch.setattr(c, "_query", fake_query)
    out = c.create_or_get_project("New", team_id="team-1")
    assert out.get("success") is True
    assert out.get("created") is True
    assert out["project"]["id"] == "p2"
