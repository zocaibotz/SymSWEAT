import os
import json
import re
import requests
import argparse
import subprocess
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Assuming usage of OpenAI library for the LLM parsing
from openai import OpenAI

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
LINEAR_TEAM_ID = os.environ.get("LINEAR_TEAM_ID") # Needed to create issues

# Fallback to Minimax if OpenAI key is fake
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
MINIMAX_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M2.5")

if OPENAI_API_KEY and "FAKE" in OPENAI_API_KEY and MINIMAX_API_KEY:
    OPENAI_API_KEY = MINIMAX_API_KEY
    os.environ["OPENAI_API_KEY"] = MINIMAX_API_KEY
    os.environ["OPENAI_BASE_URL"] = MINIMAX_BASE_URL
    MODEL = MINIMAX_MODEL
else:
    MODEL = "gpt-4o"

LINEAR_API_URL = "https://api.linear.app/graphql"

PM_PROMPT = """
You are an expert Product Manager. The user will provide a natural language idea for a software project or feature.
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

def call_llm_for_breakdown(user_request: str) -> Dict:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PM_PROMPT},
            {"role": "user", "content": user_request}
        ]
    )
    content = response.choices[0].message.content
    print(f"Raw LLM response (first 300 chars): {content[:300] if content else 'None'}")
    
    # Try to strip markdown JSON block if present
    content = content.strip()
    
    # Strip reasoning blocks (MiniMax/DeepSeek models use <think> and </think>)
    # Also handle Chinese reasoning tokens ]~b] and </think>
    reasoning_starts = ["<think>", "]~b]"]
    reasoning_ends = ["</think>", "</think>"]
    
    for start_tok in reasoning_starts:
        if content.startswith(start_tok):
            for end_tok in reasoning_ends:
                end_idx = content.find(end_tok)
                if end_idx != -1:
                    content = content[end_idx + len(end_tok):].strip()
                    break
            break
    
    # Also look for JSON block in markdown
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    # Try to find JSON object by looking for first { and last }
    json_start = content.find('{')
    json_end = content.rfind('}')
    if json_start != -1 and json_end != -1 and json_end > json_start:
        content = content[json_start:json_end+1]
        
    print(f"Parsed content (first 200 chars): {content[:200]}")
    return json.loads(content.strip())

def run_linear_graphql(query: str, variables: Dict) -> Dict:
    headers = {
        "Authorization": LINEAR_API_KEY,
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

def create_linear_project(title: str, description: str) -> str:
    query = """
    mutation CreateProject($teamId: String!, $name: String!, $description: String!) {
      projectCreate(input: { teamIds: [$teamId], name: $name, description: $description }) {
        project { id }
      }
    }
    """
    vars = {"teamId": LINEAR_TEAM_ID, "name": title, "description": description}
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
    # Note: 'blocks' relation means issueId blocks relatedId
    vars = {"issueId": issue_id, "relatedId": blocks_issue_id}
    run_linear_graphql(query, vars)

def create_github_repo(repo_name: str, description: str):
    print(f"Scaffolding GitHub repository: {repo_name}")
    try:
        subprocess.run(["gh", "repo", "create", repo_name, "--public", "--add-readme", "-d", description], check=True)
        print(f"Successfully created GitHub repo: {repo_name}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to create GitHub repo {repo_name} (it may already exist). Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="PM Agent for SWARMINSYM")
    parser.add_argument("request", type=str, help="Natural language request for the new feature or app.")
    args = parser.parse_args()

    if not LINEAR_API_KEY or not LINEAR_TEAM_ID or not OPENAI_API_KEY:
        print("Missing required environment variables: LINEAR_API_KEY, LINEAR_TEAM_ID, OPENAI_API_KEY")
        return

    print("Analyzing request and building Epic DAG...")
    plan = call_llm_for_breakdown(args.request)
    
    repo_name = plan['epic'].get('repo_name', plan['epic']['title'].lower().replace(' ', '-'))
    create_github_repo(repo_name, plan['epic']['description'])
    
    # Linear has a 255 char limit on description.
    # Keep structured repo metadata at the top so poller can parse it reliably.
    base_desc = plan['epic']['description']
    repo_url = f"https://github.com/zocaibotz/{repo_name}"
    prefix = f"REPO_URL={repo_url}\n"

    max_base_len = 255 - len(prefix) - 3
    if max_base_len < 0:
        max_base_len = 0
    if len(base_desc) > max_base_len:
        base_desc = base_desc[:max_base_len] + "..."

    epic_desc = prefix + base_desc
    
    print(f"Creating Epic (Project): {plan['epic']['title']}")
    project_id = create_linear_project(plan['epic']['title'], epic_desc)
    
    ticket_map = {} # ref_id -> linear_issue_id
    
    # We must create tickets first to get their IDs
    for ticket in plan['tickets']:
        desc = f"{ticket['description']}\n\n**Acceptance Criteria:**\n{ticket['acceptance_criteria']}"
        print(f"Creating Ticket: {ticket['title']}")
        issue_id = create_linear_issue(LINEAR_TEAM_ID, project_id, ticket['title'], desc)
        ticket_map[ticket['ref_id']] = issue_id

    print("Linking dependencies (Blocked By relations)...")
    for ticket in plan['tickets']:
        target_id = ticket_map[ticket['ref_id']]
        for dep_ref in ticket.get('dependencies', []):
            blocker_id = ticket_map.get(dep_ref)
            if blocker_id:
                # Blocker blocks Target
                create_issue_relation(blocker_id, target_id)

    print(f"Successfully generated Epic and {len(plan['tickets'])} tickets in Linear!")

if __name__ == "__main__":
    main()
