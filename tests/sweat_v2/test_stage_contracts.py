from src.sweat_v2.stage_contracts import validate_stage_contract
from src.sweat_v2.state import Stage, SweatRunState


def test_stage_contract_planning_requires_linear_issue_key() -> None:
    s = SweatRunState(run_id="r1", project_id="p1", task_id="t1", stage=Stage.planning)
    v = validate_stage_contract(s)
    assert "missing_metadata:linear_issue_key" in v


def test_stage_contract_qa_requires_tests_executed() -> None:
    s = SweatRunState(
        run_id="r1",
        project_id="p1",
        task_id="t1",
        stage=Stage.qa,
        metadata={"coding_status": "implemented"},
    )
    v = validate_stage_contract(s)
    assert "missing_quality_flag:tests_executed" in v
