from src.tools.definitions import write_file, read_file, list_directory, commit_changes, git_status, git_diff
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.state import ProjectState
from src.utils.llm import get_llm, get_coder_llm
from src.tools.git import get_git_tool
from src.tools.automation import get_n8n_tool
from src.tools.devops import ci_template, dockerfile_template, k8s_deployment_template
from src.tools.linear import get_linear_client
from src.tools.github_bootstrap import get_github_bootstrap_tool
from src.tools.specify_runner import get_specify_runner
from src.utils.logger import logger
from src.utils.memory import get_memory
from src.utils.parser import (
    extract_json_content,
    extract_coverage_percent,
    strip_think_blocks,
    extract_tool_call_from_markup,
)
from typing import Dict, Any, Tuple, List
import json
import os
import re
import sys

llm = get_llm()
coder_llm = get_coder_llm()
git_tool = get_git_tool()
n8n = get_n8n_tool()
linear = get_linear_client()
github_bootstrap = get_github_bootstrap_tool()
specify_runner = get_specify_runner()
memory = get_memory()


def _workspace_root(state: ProjectState) -> str:
    return state.get("project_workspace_path") or "."


def _ws_rel_path(state: ProjectState, rel_path: str) -> str:
    root = _workspace_root(state)
    return os.path.join(root, rel_path) if root != "." else rel_path


def _write_project_file(state: ProjectState, rel_path: str, content: str) -> None:
    write_file.invoke({"path": _ws_rel_path(state, rel_path), "content": content})


def _hydrate_requirements_from_workspace(state: ProjectState) -> Dict[str, Any]:
    root = _workspace_root(state)
    candidates = [
        os.path.join(root, "state", "resume_state.json"),
        os.path.join(root, "state", "project_state.json"),
    ]
    for p in candidates:
        try:
            if os.path.exists(p):
                doc = json.loads(open(p, "r", encoding="utf-8").read())
                req = doc.get("requirements")
                if isinstance(req, dict) and req:
                    return req
        except Exception:
            continue
    return {}

def _decide_project_strategy(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide whether work should spin up a new Linear project vs use backlog.
    Heuristic policy (can be replaced later with explicit planner scoring):
    - start new project if requirements indicate larger initiative.
    """
    text = json.dumps(requirements or {}, ensure_ascii=False).lower()

    score = 0
    if any(k in text for k in ["initiative", "epic", "roadmap", "milestone", "multi-phase", "cross-functional"]):
        score += 2
    if any(k in text for k in ["launch", "v1", "release", "production", "stakeholder"]):
        score += 1
    if any(k in text for k in ["quick fix", "small", "minor", "single bug", "typo"]):
        score -= 2

    estimated_tasks = requirements.get("estimated_tasks") if isinstance(requirements, dict) else None
    if isinstance(estimated_tasks, int):
        if estimated_tasks >= 8:
            score += 2
        elif estimated_tasks <= 3:
            score -= 1

    should_create = score >= 2
    project_name = requirements.get("project_name") if isinstance(requirements, dict) else None
    if not project_name and should_create:
        title = requirements.get("name") if isinstance(requirements, dict) else None
        project_name = (title or "SWEAT Initiative").strip()

    return {
        "should_create_linear_project": should_create,
        "linear_project_name": project_name,
        "project_decision_score": score,
    }


def _validate_requirements_for_sdd(req: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    reasons: List[str] = []
    questions: List[str] = []

    if not isinstance(req, dict) or not req:
        reasons.append("missing_requirements")
        questions.append("Please provide project requirements in structured form.")
        return False, reasons, questions

    if not req.get("name"):
        reasons.append("missing_required_fields")
        questions.append("What is the project/feature name?")

    ac = req.get("acceptance_criteria")
    if not isinstance(ac, list) or len(ac) == 0:
        if "missing_required_fields" not in reasons:
            reasons.append("missing_required_fields")
        questions.append("List acceptance criteria as testable statements.")

    _, quality_notes = _score_sdd_requirements(req)
    if any("non-testable acceptance criteria" in n for n in quality_notes):
        reasons.append("non_testable_acceptance_criteria")
        questions.append("Rewrite acceptance criteria with clear actions and verifiable outcomes.")

    return len(reasons) == 0, reasons, questions


def req_master_interview_node(state: ProjectState) -> Dict[str, Any]:
    """Interview-first requirement capture for SDD readiness with human-in-the-loop pause."""
    req = state.get("requirements") if isinstance(state.get("requirements"), dict) else {}
    revision_reasons = list(state.get("requirements_revision_reasons") or [])
    revision_count = int(state.get("requirements_revision_count") or 0)

    def _await_human(questions: List[str], reasons: List[str]) -> Dict[str, Any]:
        bullets = "\n".join([f"- {q}" for q in questions])
        return {
            "requirements_interview_status": "awaiting_human",
            "requirements_questions_asked": questions,
            "requirements_open_questions": questions,
            "requirements_revision_reasons": reasons,
            "human_input_required": True,
            "next_agent": "__end__",
            "messages": [AIMessage(content=f"ReqMaster needs answers from requester before SDD.\nQuestions:\n{bullets}")],
        }

    # If SDD previously rejected requirements, force targeted revision path (do not auto-complete).
    if revision_reasons:
        valid, inferred_reasons, questions = _validate_requirements_for_sdd(req)
        merged_reasons = list(dict.fromkeys(revision_reasons + inferred_reasons))

        if revision_count >= 3:
            return {
                "requirements_interview_status": "blocked",
                "requirements_revision_reasons": merged_reasons,
                "human_input_required": True,
                "next_agent": "__end__",
                "messages": [AIMessage(content="Requirements interview blocked after 3 revision attempts. Please provide explicit, testable acceptance criteria and required fields.")],
            }

        # Only attempt auto-regeneration when there is fresh human input.
        last_msg = state.get("messages", [])[-1] if state.get("messages") else None
        if isinstance(last_msg, HumanMessage):
            base = req_master_node({**state, "requirements": None})
            new_req = base.get("requirements") if isinstance(base.get("requirements"), dict) else {}
            new_valid, new_reasons, new_questions = _validate_requirements_for_sdd(new_req)
            if new_valid:
                return {
                    **base,
                    "requirements_interview_status": "complete",
                    "requirements_open_questions": [],
                    "requirements_revision_reasons": [],
                    "requirements_revision_count": revision_count + 1,
                    "human_input_required": False,
                    "requirements_sdd_prompt": f"Use clarified requester answers and validated requirements for SDD specify. Requirements: {json.dumps(new_req, ensure_ascii=False)}",
                    "next_agent": "sdd_specify",
                }
            return _await_human(new_questions or questions, list(dict.fromkeys(merged_reasons + new_reasons))) | {
                "requirements_revision_count": revision_count + 1,
                "messages": [AIMessage(content=f"ReqMaster still needs requirement revisions: {', '.join(list(dict.fromkeys(merged_reasons + new_reasons)))}")],
            }

        if valid:
            return {
                "requirements_interview_status": "complete",
                "requirements_open_questions": [],
                "requirements_revision_reasons": [],
                "human_input_required": False,
                "requirements_sdd_prompt": f"Use clarified requester answers and validated requirements for SDD specify. Requirements: {json.dumps(req, ensure_ascii=False)}",
                "next_agent": "sdd_specify",
                "messages": [AIMessage(content="ReqMaster interview complete. Proceeding to SDD specify stage.")],
            }

        return _await_human(questions, merged_reasons) | {
            "requirements_revision_count": revision_count,
            "messages": [AIMessage(content=f"ReqMaster needs requirement revisions before SDD: {', '.join(merged_reasons)}")],
        }

    # Normal path: only proceed when requirements satisfy SDD contract.
    valid, reasons, questions = _validate_requirements_for_sdd(req)
    if valid:
        return {
            "requirements_interview_status": "complete",
            "requirements_open_questions": [],
            "human_input_required": False,
            "requirements_sdd_prompt": f"Use validated requirements for SDD specify. Requirements: {json.dumps(req, ensure_ascii=False)}",
            "next_agent": "sdd_specify",
            "messages": [AIMessage(content="ReqMaster interview complete. Proceeding to SDD specify stage.")],
        }

    base = req_master_node(state)
    base_req = base.get("requirements") if isinstance(base.get("requirements"), dict) else {}
    b_valid, b_reasons, b_questions = _validate_requirements_for_sdd(base_req)
    if b_valid:
        return {
            **base,
            "requirements_interview_status": "complete",
            "requirements_open_questions": [],
            "requirements_revision_reasons": [],
            "human_input_required": False,
            "requirements_sdd_prompt": f"Use requester interview answers + generated requirements for SDD specify. Requirements: {json.dumps(base_req, ensure_ascii=False)}",
            "next_agent": "sdd_specify",
        }

    questions = [
        "What business outcome should this feature achieve?",
        "What is in-scope and explicitly out-of-scope?",
        "What are the acceptance criteria we must test?",
        "Any constraints (security/performance/deadline/tech stack)?",
    ]
    return _await_human(questions, reasons or ["missing_required_fields"]) | {
        "messages": [AIMessage(content="ReqMaster needs more detail before SDD. Please answer interview questions.")],
    }


def _score_sdd_requirements(req: Dict[str, Any]) -> tuple[float, list[str]]:
    notes = []
    score = 0.0

    if not isinstance(req, dict):
        return 0.0, ["requirements is not a JSON object"]

    # Core fields
    if req.get("name"):
        score += 20
    else:
        notes.append("missing name")

    ac = req.get("acceptance_criteria")
    if isinstance(ac, list) and len(ac) > 0:
        score += 30
        # testability heuristic
        action_keywords = [
            "can", "must", "should", "when", "then", "returns", "response",
            "create", "list", "update", "delete", "mark", "print", "calculate", "save", "load", "render",
        ]
        vague_keywords = ["awesome", "intuitive", "nice", "beautiful", "fast enough", "easy"]
        non_testable = []
        for x in ac:
            if not isinstance(x, str):
                non_testable.append(str(x))
                continue
            low = x.lower().strip()
            has_action = any(k in low for k in action_keywords)
            is_vague = any(v in low for v in vague_keywords)
            if (not has_action) and is_vague:
                non_testable.append(x)

        if non_testable:
            notes.append(f"non-testable acceptance criteria candidates: {len(non_testable)}")
        else:
            score += 15
    else:
        notes.append("missing acceptance_criteria list")

    if req.get("goal"):
        score += 10
    if req.get("constraints") or req.get("non_functional"):
        score += 10
    if req.get("estimated_tasks"):
        score += 5
    if req.get("project_name"):
        score += 5
    if req.get("stakeholder") or req.get("users"):
        score += 5

    # clamp
    score = min(100.0, score)
    return score, notes


def _build_traceability_map(req: Dict[str, Any]) -> Dict[str, Any]:
    ac = req.get("acceptance_criteria") if isinstance(req, dict) else []
    if not isinstance(ac, list):
        ac = []
    items = []
    for i, criterion in enumerate(ac, start=1):
        cid = f"AC-{i:03d}"
        items.append({
            "id": cid,
            "requirement": criterion,
            "tests": {
                "unit": [f"tests/unit/test_{cid.lower()}.py"],
                "integration": [f"tests/integration/test_{cid.lower()}.py"],
                "e2e": [f"tests/e2e/{cid.lower()}.spec.ts"],
            },
            "implementation_targets": [
                "src/app.py",
                "src/App.jsx",
            ],
        })
    return {"items": items}


def sdd_specify_node(state: ProjectState) -> Dict[str, Any]:
    req = state.get("requirements")
    if not isinstance(req, dict) or not req:
        req = _hydrate_requirements_from_workspace(state)

    if not req:
        return {
            "sdd_spec_status": "draft",
            "requirements_interview_status": "needs_revision",
            "requirements_revision_reasons": ["missing_requirements"],
            "next_agent": "req_master_interview",
            "messages": [AIMessage(content="Missing requirements for SDD specify. Returning to interview.")],
        }

    # Ambiguity/completeness gate
    required = ["name", "acceptance_criteria"]
    missing = [k for k in required if not req.get(k)] if isinstance(req, dict) else required
    if missing:
        return {
            "sdd_spec_status": "draft",
            "requirements_interview_status": "needs_revision",
            "requirements_revision_reasons": ["missing_required_fields"],
            "requirements_open_questions": [f"Provide missing fields: {', '.join(missing)}"],
            "next_agent": "req_master_interview",
            "messages": [AIMessage(content=f"SDD specify blocked: missing requirement fields: {', '.join(missing)}")],
        }

    quality_score, quality_notes = _score_sdd_requirements(req if isinstance(req, dict) else {})
    # Strict gate for non-testable criteria flags
    if any("non-testable acceptance criteria" in n for n in quality_notes):
        return {
            "sdd_spec_status": "draft",
            "sdd_quality_score": quality_score,
            "sdd_quality_notes": quality_notes,
            "requirements_interview_status": "needs_revision",
            "requirements_revision_reasons": ["non_testable_acceptance_criteria"],
            "requirements_open_questions": ["Rewrite acceptance criteria as testable, action-oriented statements."],
            "next_agent": "req_master_interview",
            "messages": [AIMessage(content=f"SDD specify blocked: acceptance criteria must be testable. Notes: {quality_notes}")],
        }

    # Try first-class specify CLI flow (best-effort)
    specify_result = specify_runner.run_specify_flow(cwd=_workspace_root(state))

    spec_md = "# Product Spec (SDD)\n\n" + json.dumps(req, indent=2, ensure_ascii=False)
    if not specify_result.get("success"):
        spec_md += f"\n\n> specify runner fallback: {specify_result.get('error', 'not available')}"

    traceability = _build_traceability_map(req if isinstance(req, dict) else {})

    _write_project_file(state, "docs/spec/spec.md", spec_md)
    _write_project_file(state, "docs/spec/spec.json", json.dumps(req, indent=2, ensure_ascii=False))
    _write_project_file(state, "docs/spec/specify_runner_result.json", json.dumps(specify_result, indent=2, ensure_ascii=False))
    _write_project_file(state, "docs/spec/traceability_map.json", json.dumps(traceability, indent=2, ensure_ascii=False))

    return {
        "requirements": req,
        "sdd_spec_path": _ws_rel_path(state, "docs/spec/spec.md"),
        "sdd_spec_status": "approved",
        "sdd_status": "specify_done",
        "sdd_quality_score": quality_score,
        "sdd_quality_notes": quality_notes,
        "traceability_map_path": _ws_rel_path(state, "docs/spec/traceability_map.json"),
        "requirements_revision_reasons": [],
        "requirements_open_questions": [],
        "next_agent": "sdd_plan",
        "messages": [AIMessage(content=f"SDD spec generated (score={quality_score}).")],
    }


def sdd_plan_node(state: ProjectState) -> Dict[str, Any]:
    req = state.get("requirements", {})
    plan_md = (
        "# Technical Plan (SDD)\n\n"
        "## Goals\n- Implement requirements from SDD spec\n\n"
        "## Constraints\n- Follow architecture + test-first process\n\n"
        f"## Requirement Snapshot\n```json\n{json.dumps(req, indent=2, ensure_ascii=False)}\n```\n"
    )
    _write_project_file(state, "docs/spec/plan.md", plan_md)
    return {
        "sdd_plan_path": _ws_rel_path(state, "docs/spec/plan.md"),
        "sdd_status": "plan_done",
        "next_agent": "sdd_tasks",
        "messages": [AIMessage(content="SDD plan generated.")],
    }


def sdd_tasks_node(state: ProjectState) -> Dict[str, Any]:
    tasks_md = (
        "# SDD Tasks\n\n"
        "- [ ] Finalize architecture\n"
        "- [ ] Produce UX package (Pixel)\n"
        "- [ ] Produce UI contract (Frontman)\n"
        "- [ ] Prepare TDD assets (unit/integration/e2e)\n"
        "- [ ] Implement with CodeSmith\n"
        "- [ ] Pass review + CI gates\n"
    )
    _write_project_file(state, "docs/spec/tasks.md", tasks_md)
    return {
        "sdd_tasks_path": _ws_rel_path(state, "docs/spec/tasks.md"),
        "sdd_status": "tasks_done",
        "next_agent": "architect",
        "messages": [AIMessage(content="SDD tasks generated.")],
    }


def req_master_node(state: ProjectState) -> Dict[str, Any]:
    logger.info("ReqMaster: analyzing input.")
    if state.get("requirements"):
        return {"messages": [AIMessage(content="Requirements already gathered.")]}
    # Memory Retrieval
    last_msg = state["messages"][-1].content if state["messages"] else ""
    past_reqs = []
    if last_msg:
        try:
            past_reqs = memory.retrieve_context(f"requirements related to: {last_msg}", k=2)
        except Exception as e:
            logger.warning(f"ReqMaster memory retrieval failed: {e}")
    
    context_str = "\n".join(past_reqs) if past_reqs else "No prior context."

    response = llm.invoke([
        SystemMessage(content=(
            f"You are ReqMaster. Gather requirements. Context from memory:\n{context_str}\n"
            "Output STRICT JSON object only when complete with keys: "
            "name (string), acceptance_criteria (array of testable strings), optional goal/constraints/project_name. "
            "If incomplete, ask concise clarification questions in plain text and do not output partial JSON."
        )),
    ] + state["messages"])

    content = response.content.strip()
    
    try:
        # Robustly parse JSON for Requirements
        requirements = extract_json_content(content)
        if isinstance(requirements, dict) and len(requirements) > 0:
             valid, reasons, _ = _validate_requirements_for_sdd(requirements)
             if valid:
                 decision = _decide_project_strategy(requirements)
                 return {
                     "requirements": requirements,
                     "messages": [response],
                     "next_agent": "sdd_specify",
                     **decision,
                 }
             logger.info(f"ReqMaster produced partial requirements (needs revision): {reasons}")
    except Exception as e:
        logger.debug(f"ReqMaster output not JSON: {e}")

    return {"messages": [response]}


def architect_node(state: ProjectState) -> Dict[str, Any]:
    logger.info("Architech: designing system.")
    requirements = state.get("requirements", {})
    req_text = json.dumps(requirements, ensure_ascii=False)
    response = llm.invoke([
        SystemMessage(content="You are Architech 🏛️. Produce architecture doc markdown from requirements."),
        HumanMessage(content=f"Requirements:\n{req_text}"),
    ] + state["messages"])
    
    # Save architecture decision to memory
    try:
        memory.save_context(response.content, {"type": "architecture", "project_id": state.get("project_id", "unknown")})
    except Exception as e:
        logger.warning(f"Failed to save memory: {e}")
        
    return {"messages": [response], "architecture_docs": response.content, "next_agent": "pixel"}


def pixel_node(state: ProjectState) -> Dict[str, Any]:
    requirements = state.get("requirements", {})
    req_text = json.dumps(requirements, ensure_ascii=False)
    response = llm.invoke([
        SystemMessage(content="You are Pixel 🎨. Output ONLY JSON with keys: personas (list), user_journey (list), screens (list), style_tokens (object)."),
        HumanMessage(content=f"Requirements: {req_text}"),
    ])

    try:
        ux_package = extract_json_content(response.content)
        valid, reason = _validate_pixel_package(ux_package)
        if not valid:
            raise ValueError(reason)

        _write_project_file(state, "docs/ux/package.json", json.dumps(ux_package, indent=2))
        _write_project_file(state, "docs/ux/wireframes.md", json.dumps(ux_package, indent=2))
        return {
            "messages": [AIMessage(content="Pixel produced structured UX package.")],
            "ux_wireframes": json.dumps(ux_package, indent=2),
            "personas": ux_package.get("personas", []),
            "next_agent": "frontman",
        }
    except Exception as e:
        _write_project_file(state, "docs/ux/wireframes.md", response.content)
        return {
            "messages": [AIMessage(content=f"Pixel fallback output used: {e}")],
            "ux_wireframes": response.content,
            "next_agent": "frontman",
        }


def frontman_node(state: ProjectState) -> Dict[str, Any]:
    ux = state.get("ux_wireframes", "")
    try:
        ux_package = json.loads(ux) if isinstance(ux, str) and ux.strip().startswith("{") else {"raw": ux}
    except Exception:
        ux_package = {"raw": ux}

    response = llm.invoke([
        SystemMessage(content=_build_frontman_prompt(ux_package)),
        HumanMessage(content="Generate the tool-call JSON now."),
    ])

    try:
        tool_call = extract_json_content(response.content)
        valid, reason = _validate_tool_call(tool_call, {"write_file"}, workspace_root=_workspace_root(state))
        if not valid:
            raise ValueError(reason)

        path = tool_call.get("args", {}).get("path", "src/App.jsx")
        if not (path.startswith("src/") and (path.endswith(".jsx") or path.endswith(".tsx"))):
            raise ValueError("Frontman output path must be src/*.jsx or src/*.tsx")

        result = _execute_tool(tool_call.get("tool"), tool_call.get("args", {}), state=state)
        msg = f"Frontman generated UI code: {result}"
        library_path = path

        # Handoff contract artifact: Pixel -> Frontman
        handoff = {
            "input": "docs/ux/package.json",
            "output": library_path,
            "props_contract": ["title", "items", "onPrimaryAction"],
            "style_tokens_source": "docs/ux/package.json#style_tokens",
        }
        _write_project_file(state, "docs/ui/handoff_contract.json", json.dumps(handoff, indent=2))
    except Exception as e:
        msg = f"Frontman failed to generate code (fallback to plan): {e}"
        _write_project_file(state, "docs/ui/component-plan.md", response.content)
        library_path = _ws_rel_path(state, "docs/ui/component-plan.md")

    return {"messages": [AIMessage(content=msg)], "ui_component_library": library_path, "next_agent": "design_approval_gate"}


def design_approval_gate_node(state: ProjectState) -> Dict[str, Any]:
    checks = {
        "spec": bool(state.get("sdd_spec_path")),
        "plan": bool(state.get("sdd_plan_path")),
        "tasks": bool(state.get("sdd_tasks_path")),
        "architecture": bool(state.get("architecture_docs")),
        "ux": bool(state.get("ux_wireframes")),
        "ui": bool(state.get("ui_component_library")),
    }
    missing = [k for k, v in checks.items() if not v]
    if missing:
        return {
            "design_approval_status": "rejected",
            "design_approval_notes": f"Missing design prerequisites: {', '.join(missing)}",
            "decision_reason_code": "design_missing_prerequisites",
            "next_agent": "architect",
            "messages": [AIMessage(content=f"Design approval rejected. Missing: {', '.join(missing)}")],
        }

    _write_project_file(state, "docs/design/design.md", "# Design Approval\n\nApproved for TDD stage.")
    return {
        "design_doc_path": _ws_rel_path(state, "docs/design/design.md"),
        "design_approval_status": "approved",
        "design_approval_notes": "All design prerequisites satisfied.",
        "decision_reason_code": "design_prerequisites_satisfied",
        "next_agent": "tdd_orchestrator",
        "messages": [AIMessage(content="Design approved. Proceeding to TDD stage.")],
    }


def tdd_orchestrator_node(state: ProjectState) -> Dict[str, Any]:
    target = int(state.get("coverage_target") or 95)
    return {
        "coverage_target": max(target, 95),
        "next_agent": "unit_test_author",
        "messages": [AIMessage(content="TDD orchestrator initialized. Starting unit test authoring.")],
    }


def unit_test_author_node(state: ProjectState) -> Dict[str, Any]:
    coverage_target = int(state.get("coverage_target") or 95)
    _write_project_file(state, "docs/tests/unit_test_plan.md", "# Unit Test Plan\n\nMap each acceptance criterion to unit tests before coding.")
    _write_project_file(state, "docs/tests/coverage_policy.md", f"# Coverage Policy\n\nRequired minimum line coverage: {coverage_target}%\nUse: pytest --cov=src --cov-report=term-missing --cov-fail-under={coverage_target}\n")
    return {
        "unit_test_plan_path": _ws_rel_path(state, "docs/tests/unit_test_plan.md"),
        "coverage_target": coverage_target,
        "next_agent": "integration_test_author",
        "messages": [AIMessage(content=f"Unit test plan generated with coverage target {coverage_target}%.")],
    }


def integration_test_author_node(state: ProjectState) -> Dict[str, Any]:
    _write_project_file(state, "docs/tests/integration_test_plan.md", "# Integration Test Plan\n\nAutomate API/service integration checks using pytest + httpx/testcontainers as needed.")
    _write_project_file(state, "tests/integration/test_placeholder.py", "def test_integration_placeholder():\n    assert True\n")
    return {
        "integration_test_plan_path": _ws_rel_path(state, "docs/tests/integration_test_plan.md"),
        "next_agent": "playwright_test_author",
        "messages": [AIMessage(content="Integration test plan generated.")],
    }


def playwright_test_author_node(state: ProjectState) -> Dict[str, Any]:
    _write_project_file(state, "docs/tests/playwright_test_plan.md", "# Playwright Functional Test Plan\n\nCover happy path, critical failures, and auth/session where applicable.")
    _write_project_file(state, "tests/e2e/README.md", "# E2E Tests\n\nInitialize Playwright specs here.\n")
    return {
        "playwright_test_plan_path": _ws_rel_path(state, "docs/tests/playwright_test_plan.md"),
        "next_agent": "test_readiness_gate",
        "messages": [AIMessage(content="Playwright test plan generated.")],
    }


def tdd_readiness_gate_node(state: ProjectState) -> Dict[str, Any]:
    required = [
        state.get("unit_test_plan_path"),
        state.get("integration_test_plan_path"),
        state.get("playwright_test_plan_path"),
    ]
    coverage_target = int(state.get("coverage_target") or 0)
    if all(required) and coverage_target >= 95:
        return {
            "test_readiness_status": "ready",
            "decision_reason_code": "tdd_ready",
            "next_agent": "github_bootstrap",
            "messages": [AIMessage(content="TDD readiness gate passed. Proceeding to GitHub bootstrap.")],
        }

    return {
        "test_readiness_status": "not_ready",
        "decision_reason_code": "tdd_not_ready",
        "next_agent": "tdd_orchestrator",
        "messages": [AIMessage(content="TDD readiness gate failed. Returning to TDD orchestration.")],
    }


def _slugify_project_name(name: str) -> str:
    s = (name or "project").strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "project"


def github_bootstrap_node(state: ProjectState) -> Dict[str, Any]:
    project_name = (
        state.get("linear_project_name")
        or ((state.get("requirements") or {}).get("project_name") if isinstance(state.get("requirements"), dict) else None)
        or ((state.get("requirements") or {}).get("name") if isinstance(state.get("requirements"), dict) else None)
        or state.get("project_id")
        or "sweat-project"
    )

    slug = _slugify_project_name(project_name)
    workspace_path = state.get("project_workspace_path") or os.path.join("projects", slug)
    os.makedirs(workspace_path, exist_ok=True)

    # Ensure project folder has a starter README so first commit is meaningful.
    readme_path = os.path.join(workspace_path, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# {project_name}\n\nBootstrapped by SWEAT GitHub bootstrap node.\n")

    out = github_bootstrap.bootstrap_repo(
        project_name=project_name,
        cwd=workspace_path,
        private=True,
        description="Created by SWEAT Factory bootstrap",
    )

    if not out.get("success"):
        allow_local_fallback = os.getenv("SWEAT_ALLOW_LOCAL_BOOTSTRAP_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}
        msg = f"GitHub bootstrap failed: {out.get('error')}"
        if allow_local_fallback:
            return {
                "messages": [AIMessage(content=msg + " | continuing with local workspace bootstrap fallback")],
                "github_repo": None,
                "github_default_branch": "master",
                "github_url": None,
                "project_workspace_path": workspace_path,
                "next_agent": "codesmith",
            }
        return {
            "messages": [AIMessage(content=msg)],
            "next_agent": "__end__",
        }

    note = f"GitHub bootstrap ready: {out.get('repo')} -> {out.get('url')}"
    if out.get("branch_protection_applied") is False and out.get("branch_protection_error"):
        note += f" | branch protection warning: {out.get('branch_protection_error')}"

    return {
        "messages": [AIMessage(content=note + f" | workspace={workspace_path}")],
        "github_repo": out.get("repo"),
        "github_default_branch": "master",
        "github_url": out.get("url"),
        "project_workspace_path": workspace_path,
        "next_agent": "codesmith",
    }


def _is_path_in_workspace(path: str, workspace_root: str = ".") -> bool:
    try:
        root = os.path.abspath(workspace_root)
        target = os.path.abspath(os.path.join(root, path))
        return os.path.commonpath([root, target]) == root
    except Exception:
        return False


def _validate_tool_call(tool_call: Dict[str, Any], allowed_tools: set[str], workspace_root: str = ".") -> Tuple[bool, str]:
    if not isinstance(tool_call, dict):
        return False, "Tool call must be a JSON object."

    tool_name = tool_call.get("tool")
    args = tool_call.get("args")

    if not isinstance(tool_name, str) or not tool_name.strip():
        return False, "Tool call missing valid 'tool' string."

    if tool_name not in allowed_tools:
        return False, f"Tool '{tool_name}' is not allowed in this context."

    if args is None:
        args = {}
    if not isinstance(args, dict):
        return False, "Tool call 'args' must be a JSON object."

    # Extra sandbox guard for filesystem tools.
    if tool_name in {"write_file", "read_file", "list_directory"}:
        path = args.get("path", ".")
        if not isinstance(path, str) or not path.strip():
            return False, "Filesystem tool call requires non-empty string path."
        if not _is_path_in_workspace(path, workspace_root=workspace_root):
            return False, f"Path escapes workspace sandbox: {path}"

    return True, "ok"


def _validate_pixel_package(package: Dict[str, Any]) -> Tuple[bool, str]:
    required = {
        "personas": list,
        "user_journey": list,
        "screens": list,
        "style_tokens": dict,
    }
    if not isinstance(package, dict):
        return False, "Pixel package must be a JSON object."

    for key, expected_type in required.items():
        if key not in package:
            return False, f"Missing Pixel field: {key}"
        if not isinstance(package[key], expected_type):
            return False, f"Pixel field '{key}' must be {expected_type.__name__}."

    return True, "ok"


def _build_frontman_prompt(ux_package: Dict[str, Any]) -> str:
    return (
        "You are Frontman 🧩. Use the UX package to generate executable React UI code. "
        "Return ONLY one JSON object for write_file tool call.\n"
        "Schema:\n"
        "{\"tool\":\"write_file\",\"args\":{\"path\":\"src/App.jsx\",\"content\":\"...React code...\"}}\n"
        "Requirements:\n"
        "- path must be inside src/ and end with .jsx or .tsx\n"
        "- content must be valid React component code using exported default function App()\n"
        f"UX package:\n{json.dumps(ux_package, indent=2)}"
    )


def _extract_structured_tool_call(response: AIMessage | Any, allow_json_fallback: bool = True) -> Dict[str, Any]:
    """
    Prefer provider-native tool_calls. Fallback to JSON content only when enabled.
    Normalized output: {"tool": str, "args": dict}
    """
    additional = getattr(response, "additional_kwargs", {}) or {}
    tool_calls = additional.get("tool_calls") or getattr(response, "tool_calls", None) or []

    if tool_calls:
        first = tool_calls[0]
        # OpenAI-style: {"type":"function","function":{"name":"...","arguments":"{...}"}}
        fn = first.get("function", {}) if isinstance(first, dict) else {}
        name = fn.get("name") if isinstance(fn, dict) else None
        args_raw = fn.get("arguments", "{}") if isinstance(fn, dict) else "{}"
        if isinstance(args_raw, str):
            args = json.loads(args_raw or "{}")
        elif isinstance(args_raw, dict):
            args = args_raw
        else:
            args = {}
        return {"tool": name, "args": args}

    if allow_json_fallback:
        raw = (getattr(response, "content", "") or "").strip()
        raw = strip_think_blocks(raw)

        # 1) Try provider wrapper markup parser (e.g. MiniMax invoke wrapper)
        wrapped = extract_tool_call_from_markup(raw)
        if wrapped:
            return wrapped

        # 2) Try normal JSON extraction fallback
        return extract_json_content(raw)

    raise ValueError("No structured tool call found in model response.")


def _execute_tool(tool_name: str, args: Dict[str, Any], state: ProjectState | None = None) -> Any:
    args = dict(args or {})
    if state and tool_name in {"write_file", "read_file", "list_directory"}:
        path = args.get("path")
        if isinstance(path, str) and path.strip():
            args["path"] = _ws_rel_path(state, path)

    if tool_name == "write_file":
        return write_file.invoke(args)
    if tool_name == "read_file":
        return read_file.invoke(args)
    if tool_name == "list_directory":
        return list_directory.invoke(args)
    if tool_name == "commit_changes":
        return commit_changes.invoke(args)
    if tool_name == "git_status":
        return git_status.invoke(args)
    return f"Tool {tool_name} not found."


def codesmith_node(state: ProjectState) -> Dict[str, Any]:
    if state.get("test_readiness_status") != "ready":
        return {
            "messages": [AIMessage(content="CodeSmith blocked: TDD readiness gate not passed yet.")],
            "next_agent": "tdd_orchestrator",
        }

    # Circuit breaker to avoid infinite self-loop on parser/tool-call failures.
    retry_count = int(state.get("codesmith_retry_count") or 0)
    max_retries = int(os.getenv("SWEAT_CODESMITH_MAX_RETRIES", "5"))
    if retry_count >= max_retries:
        return {
            "messages": [AIMessage(content=f"CodeSmith halted after {retry_count} retries without valid tool-call output.")],
            "codesmith_retry_count": retry_count,
            "next_agent": "gatekeeper",
        }

    logger.info("CodeSmith: writing code.")
    messages = state["messages"]
    architecture = state.get("architecture_docs", "No architecture defined yet.")

    # Memory Retrieval for Coding Standards
    try:
        past_code_context = memory.retrieve_context("coding standards python style patterns", k=2)
    except Exception as e:
        logger.warning(f"CodeSmith memory retrieval failed: {e}")
        past_code_context = []
        
    code_context_str = "\n".join(past_code_context) if past_code_context else "No specific standards found."

    try:
        git_tool.init()
    except Exception:
        pass

    last_diag = state.get("last_pipeline_diag") or "No prior pipeline diagnostics."
    last_failures = state.get("pipeline_failure_reasons") or []
    prompt_text = (
        f"You are CodeSmith 🔨. Implement feature from architecture:\n{architecture}\n"
        f"Relevant Coding Standards/Memory:\n{code_context_str}\n"
        f"Latest pipeline diagnostics (fix these first):\n{last_diag}\n"
        f"Failure reasons: {last_failures}\n"
        "Priority: resolve pipeline/test failures before new features.\n"
        "Output JSON tool command only:\n"
        "```json\n{\"tool\":\"write_file\",\"args\":{\"path\":\"src/app.py\",\"content\":\"...\"}}\n```\n"
        "Then commit:\n"
        "```json\n{\"tool\":\"commit_changes\",\"args\":{\"message\":\"feat: implement\",\"agent_name\":\"codesmith\"}}\n```"
    )

    response = coder_llm.invoke([SystemMessage(content=prompt_text)] + messages)

    strict_tools = os.getenv("SWEAT_CODEX_STRICT_TOOLS", "true").lower() in {"1", "true", "yes", "on"}

    try:
        tool_call = _extract_structured_tool_call(response, allow_json_fallback=not strict_tools)
        valid, reason = _validate_tool_call(
            tool_call,
            {"write_file", "read_file", "list_directory", "commit_changes", "git_status"},
            workspace_root=_workspace_root(state),
        )
        if not valid:
            raise ValueError(reason)

        result = _execute_tool(tool_call.get("tool"), tool_call.get("args", {}), state=state)
        return {
            "messages": [response, AIMessage(content=f"Tool executed: {result}")],
            "codesmith_retry_count": 0,
            "next_agent": "gatekeeper",
        }
    except Exception as e:
        logger.warning(f"CodeSmith tool parsing failed: {e}")
        return {
            "messages": [response, AIMessage(content=f"Tool parsing error: {e}")],
            "codesmith_retry_count": retry_count + 1,
            "next_agent": "codesmith",
        }


def bughunter_node(state: ProjectState) -> Dict[str, Any]:
    architecture = state.get("architecture_docs", "")
    last_diag = state.get("last_pipeline_diag") or "No pipeline diagnostics found."
    last_failures = state.get("pipeline_failure_reasons") or []
    last_output = (state.get("last_pipeline_output") or "")[-3000:]
    response = llm.invoke([
        SystemMessage(content="You are BugHunter 🐞. Produce an actionable remediation plan tied to failing CI checks. Focus on concrete root causes and file-level fixes."),
        HumanMessage(content=(
            f"Architecture:\n{architecture}\n\n"
            f"Latest pipeline diagnostics:\n{last_diag}\n"
            f"Failure reasons: {last_failures}\n\n"
            f"Recent CI output excerpt:\n{last_output}\n\n"
            "Return:\n"
            "1) prioritized root causes,\n"
            "2) exact files/functions to patch,\n"
            "3) minimal fix sequence for CodeSmith."
        )),
    ])
    _write_project_file(state, "docs/qa/test-plan.md", response.content)
    return {
        "messages": [response, AIMessage(content="BugHunter produced targeted remediation guidance from latest CI diagnostics. Routing to CodeSmith for fixes before review.")],
        "test_results": {"plan": _ws_rel_path(state, "docs/qa/test-plan.md")},
        "decision_reason_code": "bughunter_to_codesmith_remediation",
        "next_agent": "codesmith",
    }


def gatekeeper_node(state: ProjectState) -> Dict[str, Any]:
    logger.info("Gatekeeper: reviewing diff.")
    diff_output = git_tool.diff()
    prompt_text = (
        "You are Gatekeeper 🛡️. Review this diff. Reply APPROVED if clean, otherwise list blocking issues.\n"
        f"```diff\n{diff_output}\n```"
    )
    msgs = [SystemMessage(content=prompt_text)] + state["messages"]
    if not state["messages"]:
        msgs.append(HumanMessage(content="Review now."))

    try:
        response = llm.invoke(msgs)
        approved = "APPROVED" in response.content.upper()

        fallback = os.getenv("SWEAT_GATEKEEPER_TIMEOUT_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
        always_forward = os.getenv("SWEAT_GATEKEEPER_ALWAYS_FORWARD_ON_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
        forward_on_halt = os.getenv("SWEAT_GATEKEEPER_FORWARD_ON_CODESMITH_HALT", "true").lower() in {"1", "true", "yes", "on"}
        max_retries = int(os.getenv("SWEAT_CODESMITH_MAX_RETRIES", "5"))
        halted = int(state.get("codesmith_retry_count") or 0) >= max_retries
        if not approved and ((fallback and (halted or always_forward)) or (forward_on_halt and halted)):
            warn = "Gatekeeper soft-approved due fallback/halt policy."
            return {
                "messages": [AIMessage(content=warn)],
                "code_review_feedback": warn + "\n" + (response.content or ""),
                "next_agent": "pipeline",
            }

        return {
            "messages": [response],
            "code_review_feedback": response.content,
            "next_agent": "pipeline" if approved else "codesmith",
        }
    except Exception as e:
        fallback = os.getenv("SWEAT_GATEKEEPER_TIMEOUT_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
        msg = f"Gatekeeper error: {e}"
        if fallback:
            msg += " | Fallback enabled: forwarding to pipeline with warning."
            return {
                "messages": [AIMessage(content=msg)],
                "code_review_feedback": msg,
                "next_agent": "pipeline",
            }

        return {
            "messages": [AIMessage(content=msg)],
            "code_review_feedback": msg,
            "next_agent": "codesmith",
        }


def _post_pipeline_summary_to_linear(state: ProjectState, status: str, diag: str) -> None:
    if os.getenv("SWEAT_LINEAR_PIPELINE_COMMENT", "true").lower() not in {"1", "true", "yes", "on"}:
        return

    project_id = state.get("linear_project_id")
    if not project_id:
        return

    listed = linear.list_project_issues(project_id=project_id, first=30)
    if not listed.get("success"):
        return

    issues = listed.get("issues", [])
    if not issues:
        return

    # Prefer first non-completed issue; fallback to first.
    target = None
    for it in issues:
        st = ((it.get("state") or {}).get("type") or "").lower()
        if st not in {"completed", "canceled"}:
            target = it
            break
    if not target:
        target = issues[0]

    security_note = "security remediation report: n/a"
    sec_report = "reports/security/security_remediation_report.md"
    if os.path.exists(sec_report):
        try:
            with open(sec_report, "r", encoding="utf-8") as f:
                excerpt = f.read()[:1200]
            security_note = f"security remediation report excerpt:\n{excerpt}"
        except Exception:
            pass

    body = (
        "SWEAT pipeline update:\n"
        f"- status: {status}\n"
        f"- diagnostics: {diag}\n\n"
        f"{security_note}\n"
    )
    if target.get("id"):
        linear.comment_issue(issue_id=target.get("id"), body=body)


def _playwright_required(state: ProjectState, strict: bool) -> bool:
    if not strict:
        return False
    root = _workspace_root(state)
    has_node_project = os.path.exists(os.path.join(root, "package.json"))
    has_e2e_dir = os.path.exists(os.path.join(root, "tests", "e2e"))
    force = os.getenv("SWEAT_REQUIRE_PLAYWRIGHT", "auto").lower()
    if force in {"1", "true", "yes", "on"}:
        return True
    if force in {"0", "false", "no", "off"}:
        return False
    return has_node_project and has_e2e_dir


def _resolve_workspace_python(workspace_root: str) -> str | None:
    root = os.path.abspath(workspace_root or ".")
    candidate = os.path.join(root, ".venv", "bin", "python")
    return candidate if os.path.exists(candidate) else None


def _resolve_repo_python() -> str | None:
    # SWEAT repo-root venv fallback (absolute), used when project workspace is a subdir without its own .venv.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    candidate = os.path.join(repo_root, ".venv", "bin", "python")
    return candidate if os.path.exists(candidate) else None


def _resolve_pytest_cmd(workspace_root: str) -> list[str]:
    configured = os.getenv("SWEAT_PYTEST_BIN")
    if configured:
        return [configured]

    workspace_python = _resolve_workspace_python(workspace_root)
    if workspace_python:
        return [workspace_python, "-m", "pytest"]

    repo_python = _resolve_repo_python()
    if repo_python:
        return [repo_python, "-m", "pytest"]

    import shutil as _shutil
    found = _shutil.which("pytest")
    if found:
        return [found]

    return [sys.executable, "-m", "pytest"]


def _resolve_playwright_cmd(workspace_root: str) -> list[str] | None:
    configured = os.getenv("SWEAT_PLAYWRIGHT_BIN")
    if configured:
        return [configured, "test"]

    workspace_python = _resolve_workspace_python(workspace_root)
    if workspace_python:
        return [workspace_python, "-m", "playwright", "test"]

    repo_python = _resolve_repo_python()
    if repo_python:
        return [repo_python, "-m", "playwright", "test"]

    import shutil as _shutil
    found = _shutil.which("playwright")
    if found:
        return [found, "test"]

    return None


def pipeline_node(state: ProjectState) -> Dict[str, Any]:
    logger.info("PipeLine: starting CI.")
    import subprocess

    coverage_target = float(state.get("coverage_target") or 95)
    strict = os.getenv("SWEAT_STRICT_TEST_GATE", "true").lower() in {"1", "true", "yes", "on"}
    workspace_root = os.path.abspath(_workspace_root(state))

    pytest_cmd_base = _resolve_pytest_cmd(workspace_root)
    playwright_cmd = _resolve_playwright_cmd(workspace_root)

    logs = []
    unit_passed = False
    integration_passed = False
    playwright_passed = False
    playwright_required = _playwright_required(state, strict=strict)
    coverage = None

    try:
        # 1) Unit tests + coverage gate (mandatory in strict mode)
        unit_cmd = [
            *pytest_cmd_base, "-q",
            "--cov=src", "--cov-report=term-missing",
            "--ignore=tests/test_ci.py", "--ignore=tests/debug_import.py",
        ]
        if strict:
            unit_cmd.append(f"--cov-fail-under={coverage_target}")

        unit = subprocess.run(unit_cmd, capture_output=True, text=True, cwd=workspace_root)
        unit_out = (unit.stdout or "") + (unit.stderr or "")
        coverage = extract_coverage_percent(unit_out)
        if strict:
            unit_passed = unit.returncode == 0 and (coverage is not None and coverage >= coverage_target)
        else:
            unit_passed = unit.returncode == 0
        logs.append(f"[UNIT] cmd={' '.join(unit_cmd)}\n{unit_out}")

        # 2) Integration tests (mandatory in strict mode)
        int_cmd = [*pytest_cmd_base, "-q", "tests/integration"]
        integration = subprocess.run(int_cmd, capture_output=True, text=True, cwd=workspace_root)
        int_out = (integration.stdout or "") + (integration.stderr or "")
        integration_passed = integration.returncode == 0
        logs.append(f"[INTEGRATION] cmd={' '.join(int_cmd)}\n{int_out}")

            # 3) Playwright functional tests (only when required)
        if playwright_required:
            if playwright_cmd:
                pw = subprocess.run(playwright_cmd, capture_output=True, text=True, cwd=workspace_root)
                pw_out = (pw.stdout or "") + (pw.stderr or "")
                playwright_passed = pw.returncode == 0
                logs.append(f"[PLAYWRIGHT] cmd={' '.join(playwright_cmd)}\n{pw_out}")
            else:
                pw_out = "Playwright required but CLI/interpreter not found (workspace .venv or PATH)."
                logs.append(f"[PLAYWRIGHT] {pw_out}")
                playwright_passed = False
        else:
            playwright_passed = True
            logs.append("[PLAYWRIGHT] skipped (not required for this project/workspace)")

    except Exception as e:
        logs.append(f"CI Execution Error: {e}")

    if strict:
        passed = unit_passed and integration_passed and playwright_passed
    else:
        passed = unit_passed

    pipeline_run_count = int(state.get("pipeline_run_count") or 0) + 1
    pipeline_retry_budget = int(os.getenv("SWEAT_PIPELINE_RETRY_BUDGET", "3"))

    fail_reasons = []
    if not unit_passed:
        fail_reasons.append("unit_failed")
    if strict and not integration_passed:
        fail_reasons.append("integration_failed")
    if strict and not playwright_passed:
        fail_reasons.append("playwright_failed")

    status = "PASSED" if passed else "FAILED"
    output = "\n\n".join(logs)
    diag = f"strict={strict}, unit={unit_passed}, integration={integration_passed}, playwright_required={playwright_required}, playwright={playwright_passed}, coverage={coverage}, target={coverage_target}, reasons={fail_reasons}"

    # Auto-document pipeline + security summary into Linear when project context exists.
    _post_pipeline_summary_to_linear(state=state, status=status, diag=diag)

    if passed:
        next_agent = "deployer"
        lifecycle_fail_reason = None
    else:
        exhausted = pipeline_run_count >= pipeline_retry_budget
        # Never terminate directly on failed CI; force remediation path.
        next_agent = "codesmith" if not exhausted else "bughunter"
        lifecycle_fail_reason = "pipeline_retry_budget_exhausted" if exhausted else None

    return {
        "messages": [AIMessage(content=f"PipeLine 🚀: CI Status: {status}\n\nDiagnostics:\n{diag}\n\nOutput:\n{output}")],
        "decision_reason_code": "pipeline_pass" if passed else ("pipeline_retry_budget_exhausted" if lifecycle_fail_reason else "pipeline_failed_retry"),
        "ci_pipeline_status": status,
        "ci_passed": passed,
        "coverage_percent": coverage,
        "unit_test_passed": unit_passed,
        "integration_test_passed": integration_passed,
        "playwright_test_passed": playwright_passed,
        "pipeline_failure_reasons": fail_reasons,
        "last_pipeline_diag": diag,
        "last_pipeline_output": output[-20000:] if isinstance(output, str) else "",
        "pipeline_run_count": pipeline_run_count,
        "lifecycle_fail_reason": lifecycle_fail_reason,
        "next_agent": next_agent,
    }


def integrator_node(state: ProjectState) -> Dict[str, Any]:
    req = state.get("requirements", {})
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are Integrator 🔌. Produce integration contract: external APIs, auth scheme, retries, error map."),
        ("human", f"Requirements: {req}")
    ])
    response = (prompt | llm).invoke({})
    _write_project_file(state, "docs/integration/contracts.md", response.content)
    return {"messages": [response], "integration_endpoints": [_ws_rel_path(state, "docs/integration/contracts.md")], "next_agent": "automator"}


def automator_node(state: ProjectState) -> Dict[str, Any]:
    # Loop cleanup: if already completed once, stop.
    if state.get("automation_completed"):
        return {
            "messages": [AIMessage(content="Automator: already completed; ending flow.")],
            "decision_reason_code": "automator_already_completed",
            "next_agent": "__end__",
        }

    run_count = int(state.get("automator_run_count") or 0) + 1

    # Automator triggers n8n if webhook is configured
    workflow = n8n.create_workflow(
        name="sweat-build-notify",
        trigger="webhook",
        actions=[
            {"type": "http", "name": "trigger-ci"},
            {"type": "notify", "name": "send-status"},
        ],
    )
    content = json.dumps(workflow, indent=2)
    _write_project_file(state, "automation/n8n/workflow.json", content)

    status_msg = f"Automator: Workflow '{workflow['name']}' status: {workflow.get('remote_status', 'draft')}."
    if workflow.get("error"):
        status_msg += f" Error: {workflow['error']}"

    success = workflow.get("remote_status") == "synced"
    if success:
        next_agent = "__end__"
        lifecycle_fail_reason = None
    else:
        retry_pipeline = os.getenv("SWEAT_AUTOMATOR_RETRY_VIA_PIPELINE", "true").lower() in {"1", "true", "yes", "on"}
        automator_retry_budget = int(os.getenv("SWEAT_AUTOMATOR_RETRY_BUDGET", "3"))
        exhausted = run_count >= automator_retry_budget
        next_agent = "pipeline" if (retry_pipeline and not exhausted) else "__end__"
        lifecycle_fail_reason = "automator_retry_budget_exhausted" if exhausted else "automator_sync_failed"

    return {
        "messages": [AIMessage(content=status_msg)],
        "decision_reason_code": "automator_synced" if success else ("automator_retry_budget_exhausted" if lifecycle_fail_reason == "automator_retry_budget_exhausted" else "automator_sync_failed"),
        "automation_workflows": [workflow],
        "automation_completed": success,
        "automator_run_count": run_count,
        "lifecycle_fail_reason": lifecycle_fail_reason,
        "next_agent": next_agent,
    }


def deployer_node(state: ProjectState) -> Dict[str, Any]:
    deployer_run_count = int(state.get("deployer_run_count") or 0) + 1
    deployer_retry_budget = int(os.getenv("SWEAT_DEPLOYER_RETRY_BUDGET", "3"))

    strict_ci = os.getenv("SWEAT_DEPLOY_STRICT_CI", "true").lower() in {"1", "true", "yes", "on"}
    _write_project_file(state, ".github/workflows/ci.yml", ci_template("python", strict=strict_ci))
    _write_project_file(state, "deploy/Dockerfile", dockerfile_template("sweat"))
    _write_project_file(state, "deploy/k8s-deployment.yaml", k8s_deployment_template("sweat", "zocaibotz/sweat:latest"))
    _write_project_file(state, ".github/workflows/nightly-healthcheck.yml", """name: Nightly Healthcheck\non:\n  schedule:\n    - cron: '0 2 * * *'\n  workflow_dispatch:\n\njobs:\n  integration_health:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n      - run: pip install -r requirements.txt\n      - run: python -c \"print('Nightly drift/healthcheck placeholder: add Linear/n8n/provider checks')\"\n      - uses: actions/upload-artifact@v4\n        with:\n          name: nightly-healthcheck\n          path: .\n""")
    chain_automator = os.getenv("SWEAT_CHAIN_AUTOMATOR_AFTER_DEPLOY", "true").lower() in {"1", "true", "yes", "on"}
    exhausted = deployer_run_count >= deployer_retry_budget
    next_agent = "automator" if (chain_automator and not exhausted) else "__end__"
    fail_reason = "deployer_retry_budget_exhausted" if exhausted else None

    return {
        "messages": [AIMessage(content="Deployer: generated CI workflow + Dockerfile + K8s manifest.")],
        "decision_reason_code": "deployer_to_automator" if next_agent == "automator" else "deployer_retry_budget_exhausted",
        "deployment_url": "pending",
        "deployment_approved": next_agent == "automator",
        "infrastructure_config": _ws_rel_path(state, "deploy/k8s-deployment.yaml"),
        "deployer_run_count": deployer_run_count,
        "lifecycle_fail_reason": fail_reason,
        "next_agent": next_agent,
    }


def sprint_executor_node(state: ProjectState) -> Dict[str, Any]:
    """
    Autonomous sprint loop v2:
    - priority-aware selection
    - WIP limit guard
    - multi-issue cycle per run
    - status digest summary
    """
    project_id = state.get("linear_project_id")
    if not project_id:
        return {
            "messages": [AIMessage(content="Sprint executor skipped: no linear_project_id.")],
            "sprint_executor_completed": False,
            "next_agent": "__end__",
        }

    listed = linear.list_project_issues(project_id=project_id, first=100)
    if not listed.get("success"):
        return {
            "messages": [AIMessage(content=f"Sprint executor failed to list issues: {listed.get('error')}")],
            "sprint_executor_completed": False,
            "next_agent": "__end__",
        }

    issues = listed.get("issues", [])
    wip_limit = int(os.getenv("SWEAT_SPRINT_WIP_LIMIT", "1"))
    max_per_run = int(os.getenv("SWEAT_SPRINT_MAX_ISSUES_PER_RUN", "2"))

    in_progress = [i for i in issues if ((i.get("state") or {}).get("type") or "").lower() == "started"]
    if len(in_progress) >= wip_limit:
        return {
            "messages": [AIMessage(content=f"Sprint executor paused: WIP limit reached ({len(in_progress)}/{wip_limit}).")],
            "sprint_execution_log": [],
            "sprint_executor_completed": True,
            "next_agent": "__end__",
        }

    def priority_key(it: Dict[str, Any]):
        # Linear: lower numeric values are typically higher priority (1 urgent), 0 often unset.
        p = it.get("priority")
        if p in (None, 0):
            p = 999
        return int(p)

    actionable = [
        i for i in issues
        if ((i.get("state") or {}).get("type") or "").lower() in {"backlog", "unstarted", "triage", "started"}
    ]
    actionable.sort(key=priority_key)

    allowance = max(0, wip_limit - len(in_progress))
    budget = min(max_per_run, allowance if allowance > 0 else 0)
    targets = actionable[:budget]

    if not targets:
        return {
            "messages": [AIMessage(content="Sprint executor: no actionable issues within current WIP budget.")],
            "sprint_execution_log": [],
            "sprint_executor_completed": True,
            "next_agent": "__end__",
        }

    log = []
    processed = []
    for target in targets:
        ident = target.get("identifier")
        if not ident:
            continue

        r1 = linear.transition_issue(ident, "started")
        log.append({"identifier": ident, "action": "started", "result": r1})

        note = "SWEAT sprint executor processed this issue in autonomous loop (v2 priority/WIP mode)."
        if target.get("id"):
            linear.comment_issue(issue_id=target.get("id"), body=note)

        r2 = linear.close_issue(ident)
        log.append({"identifier": ident, "action": "completed", "result": r2})
        processed.append(ident)

    digest = (
        f"Sprint executor processed {len(processed)} issue(s): {', '.join(processed)} | "
        f"WIP limit={wip_limit}, max_per_run={max_per_run}"
    )

    return {
        "messages": [AIMessage(content=digest)],
        "sprint_execution_log": log,
        "sprint_executor_completed": True,
        "next_agent": "__end__",
    }


def scrumlord_node(state: ProjectState) -> Dict[str, Any]:
    logger.info("ScrumLord: planning sprint.")
    reqs = state.get("requirements", {})
    arch = state.get("architecture_docs", "")

    # Generate tickets via LLM
    req_text = json.dumps(reqs, ensure_ascii=False)
    response = llm.invoke([
        SystemMessage(content="You are ScrumLord. Break down the project into 3-5 key tasks based on requirements/architecture. Output ONLY JSON list with fields: title, description, priority."),
        HumanMessage(content=f"Requirements: {req_text}\nArchitecture: {arch}"),
    ])

    backlog = []
    sync_updates = []
    project_context = {}
    try:
        project_id = state.get("linear_project_id")
        should_create_project = bool(state.get("should_create_linear_project"))
        project_name = state.get("linear_project_name") or f"SWEAT-{state.get('project_id', 'initiative')}"

        if not project_id and should_create_project:
            proj = linear.create_or_get_project(name=project_name, description="Created by ScrumLord for scoped initiative")
            if proj.get("success"):
                project = proj.get("project") or {}
                project_id = project.get("id")
                project_context = {
                    "linear_project_id": project.get("id"),
                    "linear_project_name": project.get("name"),
                    "linear_project_url": project.get("url"),
                    "linear_project_created": proj.get("created", False),
                }
            else:
                project_context = {"linear_project_error": proj.get("error")}

        tasks = extract_json_content(response.content)
        if isinstance(tasks, list):
            for task in tasks:
                res = linear.create_issue(
                    title=task.get("title", "Untitled Task"),
                    description=task.get("description", ""),
                    priority=task.get("priority", 0),
                    project_id=project_id,
                )
                if res.get("success"):
                    issue = res["issue"]
                    backlog.append({"id": issue["identifier"], "title": issue["title"], "url": issue["url"]})
                else:
                    backlog.append({"id": "ERROR", "title": task.get("title"), "error": res.get("error")})

        # Optional robust sync/update routines from state, example:
        # state["scrum_updates"] = [
        #   {"identifier":"ZOC-1","transition_to":"started"},
        #   {"identifier":"ZOC-2","assignee_id":"..."},
        #   {"identifier":"ZOC-3","close":true}
        # ]
        for upd in (state.get("scrum_updates") or []):
            identifier = upd.get("identifier")
            if not identifier:
                sync_updates.append({"success": False, "error": "missing identifier", "input": upd})
                continue

            step_results = {"identifier": identifier, "actions": []}

            if upd.get("transition_to"):
                r = linear.transition_issue(identifier, upd.get("transition_to"))
                step_results["actions"].append({"type": "transition", "to": upd.get("transition_to"), "result": r})

            if upd.get("assignee_id"):
                r = linear.assign_issue_by_identifier(identifier, upd.get("assignee_id"))
                step_results["actions"].append({"type": "assign", "assignee_id": upd.get("assignee_id"), "result": r})

            if upd.get("close"):
                r = linear.close_issue(identifier)
                step_results["actions"].append({"type": "close", "result": r})

            sync_updates.append(step_results)

    except Exception as e:
        logger.error(f"ScrumLord failed parsing: {e}")
        backlog.append({"error": f"Failed to parse tasks: {e}"})

    summary = "\n".join([f"- {t.get('id')}: {t.get('title')} ({t.get('url', 'no-url')})" for t in backlog])
    if sync_updates:
        summary += "\n\nSync updates:\n" + json.dumps(sync_updates, ensure_ascii=False)

    run_executor = os.getenv("SWEAT_SPRINT_EXECUTOR_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    return {
        "messages": [AIMessage(content=f"ScrumLord Sprint Backlog:\n{summary}")],
        "sprint_backlog": backlog,
        "scrum_sync_updates": sync_updates,
        **project_context,
        "next_agent": "sprint_executor" if run_executor else "__end__",
    }
