from pathlib import Path


def test_frontend_contains_critical_render_states():
    app = Path("src/App.jsx").read_text(encoding="utf-8")

    required_labels = [
        "Loading monitoring data...",
        "API Error:",
        "Live Stream:",
        "Project Monitoring Dashboard",
        "Current Stage Deep Details",
        "Timeline / History",
        "Blockers / Failures",
        "Req Master Interview",
        "Artifact Registry",
    ]
    for label in required_labels:
        assert label in app


def test_frontend_stage_flow_matches_sweat_pipeline():
    app = Path("src/App.jsx").read_text(encoding="utf-8")
    expected_stages = [
        "requirement_master",
        "specify",
        "plan",
        "tasks",
        "architect",
        "pixel",
        "frontman",
        "code_smith",
        "review",
        "ci_deploy_automator",
    ]
    for stage in expected_stages:
        assert stage in app
