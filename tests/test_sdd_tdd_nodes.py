import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.workers import (
    sdd_specify_node,
    sdd_plan_node,
    sdd_tasks_node,
    design_approval_gate_node,
    tdd_orchestrator_node,
    unit_test_author_node,
    integration_test_author_node,
    playwright_test_author_node,
    tdd_readiness_gate_node,
)


def test_sdd_nodes_happy_path():
    state = {"requirements": {"name": "demo", "acceptance_criteria": ["User can create item"]}}
    a = sdd_specify_node(state)
    assert a["sdd_spec_status"] == "approved"
    assert a["sdd_quality_score"] > 0
    assert a["traceability_map_path"] == "docs/spec/traceability_map.json"


def test_sdd_specify_requires_acceptance_criteria():
    out = sdd_specify_node({"requirements": {"name": "demo"}})
    assert out["sdd_spec_status"] == "draft"
    assert out["next_agent"] == "req_master_interview"


def test_sdd_specify_blocks_non_testable_acceptance_criteria():
    out = sdd_specify_node({"requirements": {"name": "demo", "acceptance_criteria": ["be awesome"]}})
    assert out["sdd_spec_status"] == "draft"
    assert out["next_agent"] == "req_master_interview"
    assert "testable" in out["messages"][0].content.lower()

    b = sdd_plan_node({"requirements": {"name": "demo", "acceptance_criteria": ["x"]}})
    assert b["sdd_status"] == "plan_done"

    c = sdd_tasks_node({})
    assert c["sdd_status"] == "tasks_done"


def test_design_and_tdd_gate_happy_path():
    design_state = {
        "sdd_spec_path": "docs/spec/spec.md",
        "sdd_plan_path": "docs/spec/plan.md",
        "sdd_tasks_path": "docs/spec/tasks.md",
        "architecture_docs": "ok",
        "ux_wireframes": "ok",
        "ui_component_library": "src/App.jsx",
    }
    d = design_approval_gate_node(design_state)
    assert d["design_approval_status"] == "approved"

    t = tdd_orchestrator_node({})
    assert t["coverage_target"] >= 95

    u = unit_test_author_node({"coverage_target": 95})
    i = integration_test_author_node({})
    p = playwright_test_author_node({})

    gate = tdd_readiness_gate_node({
        "unit_test_plan_path": u["unit_test_plan_path"],
        "integration_test_plan_path": i["integration_test_plan_path"],
        "playwright_test_plan_path": p["playwright_test_plan_path"],
        "coverage_target": 95,
    })
    assert gate["test_readiness_status"] == "ready"
    assert gate["next_agent"] == "github_bootstrap"
