from src.sweat_v2.graph import RuntimeGraph
from src.sweat_v2.state import Stage, SweatRunState


def test_runtime_graph_reaches_done() -> None:
    g = RuntimeGraph()
    s = SweatRunState(
        run_id="r1",
        project_id="p1",
        task_id="t1",
        stage=Stage.planning,
        metadata={"linear_issue_key": "SWEAT-1", "use_real_workers": "false"},
    )
    s.quality.tests_executed = True
    s.quality.tests_passed = True
    out = g.run_to_terminal(s)
    assert out.stage == Stage.done
    assert out.metadata.get("governance_checked") == "true"
    assert out.metadata.get("pm_synced") == "true"


def test_runtime_graph_blocks_on_contract_violation() -> None:
    g = RuntimeGraph()
    s = SweatRunState(run_id="r1", project_id="p1", task_id="t1", stage=Stage.planning)
    out = g.run_to_terminal(s)
    assert out.stage == Stage.blocked
    assert any(v.startswith("missing_metadata") for v in out.quality.policy_violations)
