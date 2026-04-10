from typing import Any, Dict, List


def _is_non_empty_str(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def validate_state_patch(node_name: str, patch: Dict[str, Any]) -> List[str]:
    """Lightweight contract checks for high-risk handoff nodes.

    Returns list of validation errors.
    """
    errs: List[str] = []
    p = patch or {}

    if node_name == "req_master_interview":
        st = p.get("requirements_interview_status")
        if st is not None and st not in {"in_progress", "complete", "blocked", "needs_revision", "awaiting_human"}:
            errs.append("requirements_interview_status invalid")

    if node_name == "sdd_specify":
        status = p.get("sdd_spec_status")
        if status is not None and status not in {"draft", "approved"}:
            errs.append("sdd_spec_status invalid")
        if status == "approved" and not _is_non_empty_str(p.get("sdd_spec_path")):
            errs.append("approved sdd_specify must set sdd_spec_path")

    if node_name == "design_approval_gate":
        st = p.get("design_approval_status")
        if st is not None and st not in {"approved", "rejected"}:
            errs.append("design_approval_status invalid")

    if node_name == "test_readiness_gate":
        st = p.get("test_readiness_status")
        if st is not None and st not in {"ready", "not_ready"}:
            errs.append("test_readiness_status invalid")

    if node_name == "pipeline":
        st = p.get("ci_pipeline_status")
        if st is not None and str(st).upper() not in {"PASSED", "FAILED"}:
            errs.append("ci_pipeline_status invalid")

    if node_name == "codesmith":
        na = p.get("next_agent")
        if na is not None and na not in {"gatekeeper", "codesmith", "bughunter", "__end__"}:
            errs.append("codesmith next_agent invalid")

    if node_name == "gatekeeper":
        na = p.get("next_agent")
        if na is not None and na not in {"pipeline", "codesmith", "bughunter", "__end__"}:
            errs.append("gatekeeper next_agent invalid")

    if node_name == "automator":
        if p.get("automation_completed") is not None and not isinstance(p.get("automation_completed"), bool):
            errs.append("automation_completed must be bool")

    if node_name == "deployer":
        if p.get("infrastructure_config") is not None and not _is_non_empty_str(p.get("infrastructure_config")):
            errs.append("infrastructure_config invalid")

    return errs
