import subprocess
from contextlib import contextmanager
from typing import Dict

# Agent Personas
PERSONAS = {
    "codesmith": {
        "name": "SWEAT - CodeSmith 🔨",
        "email": "zoc.ai.botz+codesmith@gmail.com"
    },
    "architect": {
        "name": "SWEAT - Architect 🏛️",
        "email": "zoc.ai.botz+architect@gmail.com"
    },
    "bughunter": {
        "name": "SWEAT - BugHunter 🐞",
        "email": "zoc.ai.botz+bughunter@gmail.com"
    },
    "gatekeeper": {
        "name": "SWEAT - Gatekeeper 🛡️",
        "email": "zoc.ai.botz+gatekeeper@gmail.com"
    },
    "zocai": {
        "name": "SWEAT - Zocai 🦉",
        "email": "zoc.ai.botz@gmail.com"
    }
}

class GitTool:
    def run_command(self, command: list, check: bool = True) -> str:
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=check
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Git Error: {e.stderr}"

    def set_identity(self, agent_name: str) -> None:
        """Sets the local git config to match the agent's persona."""
        persona = PERSONAS.get(agent_name.lower(), PERSONAS["zocai"])
        self.run_command(["git", "config", "user.name", persona["name"]])
        self.run_command(["git", "config", "user.email", persona["email"]])

    def commit(self, message: str, agent_name: str) -> str:
        """Commits staged changes with the agent's identity."""
        self.set_identity(agent_name)
        return self.run_command(["git", "commit", "-m", message])

    def stage_all(self) -> str:
        return self.run_command(["git", "add", "."])

    def status(self) -> str:
        return self.run_command(["git", "status", "--short"])

    def init(self) -> str:
        return self.run_command(["git", "init"])

    def diff(self) -> str:
        """Returns the diff of staged/unstaged changes."""
        # Check staged
        staged = self.run_command(["git", "diff", "--cached"])
        # Check unstaged
        unstaged = self.run_command(["git", "diff"])
        
        if not staged and not unstaged:
            # Maybe check last commit if clean
            return self.run_command(["git", "show", "--stat"])
            
        return f"STAGED:\n{staged}\n\nUNSTAGED:\n{unstaged}"

# Singleton
_git_tool = GitTool()

def get_git_tool() -> GitTool:
    return _git_tool
