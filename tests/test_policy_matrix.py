import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers
from src.agents.workers import _playwright_required


class _StubResp:
    def __init__(self, content):
        self.content = content


class _StubLLM:
    def invoke(self, msgs):
        return _StubResp("needs changes")


class _Git:
    def diff(self):
        return "diff"


def test_policy_matrix_playwright_flag_override(tmp_path, monkeypatch):
    ws = tmp_path / "p"
    ws.mkdir(parents=True)
    monkeypatch.setenv("SWEAT_REQUIRE_PLAYWRIGHT", "false")
    assert _playwright_required({"project_workspace_path": str(ws)}, strict=True) is False


def test_policy_matrix_gatekeeper_no_forward_on_halt(monkeypatch):
    monkeypatch.setenv("SWEAT_GATEKEEPER_FORWARD_ON_CODESMITH_HALT", "false")
    monkeypatch.setenv("SWEAT_GATEKEEPER_TIMEOUT_FALLBACK", "false")
    monkeypatch.setenv("SWEAT_CODESMITH_MAX_RETRIES", "5")
    monkeypatch.setattr(workers, "llm", _StubLLM())
    monkeypatch.setattr(workers, "git_tool", _Git())

    out = workers.gatekeeper_node({"messages": [], "codesmith_retry_count": 5})
    assert out.get("next_agent") == "codesmith"
