import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.contracts import validate_state_patch


def test_sdd_specify_contract():
    errs = validate_state_patch("sdd_specify", {"sdd_spec_status": "approved"})
    assert any("sdd_spec_path" in e for e in errs)


def test_pipeline_contract():
    errs = validate_state_patch("pipeline", {"ci_pipeline_status": "unknown"})
    assert any("ci_pipeline_status" in e for e in errs)


def test_design_gate_contract_ok():
    errs = validate_state_patch("design_approval_gate", {"design_approval_status": "approved"})
    assert errs == []


def test_codesmith_contract_next_agent_guard():
    errs = validate_state_patch("codesmith", {"next_agent": "pipeline"})
    assert any("codesmith" in e for e in errs)


def test_automator_contract_bool_guard():
    errs = validate_state_patch("automator", {"automation_completed": "yes"})
    assert any("automation_completed" in e for e in errs)
