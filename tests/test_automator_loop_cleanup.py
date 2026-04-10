import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


class _N8NStub:
    def __init__(self, status="synced"):
        self.status = status

    def create_workflow(self, name, trigger, actions):
        return {
            "name": name,
            "trigger": trigger,
            "actions": actions,
            "remote_status": self.status,
        }


def test_automator_ends_after_success(monkeypatch):
    monkeypatch.setattr(workers, "n8n", _N8NStub(status="synced"))
    out = workers.automator_node({})
    assert out["automation_completed"] is True
    assert out["next_agent"] == "__end__"


def test_automator_short_circuit_when_already_completed(monkeypatch):
    out = workers.automator_node({"automation_completed": True})
    assert out["next_agent"] == "__end__"
