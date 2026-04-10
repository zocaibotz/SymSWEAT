import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import _apply_runtime_guards


def test_pipeline_bughunter_gatekeeper_loop_escalates_to_codesmith(monkeypatch):
    monkeypatch.setenv("SWEAT_PIPELINE_REMEDIATION_LOOP_BUDGET", "3")
    state = {"pipeline_remediation_bounce_count": 2, "pipeline_remediation_escalation_count": 0}

    out = _apply_runtime_guards("gatekeeper", state, {"next_agent": "pipeline", "messages": []})

    assert out["next_agent"] == "codesmith"
    assert out["pipeline_remediation_escalation_count"] == 1
    assert out["decision_reason_code"] == "pipeline_bughunter_gatekeeper_loop_escalated"


def test_pipeline_bughunter_gatekeeper_loop_second_escalation_halts(monkeypatch):
    monkeypatch.setenv("SWEAT_PIPELINE_REMEDIATION_LOOP_BUDGET", "3")
    state = {"pipeline_remediation_bounce_count": 2, "pipeline_remediation_escalation_count": 1}

    out = _apply_runtime_guards("pipeline", state, {"next_agent": "bughunter", "messages": []})

    assert out["next_agent"] == "__end__"
    assert out["lifecycle_fail_reason"] == "pipeline_bughunter_gatekeeper_loop_exhausted"
