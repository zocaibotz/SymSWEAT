import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


def test_automator_budget_exhaustion_ends(monkeypatch):
    monkeypatch.setenv("SWEAT_AUTOMATOR_RETRY_BUDGET", "1")
    monkeypatch.setenv("SWEAT_AUTOMATOR_RETRY_VIA_PIPELINE", "true")

    class StubN8N:
        def create_workflow(self, **kwargs):
            return {"name": "wf", "remote_status": "draft", "error": "sync failed"}

    monkeypatch.setattr(workers, "n8n", StubN8N())

    out = workers.automator_node({"automator_run_count": 0})
    assert out["next_agent"] == "__end__"
    assert out["lifecycle_fail_reason"] == "automator_retry_budget_exhausted"


def test_deployer_budget_exhaustion_ends(monkeypatch):
    monkeypatch.setenv("SWEAT_DEPLOYER_RETRY_BUDGET", "1")
    monkeypatch.setenv("SWEAT_CHAIN_AUTOMATOR_AFTER_DEPLOY", "true")

    out = workers.deployer_node({"deployer_run_count": 0})
    assert out["next_agent"] == "__end__"
    assert out["lifecycle_fail_reason"] == "deployer_retry_budget_exhausted"
