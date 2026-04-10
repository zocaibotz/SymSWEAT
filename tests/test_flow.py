import sys
import os
from langchain_core.messages import HumanMessage
from langchain_community.chat_models import FakeListChatModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import build_graph
import src.agents.orchestrator as orchestrator_mod
import src.agents.workers as workers_mod


def test_initial_greeting():
    # Deterministic, no external LLM calls
    orchestrator_mod.llm = FakeListChatModel(responses=['{"next_agent":"req_master_interview"}'])
    workers_mod.llm = FakeListChatModel(responses=['{"name":"demo-app","goal":"test"}'])

    graph = build_graph()
    initial_state = {
        "messages": [HumanMessage(content="Hello, I want to build a Python app.")],
        "project_id": "test-001",
        "next_agent": None,
    }

    events = []
    for i, event in enumerate(graph.stream(initial_state), start=1):
        events.append(event)
        if i >= 5:
            break

    seen_nodes = []
    for event in events:
        seen_nodes.extend(list(event.keys()))

    assert "zocai" in seen_nodes
    assert "req_master_interview" in seen_nodes
    assert "sdd_specify" in seen_nodes
