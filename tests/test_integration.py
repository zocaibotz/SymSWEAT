# SWEAT Integration Test Suite (deterministic)
import sys
import os
import pytest
from langchain_core.messages import HumanMessage
from langchain_community.chat_models import FakeListChatModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import build_graph
from src.tools.git import get_git_tool
import src.main as main_mod
import src.agents.orchestrator as orchestrator_mod
import src.agents.workers as workers_mod


@pytest.mark.integration
def test_full_software_lifecycle(monkeypatch):
    """
    Deterministic end-to-end lifecycle using fake LLM responses:
    Requirement -> Architecture -> UX -> UI -> Code -> Review -> CI -> Deploy
    """
    print("\n--- Starting End-to-End Lifecycle Test ---")

    # Route from orchestrator to interview-first phase.
    orchestrator_mod.llm = FakeListChatModel(responses=['{"next_agent":"req_master_interview"}'])

    # Worker sequence responses in invocation order:
    # req_master, architect, pixel, frontman, codesmith, gatekeeper
    workers_mod.llm = FakeListChatModel(
        responses=[
            '{"name":"hello-sweat","description":"simple script","acceptance_criteria":["prints hello","calculates sum"]}',
            '# Architecture\n- Single python file app',
            '{"personas":[{"name":"dev"}],"user_journey":["open app"],"screens":[{"name":"home"}],"style_tokens":{"primary":"#111"}}',
            '{"tool":"write_file","args":{"path":"src/App.jsx","content":"export default function App(){return <div>Hello SWEAT UI</div>; }"}}',
            '{"tool":"write_file","args":{"path":"src/app.py","content":"print(\'Hello SWEAT\')\\nprint(5+5)\\n"}}',
            'APPROVED',
        ]
    )

    # CodeSmith uses coder_llm
    workers_mod.coder_llm = FakeListChatModel(
        responses=['{"tool":"write_file","args":{"path":"src/app.py","content":"print(\'Hello SWEAT\')\\nprint(5+5)\\n"}}']
    )

    # Keep E2E deterministic: CI step is validated in separate tests.
    monkeypatch.setattr(
        main_mod,
        "pipeline_node",
        lambda state: {
            "messages": [],
            "ci_pipeline_status": "PASSED",
            "next_agent": "deployer",
        },
    )

    class _GitHubStub:
        def bootstrap_repo(self, project_name, cwd='.', private=True, description=''):
            return {"success": True, "repo": "zocaibotz/integration-test", "url": "https://github.com/zocaibotz/integration-test"}

    monkeypatch.setattr(workers_mod, "github_bootstrap", _GitHubStub())

    graph = build_graph()

    initial_state = {
        "messages": [HumanMessage(content="Build a simple Python script that prints 'Hello SWEAT' and calculates 5+5.")],
        "project_id": "integration-test-001",
    }

    agent_sequence = []
    max_steps = 30

    for i, event in enumerate(graph.stream(initial_state), start=1):
        if i > max_steps:
            break
        for node, value in event.items():
            agent_sequence.append(node)
            print(f"[{i}] Node: {node}")
            if node == "pipeline":
                assert "ci_pipeline_status" in value

    # Assert expected path includes major phases.
    expected = [
        "zocai", "req_master_interview", "sdd_specify", "sdd_plan", "sdd_tasks",
        "architect", "pixel", "frontman", "design_approval_gate",
        "tdd_orchestrator", "unit_test_author", "integration_test_author", "playwright_test_author", "test_readiness_gate",
        "github_bootstrap", "codesmith", "gatekeeper", "pipeline", "deployer"
    ]
    for e in expected:
        assert e in agent_sequence

    # Assert generated artifacts
    git = get_git_tool()
    files = git.run_command(["ls", "-R"])
    assert "app.py" in files
    assert "App.jsx" in files
    assert "package.json" in files
    assert "handoff_contract.json" in files

    print("--- End-to-End Test Completed Successfully ---")
