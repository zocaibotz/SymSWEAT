"""
Playwright E2E tests for the SWEAT Monitoring UI.

These tests verify:
1. Login / logout flow
2. Lifecycle bucket logic for awaiting_human (HITL) projects
3. Interview question display and answer submission
4. Project detail view stage rendering

Run with:  pytest tests/test_monitoring_ui_e2e.py -v
Or standalone:  python -m playwright test tests/test_monitoring_ui_e2e.py
"""

import json
import tempfile
import threading
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sweat_env():
    """Environment vars needed by monitoring_api when it starts."""
    return {
        "SWEAT_USERS": "admin:testpass123",
        "MOONSHOT_API_KEY": "sk-fake",
        "MINIMAX_API_KEY": "sk-fake",
        "OPENAI_API_KEY": "sk-fake",
    }


@pytest.fixture(scope="module")
def test_projects_root(tmp_path_factory):
    """Creates a temp projects directory that mimics the real structure,
    including the KidsFunTodo project in various lifecycle states."""
    root = tmp_path_factory.mktemp("sweat_projects")

    # ---------------------------------------------------------------------------
    # KidsFunTodo — paused at requirement_master, awaiting_human
    # (the key scenario our lifecycle fix handles)
    # ---------------------------------------------------------------------------
    kt_root = root / "KidsFunTodo"
    kt_state = kt_root / "state"
    kt_state.mkdir(parents=True)

    (kt_state / "project_state.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "state_version": 2,
                "project_id": "KidsFunTodo",
                "project_slug": "kidsfuntodo",
                "lifecycle": {
                    "phase": "__end__",           # LangGraph paused at boundary
                    "status": "in_progress",
                    "current_run_id": "run_2026-04-11T05-52-43Z_a332e9",
                    "last_updated_utc": "2026-04-11T05-52:47Z",
                },
                "gates": {
                    "design_approved": False,
                    "tdd_ready": False,
                    "ci_passed": False,
                    "deployment_approved": False,
                },
                "artifacts": {},
            }
        ),
        encoding="utf-8",
    )

    (kt_state / "run_index.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "project_id": "KidsFunTodo",
                "latest_run_id": "run_2026-04-11T05-52-43Z_a332e9",
                "runs": {
                    "run_2026-04-11T05-52-43Z_a332e9": {
                        "status": "completed",   # LangGraph thread finished
                        "started_at_utc": "2026-04-11T05:52:43Z",
                        "ended_at_utc": "2026-04-11T05:52:47Z",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    events = [
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000001_43fe",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:43Z",
            "node": "zocai",
            "event_type": "run_start",
            "seq": 1,
            "payload": {"status": "running"},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000002_2e6e",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:43Z",
            "node": "zocai",
            "event_type": "node_enter",
            "seq": 2,
            "payload": {},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000003_6386",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:43Z",
            "node": "zocai",
            "event_type": "route_decision",
            "seq": 3,
            "payload": {"next_node": "req_master_interview"},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000004_32fe",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:43Z",
            "node": "zocai",
            "event_type": "node_exit",
            "seq": 4,
            "payload": {"status": "success", "next_agent": "req_master_interview"},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000005_7da4",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:43Z",
            "node": "zocai",
            "event_type": "state_patch_applied",
            "seq": 5,
            "payload": {},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000006_544c",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:43Z",
            "node": "req_master_interview",
            "event_type": "node_enter",
            "seq": 6,
            "payload": {},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000007_9d62",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:47Z",
            "node": "req_master_interview",
            "event_type": "route_decision",
            "seq": 7,
            "payload": {
                "next_node": "__end__",
                "requirements_present": False,
                "revision_reasons": ["missing_requirements"],
            },
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000008_eaf4",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:47Z",
            "node": "req_master_interview",
            "event_type": "node_exit",
            "seq": 8,
            "payload": {"status": "success", "next_agent": "__end__"},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000009_11df",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:47Z",
            "node": "req_master_interview",
            "event_type": "state_patch_applied",
            "seq": 9,
            "payload": {},
        },
        {
            "schema_version": "1.0.0",
            "event_id": "evt_000010_b51a",
            "run_id": "run_2026-04-11T05-52-43Z_a332e9",
            "project_id": "KidsFunTodo",
            "ts_utc": "2026-04-11T05-52:47Z",
            "node": "zocai",
            "event_type": "run_end",
            "seq": 10,
            "payload": {"status": "completed"},
        },
    ]
    (kt_state / "run_events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
    )

    (kt_state / "resume_state.json").write_text(
        json.dumps(
            {
                "project_state_version": 1,
                "requirements_open_questions": [
                    "What business outcome should this feature achieve?",
                    "What is in-scope and explicitly out-of-scope?",
                    "What are the acceptance criteria we must test?",
                    "Any constraints (security/performance/deadline/tech stack)?",
                ],
                "requirements_interview_status": "awaiting_human",
                "project_id": "KidsFunTodo",
                "run_started": True,
                "run_id": "run_2026-04-11T05-52-43Z_a332e9",
                "next_agent": "__end__",
                "requirements_revision_reasons": ["missing_requirements"],
                "snapshot_kind": "resume",
            }
        ),
        encoding="utf-8",
    )

    # ---------------------------------------------------------------------------
    # proj-active — genuinely in_progress, should show in Active tab
    # ---------------------------------------------------------------------------
    pa_root = root / "proj-active"
    pa_state = pa_root / "state"
    pa_state.mkdir(parents=True)

    (pa_state / "project_state.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "state_version": 2,
                "project_id": "proj-active",
                "project_slug": "proj-active",
                "lifecycle": {
                    "phase": "sdd_plan",
                    "status": "running",
                    "current_run_id": "run_active_1",
                    "last_updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
                "gates": {},
                "artifacts": {},
            }
        ),
        encoding="utf-8",
    )

    (pa_state / "run_index.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "project_id": "proj-active",
                "latest_run_id": "run_active_1",
                "runs": {
                    "run_active_1": {
                        "status": "running",
                        "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    (pa_state / "run_events.jsonl").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "event_id": "evt_a1",
                "run_id": "run_active_1",
                "project_id": "proj-active",
                "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "node": "sdd_plan",
                "event_type": "node_enter",
                "seq": 1,
                "payload": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    (pa_state / "resume_state.json").write_text(
        json.dumps({"requirements_interview_status": "complete", "project_id": "proj-active"}),
        encoding="utf-8",
    )

    # ---------------------------------------------------------------------------
    # proj-archived — genuinely old/completed, should show in Archived tab
    # ---------------------------------------------------------------------------
    pb_root = root / "proj-archived"
    pb_state = pb_root / "state"
    pb_state.mkdir(parents=True)

    (pb_state / "project_state.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "state_version": 2,
                "project_id": "proj-archived",
                "project_slug": "proj-archived",
                "lifecycle": {
                    "phase": "ci_deploy_automator",
                    "status": "completed",
                    "current_run_id": "run_old_1",
                    "last_updated_utc": "2026-03-01T10:00:00Z",
                },
                "gates": {"design_approved": True, "tdd_ready": True, "ci_passed": True, "deployment_approved": True},
                "artifacts": {},
            }
        ),
        encoding="utf-8",
    )

    (pb_state / "run_index.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "project_id": "proj-archived",
                "latest_run_id": "run_old_1",
                "runs": {
                    "run_old_1": {
                        "status": "completed",
                        "started_at_utc": "2026-03-01T09:00:00Z",
                        "ended_at_utc": "2026-03-01T10:00:00Z",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    (pb_state / "run_events.jsonl").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "event_id": "evt_b1",
                "run_id": "run_old_1",
                "project_id": "proj-archived",
                "ts_utc": "2026-03-01T10:00:00Z",
                "node": "deployer",
                "event_type": "node_exit",
                "seq": 1,
                "payload": {"status": "success"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    (pb_state / "resume_state.json").write_text(
        json.dumps({"requirements_interview_status": "complete", "project_id": "proj-archived"}),
        encoding="utf-8",
    )

    return root


@pytest.fixture(scope="module")
def app_server(sweat_env, test_projects_root):
    """Start the monitoring API in a background thread, yield the base URL, then stop."""
    import os
    from pathlib import Path as P

    # Set env vars in the OS environment so the server thread inherits them
    for k, v in sweat_env.items():
        os.environ[k] = v
    os.environ["PROJECTS_ROOT"] = str(test_projects_root)

    # Patch PROJECTS_ROOT in the module so the API uses our temp projects dir
    import src.monitoring_api as api_module
    original_root = api_module.PROJECTS_ROOT
    api_module.PROJECTS_ROOT = P(test_projects_root)

    from src.monitoring_api import create_app
    import uvicorn

    app = create_app()
    port = 18765
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=lambda: server.run(), daemon=True)
    thread.start()
    time.sleep(1.5)   # let server bind

    yield f"http://127.0.0.1:{port}"

    # Restore
    api_module.PROJECTS_ROOT = original_root
    for k in sweat_env:
        if k in os.environ:
            del os.environ[k]
    if "PROJECTS_ROOT" in os.environ:
        del os.environ["PROJECTS_ROOT"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def do_login(page, username: str, password: str, base_url: str):
    page.goto(f"{base_url}/ui")
    page.wait_for_url(f"{base_url}/ui")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/ui")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoginFlow:
    def test_login_page_renders(self, page, app_server):
        page.goto(f"{app_server}/ui")
        page.wait_for_url(f"{app_server}/ui")
        assert page.locator('input[name="username"]').is_visible()
        assert page.locator('input[name="password"]').is_visible()
        assert page.locator('button[type="submit"]').is_visible()
        assert "SWEAT Command Center" in page.content()

    def test_login_success(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)
        # Should land back on /ui (dashboard), not redirected to login
        # The URL may or may not have a trailing slash — normalise before comparing
        assert page.url.rstrip("/") == f"{app_server}/ui".rstrip("/"), f"Expected dashboard URL, got {page.url}"
        # No 401 anywhere in the DOM
        assert "401" not in page.content()

    def test_login_failure_rejects(self, page, app_server):
        page.goto(f"{app_server}/ui")
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "wrongpassword")
        page.click('button[type="submit"]')
        # Should stay on login page with 401 message
        assert page.locator("text=Invalid username or password").is_visible()


class TestLifecycleBucket:
    """Verify that awaiting_human projects stay in the Active tab, not Archived."""

    def test_awaiting_human_project_in_active_tab(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)

        # KidsFunTodo — even though its run is "completed" and phase is "__end__",
        # its interview status is "awaiting_human" so it must be in Active
        page.click("#tab-main")   # Active tab
        page.wait_for_timeout(800)
        html = page.content()
        assert "KidsFunTodo" in html, "KidsFunTodo should appear in Active tab"
        # Lifecycle bucket label should be "active" (not "archived")
        active_row = page.locator("tr", has_text="KidsFunTodo")
        assert active_row.count() >= 1

    def test_truly_archived_project_in_archived_tab(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)
        page.click("#tab-archived")
        page.wait_for_timeout(800)
        html = page.content()
        assert "proj-archived" in html, "proj-archived should appear in Archived tab"

    def test_active_project_in_active_tab(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)
        page.click("#tab-main")
        page.wait_for_timeout(800)
        html = page.content()
        assert "proj-active" in html, "proj-active should appear in Active tab"


class TestProjectDetail:
    def test_project_detail_loads(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)
        page.goto(f"{app_server}/ui/project/KidsFunTodo")
        page.wait_for_url(f"{app_server}/ui/project/KidsFunTodo")
        # Status line should contain "requirement_master"
        assert "requirement_master" in page.locator("#project-meta").inner_text()

    def test_interview_section_visible_for_awaiting_human(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)
        page.goto(f"{app_server}/ui/project/KidsFunTodo")
        page.wait_for_timeout(1000)
        section = page.locator("#interview-section")
        assert section.is_visible(), "Interview section should be visible for awaiting_human project"
        # Should show all 4 questions
        questions_el = page.locator("#interview-questions")
        assert "What business outcome" in questions_el.inner_text()
        assert "in-scope" in questions_el.inner_text()
        assert "acceptance criteria" in questions_el.inner_text()
        assert "constraints" in questions_el.inner_text()

    def test_interview_section_absent_when_no_pending_questions(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)
        page.goto(f"{app_server}/ui/project/proj-active")
        page.wait_for_timeout(1000)
        section = page.locator("#interview-section")
        # Should be hidden (display:none) for projects without pending questions
        assert section.is_hidden(), "Interview section should be hidden for completed interview"


class TestInterviewAnswerSubmission:
    def test_submit_answer_removes_question(self, page, app_server):
        """Typing a full sentence and submitting removes that question from the list."""
        do_login(page, "admin", "testpass123", app_server)
        page.goto(f"{app_server}/ui/project/KidsFunTodo")
        page.wait_for_timeout(1000)

        # Find the first unanswered textarea
        textarea = page.locator('textarea[data-qhash]').first
        assert textarea.is_visible(), "First question textarea should be visible"
        textarea.fill('A fun app to help kids manage their daily tasks and build good habits.')

        # Verify the text stuck (form-preservation sanity check)
        assert 'A fun app' in textarea.input_value()

        # Submit via the Submit Answer button in the interview section
        submit_btn = page.locator('#interview-questions button').first
        with page.expect_response(f"{app_server}/api/monitoring/projects/KidsFunTodo/interview/answer", timeout=8000) as resp:
            submit_btn.click()
        assert resp.value.ok, f"Answer submission failed: {resp.value.status}"

        # After the POST completes, the question should be gone from the list
        page.wait_for_timeout(1500)
        after_text = page.locator("#interview-questions").inner_text()
        assert "What business outcome" not in after_text, f"First question should be gone after submission. Got: {after_text}"

    def test_typing_survives_periodic_reload(self, page, app_server):
        """Simulate the 10-second polling interval: fill text, trigger a reload,
        verify the text survives the re-render (form-preservation fix)."""
        do_login(page, "admin", "testpass123", app_server)
        page.goto(f"{app_server}/ui/project/KidsFunTodo")
        page.wait_for_timeout(500)

        textarea = page.locator('textarea[data-qhash]').first
        textarea.fill('This answer should survive a reload')
        page.wait_for_timeout(500)

        # Trigger load() manually (this is what the 10-second setInterval does)
        page.evaluate('load()')
        page.wait_for_timeout(1000)

        # Text should still be present after re-render
        textarea_after = page.locator('textarea[data-qhash]').first
        assert 'This answer should survive a reload' in textarea_after.input_value(), \
            "Typed text should be preserved across the periodic re-render"

    def test_all_four_questions_answered_hides_interview_section(self, page, app_server):
        """Answering all 4 interview questions should remove the interview section entirely."""
        do_login(page, "admin", "testpass123", app_server)
        page.goto(f"{app_server}/ui/project/KidsFunTodo")
        page.wait_for_timeout(1000)

        answers = [
            "A mobile app that helps children track and complete their daily tasks.",
            "In-scope: task creation, reminders, progress tracking. Out-of-scope: social features, ads.",
            "A parent can create tasks, child marks them done, parent gets notified.",
            "Must work on iOS and Android; must be accessible to children ages 5-12.",
        ]

        for i, answer_text in enumerate(answers):
            # Keep re-locating since the DOM is rebuilt after each submission
            # Use a generous timeout; the API write + reload can take a moment
            try:
                page.wait_for_selector('textarea[data-qhash]', timeout=12000)
            except Exception:
                # No more textareas = all questions answered
                break
            textarea = page.locator('textarea[data-qhash]').first
            textarea.fill(answer_text)
            btn = page.locator('#interview-questions button').first
            with page.expect_response(f"{app_server}/api/monitoring/projects/KidsFunTodo/interview/answer", timeout=12000):
                btn.click()
            page.wait_for_timeout(1500)

        # After all 4 are answered, the interview section should be hidden
        interview_section = page.locator("#interview-section")
        assert interview_section.is_hidden(), \
            f"Interview section should be hidden after all questions answered. Section HTML: {interview_section.inner_html()}"


class TestStageRendering:
    def test_pipeline_stages_render_in_order(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)
        page.goto(f"{app_server}/ui/project/KidsFunTodo")
        page.wait_for_timeout(1000)
        progress = page.locator("#stage-progress")
        text = progress.inner_text()
        assert "requirement_master" in text, "requirement_master should be the active stage"
        # Active stage should be highlighted (blue border)
        assert "requirement_master" in text


class TestLogout:
    def test_logout_redirects_to_login(self, page, app_server):
        do_login(page, "admin", "testpass123", app_server)
        page.click('button:has-text("Logout")')
        page.wait_for_url(f"{app_server}/ui")
        # After logout, the login form should be visible again
        assert page.locator('input[name="username"]').is_visible()
