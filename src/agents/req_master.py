from langchain_core.messages import AIMessage, SystemMessage
from src.state import ProjectState
from src.utils.llm import get_llm
from src.utils.logger import logger
from src.utils.parser import extract_json_content, strip_think_blocks
import os
import json
import requests
import subprocess
from typing import Dict, Any

llm = get_llm()

LINEAR_API_URL = "https://api.linear.app/graphql"

PM_PROMPT = """
You are an expert Product Manager (ReqMaster). The user will provide a natural language idea for a software project or feature.
Your job is to break it down into a structured Epic and a Directed Acyclic Graph (DAG) of actionable engineering tickets.

Rules:
1. The first ticket (T1) MUST be the "Architect Run" ticket. It must be tasked with writing the global `docs/architecture/SYSTEM_DESIGN.md` and `API_CONTRACTS.md`.
2. The second ticket (T2) MUST be the "Core Observability Setup" ticket. It must be tasked with setting up global logger, OpenTelemetry tracing, and APM configuration. It must be blocked by T1 and block all subsequent implementation tickets.
3. The final ticket MUST be "Integration Testing". It must use Playwright for E2E testing based on BDD User Journeys. It must be blocked by all frontend/backend implementation tickets.
4. Map out the dependencies logically using the 'dependencies' array.
5. Keep titles concise.
6. Acceptance Criteria must be verifiable and strict.

Output EXCLUSIVELY in the following JSON format:
{
  "epic": {
    "title": "Epic Title",
    "description": "Epic description...",
    "repo_name": "repo-name-in-kebab-case"
  },
  "tickets": [
    {
      "ref_id": "T1",
      "title": "Architect System Design",
      "description": "Create SYSTEM_DESIGN.md...",
      "acceptance_criteria": "- SYSTEM_DESIGN.md is merged.",
      "dependencies": []
    },
    {
      "ref_id": "T2",
      "title": "Core Observability Setup",
      "description": "Setup OpenTelemetry and global logging...",
      "acceptance_criteria": "- Logger is globally available.",
      "dependencies": ["T1"]
    }
  ]
}
"""

def run_linear_graphql(query: str, variables: Dict) -> Dict:
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        raise Exception("LINEAR_API_KEY not set")
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    response = requests.post(
        LINEAR_API_URL,
        headers=headers,
        json={"query": query, "variables": variables}
    )
    response.raise_for_status()
    result = response.json()
    if "errors" in result:
        raise Exception(f"Linear API errors: {result['errors']}")
    return result

def create_linear_project(team_id: str, title: str, description: str) -> str:
    query = """
    mutation CreateProject($teamId: String!, $name: String!, $description: String!) {
      projectCreate(input: { teamIds: [$teamId], name: $name, description: $description }) {
        project { id }
      }
    }
    """
    vars = {"teamId": team_id, "name": title, "description": description}
    res = run_linear_graphql(query, vars)
    return res["data"]["projectCreate"]["project"]["id"]

def create_linear_issue(team_id: str, project_id: str, title: str, description: str) -> str:
    query = """
    mutation CreateIssue($teamId: String!, $projectId: String!, $title: String!, $description: String!) {
      issueCreate(input: { teamId: $teamId, projectId: $projectId, title: $title, description: $description }) {
        issue { id }
      }
    }
    """
    vars = {"teamId": team_id, "projectId": project_id, "title": title, "description": description}
    res = run_linear_graphql(query, vars)
    return res["data"]["issueCreate"]["issue"]["id"]

def create_issue_relation(issue_id: str, blocks_issue_id: str):
    query = """
    mutation CreateRelation($issueId: String!, $relatedId: String!) {
      issueRelationCreate(input: { issueId: $issueId, relatedIssueId: $relatedId, type: blocks }) {
        success
      }
    }
    """
    vars = {"issueId": issue_id, "relatedId": blocks_issue_id}
    run_linear_graphql(query, vars)

def create_github_repo(repo_name: str, description: str):
    logger.info(f"Scaffolding GitHub repository: {repo_name}")
    try:
        subprocess.run(["gh", "repo", "create", repo_name, "--public", "--add-readme", "-d", description], check=True, capture_output=True)
        logger.info(f"Successfully created GitHub repo: {repo_name}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to create GitHub repo {repo_name} (may already exist). Error: {e.stderr.decode()}")

def req_master_node(state: ProjectState) -> Dict[str, Any]:
    logger.info("ReqMaster: analyzing natural language input for Epic and DAG.")
    
    if state.get("requirements"):
        return {"messages": [AIMessage(content="Requirements already gathered.")]}
        
    last_msg = state["messages"][-1].content if state["messages"] else ""
    if not last_msg:
        return {"messages": [AIMessage(content="No input provided to ReqMaster.")]}

    response = llm.invoke([
        SystemMessage(content=PM_PROMPT),
        *state["messages"]
    ])

    content = strip_think_blocks(response.content.strip())
    
    try:
        plan = extract_json_content(content)
        if not isinstance(plan, dict) or "epic" not in plan or "tickets" not in plan:
            raise ValueError("Invalid DAG plan format")
            
        repo_name = plan['epic'].get('repo_name', plan['epic']['title'].lower().replace(' ', '-'))
        create_github_repo(repo_name, plan['epic']['description'])
        
        linear_team_id = os.environ.get("LINEAR_TEAM_ID")
        project_id = None
        if linear_team_id:
            base_desc = plan['epic']['description']
            repo_url = f"https://github.com/zocaibotz/{repo_name}"
            prefix = f"REPO_URL={repo_url}\\n"
            max_base_len = max(0, 255 - len(prefix) - 3)
            epic_desc = prefix + (base_desc[:max_base_len] + "..." if len(base_desc) > max_base_len else base_desc)
            
            logger.info(f"Creating Epic (Project): {plan['epic']['title']}")
            project_id = create_linear_project(linear_team_id, plan['epic']['title'], epic_desc)
            
            ticket_map = {}
            for ticket in plan['tickets']:
                desc = f"{ticket['description']}\\n\\n**Acceptance Criteria:**\\n{ticket['acceptance_criteria']}"
                issue_id = create_linear_issue(linear_team_id, project_id, ticket['title'], desc)
                ticket_map[ticket['ref_id']] = issue_id
                
            for ticket in plan['tickets']:
                target_id = ticket_map.get(ticket['ref_id'])
                if not target_id: continue
                for dep_ref in ticket.get('dependencies', []):
                    blocker_id = ticket_map.get(dep_ref)
                    if blocker_id:
                        create_issue_relation(blocker_id, target_id)
                        
            logger.info(f"Successfully generated Epic and {len(plan['tickets'])} tickets in Linear!")

        # Format as standard requirements for the rest of SWEAT pipeline
        requirements = {
            "name": plan['epic']['title'],
            "project_name": plan['epic']['title'],
            "goal": plan['epic']['description'],
            "acceptance_criteria": [t['acceptance_criteria'] for t in plan['tickets']],
            "estimated_tasks": len(plan['tickets']),
            "pm_dag_plan": plan
        }
        
        return {
            "requirements": requirements,
            "linear_project_id": project_id,
            "github_repo": f"zocaibotz/{repo_name}",
            "messages": [response],
            "next_agent": "sdd_specify"
        }
    except Exception as e:
        logger.error(f"ReqMaster failed to process input: {e}")
        return {"messages": [response, AIMessage(content=f"Error generating DAG: {e}")]}
