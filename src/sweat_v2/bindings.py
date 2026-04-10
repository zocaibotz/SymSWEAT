from __future__ import annotations

from typing import Any, Dict

from src.agents import workers
from src.sweat_v2.state import Stage, SweatRunState


def v2_to_legacy(state: SweatRunState) -> Dict[str, Any]:
    return {
        "project_id": state.project_id,
        "run_id": state.run_id,
        "requirements": {
            "acceptance_criteria": state.acceptance_criteria,
            "name": state.metadata.get("project_name", state.project_id),
        },
        "requirements_interview_status": state.metadata.get("requirements_interview_status"),
        "sdd_status": state.metadata.get("sdd_status"),
        "design_approval_status": state.metadata.get("design_approval_status", "pending"),
        "test_readiness_status": state.metadata.get("test_readiness_status", "not_ready"),
        "messages": [],
    }


def apply_legacy_patch(state: SweatRunState, patch: Dict[str, Any]) -> SweatRunState:
    if "requirements_interview_status" in patch:
        state.metadata["requirements_interview_status"] = str(patch["requirements_interview_status"])
    if "sdd_status" in patch:
        state.metadata["sdd_status"] = str(patch["sdd_status"])
    if "design_approval_status" in patch:
        state.metadata["design_approval_status"] = str(patch["design_approval_status"])
    if "test_readiness_status" in patch:
        state.metadata["test_readiness_status"] = str(patch["test_readiness_status"])
    return state


def run_planning_worker(state: SweatRunState, worker_name: str) -> Dict[str, Any]:
    legacy = v2_to_legacy(state)
    fn = {
        "req_master_interview": workers.req_master_interview_node,
        "sdd_specify": workers.sdd_specify_node,
        "sdd_plan": workers.sdd_plan_node,
        "sdd_tasks": workers.sdd_tasks_node,
    }[worker_name]
    return fn(legacy) or {}


def planning_route_from_state(state: SweatRunState) -> str:
    if state.metadata.get("requirements_interview_status") != "complete":
        return "req_master_interview"
    sdd_status = state.metadata.get("sdd_status")
    if sdd_status not in {"specify_done", "plan_done", "tasks_done"}:
        return "sdd_specify"
    if sdd_status == "specify_done":
        return "sdd_plan"
    if sdd_status == "plan_done":
        return "sdd_tasks"
    return "done"


def map_stage_after_planning(state: SweatRunState) -> SweatRunState:
    route = planning_route_from_state(state)
    if route in {"req_master_interview", "sdd_specify", "sdd_plan", "sdd_tasks"}:
        state.stage = Stage.planning
    else:
        state.metadata["planning_status"] = "specified"
        state.stage = Stage.design
    return state
