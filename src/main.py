import sys
import os
import shutil
import time
import json
import hashlib

# Ensure src is in pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Dict, TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
from src.state import ProjectState
from src.agents.orchestrator import orchestrator_node
from src.agents.req_master import req_master_node
from src.agents.workers import (
    req_master_interview_node,
    sdd_specify_node,
    sdd_plan_node,
    sdd_tasks_node,
    architect_node,
    pixel_node,
    frontman_node,
    design_approval_gate_node,
    tdd_orchestrator_node,
    unit_test_author_node,
    integration_test_author_node,
    playwright_test_author_node,
    tdd_readiness_gate_node,
    github_bootstrap_node,
    codesmith_node,
    bughunter_node,
    gatekeeper_node,
    pipeline_node,
    integrator_node,
    automator_node,
    deployer_node,
    scrumlord_node,
    sprint_executor_node
)
from src.utils.state_store import StateStore, VersionConflictError
from src.utils.resume_state import write_resume_state, load_resume_state
from src.utils.contracts import validate_state_patch

def _route_next(state):
    return state.get("next_agent", "__end__")


def _apply_runtime_guards(node_name: str, state: dict, result: dict) -> dict:
    """Global runtime guards: HITL pause + loop detection/escalation across critical remediation cycles."""
    result = dict(result or {})

    # HITL guard: when req_master asks for human input, keep run paused.
    if node_name == "req_master_interview" and result.get("human_input_required"):
        result["next_agent"] = "__end__"

    # Loop detection guard for codesmith <-> gatekeeper bouncing.
    nxt = result.get("next_agent")
    pair_hit = (node_name == "codesmith" and nxt == "gatekeeper") or (node_name == "gatekeeper" and nxt == "codesmith")
    bounce = int(state.get("codesmith_gatekeeper_bounce_count") or 0)
    escalation_count = int(state.get("loop_escalation_count") or 0)
    loop_budget = int(os.getenv("SWEAT_CODE_REVIEW_LOOP_BUDGET", "10"))

    if pair_hit:
        bounce += 1
    else:
        bounce = 0

    result["codesmith_gatekeeper_bounce_count"] = bounce

    if bounce >= loop_budget:
        escalation_count += 1
        result["loop_escalation_count"] = escalation_count
        result["codesmith_gatekeeper_bounce_count"] = 0

        if escalation_count == 1:
            result["next_agent"] = "bughunter"
            msgs = list(result.get("messages") or [])
            msgs.append(AIMessage(content=f"Loop guard triggered after {loop_budget} CodeSmith↔Gatekeeper bounces. Escalating to BugHunter for diagnostic test plan."))
            result["messages"] = msgs
        else:
            result["next_agent"] = "__end__"
            result["lifecycle_fail_reason"] = "codesmith_gatekeeper_loop_exhausted"
            msgs = list(result.get("messages") or [])
            msgs.append(AIMessage(content="Loop guard triggered again after escalation. Halting for human intervention."))
            result["messages"] = msgs

    # Loop detection guard for pipeline -> bughunter -> gatekeeper -> pipeline cycling.
    nxt = result.get("next_agent")
    remediation_hit = (
        (node_name == "pipeline" and nxt == "bughunter")
        or (node_name == "bughunter" and nxt == "gatekeeper")
        or (node_name == "gatekeeper" and nxt == "pipeline")
    )
    remediation_bounce = int(state.get("pipeline_remediation_bounce_count") or 0)
    remediation_escalations = int(state.get("pipeline_remediation_escalation_count") or 0)
    remediation_budget = int(os.getenv("SWEAT_PIPELINE_REMEDIATION_LOOP_BUDGET", "6"))

    if remediation_hit:
        remediation_bounce += 1
    else:
        remediation_bounce = 0

    result["pipeline_remediation_bounce_count"] = remediation_bounce

    if remediation_bounce >= remediation_budget:
        remediation_escalations += 1
        result["pipeline_remediation_escalation_count"] = remediation_escalations
        result["pipeline_remediation_bounce_count"] = 0

        msgs = list(result.get("messages") or [])
        if remediation_escalations == 1:
            result["next_agent"] = "codesmith"
            result["decision_reason_code"] = "pipeline_bughunter_gatekeeper_loop_escalated"
            msgs.append(AIMessage(content=f"Loop guard detected repeated pipeline→bughunter→gatekeeper cycling ({remediation_budget} transitions). Escalating to CodeSmith for direct remediation."))
        else:
            result["next_agent"] = "__end__"
            result["lifecycle_fail_reason"] = "pipeline_bughunter_gatekeeper_loop_exhausted"
            msgs.append(AIMessage(content="Loop guard detected repeated remediation cycling again after escalation. Halting for human intervention."))
        result["messages"] = msgs

    return result


def _telemetry_wrap(node_name, fn):
    def _wrapped(state):
        run_id = state.get("run_id") or StateStore.new_run_id()
        project_id = state.get("project_id") or "unknown"
        workspace_path = state.get("project_workspace_path") or os.path.join("projects", project_id)
        store = StateStore(project_id=project_id, workspace_path=workspace_path)

        # Resume bootstrap + run bootstrap on first entry
        if not state.get("run_started"):
            auto_resume = os.getenv("SWEAT_AUTO_RESUME", "true").lower() in {"1", "true", "yes", "on"}
            if auto_resume:
                resumed = load_resume_state(store.state_dir)
                if isinstance(resumed, dict):
                    # Keep explicit incoming keys authoritative.
                    state = resumed | state
                    run_id = state.get("run_id") or run_id

            store.start_run(run_id)
            startup = {
                "run_id": run_id,
                "project_id": project_id,
                "cwd": os.getcwd(),
                "workspace_path": workspace_path,
                "linear": {
                    "has_api_key": bool(os.getenv("LINEAR_API_KEY")),
                    "has_team_id": bool(os.getenv("LINEAR_TEAM_ID")),
                },
                "providers": {
                    "has_gemini_api_key": bool(os.getenv("GEMINI_API_KEY")),
                    "has_openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
                    "has_anthropic_api_key": bool(os.getenv("ANTHROPIC_API_KEY")),
                },
                "ts": int(time.time()),
            }
            os.makedirs("reports/runs", exist_ok=True)
            with open("reports/runs/startup_check.json", "w", encoding="utf-8") as f:
                json.dump(startup, f, indent=2)
            with open(os.path.join(store.state_dir, "startup_check.json"), "w", encoding="utf-8") as f:
                json.dump(startup, f, indent=2)

        input_fingerprint = hashlib.sha256(
            json.dumps({
                "node": node_name,
                "messages_len": len(state.get("messages") or []),
                "next_agent": state.get("next_agent"),
                "last_agent": state.get("last_agent"),
            }, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        store.append_event(
            run_id=run_id,
            node=node_name,
            event_type="node_enter",
            payload={"input_hash": f"sha256:{input_fingerprint}"},
            idempotency_key=f"{run_id}:{node_name}:enter:{input_fingerprint}",
        )

        t0 = time.time()
        result = fn(state)
        dt = int((time.time() - t0) * 1000)

        # Global runtime guards (HITL + anti-loop escalation)
        result = _apply_runtime_guards(node_name, state, result)

        # P1 contract enforcement (soft-by-default, hard-stop when enabled)
        result = result or {}
        contract_errors = validate_state_patch(node_name, result)
        strict_contracts = os.getenv("SWEAT_STRICT_CONTRACTS", "true").lower() in {"1", "true", "yes", "on"}
        if contract_errors:
            store.append_event(
                run_id=run_id,
                node=node_name,
                event_type="validation_error",
                payload={"kind": "contract_violation", "errors": contract_errors},
            )
            if strict_contracts:
                result["next_agent"] = "__end__"
                msgs = list(result.get("messages") or [])
                msgs.append(AIMessage(content=f"Contract violation at {node_name}: {contract_errors}"))
                result["messages"] = msgs

        telemetry = list(state.get("run_telemetry") or [])
        telemetry.append({
            "node": node_name,
            "duration_ms": dt,
            "next_agent": (result or {}).get("next_agent"),
        })

        report = {
            "project_id": project_id,
            "run_id": run_id,
            "events": telemetry,
            "updated_at_epoch": int(time.time()),
        }
        os.makedirs("reports/runs", exist_ok=True)
        report_path = "reports/runs/latest_run_report.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except Exception:
            pass

        result = result or {}
        result["run_telemetry"] = telemetry
        result["run_report_path"] = report_path
        result["run_id"] = run_id
        result["run_started"] = True
        merged_state = state | result

        if merged_state.get("human_input_required"):
            try:
                questions = merged_state.get("requirements_open_questions") or []
                qtext = " | ".join([str(q) for q in questions[:5]])
                msg = f"SWEAT HITL required for {project_id}: {qtext}" if qtext else f"SWEAT HITL required for {project_id}."
                safe_msg = msg.replace('"', "'")
                os.system(f'openclaw system event --text "{safe_msg}" --mode now >/dev/null 2>&1')
            except Exception:
                pass

        if result.get("next_agent") is not None:
            req = merged_state.get("requirements") if isinstance(merged_state.get("requirements"), dict) else {}
            store.append_event(
                run_id=run_id,
                node=node_name,
                event_type="route_decision",
                payload={
                    "next_node": result.get("next_agent"),
                    "v2_shadow_mode": merged_state.get("v2_shadow_mode"),
                    "v2_stage": merged_state.get("v2_stage"),
                    "v2_next_agent_recommendation": merged_state.get("v2_next_agent_recommendation"),
                    "v2_policy_violations": merged_state.get("v2_policy_violations") or [],
                    "requirements_present": bool(req),
                    "revision_count": merged_state.get("requirements_revision_count"),
                    "revision_reasons": merged_state.get("requirements_revision_reasons") or [],
                },
                idempotency_key=f"{run_id}:{node_name}:route:{result.get('next_agent')}:{input_fingerprint}",
            )

        store.append_event(
            run_id=run_id,
            node=node_name,
            event_type="node_exit",
            payload={
                "status": "success",
                "duration_ms": dt,
                "next_agent": result.get("next_agent"),
            },
            idempotency_key=f"{run_id}:{node_name}:exit:{input_fingerprint}",
        )

        expected_version = state.get("project_state_version")
        try:
            resume_path = write_resume_state(store.state_dir, merged_state)
            snap = store.write_snapshot(merged_state, run_id=run_id, expected_version=expected_version)
            result["project_state_version"] = snap.get("state_version")
            store.append_event(
                run_id=run_id,
                node=node_name,
                event_type="state_patch_applied",
                payload={"snapshot_path": snap.get("path"), "resume_path": resume_path, "state_version": snap.get("state_version")},
                idempotency_key=f"{run_id}:{node_name}:snapshot:{snap.get('state_version')}",
            )
        except VersionConflictError as e:
            msg = f"State version conflict: {e}. Halting run for safe retry."
            store.append_event(
                run_id=run_id,
                node=node_name,
                event_type="validation_error",
                payload={"error": str(e), "kind": "version_conflict", "action": "halt"},
            )
            result["next_agent"] = "__end__"
            result["messages"] = list(result.get("messages") or []) + [AIMessage(content=msg)]
            store.end_run(run_id, status="failed")

        if result.get("next_agent") == "__end__":
            store.end_run(run_id, status="completed")

        return result
    return _wrapped


def build_graph():
    """
    Constructs the SWEAT agent graph.
    """
    workflow = StateGraph(ProjectState)

    # Add nodes with telemetry wrappers
    node_map = {
        "zocai": orchestrator_node,
        "req_master": req_master_node,
        "req_master_interview": req_master_interview_node,
        "sdd_specify": sdd_specify_node,
        "sdd_plan": sdd_plan_node,
        "sdd_tasks": sdd_tasks_node,
        "architect": architect_node,
        "pixel": pixel_node,
        "frontman": frontman_node,
        "design_approval_gate": design_approval_gate_node,
        "tdd_orchestrator": tdd_orchestrator_node,
        "unit_test_author": unit_test_author_node,
        "integration_test_author": integration_test_author_node,
        "playwright_test_author": playwright_test_author_node,
        "test_readiness_gate": tdd_readiness_gate_node,
        "github_bootstrap": github_bootstrap_node,
        "codesmith": codesmith_node,
        "bughunter": bughunter_node,
        "gatekeeper": gatekeeper_node,
        "pipeline": pipeline_node,
        "integrator": integrator_node,
        "automator": automator_node,
        "deployer": deployer_node,
        "scrumlord": scrumlord_node,
        "sprint_executor": sprint_executor_node,
    }
    for n, fn in node_map.items():
        workflow.add_node(n, _telemetry_wrap(n, fn))

    # Add edges
    workflow.add_edge(START, "zocai")

    # Conditional edges from Zocai to workers
    workflow.add_conditional_edges(
        "zocai",
        lambda state: state.get("next_agent", "req_master_interview"),
        {
            "req_master": "req_master",
            "req_master_interview": "req_master_interview",
            "sdd_specify": "sdd_specify",
            "sdd_plan": "sdd_plan",
            "sdd_tasks": "sdd_tasks",
            "architect": "architect",
            "pixel": "pixel",
            "frontman": "frontman",
            "design_approval_gate": "design_approval_gate",
            "tdd_orchestrator": "tdd_orchestrator",
            "unit_test_author": "unit_test_author",
            "integration_test_author": "integration_test_author",
            "playwright_test_author": "playwright_test_author",
            "test_readiness_gate": "test_readiness_gate",
            "github_bootstrap": "github_bootstrap",
            "codesmith": "codesmith",
            "bughunter": "bughunter",
            "gatekeeper": "gatekeeper",
            "pipeline": "pipeline",
            "integrator": "integrator",
            "automator": "automator",
            "deployer": "deployer",
            "scrumlord": "scrumlord",
            "sprint_executor": "sprint_executor",
            "__end__": END,
        }
    )

    # Phase 4.1: worker-to-worker automatic routing via next_agent
    route_map = {
        "req_master": "req_master",
        "req_master_interview": "req_master_interview",
        "sdd_specify": "sdd_specify",
        "sdd_plan": "sdd_plan",
        "sdd_tasks": "sdd_tasks",
        "architect": "architect",
        "pixel": "pixel",
        "frontman": "frontman",
        "design_approval_gate": "design_approval_gate",
        "tdd_orchestrator": "tdd_orchestrator",
        "unit_test_author": "unit_test_author",
        "integration_test_author": "integration_test_author",
        "playwright_test_author": "playwright_test_author",
        "test_readiness_gate": "test_readiness_gate",
        "github_bootstrap": "github_bootstrap",
        "codesmith": "codesmith",
        "bughunter": "bughunter",
        "gatekeeper": "gatekeeper",
        "pipeline": "pipeline",
        "integrator": "integrator",
        "automator": "automator",
        "deployer": "deployer",
        "scrumlord": "scrumlord",
        "sprint_executor": "sprint_executor",
        "__end__": END,
    }

    for worker in [
        "req_master", "req_master_interview", "sdd_specify", "sdd_plan", "sdd_tasks",
        "architect", "pixel", "frontman", "design_approval_gate", "tdd_orchestrator",
        "unit_test_author", "integration_test_author", "playwright_test_author", "test_readiness_gate", "github_bootstrap",
        "codesmith", "bughunter", "gatekeeper", "pipeline", "integrator", "automator", "deployer", "scrumlord", "sprint_executor"
    ]:
        workflow.add_conditional_edges(worker, _route_next, route_map)

    return workflow.compile()

def detect_backends() -> tuple[str, str]:
    """Returns (main_llm_backend, coder_llm_backend) based on current policy."""
    if os.getenv("OPENAI_API_KEY"):
        main_backend = "OpenAI (gpt-4o)"
        coder_backend = "OpenAI (gpt-4o)"
        return main_backend, coder_backend

    if os.getenv("ANTHROPIC_API_KEY"):
        main_backend = "Anthropic (claude-3-5-sonnet)"
        coder_backend = "Anthropic (claude-3-5-sonnet)"
        return main_backend, coder_backend

    # Main defaults to Gemini API when key exists
    if os.getenv("GEMINI_API_KEY"):
        main_backend = "Gemini API (gemini-2.5-flash)"
    elif shutil.which("gemini"):
        main_backend = "Gemini CLI"
    else:
        main_backend = "Mock"

    use_codex = os.getenv("SWEAT_USE_CODEX_CLI", "false").lower() in {"1", "true", "yes", "on"}
    if use_codex and shutil.which("codex"):
        coder_backend = "Codex CLI"
    elif os.getenv("GEMINI_API_KEY"):
        coder_backend = "Gemini API (gemini-2.5-flash)"
    elif shutil.which("gemini"):
        coder_backend = "Gemini CLI"
    else:
        coder_backend = "Mock"

    return main_backend, coder_backend


def main():
    graph = build_graph()
    main_backend, coder_backend = detect_backends()
    
    print("🗿 SWEAT (SoftWare Engineering Agentic Titan) Initialized.")
    print(f"LLM Backends → Main: {main_backend} | CodeSmith: {coder_backend}")
    print("Zocai is listening. Type 'exit' to quit.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "project_id": "demo-001",
            "next_agent": None
        }
        
        # Stream the graph execution
        for event in graph.stream(initial_state):
            for node, value in event.items():
                if "messages" in value and value["messages"]:
                    last_msg = value["messages"][-1]
                    print(f"\n{node.upper()}: {last_msg.content}")

if __name__ == "__main__":
    main()
