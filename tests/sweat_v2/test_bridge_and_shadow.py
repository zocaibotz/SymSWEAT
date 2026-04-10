from src.sweat_v2.bridge import route_with_v2
from src.sweat_v2.config import V2Flags
from src.sweat_v2.shadow_runner import append_shadow_record, build_shadow_record, run_shadow_once


def test_route_with_v2_returns_agent_and_stage() -> None:
    state = {
        "project_id": "p1",
        "run_id": "r1",
        "requirements": {"acceptance_criteria": ["A"]},
        "design_approval_status": "pending",
        "test_readiness_status": "not_ready",
    }
    result = route_with_v2(state, V2Flags(enabled=True, shadow_mode=True))
    assert result.next_agent
    assert result.v2_stage in {"planning", "design", "tdd", "coding", "qa", "deploy", "done", "blocked"}


def test_shadow_runner_outputs_comparison_record() -> None:
    state = {
        "project_id": "p1",
        "messages": [],
        "requirements": {"acceptance_criteria": ["A"], "name": "test"},
        "requirements_interview_status": "complete",
        "design_approval_status": "approved",
        "test_readiness_status": "ready",
        "ci_pipeline_status": "running",
    }
    record = run_shadow_once(state)
    assert "v1_next_agent" in record
    assert "v2_next_agent" in record
    assert isinstance(record["agreed"], bool)


def test_build_and_append_shadow_record(tmp_path) -> None:
    state = {"project_id": "p1"}

    class V2:
        next_agent = "sdd_specify"
        v2_stage = "planning"
        policy_violations = []

    rec = build_shadow_record(state, "req_master_interview", V2())
    out = append_shadow_record(rec, str(tmp_path / "shadow.jsonl"))
    assert out["project_id"] == "p1"
