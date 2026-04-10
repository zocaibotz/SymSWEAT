import sys
import os
import tempfile
import subprocess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.github_bootstrap import GitHubBootstrapTool


def test_bootstrap_rejects_public_repo():
    tool = GitHubBootstrapTool(owner="zocaibotz")
    out = tool.bootstrap_repo(project_name="demo", cwd=".", private=False)
    assert out["success"] is False
    assert "must be private" in out["error"].lower()


def test_ensure_gitignore_includes_env_patterns(monkeypatch):
    monkeypatch.setenv("SWEAT_ALLOW_BRANCH_PROTECTION_BYPASS", "true")
    tool = GitHubBootstrapTool(owner="zocaibotz")
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "init"], cwd=d, capture_output=True)
        # invoke internals via bootstrap path but avoid gh create by adding origin early
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/zocaibotz/dummy"], cwd=d, capture_output=True)
        out = tool.bootstrap_repo(project_name="dummy", cwd=d, private=True)
        assert out["success"] is True
        gi = open(os.path.join(d, ".gitignore"), "r", encoding="utf-8").read()
        assert ".env" in gi
        assert ".env.*" in gi
        assert "!.env.example" in gi


def test_branch_protection_hard_fail_without_bypass(monkeypatch):
    monkeypatch.delenv("SWEAT_ALLOW_BRANCH_PROTECTION_BYPASS", raising=False)
    tool = GitHubBootstrapTool(owner="zocaibotz")
    monkeypatch.setattr(tool, "_apply_branch_protection", lambda **kwargs: {"success": False, "error": "no perms"})

    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "init"], cwd=d, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/zocaibotz/dummy"], cwd=d, capture_output=True)
        out = tool.bootstrap_repo(project_name="dummy", cwd=d, private=True)
        assert out["success"] is False
        assert "Branch protection enforcement failed" in out["error"]
