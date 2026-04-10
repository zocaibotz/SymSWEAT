import sys
import os
from types import SimpleNamespace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


def _cp(returncode=0, out="", err=""):
    return SimpleNamespace(returncode=returncode, stdout=out, stderr=err)


class _LinearStub:
    def __init__(self):
        self.comments = []

    def list_project_issues(self, project_id: str, first: int = 30):
        return {
            "success": True,
            "issues": [
                {"id": "i1", "identifier": "ZOC-1", "state": {"type": "unstarted"}}
            ],
        }

    def comment_issue(self, issue_id: str, body: str):
        self.comments.append((issue_id, body))
        return {"success": True}


def test_pipeline_posts_summary_to_linear(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SWEAT_STRICT_TEST_GATE", "false")
    monkeypatch.setenv("SWEAT_LINEAR_PIPELINE_COMMENT", "true")

    lin = _LinearStub()
    monkeypatch.setattr(workers, "linear", lin)

    def fake_run(cmd, capture_output=True, text=True):
        if cmd[0].endswith("pytest") and "tests/integration" in cmd:
            return _cp(0, "1 passed", "")
        if cmd[0].endswith("pytest"):
            return _cp(0, "TOTAL 10 0 100%", "")
        if cmd[0].endswith("playwright"):
            return _cp(0, "2 passed", "")
        return _cp(1, "", "bad")

    monkeypatch.setattr(__import__("subprocess"), "run", fake_run)
    monkeypatch.setattr(__import__("shutil"), "which", lambda x: "/usr/bin/playwright" if x == "playwright" else "/usr/bin/pytest")
    monkeypatch.setattr(workers, "extract_coverage_percent", lambda s: 100.0)

    out = workers.pipeline_node({"coverage_target": 95, "linear_project_id": "p1"})
    assert out["ci_pipeline_status"] == "PASSED"
    assert len(lin.comments) == 1
    assert "SWEAT pipeline update" in lin.comments[0][1]
