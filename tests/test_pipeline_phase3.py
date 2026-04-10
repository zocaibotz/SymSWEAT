import sys
import os
from types import SimpleNamespace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.agents.workers as workers


def _cp(returncode=0, out="", err=""):
    return SimpleNamespace(returncode=returncode, stdout=out, stderr=err)


def test_pipeline_phase3_strict_pass(monkeypatch):
    monkeypatch.setenv("SWEAT_STRICT_TEST_GATE", "true")
    monkeypatch.setenv("SWEAT_REQUIRE_PLAYWRIGHT", "true")

    calls = []

    def fake_run(cmd, capture_output=True, text=True, cwd=None):
        calls.append((cmd, cwd))
        joined = " ".join(cmd)
        if "tests/integration" in joined:
            return _cp(0, "1 passed", "")
        if "pytest" in joined:
            return _cp(0, "TOTAL 10 0 100%", "")
        if "playwright" in joined:
            return _cp(0, "2 passed", "")
        return _cp(1, "", "bad")

    monkeypatch.setattr(workers, "extract_coverage_percent", lambda s: 100.0)
    monkeypatch.setattr(__import__("subprocess"), "run", fake_run)
    monkeypatch.setattr(__import__("shutil"), "which", lambda x: "/usr/bin/playwright" if x == "playwright" else "/usr/bin/pytest")

    out = workers.pipeline_node({"coverage_target": 95})
    assert out["ci_pipeline_status"] == "PASSED"
    assert out["unit_test_passed"] is True
    assert out["integration_test_passed"] is True
    assert out["playwright_test_passed"] is True
    assert calls, "expected subprocess calls"


def test_pipeline_phase3_strict_fail_without_playwright(monkeypatch):
    monkeypatch.setenv("SWEAT_STRICT_TEST_GATE", "true")
    monkeypatch.setenv("SWEAT_REQUIRE_PLAYWRIGHT", "true")

    def fake_run(cmd, capture_output=True, text=True, cwd=None):
        joined = " ".join(cmd)
        if "tests/integration" in joined:
            return _cp(0, "1 passed", "")
        if "pytest" in joined:
            return _cp(0, "TOTAL 10 0 100%", "")
        return _cp(1, "", "bad")

    monkeypatch.setattr(workers, "extract_coverage_percent", lambda s: 100.0)
    monkeypatch.setattr(__import__("subprocess"), "run", fake_run)
    monkeypatch.setattr(__import__("shutil"), "which", lambda x: "/usr/bin/pytest" if x == "pytest" else None)

    out = workers.pipeline_node({"coverage_target": 95})
    assert out["ci_pipeline_status"] == "FAILED"
    assert out["playwright_test_passed"] is False


def test_pipeline_prefers_workspace_venv_python_when_cwd_is_subdir(tmp_path, monkeypatch):
    monkeypatch.setenv("SWEAT_STRICT_TEST_GATE", "true")
    monkeypatch.setenv("SWEAT_REQUIRE_PLAYWRIGHT", "false")

    ws = tmp_path / "proj"
    subdir = ws / "nested"
    venv_python = ws / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("#!/usr/bin/env python\n")
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)

    calls = []

    def fake_run(cmd, capture_output=True, text=True, cwd=None):
        calls.append((cmd, cwd))
        if "tests/integration" in " ".join(cmd):
            return _cp(0, "ok", "")
        return _cp(0, "TOTAL 10 0 100%", "")

    monkeypatch.setattr(workers, "extract_coverage_percent", lambda s: 100.0)
    monkeypatch.setattr(__import__("subprocess"), "run", fake_run)

    out = workers.pipeline_node({"coverage_target": 95, "project_workspace_path": str(ws)})
    assert out["ci_pipeline_status"] == "PASSED"
    assert calls[0][0][:3] == [str(venv_python), "-m", "pytest"]
    assert calls[1][0][:3] == [str(venv_python), "-m", "pytest"]
    assert calls[0][1] == str(ws)


def test_pipeline_falls_back_to_sys_executable_pytest_when_missing(monkeypatch):
    monkeypatch.setenv("SWEAT_STRICT_TEST_GATE", "false")

    def fake_run(cmd, capture_output=True, text=True, cwd=None):
        return _cp(0, "TOTAL 10 0 100%", "")

    monkeypatch.setattr(workers, "extract_coverage_percent", lambda s: 100.0)
    monkeypatch.setattr(__import__("subprocess"), "run", fake_run)
    monkeypatch.setattr(__import__("shutil"), "which", lambda x: None)
    monkeypatch.setattr(workers, "_resolve_repo_python", lambda: None)

    cmd = workers._resolve_pytest_cmd("/nonexistent/workspace")
    assert cmd[:2] == [sys.executable, "-m"]


def test_pipeline_prefers_repo_venv_python_when_workspace_venv_missing(monkeypatch):
    monkeypatch.setattr(workers, "_resolve_workspace_python", lambda _ws: None)
    monkeypatch.setattr(workers, "_resolve_repo_python", lambda: "/abs/repo/.venv/bin/python")
    cmd = workers._resolve_pytest_cmd("/tmp/workspace-without-venv")
    assert cmd == ["/abs/repo/.venv/bin/python", "-m", "pytest"]
