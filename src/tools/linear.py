import os
import requests
from typing import Optional, List, Dict, Any
from src.utils.logger import logger


class LinearClient:
    """Client for Linear API (GraphQL)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("LINEAR_API_KEY", "")
        self.api_url = "https://api.linear.app/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"{self.api_key}",
        }

    def _diagnostics(self, require_team: bool = False, team_id: str = None) -> dict:
        resolved_team = self._resolve_team_id(team_id)
        return {
            "api_url": self.api_url,
            "has_api_key": bool(self.api_key),
            "has_team_id": bool(resolved_team),
            "team_id_hint": resolved_team[:8] + "..." if resolved_team else None,
            "require_team": require_team,
        }

    def _require_config(self, require_team: bool = False, team_id: str = None) -> Optional[dict]:
        d = self._diagnostics(require_team=require_team, team_id=team_id)
        if not d["has_api_key"]:
            msg = "Linear hard-fail: LINEAR_API_KEY missing; refusing API call"
            logger.error(msg)
            return {"success": False, "error": msg, "diagnostics": d, "error_code": "LINEAR_CONFIG_MISSING_API_KEY"}
        if require_team and not d["has_team_id"]:
            msg = "Linear hard-fail: LINEAR_TEAM_ID missing for team-scoped operation"
            logger.error(msg)
            return {"success": False, "error": msg, "diagnostics": d, "error_code": "LINEAR_CONFIG_MISSING_TEAM_ID"}
        return None

    def _query(self, query: str, variables: dict = None) -> dict:
        variables = variables or {}
        if not self.api_key:
            msg = "Linear hard-fail: LINEAR_API_KEY missing; refusing GraphQL query"
            logger.error(msg)
            return {"errors": [msg], "error_code": "LINEAR_CONFIG_MISSING_API_KEY", "diagnostics": self._diagnostics()}

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Linear API error: {e}")
            return {"errors": [str(e)]}

    @staticmethod
    def _unwrap(result: dict, path: List[str], default=None):
        cur = result
        for p in path:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(p)
            if cur is None:
                return default
        return cur

    def _resolve_team_id(self, team_id: Optional[str]) -> str:
        resolved = (team_id or os.getenv("LINEAR_TEAM_ID", "")).strip()
        return resolved

    def create_project(self, name: str, description: str = "", team_id: str = None) -> dict:
        cfg = self._require_config(require_team=True, team_id=team_id)
        if cfg:
            return cfg
        resolved_team = self._resolve_team_id(team_id)
        mutation = """
        mutation ProjectCreate($input: ProjectCreateInput!) {
          projectCreate(input: $input) {
            success
            project {
              id
              name
              url
              state
            }
          }
        }
        """
        result = self._query(
            mutation,
            {"input": {"name": name, "description": description, "teamIds": [resolved_team]}},
        )
        payload = self._unwrap(result, ["data", "projectCreate"])
        if isinstance(payload, dict):
            return payload
        return {"success": False, "error": result.get("errors", "Project create failed")}

    def find_project_by_name(self, name: str) -> dict:
        cfg = self._require_config(require_team=False)
        if cfg:
            return cfg
        query = """
        query ProjectByName($name: String!) {
          projects(filter: { name: { eq: $name } }) {
            nodes {
              id
              name
              url
              state
            }
          }
        }
        """
        result = self._query(query, {"name": name})
        nodes = self._unwrap(result, ["data", "projects", "nodes"], default=[])
        if isinstance(nodes, list) and nodes:
            return {"success": True, "project": nodes[0]}
        if isinstance(nodes, list):
            return {"success": False, "error": "Project not found"}
        return {"success": False, "error": result.get("errors", "Project lookup failed")}

    def create_or_get_project(self, name: str, description: str = "", team_id: str = None) -> dict:
        existing = self.find_project_by_name(name)
        if existing.get("success"):
            return {"success": True, "project": existing["project"], "created": False}

        created = self.create_project(name=name, description=description, team_id=team_id)
        if created.get("success"):
            return {"success": True, "project": created.get("project"), "created": True}
        return {"success": False, "error": created.get("error")}

    def create_issue(self, title: str, description: str, team_id: str = None, priority: int = 0, project_id: str = None) -> dict:
        cfg = self._require_config(require_team=True, team_id=team_id)
        if cfg:
            return cfg
        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    title
                    identifier
                    url
                    state { id name type }
                    assignee { id name email }
                }
            }
        }
        """

        resolved_team = self._resolve_team_id(team_id)
        variables = {
            "input": {
                "title": title,
                "description": description,
                "teamId": resolved_team,
                "priority": priority,
            }
        }
        if project_id:
            variables["input"]["projectId"] = project_id

        result = self._query(mutation, variables)
        payload = self._unwrap(result, ["data", "issueCreate"])
        if isinstance(payload, dict):
            return payload
        return {"success": False, "error": result.get("errors", "Unknown error")}

    def get_issue(self, identifier: str) -> dict:
        cfg = self._require_config(require_team=False)
        if cfg:
            return cfg
        ident = (identifier or "").strip()

        # Path A: direct by UUID id
        query_by_id = """
        query IssueById($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            url
            state { id name type }
            assignee { id name email }
            project { id name }
            team { id key name }
          }
        }
        """
        if len(ident) >= 32 and "-" in ident:
            result = self._query(query_by_id, {"id": ident})
            issue = self._unwrap(result, ["data", "issue"])
            if issue:
                return {"success": True, "issue": issue}

        # Path B: identifier like TEAM-123 -> query by number (supported by IssueFilter)
        team_key = None
        num = None
        if "-" in ident:
            parts = ident.split("-", 1)
            if len(parts) == 2 and parts[1].isdigit():
                team_key, num = parts[0], int(parts[1])

        if num is not None:
            query_by_num = """
            query IssueByNumber($n: Float!, $key: String) {
              issues(filter: { number: { eq: $n }, team: { key: { eq: $key } } }, first: 5) {
                nodes {
                  id
                  identifier
                  title
                  url
                  state { id name type }
                  assignee { id name email }
                  project { id name }
                  team { id key name }
                }
              }
            }
            """
            result = self._query(query_by_num, {"n": float(num), "key": team_key})
            nodes = self._unwrap(result, ["data", "issues", "nodes"], default=[])
            if isinstance(nodes, list) and nodes:
                exact = next((n for n in nodes if (n.get("identifier") or "").upper() == ident.upper()), nodes[0])
                return {"success": True, "issue": exact}

        return {"success": False, "error": f"Issue not found: {ident}"}

    def list_workflow_states(self, team_id: str = None) -> dict:
        cfg = self._require_config(require_team=True, team_id=team_id)
        if cfg:
            return cfg
        resolved_team = self._resolve_team_id(team_id)
        query = """
        query TeamStates($teamId: String!) {
          team(id: $teamId) {
            id
            name
            states {
              nodes {
                id
                name
                type
              }
            }
          }
        }
        """
        result = self._query(query, {"teamId": resolved_team})
        states = self._unwrap(result, ["data", "team", "states", "nodes"], default=[])
        if isinstance(states, list):
            return {"success": True, "states": states}
        return {"success": False, "error": result.get("errors", "Could not load team states")}

    def update_issue(self, issue_id: str, state_id: str = None, assignee_id: str = None) -> dict:
        mutation = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
              identifier
              title
              url
              state { id name type }
              assignee { id name email }
            }
          }
        }
        """
        issue_input: Dict[str, Any] = {}
        if state_id:
            issue_input["stateId"] = state_id
        if assignee_id:
            issue_input["assigneeId"] = assignee_id

        if not issue_input:
            return {"success": False, "error": "No update fields provided"}

        result = self._query(mutation, {"id": issue_id, "input": issue_input})
        payload = self._unwrap(result, ["data", "issueUpdate"])
        if isinstance(payload, dict):
            return payload
        return {"success": False, "error": result.get("errors", "Issue update failed")}

    def find_state_id_by_type(self, state_type: str, team_id: str = None) -> dict:
        state_type = (state_type or "").strip().lower()
        valid_types = {"triage", "backlog", "unstarted", "started", "completed", "canceled"}
        if state_type not in valid_types:
            return {"success": False, "error": f"Unsupported state type: {state_type}"}

        states_result = self.list_workflow_states(team_id=team_id)
        if not states_result.get("success"):
            return states_result

        for st in states_result.get("states", []):
            if (st.get("type") or "").lower() == state_type:
                return {"success": True, "state_id": st.get("id"), "state": st}

        return {"success": False, "error": f"State type not found in team workflow: {state_type}"}

    def transition_issue(self, identifier: str, to_state_type: str, team_id: str = None) -> dict:
        cfg = self._require_config(require_team=True, team_id=team_id)
        if cfg:
            return cfg
        issue_result = self.get_issue(identifier)
        if not issue_result.get("success"):
            return issue_result

        state_lookup = self.find_state_id_by_type(to_state_type, team_id=team_id)
        if not state_lookup.get("success"):
            return state_lookup

        issue = issue_result["issue"]
        return self.update_issue(issue_id=issue["id"], state_id=state_lookup["state_id"])

    def assign_issue_by_identifier(self, identifier: str, assignee_id: str) -> dict:
        issue_result = self.get_issue(identifier)
        if not issue_result.get("success"):
            return issue_result
        issue = issue_result["issue"]
        return self.update_issue(issue_id=issue["id"], assignee_id=assignee_id)

    def close_issue(self, identifier: str, team_id: str = None) -> dict:
        return self.transition_issue(identifier=identifier, to_state_type="completed", team_id=team_id)

    def list_project_issues(self, project_id: str, first: int = 50) -> dict:
        cfg = self._require_config(require_team=False)
        if cfg:
            return cfg
        query = """
        query ProjectIssues($id: String!, $first: Int!) {
          project(id: $id) {
            id
            name
            issues(first: $first) {
              nodes {
                id
                identifier
                title
                url
                priority
                state { id name type }
                assignee { id name email }
                relations {
                  nodes {
                    type
                    issue { id state { type } }
                    relatedIssue { id state { type } }
                  }
                }
              }
            }
          }
        }
        """
        result = self._query(query, {"id": project_id, "first": first})
        nodes = self._unwrap(result, ["data", "project", "issues", "nodes"], default=[])
        if isinstance(nodes, list):
            return {"success": True, "issues": nodes}
        return {"success": False, "error": result.get("errors", "Could not load project issues")}

    def comment_issue(self, issue_id: str, body: str) -> dict:
        cfg = self._require_config(require_team=False)
        if cfg:
            return cfg
        mutation = """
        mutation CommentCreate($input: CommentCreateInput!) {
          commentCreate(input: $input) {
            success
            comment { id body }
          }
        }
        """
        result = self._query(mutation, {"input": {"issueId": issue_id, "body": body}})
        payload = self._unwrap(result, ["data", "commentCreate"])
        if isinstance(payload, dict):
            return payload
        return {"success": False, "error": result.get("errors", "Comment create failed")}


_linear_client = LinearClient()


def get_linear_client() -> LinearClient:
    return _linear_client
