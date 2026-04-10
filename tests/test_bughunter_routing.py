import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


class _StubResp:
    def __init__(self, content):
        self.content = content


class _StubLLM:
    def invoke(self, _msgs):
        return _StubResp("test plan")


def test_bughunter_routes_to_codesmith_for_remediation(monkeypatch, tmp_path):
    monkeypatch.setattr(workers, "llm", _StubLLM())
    state = {"project_workspace_path": str(tmp_path), "architecture_docs": "arch"}

    out = workers.bughunter_node(state)

    assert out["next_agent"] == "codesmith"
    assert out["decision_reason_code"] == "bughunter_to_codesmith_remediation"
    assert "test_results" in out
