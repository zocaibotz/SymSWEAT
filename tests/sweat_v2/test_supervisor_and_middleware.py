from src.sweat_v2.graph.supervisor import SupervisorGraph
from src.sweat_v2.harness.middleware import (
    LocalContextMiddleware,
    LoopDetectionMiddleware,
    PolicyGuardMiddleware,
    PreCompletionChecklistMiddleware,
    ReasoningBudgetMiddleware,
)
from src.sweat_v2.state import Stage, SweatRunState


def build_state() -> SweatRunState:
    return SweatRunState(
        run_id="r1",
        project_id="p1",
        task_id="t1",
        stage=Stage.planning,
        acceptance_criteria=["all tests pass", "criteria coverage >= 95%"],
        metadata={
            "linear_issue_key": "SWEAT-123",
            "artifact_sync_target": "SWEAT-private",
        },
    )


def test_supervisor_advances_stage_and_sets_reasoning_mode() -> None:
    state = build_state()
    graph = SupervisorGraph(
        middleware=[
            LocalContextMiddleware(),
            ReasoningBudgetMiddleware(),
            LoopDetectionMiddleware(),
            PolicyGuardMiddleware(),
            PreCompletionChecklistMiddleware(),
        ]
    )

    state = graph.run_stage(state)
    assert state.stage == Stage.design
    assert state.metadata.get("workspace_map") == "pending-discovery"


def test_precompletion_adds_violation_when_tests_missing() -> None:
    state = build_state()
    graph = SupervisorGraph(middleware=[PreCompletionChecklistMiddleware()])
    state = graph.finalize(state)

    assert "tests_not_executed" in state.quality.policy_violations
