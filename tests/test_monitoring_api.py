import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from src import monitoring_api


def _seed_project(tmp_path: Path, project_id: str = "proj-a") -> Path:
    root = tmp_path / "projects" / project_id
    state = root / "state"
    state.mkdir(parents=True)

    (state / "project_state.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "state_version": 3,
                "project_id": project_id,
                "project_slug": "alpha-monitor",
                "lifecycle": {
                    "phase": "sdd_plan",
                    "status": "in_progress",
                    "current_run_id": "run_1",
                    "last_updated_utc": "2026-03-03T00:00:00Z",
                },
                "gates": {
                    "design_approved": True,
                    "tdd_ready": False,
                    "ci_passed": False,
                    "deployment_approved": False,
                },
                "artifacts": {"spec": str(root / "docs/spec/spec.md")},
            }
        ),
        encoding="utf-8",
    )

    (state / "run_index.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "project_id": project_id,
                "latest_run_id": "run_1",
                "runs": {
                    "run_1": {
                        "status": "failed",
                        "started_at_utc": "2026-03-03T00:00:00Z",
                        "ended_at_utc": "2026-03-03T00:01:00Z",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    events = [
        {
            "schema_version": "1.0.0",
            "event_id": "evt_1",
            "run_id": "run_1",
            "project_id": project_id,
            "ts_utc": "2026-03-03T00:00:01Z",
            "node": "req_master_interview",
            "event_type": "route_decision",
            "seq": 1,
            "payload": {"next_node": "sdd_specify"},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_2",
            "run_id": "run_1",
            "project_id": project_id,
            "ts_utc": "2026-03-03T00:00:02Z",
            "node": "sdd_plan",
            "event_type": "node_exit",
            "seq": 2,
            "payload": {"status": "success"},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_3",
            "run_id": "run_1",
            "project_id": project_id,
            "ts_utc": "2026-03-03T00:00:03Z",
            "node": "pipeline",
            "event_type": "validation_error",
            "seq": 3,
            "payload": {"error": "pipeline broke"},
        },
    ]
    (state / "run_events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    resume = {
        "requirements_interview_status": "in_progress",
        "requirements_open_questions": ["What is SLA?", "Who owns release?"],
    }
    (state / "resume_state.json").write_text(json.dumps(resume), encoding="utf-8")

    docs = root / "docs/spec"
    docs.mkdir(parents=True)
    (docs / "spec.md").write_text("# Spec", encoding="utf-8")
    return root


def test_projects_and_details(monkeypatch, tmp_path):
    _seed_project(tmp_path)
    monkeypatch.setattr(monitoring_api, "PROJECTS_ROOT", tmp_path / "projects")

    app = monitoring_api.create_app()
    client = TestClient(app)

    lst = client.get("/api/monitoring/projects")
    assert lst.status_code == 200
    body = lst.json()
    assert body["total_count"] == 1
    assert body["projects"][0]["current_stage"] == "plan"
    assert body["projects"][0]["blockers"]

    details = client.get("/api/monitoring/projects/proj-a")
    assert details.status_code == 200
    d = details.json()
    assert d["stage_details"]["stage"] == "plan"
    assert d["interview"]["pending_questions"][0] == "What is SLA?"
    assert any(a["key"] == "spec" for a in d["artifacts"])


def test_interview_answer_and_artifact_preview(monkeypatch, tmp_path):
    _seed_project(tmp_path)
    monkeypatch.setattr(monitoring_api, "PROJECTS_ROOT", tmp_path / "projects")

    app = monitoring_api.create_app()
    client = TestClient(app)

    post = client.post(
        "/api/monitoring/projects/proj-a/interview/answer",
        json={"question": "What is SLA?", "answer": "99.9%"},
    )
    assert post.status_code == 200

    view = client.get("/api/monitoring/projects/proj-a/interview")
    assert view.status_code == 200
    payload = view.json()
    assert "What is SLA?" not in payload["pending_questions"]
    assert payload["answered_count"] == 1

    artifact = client.get("/api/monitoring/projects/proj-a/artifacts/spec")
    assert artifact.status_code == 200
    preview = artifact.json().get("preview")
    assert "# Spec" in preview


def test_stream_emits_snapshot(monkeypatch, tmp_path):
    _seed_project(tmp_path)
    monkeypatch.setattr(monitoring_api, "PROJECTS_ROOT", tmp_path / "projects")

    app = monitoring_api.create_app()
    client = TestClient(app)

    with client.stream("GET", "/api/monitoring/stream?project_id=proj-a&heartbeat_seconds=2&max_events=1") as response:
        assert response.status_code == 200
        first_chunk = next(response.iter_text())
        assert "event: snapshot" in first_chunk
