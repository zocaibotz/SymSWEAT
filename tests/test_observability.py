import sys
import os
from pathlib import Path
from langchain_core.messages import HumanMessage
from langchain_community.chat_models import FakeListChatModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import build_graph
import src.agents.orchestrator as orchestrator_mod
import src.agents.workers as workers_mod


def test_run_telemetry_and_report_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    orchestrator_mod.llm = FakeListChatModel(responses=['{"next_agent":"req_master_interview"}'])
    workers_mod.llm = FakeListChatModel(responses=['{"name":"demo","acceptance_criteria":["User can create item"]}'])

    graph = build_graph()
    state = {"messages": [HumanMessage(content="build app")], "project_id": "obs-1"}

    final = {}
    for i, event in enumerate(graph.stream(state), start=1):
        for _n, v in event.items():
            final.update(v)
        if i >= 5:
            break

    telemetry = final.get("run_telemetry") or []
    assert len(telemetry) > 0
    assert Path("reports/runs/latest_run_report.json").exists()
