import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


class _BoomLLM:
    def invoke(self, _msgs):
        raise TimeoutError("llm timeout")


def test_gatekeeper_timeout_fallback_enabled(monkeypatch):
    monkeypatch.setenv("SWEAT_GATEKEEPER_TIMEOUT_FALLBACK", "true")
    monkeypatch.setattr(workers, "llm", _BoomLLM())

    out = workers.gatekeeper_node({"messages": []})
    assert out["next_agent"] == "pipeline"
    assert "fallback enabled" in out["code_review_feedback"].lower()


def test_gatekeeper_soft_approve_after_codesmith_halt(monkeypatch):
    class _LLM:
        def invoke(self, _):
            from langchain_core.messages import AIMessage
            return AIMessage(content="needs changes")

    monkeypatch.setenv("SWEAT_GATEKEEPER_TIMEOUT_FALLBACK", "true")
    monkeypatch.setenv("SWEAT_CODESMITH_MAX_RETRIES", "2")
    monkeypatch.setattr(workers, "llm", _LLM())

    out = workers.gatekeeper_node({"messages": [], "codesmith_retry_count": 2})
    assert out["next_agent"] == "pipeline"
    assert "soft-approved" in out["code_review_feedback"].lower()
