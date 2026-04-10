import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


class _GitHubStub:
    def __init__(self):
        self.last_cwd = None

    def bootstrap_repo(self, project_name, cwd='.', private=True, description=''):
        self.last_cwd = cwd
        return {
            "success": True,
            "repo": f"zocaibotz/{project_name.lower().replace(' ', '-')}",
            "url": f"https://github.com/zocaibotz/{project_name.lower().replace(' ', '-')}",
            "created": True,
        }


def test_github_bootstrap_node_success(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    stub = _GitHubStub()
    monkeypatch.setattr(workers, "github_bootstrap", stub)
    out = workers.github_bootstrap_node({"requirements": {"name": "Demo App"}})
    assert out["next_agent"] == "codesmith"
    assert out["github_repo"].startswith("zocaibotz/")
    assert out["github_url"].startswith("https://github.com/")
    assert out["project_workspace_path"].startswith("projects/")
    assert stub.last_cwd == out["project_workspace_path"]
