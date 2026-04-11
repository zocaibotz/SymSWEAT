"""conftest.py — shared server/process fixtures for the pipeline E2E suite."""

from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Generator

import pytest

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))


def _pick_free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Session-scoped shared temp root
# Both app_server and graph_run MUST use the same PROJECTS_ROOT so the API
# can see the project state written by the graph_run fixture.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def shared_projects_root(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path, None, None]:
    """
    Module-scoped temp directory shared by app_server and graph_run.
    Module scope ensures graph_run (which depends on this) is initialized
    after app_server in the pytest internals, giving tmp_path_factory a
    deterministic root before PROJECTS_ROOT is read.
    """
    root = tmp_path_factory.mktemp("sweat_shared_")
    projects_root = root / "projects"
    projects_root.mkdir(parents=True, exist_ok=True)
    os.environ["PROJECTS_ROOT"] = str(projects_root)
    os.environ.setdefault("ADMIN_PASSWORD", "testpass123")
    os.environ.setdefault("SWEAT_USERS", "admin:testpass123")
    os.environ.setdefault("GEMINI_API_KEY", "fake")
    os.environ.setdefault("SWEAT_CODER_PRIMARY", "gemini_cli")
    os.environ.setdefault("SWEAT_CODER_SECONDARY", "minimax_api")
    os.environ.setdefault("SWEAT_CODER_TERTIARY", "ollama")
    os.environ.setdefault("SWEAT_CODEX_STRICT_TOOLS", "true")
    os.environ.setdefault("SWEAT_STRICT_CONTRACTS", "true")
    os.environ.setdefault("SWEAT_STRICT_TEST_GATE", "true")
    yield projects_root


@pytest.fixture(scope="module")
def monitoring_port() -> int:
    port = int(os.getenv("MONITORING_PORT", "0"))
    if port:
        return port
    return _pick_free_port()


@pytest.fixture(scope="module")
def app_server(monitoring_port: int, shared_projects_root: Path) -> Generator[str, None, None]:
    """
    Start uvicorn on a free port with auth pointing at shared_projects_root.
    Tear down when the test module ends.
    """
    import src.monitoring_api as api_module

    api_module.PROJECTS_ROOT = shared_projects_root

    from src.monitoring_api import create_app
    app = create_app()

    import uvicorn

    cfg = uvicorn.Config(app, host="127.0.0.1", port=monitoring_port, log_level="error")
    server = uvicorn.Server(cfg)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()

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


@pytest.fixture(scope="module")
def graph_run(shared_projects_root: Path) -> Generator[dict, None, None]:
    """
    Launch the LangGraph pipeline in a daemon thread, writing to shared_projects_root.
    Caller reads project_id / project_dir from the returned dict.

    The graph reaches requirement_master, pauses at HITL interview
    (awaiting_human), and waits there until the test feeds answers via the API.
    """
    project_id = "e2e-pipeline-test-" + os.urandom(4).hex()
    project_dir = str(shared_projects_root / project_id)
    Path(project_dir).mkdir(parents=True, exist_ok=True)

    result: dict = {
        "project_id": project_id,
        "project_dir": project_dir,
        "error": None,
        "done": False,
        "routes": [],
    }

    # graph.stream() is lazy — nothing executes until we actively iterate.
    # We run the generator in a background thread and poll resume_state.json
    # until requirements_interview_status appears (signals req_master_interview
    # completed and wrote its output). Then we yield to the test.
    _started_event = threading.Event()

    def _run_graph():
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
            resume_path = Path(project_dir) / "state" / "resume_state.json"

            # NOTE: graph.stream() is a LAZY generator. Nothing executes until
            # we actively iterate it. We must consume events ONE BY ONE so each
            # node actually runs. Inside the for-loop body we MUST NOT return
            # after the first event — doing so kills the daemon thread and all
            # subsequent nodes (including req_master_interview_node) are skipped.
            interview_done = False
            for event in graph.stream(state):
                _started_event.set()
                if interview_done:
                    continue  # keep consuming events; graph runs in background

                # Poll resume_state.json until requirements_interview_status appears
                for _ in range(120):  # 120 * 0.5s = 60s max wait
                    try:
                        if resume_path.exists():
                            data = json.loads(resume_path.read_text())
                            if data.get("requirements_interview_status"):
                                interview_done = True
                                break
                    except Exception:
                        pass
                    time.sleep(0.5)
                # Do NOT return here — the for loop must continue so the graph
                # keeps processing subsequent nodes (architect, codesmith, etc.)
                # After req_master_interview completes, subsequent events will
                # keep the thread alive and advance the pipeline automatically.

            result["routes"] = []
        except Exception as exc:
            result["error"] = str(exc)
        finally:
            result["done"] = True

    t1 = threading.Thread(target=_run_graph, daemon=True)
    t1.start()

    # Wait up to 30s for the FIRST node event (zocai entry point)
    assert _started_event.wait(timeout=30), (
        f"Graph never produced first event within 30s. "
        f"error={result.get('error', 'unknown')}"
    )

    # Poll until requirements_interview_status appears (up to 90s more)
    resume_path = Path(project_dir) / "state" / "resume_state.json"
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            if resume_path.exists():
                data = json.loads(resume_path.read_text())
                if data.get("requirements_interview_status"):
                    time.sleep(0.5)  # flush final writes
                    yield result
                    return
        except Exception:
            pass
        time.sleep(1)

    # Timed out — still yield but mark the error
    result["error"] = (
        f"graph_run timed out waiting for requirements_interview_status. "
        f"resume exists: {resume_path.exists()}, error={result.get('error', 'unknown')}"
    )
    yield result
