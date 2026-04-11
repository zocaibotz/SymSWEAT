"""conftest.py — shared server/process fixtures for the pipeline E2E suite."""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Generator

import pytest

# Ensure project root is on path
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))


def _pick_free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def monitoring_port() -> int:
    port = int(os.getenv("MONITORING_PORT", "0"))
    if port:
        return port
    return _pick_free_port()


@pytest.fixture(scope="session")
def app_server(monitoring_port: int, tmp_path_factory: pytest.TempPathFactory) -> Generator[str, None, None]:
    """
    Start uvicorn on a free port with auth + isolated PROJECTS_ROOT.
    Tear down when the test session ends.
    """
    tmp_root = tmp_path_factory.getroot()

    # Auth + port env vars
    os.environ.setdefault("ADMIN_PASSWORD", "testpass123")
    os.environ.setdefault("SWEAT_USERS", "admin:testpass123")
    os.environ.setdefault("PORT", str(monitoring_port))

    # Isolate test PROJECTS_ROOT from dev data
    projects_root = str(tmp_root / "projects")
    os.environ["PROJECTS_ROOT"] = projects_root

    import src.monitoring_api as api_module

    api_module.PROJECTS_ROOT = Path(projects_root)

    from src.monitoring_api import create_app

    app = create_app()

    import uvicorn

    cfg = uvicorn.Config(app, host="127.0.0.1", port=monitoring_port, log_level="error")
    server = uvicorn.Server(cfg)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    # Wait for server readiness
    import urllib.request

    base = f"http://127.0.0.1:{monitoring_port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(f"{base}/healthz", timeout=2)
            break
        except Exception:
            time.sleep(0.2)
    else:
        raise RuntimeError(f"app_server on port {monitoring_port} failed to start")

    yield base

    server.should_exit = True
    t.join(timeout=5)


@pytest.fixture(scope="session")
def graph_run(tmp_path_factory: pytest.TempPathFactory) -> Generator[dict, None, None]:
    """
    Launch the LangGraph pipeline in a daemon thread, writing to an isolated
    temp project directory.  Caller reads project_id / project_dir from the
    returned dict.

    The graph will reach requirement_master, pause at HITL interview
    (awaiting_human), and wait there until the test feeds answers via the
    monitoring API.
    """
    tmp_root = tmp_path_factory.getroot()
    project_id = "e2e-pipeline-test-" + os.urandom(4).hex()
    project_dir = str(tmp_root / "projects" / project_id)
    Path(project_dir).mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("SWEAT_STRICT_CONTRACTS", "true")
    os.environ.setdefault("SWEAT_STRICT_TEST_GATE", "true")
    os.environ.setdefault("SWEAT_CODER_PRIMARY", "gemini_cli")
    os.environ.setdefault("SWEAT_CODER_SECONDARY", "minimax_api")
    os.environ.setdefault("SWEAT_CODER_TERTIARY", "ollama")
    os.environ.setdefault("SWEAT_CODEX_STRICT_TOOLS", "true")

    result: dict = {
        "project_id": project_id,
        "project_dir": project_dir,
        "error": None,
        "done": False,
        "routes": [],
    }

    def _run():
        try:
            from langchain_core.messages import HumanMessage
            from src.main import build_graph

            prompt = (
                "Build a production-ready MVP for a task manager app. "
                "Include auth, CRUD tasks, tags, due dates, and dashboard. "
                "Provide testable acceptance criteria and architecture-ready requirements."
            )
            graph = build_graph()
            state = {
                "messages": [HumanMessage(content=prompt)],
                "project_id": project_id,
                "project_workspace_path": project_dir,
                "next_agent": None,
            }
            routes = []
            for event in graph.stream(state):
                for node, value in event.items():
                    if isinstance(value, dict) and node != "__end__":
                        nxt = value.get("next_agent")
                        routes.append({"node": node, "next_agent": nxt})
            result["routes"] = routes
        except Exception as exc:
            result["error"] = str(exc)
        finally:
            result["done"] = True

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    # Brief pause so the project directory is definitely created before we yield
    time.sleep(2)
    yield result
