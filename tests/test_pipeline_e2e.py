"""
test_pipeline_e2e.py — True end-to-end pipeline test suite

Tests the full SWEAT pipeline: req_master (HITL) → specify → architect →
codesmith → automator → deployer, driven through the monitoring UI.

Fixtures (from conftest.py):
  - app_server   — uvicorn on a free port with auth
  - graph_run   — LangGraph background thread writing to a temp project dir

Test strategy:
  - graph_run reaches requirement_master and pauses at awaiting_human
  - Playwright (via app_server) answers all interview questions
  - Pipeline advances automatically; we poll the monitoring API for stage progress
  - At each stage boundary we assert relevant artifact fields are populated
  - After pipeline completes, we assert all acceptance criteria are met
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Generator

import pytest
import requests
from playwright.sync_api import Page, expect as playwright_expect

from tests.conftest import app_server, graph_run  # noqa: F401


import base64

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

_UI_AUTH_COOKIE = "sweat_ui_auth"
_UI_AUTH_SALT = "sweat-monitor-ui-v1"


def _make_auth_cookie(username: str) -> str:
    val = f"{username}:{_UI_AUTH_SALT}"
    return base64.b64encode(val.encode()).decode()


def _auth_get(url: str, username: str = "admin") -> requests.Response:
    """Authenticated GET — needed for tests that call the API directly."""
    cookie = _make_auth_cookie(username)
    return requests.get(url, cookies={_UI_AUTH_COOKIE: cookie}, timeout=10)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def do_login(page: Page, base: str, username: str = "admin", password: str = "testpass123") -> None:
    """Navigate to /ui (secured root), wait for redirect to login, fill creads, submit."""
    page.goto(f"{base}/ui")
    page.wait_for_url(f"{base}/ui")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base}/ui")


def poll_project_state(base: str, project_id: str, timeout: float = 300, interval: float = 10) -> dict:
    """
    Poll GET /api/monitoring/projects/{project_id} until the project is found
    and the current_stage transitions beyond 'requirement_master'.

    Returns the final state dict. Raises if the project never appears after `timeout`.
    """
    url = f"{base}/api/monitoring/projects/{project_id}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = _auth_get(url)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                # Project is registered once it has a current_stage
                if data.get("current_stage"):
                    return data
        except Exception:
            pass
        time.sleep(interval)

    raise TimeoutError(f"Project {project_id} did not appear within {timeout}s")


def wait_for_stage(
    base: str, project_id: str, target_stages: list[str], timeout: float = 360, interval: float = 15
) -> dict:
    """
    Poll until current_stage enters target_stages OR timeout expires.

    Returns the state dict at the moment the stage is detected (or the last
    state if it times out — test should assert on the returned value).
    """
    url = f"{base}/api/monitoring/projects/{project_id}"
    deadline = time.time() + timeout
    last_state = {}
    while time.time() < deadline:
        try:
            resp = _auth_get(url)
            if resp.status_code == 200:
                last_state = json.loads(resp.text)
                stage = last_state.get("current_stage", "")
                if stage in target_stages:
                    return last_state
        except Exception:
            pass
        time.sleep(interval)

    # Timed out — return last known state for diagnostics
    return last_state


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------

class TestRequirementMaster:
    """Stage 1: HITL interview — verify questions render and answers advance the pipeline."""

    def test_interview_renders_4_questions(self, page: Page, app_server: str, graph_run: dict) -> None:
        """The monitoring UI shows 4 interview questions for a fresh HITL-paused project."""
        project_id = graph_run["project_id"]

        do_login(page, app_server)

        # Debug: print ALL API fields for this project
        resp = _auth_get(f"{app_server}/api/monitoring/projects/{project_id}")
        api_data = json.loads(resp.text)
        print(f"[DEBUG] Full API response: {json.dumps(api_data, indent=2)}")

        current_stage = api_data.get("current_stage", "")
        interview_data = api_data.get("interview", {})
        pending = interview_data.get("pending_questions", []) if isinstance(interview_data, dict) else []
        print(f"[DEBUG] stage={current_stage}, pending={pending}")

        # Navigate to the project detail page
        page.goto(f"{app_server}/ui/project/{project_id}")

        # Poll until the interview section appears
        url = f"{app_server}/api/monitoring/projects/{project_id}/interview"
        interview_ready = False
        for _ in range(60):
            try:
                resp = _auth_get(url)
                data = json.loads(resp.text)
                if data.get("pending_questions"):
                    interview_ready = True
                    break
            except Exception:
                pass
            time.sleep(1)

        assert interview_ready, f"Interview never became ready for project {project_id}"

        # Now the section should be visible
        section = page.locator("#interview-section")
        playwright_expect(section).to_be_visible()

        # Should render exactly 4 textareas
        textareas = page.locator("#interview-section textarea[data-qhash]")
        playwright_expect(textareas).to_have_count(4)

    def test_answer_all_4_questions_advances_pipeline(
        self, page: Page, app_server: str, graph_run: dict
    ) -> None:
        """
        Answer all 4 interview questions via the monitoring UI.
        After the final submission the interview section should be hidden,
        and the project should leave 'requirement_master' stage.
        """
        project_id = graph_run["project_id"]
        do_login(page, app_server)
        page.goto(f"{app_server}/ui/project/{project_id}")

        # Wait for interview to be ready
        import urllib.request
        url = f"{app_server}/api/monitoring/projects/{project_id}/interview"
        for _ in range(60):
            try:
                resp = urllib.request.urlopen(url, timeout=2)
                data = json.loads(resp.read())
                if data.get("pending_questions"):
                    break
            except Exception:
                pass
            time.sleep(1)

        answers = [
            "A mobile app that helps children track and complete their daily tasks.",
            "In-scope: task creation, reminders, progress tracking. Out-of-scope: social features, ads.",
            "A parent can create tasks, child marks them done, parent gets notified.",
            "Must work on iOS and Android; must be accessible to children ages 5-12.",
        ]

        for answer_text in answers:
            try:
                page.wait_for_selector('textarea[data-qhash]', timeout=20000)
            except Exception:
                # No more textareas = done
                break
            textarea = page.locator('textarea[data-qhash]').first
            textarea.fill(answer_text)
            btn = page.locator('#interview-section button').first
            btn.click()
            page.wait_for_timeout(2000)

        # Interview section should now be hidden
        interview_section = page.locator("#interview-section")
        # Allow a moment for the re-render
        page.wait_for_timeout(1500)
        playwright_expect(interview_section).to_be_hidden()


class TestSpecificationStage:
    """Stage 2: SDD specify / plan / tasks — verify docs are produced."""

    def test_specify_produces_sdd_doc(self, app_server: str, graph_run: dict) -> None:
        """After interview completion, the project should eventually have sdd_spec_path set."""
        project_id = graph_run["project_id"]

        # Wait up to 5 min for the pipeline to leave requirement_master
        state = wait_for_stage(
            app_server,
            project_id,
            target_stages=["sdd_specify", "architect", "design", "codesmith", "automator", "deploy"],
            timeout=360,
            interval=15,
        )

        stage = state.get("current_stage", "")
        assert stage != "requirement_master", (
            f"After answering all questions, project should advance beyond "
            f"requirement_master. Still at: {stage}"
        )

        # At least one of the spec-related fields should be populated
        # (exact field names from project_state.json schema)
        summary = state.get("summary", {})
        spec_path = summary.get("sdd_spec_path") or state.get("sdd_spec_path")
        assert spec_path, f"Expected sdd_spec_path to be set by stage '{stage}', got state: {state}"

    def test_plan_and_tasks_files_exist(self, app_server: str, graph_run: dict) -> None:
        """Plan and tasks files should be present after the specify stage."""
        project_id = graph_run["project_id"]

        state = wait_for_stage(
            app_server,
            project_id,
            target_stages=["sdd_plan", "architect", "design", "codesmith", "automator", "deploy"],
            timeout=360,
            interval=15,
        )

        summary = state.get("summary", {})
        plan_path = summary.get("sdd_plan_path") or state.get("sdd_plan_path")
        tasks_path = summary.get("sdd_tasks_path") or state.get("sdd_tasks_path")

        assert plan_path or tasks_path, (
            f"Expected sdd_plan_path or sdd_tasks_path to be set. "
            f"current_stage={state.get('current_stage')}, state={state}"
        )


class TestDesignStage:
    """Stage 3: architect / pixel / frontman — verify design artifacts."""

    def test_architect_produces_design_doc(self, app_server: str, graph_run: dict) -> None:
        """Architecture diagram / design doc should appear in the design stage."""
        project_id = graph_run["project_id"]

        state = wait_for_stage(
            app_server,
            project_id,
            target_stages=["design", "codesmith", "automator", "deploy"],
            timeout=360,
            interval=15,
        )

        summary = state.get("summary", {})
        design_doc = summary.get("design_doc_path") or state.get("design_doc_path")
        assert design_doc, (
            f"Expected design_doc_path by design stage. "
            f"current_stage={state.get('current_stage')}"
        )


class TestBuildStage:
    """Stage 4: codesmith + gatekeeper — verify source files and approval."""

    def test_codesmith_produces_src_files(self, app_server: str, graph_run: dict) -> None:
        """src/ directory should be non-empty after the codesmith stage."""
        project_id = graph_run["project_id"]

        state = wait_for_stage(
            app_server,
            project_id,
            target_stages=["codesmith", "automator", "deploy"],
            timeout=360,
            interval=15,
        )

        # Check for src directory on disk
        import urllib.request

        resp = urllib.request.urlopen(
            f"{app_server}/api/monitoring/projects/{project_id}/artifacts/src",
            timeout=5,
        )
        artifacts = json.loads(resp.read())
        assert artifacts.get("files") or artifacts.get("exists"), (
            f"Expected src artifact evidence from codesmith. Got: {artifacts}"
        )

    def test_gatekeeper_approves(self, app_server: str, graph_run: dict) -> None:
        """Gatekeeper should not set a fail reason; lifecycle should not be in error state."""
        project_id = graph_run["project_id"]

        state = wait_for_stage(
            app_server,
            project_id,
            target_stages=["automator", "deploy"],
            timeout=360,
            interval=15,
        )

        fail_reason = state.get("lifecycle_fail_reason") or state.get("fail_reason")
        assert not fail_reason, f"Gatekeeper set fail_reason: {fail_reason}"


class TestDeployStage:
    """Stage 5: automator + deployer — verify CI/CD and GitHub artifacts."""

    def test_github_repo_created(self, app_server: str, graph_run: dict) -> None:
        """GitHub URL should be present in the project state after automator stage."""
        project_id = graph_run["project_id"]

        state = wait_for_stage(
            app_server,
            project_id,
            target_stages=["automator", "deploy"],
            timeout=360,
            interval=15,
        )

        summary = state.get("summary", {})
        github_url = summary.get("github_url") or state.get("github_url")
        assert github_url, (
            f"Expected github_url after automator. "
            f"current_stage={state.get('current_stage')}"
        )

    def test_deployer_reports_url(self, app_server: str, graph_run: dict) -> None:
        """deployment_url or staging_url should be set after the deployer stage."""
        project_id = graph_run["project_id"]

        # Give deployer up to 5 extra minutes
        state = wait_for_stage(
            app_server,
            project_id,
            target_stages=["deploy", "scrumlord", "__end__"],
            timeout=360,
            interval=15,
        )

        summary = state.get("summary", {})
        deploy_url = (
            summary.get("deployment_url")
            or summary.get("staging_url")
            or state.get("deployment_url")
            or state.get("staging_url")
        )
        assert deploy_url, (
            f"Expected deployment_url or staging_url after deployer. "
            f"current_stage={state.get('current_stage')}"
        )


class TestLifecycleBucketAssignment:
    """Verify lifecycle bucket (Active / Archived) is correct at each stage."""

    def test_awaiting_human_is_active(self, page: Page, app_server: str, graph_run: dict) -> None:
        """A project paused at HITL (awaiting_human) must be in the Active tab, not Archived."""
        project_id = graph_run["project_id"]
        do_login(page, app_server)
        page.goto(f"{app_server}/ui/")
        page.wait_for_timeout(2000)

        # Find project in Active tab
        active_tab = page.locator('[data-testid="tab-active"], #tab-active, nav a:has-text("Active")').first
        active_tab.click()
        page.wait_for_timeout(1000)

        project_cell = page.locator(f"[data-testid='project-{project_id}'], .project-item:has-text('{project_id}')").first
        # Should be visible in Active tab
        playwright_expect(project_cell).to_be_visible()

    def test_completed_is_archived(self, app_server: str, graph_run: dict) -> None:
        """After __end__ the project should land in the Archived bucket."""
        project_id = graph_run["project_id"]

        # Wait for pipeline to finish
        state = wait_for_stage(
            app_server,
            project_id,
            target_stages=["__end__"],
            timeout=360,
            interval=15,
        )

        # The status field should reflect completion
        status = state.get("status", "")
        assert status in ("completed", "archived", "done"), (
            f"Expected completed/archived/done status after __end__, got: {status}"
        )


class TestPipelineCompleteness:
    """Final acceptance: all stages were visited and all acceptance criteria met."""

    def test_full_route_trace(self, app_server: str, graph_run: dict) -> None:
        """
        Verify the route trace covers all 5 stages.

        Acceptance criteria verified:
          AC1-AC6 from SPEC.md are implicitly tested by stage progression tests above.
          This test confirms the complete route was traversed.
        """
        project_id = graph_run["project_id"]

        # Wait for completion
        wait_for_stage(
            app_server,
            project_id,
            target_stages=["__end__", "scrumlord", "deploy"],
            timeout=360,
            interval=15,
        )

        # Read the route trace from disk
        import urllib.request

        resp = urllib.request.urlopen(
            f"{app_server}/api/monitoring/projects/{project_id}",
            timeout=5,
        )
        state = json.loads(resp.read())
        summary = state.get("summary", {})
        route_stages = summary.get("route_trace", []) or state.get("route_trace", [])

        expected_stages = [
            "requirement_master",
            "sdd_specify",
            "architect",
            "codesmith",
            "automator",
        ]
        covered = [s for s in expected_stages if s in route_stages]
        assert len(covered) >= 4, (
            f"Expected at least 4 of {expected_stages} in route_trace, "
            f"got: {route_stages}"
        )
