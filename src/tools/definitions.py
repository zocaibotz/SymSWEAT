from langchain_core.tools import tool
from src.tools.filesystem import get_filesystem_client
from src.tools.git import get_git_tool

fs_client = get_filesystem_client()
git_tool = get_git_tool()

@tool
def write_file(path: str, content: str):
    """Writes content to a file at the given path."""
    return fs_client.call_tool("write_file", {"path": path, "content": content})

@tool
def read_file(path: str):
    """Reads content from a file at the given path."""
    return fs_client.call_tool("read_file", {"path": path})

@tool
def list_directory(path: str = "."):
    """Lists files in a directory."""
    return fs_client.call_tool("list_directory", {"path": path})

@tool
def commit_changes(message: str, agent_name: str):
    """Stages all changes and commits them with the given agent's persona (e.g., 'CodeSmith')."""
    git_tool.stage_all()
    result = git_tool.commit(message, agent_name)
    return result

@tool
def git_status():
    """Returns the current status of the git repository."""
    return git_tool.status()

@tool
def git_diff():
    """Returns the diff of current changes (staged and unstaged) or the last commit if clean."""
    return git_tool.diff()
