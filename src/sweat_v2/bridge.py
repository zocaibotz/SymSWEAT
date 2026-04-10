from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from src.sweat_v2.config import V2Flags, load_v2_flags
from src.sweat_v2.graph.supervisor import SupervisorGraph
from src.sweat_v2.harness.middleware import (
    LocalContextMiddleware,
    LoopDetectionMiddleware,
    PolicyGuardMiddleware,
    PreCompletionChecklistMiddleware,
    ReasoningBudgetMiddleware,
)
from src.sweat_v2.state import Stage, SweatRunState


_STAGE_TO_AGENT: dict[Stage, str] = {
    Stage.planning: "sdd_specify",
    Stage.design: "design_approval_gate",
    Stage.tdd: "tdd_orchestrator",
    Stage.coding: "codesmith",
    Stage.qa: "gatekeeper",
    Stage.deploy: "deployer",
    Stage.done: "__end__",
    Stage.blocked: "__end__",
}


def _to_stage(state: Dict[str, Any]) -> Stage:
    if state.get("design_approval_status") != "approved":
        return Stage.design
    if state.get("test_readiness_status") != "ready":
        return Stage.tdd
    if state.get("ci_pipeline_status") not in {"passed", "success"}:
        return Stage.coding
    if state.get("deployment_url"):
        return Stage.done
    return Stage.planning


def _to_v2_state(state: Dict[str, Any]) -> SweatRunState:
    return SweatRunState(
        run_id=state.get("run_id") or "pending-run",
        project_id=state.get("project_id") or "unknown-project",
        task_id=state.get("linear_project_id") or state.get("project_id") or "unknown-task",
        stage=_to_stage(state),
        acceptance_criteria=(state.get("requirements") or {}).get("acceptance_criteria") or [],
        metadata={
            "linear_issue_key": state.get("linear_project_id") or "unmapped",
            "artifact_sync_target": "SWEAT-private",
        },
    )


@dataclass
class V2RouterResult:
    next_agent: str
    v2_stage: str
    policy_violations: list[str]
    shadow: bool


def route_with_v2(project_state: Dict[str, Any], flags: V2Flags | None = None) -> V2RouterResult:
    flags = flags or load_v2_flags()

    graph = SupervisorGraph(
        middleware=[
            LocalContextMiddleware(),
            ReasoningBudgetMiddleware(),
            LoopDetectionMiddleware(),
            PolicyGuardMiddleware(),
            PreCompletionChecklistMiddleware(),
        ]
    )

    v2_state = _to_v2_state(project_state)
    v2_state = graph.run_stage(v2_state)
    v2_state = graph.finalize(v2_state)
    return V2RouterResult(
        next_agent=_STAGE_TO_AGENT.get(v2_state.stage, "req_master_interview"),
        v2_stage=v2_state.stage.value,
        policy_violations=v2_state.quality.policy_violations,
        shadow=flags.shadow_mode,
    )
