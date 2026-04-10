import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


def test_codesmith_circuit_breaker_stops_loop(monkeypatch):
    monkeypatch.setenv("SWEAT_CODESMITH_MAX_RETRIES", "3")
    out = workers.codesmith_node({
        "test_readiness_status": "ready",
        "codesmith_retry_count": 3,
        "messages": [],
        "architecture_docs": "demo",
    })
    assert out["next_agent"] == "gatekeeper"
    assert "halted" in out["messages"][0].content.lower()
