from __future__ import annotations

from typing import Any, Dict


def compute_sweat_kpis(state: Dict[str, Any]) -> Dict[str, float]:
    checks = {
        "requirements_complete": 1.0 if state.get("requirements_interview_status") == "complete" else 0.0,
        "design_approved": 1.0 if state.get("design_approval_status") == "approved" else 0.0,
        "tdd_ready": 1.0 if state.get("test_readiness_status") == "ready" else 0.0,
        "ci_passed": 1.0 if state.get("ci_pipeline_status") in {"passed", "success"} else 0.0,
        "deployed": 1.0 if bool(state.get("deployment_url")) else 0.0,
    }
    checks["overall"] = sum(checks.values()) / len(checks)
    return checks
