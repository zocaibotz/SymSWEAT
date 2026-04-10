import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.workers import _playwright_required


def test_playwright_required_auto(tmp_path, monkeypatch):
    ws = tmp_path / "p"
    (ws / "tests" / "e2e").mkdir(parents=True)
    (ws / "package.json").write_text("{}", encoding="utf-8")

    assert _playwright_required({"project_workspace_path": str(ws)}, strict=True) is True


def test_playwright_not_required_without_node_project(tmp_path, monkeypatch):
    ws = tmp_path / "p"
    (ws / "tests" / "e2e").mkdir(parents=True)
    assert _playwright_required({"project_workspace_path": str(ws)}, strict=True) is False


def test_playwright_force_flag(tmp_path, monkeypatch):
    ws = tmp_path / "p"
    ws.mkdir(parents=True)
    monkeypatch.setenv("SWEAT_REQUIRE_PLAYWRIGHT", "true")
    assert _playwright_required({"project_workspace_path": str(ws)}, strict=True) is True
