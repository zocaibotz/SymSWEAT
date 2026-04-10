from src.sweat_v2.graph.planning_graph import PlanningGraph
from src.sweat_v2.state import Stage, SweatRunState


def test_planning_graph_real_mode_advances_with_mocked_worker(monkeypatch) -> None:
    s = SweatRunState(run_id="r1", project_id="p1", task_id="t1", stage=Stage.planning)
    s.metadata["use_real_workers"] = "true"
    s.metadata["planning_next_worker"] = "req_master_interview"
    g = PlanningGraph()

    def fake_worker(_state, _name):
        return {"requirements_interview_status": "complete", "sdd_status": "tasks_done", "next_agent": "design_approval_gate"}

    monkeypatch.setattr("src.sweat_v2.graph.planning_graph.run_planning_worker", fake_worker)

    out = g.run(s)
    assert out.stage == Stage.design
