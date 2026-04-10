from typing import TypedDict, List, Dict, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator

class ProjectState(TypedDict):
    """
    The central state of the SWEAT project.
    All agents read from and write to this state.
    """
    project_id: str
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Requirement Gatherer
    requirements: Optional[Dict]
    user_stories: Optional[List[str]]
    requirements_interview_status: Optional[str]
    requirements_questions_asked: Optional[List[str]]
    requirements_open_questions: Optional[List[str]]
    requirements_revision_reasons: Optional[List[str]]
    requirements_revision_count: Optional[int]
    human_input_required: Optional[bool]
    requirements_sdd_prompt: Optional[str]
    loop_escalation_count: Optional[int]
    codesmith_gatekeeper_bounce_count: Optional[int]

    # SDD artifacts
    sdd_spec_path: Optional[str]
    sdd_spec_status: Optional[str]
    sdd_plan_path: Optional[str]
    sdd_tasks_path: Optional[str]
    sdd_status: Optional[str]
    sdd_quality_score: Optional[float]
    sdd_quality_notes: Optional[List[str]]
    traceability_map_path: Optional[str]
    
    # Architect
    architecture_docs: Optional[str]
    system_design_diagram: Optional[str]
    design_doc_path: Optional[str]
    design_approval_status: Optional[str]
    design_approval_notes: Optional[str]
    
    # UX Designer
    ux_wireframes: Optional[str]
    personas: Optional[List[Dict]]
    
    # UI Engineer
    ui_component_library: Optional[str]
    frontend_framework: Optional[str]
    
    # Coder
    code_repository: Optional[str]
    file_structure: Optional[Dict]
    current_file_content: Optional[str]
    codesmith_retry_count: Optional[int]
    github_repo: Optional[str]
    github_default_branch: Optional[str]
    github_url: Optional[str]
    project_workspace_path: Optional[str]
    
    # Tester
    test_results: Optional[Dict]
    bug_reports: Optional[List[Dict]]
    unit_test_plan_path: Optional[str]
    integration_test_plan_path: Optional[str]
    playwright_test_plan_path: Optional[str]
    test_readiness_status: Optional[str]
    coverage_target: Optional[int]
    
    # Reviewer
    code_review_feedback: Optional[str]
    security_scan_results: Optional[Dict]
    
    # CI/CD
    ci_pipeline_status: Optional[str]
    pipeline_run_count: Optional[int]
    build_logs: Optional[str]
    unit_test_passed: Optional[bool]
    integration_test_passed: Optional[bool]
    playwright_test_passed: Optional[bool]
    coverage_percent: Optional[float]
    
    # Integrator
    integration_endpoints: Optional[List[str]]
    db_schema: Optional[str]
    
    # Automator
    automation_workflows: Optional[List[Dict]]
    automation_completed: Optional[bool]
    automator_run_count: Optional[int]
    deployer_run_count: Optional[int]
    lifecycle_fail_reason: Optional[str]
    n8n_webhook_urls: Optional[List[str]]
    
    # Deployer
    deployment_url: Optional[str]
    infrastructure_config: Optional[str]
    
    # Scrum Master
    sprint_backlog: Optional[List[Dict]]
    scrum_updates: Optional[List[Dict]]
    scrum_sync_updates: Optional[List[Dict]]
    sprint_execution_log: Optional[List[Dict]]
    sprint_executor_completed: Optional[bool]
    should_create_linear_project: Optional[bool]
    linear_project_name: Optional[str]
    linear_project_id: Optional[str]
    linear_project_url: Optional[str]
    linear_project_created: Optional[bool]
    linear_project_error: Optional[str]
    project_decision_score: Optional[int]
    burndown_chart: Optional[str]
    current_sprint: Optional[int]

    # Orchestrator Routing
    next_agent: Optional[str]
    last_agent: Optional[str]
    run_telemetry: Optional[List[Dict]]
    run_report_path: Optional[str]
    run_id: Optional[str]
    run_started: Optional[bool]
    project_state_version: Optional[int]

    # SWEAT v2 bridge/shadow metadata
    v2_shadow_mode: Optional[bool]
    v2_stage: Optional[str]
    v2_next_agent_recommendation: Optional[str]
    v2_policy_violations: Optional[List[str]]
