import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers
from src.utils.llm import _resolve_coder_alias_order


class _StubResp:
    def __init__(self, content):
        self.content = content


class _StubLLM:
    def invoke(self, msgs):
        return _StubResp("needs changes")


def test_coder_alias_default_prefers_gemini(monkeypatch):
    monkeypatch.delenv("SWEAT_CODER_PRIMARY", raising=False)
    order = _resolve_coder_alias_order()
    assert order[0] == "gemini_cli"


def test_gatekeeper_forwards_when_codesmith_halted(monkeypatch):
    monkeypatch.setenv("SWEAT_GATEKEEPER_FORWARD_ON_CODESMITH_HALT", "true")
    monkeypatch.setenv("SWEAT_CODESMITH_MAX_RETRIES", "5")
    monkeypatch.setattr(workers, "llm", _StubLLM())

    class _Git:
        def diff(self):
            return "diff"

    monkeypatch.setattr(workers, "git_tool", _Git())
    out = workers.gatekeeper_node({"messages": [], "codesmith_retry_count": 5})
    assert out.get("next_agent") == "pipeline"
