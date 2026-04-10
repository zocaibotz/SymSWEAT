from typing import Dict, Any, TypedDict, Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from src.state import ProjectState
from src.utils.llm import get_llm
from src.utils.logger import logger
from src.utils.context import trim_context
from src.utils.memory import get_memory
from src.utils.parser import extract_json_content
from src.sweat_v2.bridge import route_with_v2
from src.sweat_v2.config import load_v2_flags
from src.sweat_v2.shadow_runner import append_shadow_record, build_shadow_record
import json

llm = get_llm()
memory = get_memory()

def orchestrator_node(state: ProjectState) -> Dict[str, Any]:
    """
    Zocai (Orchestrator) decides the next step based on the project state using an LLM.
    Phase-2 policy: default to SDD interview-first flow.
    """
    flags = load_v2_flags()

    v2_decision = route_with_v2(state, flags) if flags.enabled else None

    def _with_shadow(next_agent: str) -> Dict[str, Any]:
        result = {"next_agent": next_agent}
        if flags.enabled and flags.shadow_mode and v2_decision is not None:
            result.update({
                "v2_shadow_mode": True,
                "v2_next_agent_recommendation": v2_decision.next_agent,
                "v2_stage": v2_decision.v2_stage,
                "v2_policy_violations": v2_decision.policy_violations,
            })
            try:
                shadow_record = build_shadow_record(state, next_agent, v2_decision)
                append_shadow_record(shadow_record)
            except Exception:
                pass
        return result

    # SWEAT v2 router bridge: shadow mode records recommendation, enabled mode can drive routing.
    if flags.enabled and not flags.shadow_mode and v2_decision is not None:
        return {
            "next_agent": v2_decision.next_agent,
            "v2_stage": v2_decision.v2_stage,
            "v2_policy_violations": v2_decision.policy_violations,
            "v2_shadow_mode": False,
        }

    # Phase-2 hard gates before free routing
    req = state.get("requirements") if isinstance(state.get("requirements"), dict) else {}
    has_req = bool(req) and bool(req.get("name") or req.get("project_name")) and bool(req.get("acceptance_criteria"))
    if state.get("requirements_interview_status") != "complete" and not has_req:
        return _with_shadow("req_master_interview")

    if state.get("sdd_status") not in {"tasks_done", "plan_done", "specify_done"}:
        # Once interview completes, force SDD pipeline to start.
        return _with_shadow("sdd_specify")

    if state.get("design_approval_status") != "approved":
        return _with_shadow("design_approval_gate")

    if state.get("test_readiness_status") != "ready":
        return _with_shadow("tdd_orchestrator")

    # 0. Retrieve Relevant Memory
    last_message = state["messages"][-1].content
    try:
        past_context = memory.retrieve_context(last_message, k=2)
        memory_context_str = "\n".join(past_context) if past_context else "No relevant past memory."
    except Exception as e:
        logger.warning(f"Memory retrieval failed: {e}")
        memory_context_str = "Memory unavailable."

    # 1. Prune Context
    raw_messages = state["messages"]
    pruned_messages = trim_context(raw_messages, max_messages=15)
    
    logger.info("Zocai is thinking...")
    
    # Define available agents and their roles for the LLM
    agent_descriptions = (
        "1. req_master: User requirements, clarifying project scope.\n"
        "2. architect: System design, tech stack, file structure.\n"
        "3. pixel: UX design, wireframes, user personas.\n"
        "4. frontman: UI implementation, frontend components.\n"
        "5. codesmith: Writing code, implementing features.\n"
        "6. bughunter: Testing, bug reporting, QA.\n"
        "7. gatekeeper: Code review, security checks.\n"
        "8. pipeline: CI/CD setup, build processes.\n"
        "9. integrator: API integration, database schema.\n"
        "10. automator: n8n workflows, automation tasks.\n"
        "11. deployer: Deployment to cloud/k8s.\n"
        "12. scrumlord: Sprint planning, project management.\n"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are Zocai, the Master Orchestrator of a software team. Your job is to route the conversation to the most appropriate specialist based on the last message and context.\n"
                   f"Available Agents:\n{agent_descriptions}\n"
                   f"Relevant Long-Term Memory:\n{memory_context_str}\n"
                   "Analyze the conversation. Who should act next?\n"
                   "Output ONLY a JSON object with a single key 'next_agent' and the agent name as value. Example: {{\"next_agent\": \"codesmith\"}}\n"
                   "If unsure or if it's a general greeting, route to 'req_master_interview'."),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    # Use pruned messages for the LLM call to save tokens
    response = chain.invoke({"messages": pruned_messages})
    content = response.content.strip()
    
    logger.debug(f"Zocai thought: {content}")
    
    try:
        decision = extract_json_content(content)
        next_agent = decision.get("next_agent", "req_master_interview")
    except Exception as e:
        logger.debug(f"Zocai failed JSON parse: {e}")
        # Fallback to simple keyword matching if LLM fails to output JSON
        last_msg = raw_messages[-1].content.lower()
        if "code" in last_msg: next_agent = "codesmith"
        elif "test" in last_msg: next_agent = "bughunter"
        else: next_agent = "req_master_interview"

    # If the decision contains "approved", route to pipeline
    if "approved" in content.lower():
        next_agent = "pipeline"

    # Phase-3 strict normalization: no legacy requirement bypass
    if next_agent == "req_master":
        next_agent = "req_master_interview"

    # Phase-3 strict guardrails
    if state.get("design_approval_status") != "approved" and next_agent in {"codesmith", "gatekeeper", "pipeline", "deployer", "automator"}:
        next_agent = "design_approval_gate"

    if state.get("test_readiness_status") != "ready" and next_agent in {"codesmith", "gatekeeper", "pipeline", "deployer", "automator"}:
        next_agent = "tdd_orchestrator"

    return _with_shadow(next_agent)

def should_continue(state: ProjectState) -> Literal["req_master", "req_master_interview", "sdd_specify", "sdd_plan", "sdd_tasks", "architect", "pixel", "frontman", "design_approval_gate", "tdd_orchestrator", "unit_test_author", "integration_test_author", "playwright_test_author", "test_readiness_gate", "github_bootstrap", "codesmith", "bughunter", "gatekeeper", "pipeline", "integrator", "automator", "deployer", "scrumlord", "sprint_executor", "__end__"]:
    """
    Conditional edge logic to route to the next agent.
    """
    next_agent = state.get("next_agent", "req_master_interview")

    # Ensure next_agent is valid
    valid_agents = [
        "req_master", "req_master_interview", "sdd_specify", "sdd_plan", "sdd_tasks",
        "architect", "pixel", "frontman", "design_approval_gate", "tdd_orchestrator",
        "unit_test_author", "integration_test_author", "playwright_test_author", "test_readiness_gate", "github_bootstrap",
        "codesmith", "bughunter", "gatekeeper", "pipeline", "integrator", "automator", "deployer", "scrumlord", "sprint_executor"
    ]
    if next_agent not in valid_agents:
        next_agent = "req_master_interview" # Fallback
        
    return next_agent
