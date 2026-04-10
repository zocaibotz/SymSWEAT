import os

from src.agents.orchestrator import orchestrator_node


def test_orchestrator_uses_v2_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("SWEAT_V2_ENABLED", "true")
    monkeypatch.setenv("SWEAT_V2_SHADOW_MODE", "false")

    state = {
        "project_id": "p1",
        "messages": [],
        "requirements": {"acceptance_criteria": ["x"], "name": "demo"},
        "design_approval_status": "pending",
        "test_readiness_status": "not_ready",
        "ci_pipeline_status": "running",
    }
    result = orchestrator_node(state)
    assert "next_agent" in result
    assert result.get("v2_shadow_mode") is False
