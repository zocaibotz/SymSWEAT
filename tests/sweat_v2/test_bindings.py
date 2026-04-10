from src.sweat_v2.bindings import apply_legacy_patch, map_stage_after_planning, planning_route_from_state
from src.sweat_v2.state import Stage, SweatRunState


def test_planning_route_progression() -> None:
    s = SweatRunState(run_id="r1", project_id="p1", task_id="t1", stage=Stage.planning)
    assert planning_route_from_state(s) == "req_master_interview"
    s.metadata["requirements_interview_status"] = "complete"
    assert planning_route_from_state(s) == "sdd_specify"
    s.metadata["sdd_status"] = "specify_done"
    assert planning_route_from_state(s) == "sdd_plan"
    s.metadata["sdd_status"] = "plan_done"
    assert planning_route_from_state(s) == "sdd_tasks"
    s.metadata["sdd_status"] = "tasks_done"
    assert planning_route_from_state(s) == "done"


def test_map_stage_after_planning_done() -> None:
    s = SweatRunState(run_id="r1", project_id="p1", task_id="t1", stage=Stage.planning)
    s.metadata["requirements_interview_status"] = "complete"
    s.metadata["sdd_status"] = "tasks_done"
    out = map_stage_after_planning(s)
    assert out.stage == Stage.design


def test_apply_legacy_patch() -> None:
    s = SweatRunState(run_id="r1", project_id="p1", task_id="t1", stage=Stage.planning)
    patch = {"requirements_interview_status": "complete", "sdd_status": "specify_done"}
    out = apply_legacy_patch(s, patch)
    assert out.metadata["requirements_interview_status"] == "complete"
    assert out.metadata["sdd_status"] == "specify_done"
