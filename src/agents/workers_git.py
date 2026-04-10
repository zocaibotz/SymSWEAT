from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from src.state import ProjectState
from src.utils.llm import get_llm, get_coder_llm
from src.tools.definitions import write_file, read_file, list_directory
from src.tools.git import get_git_tool
from typing import Dict, Any

llm = get_llm()
coder_llm = get_coder_llm()
git = get_git_tool()

# ... (Existing nodes) ...

def codesmith_node(state: ProjectState) -> Dict[str, Any]:
    messages = state["messages"]
    architecture = state.get("architecture_docs", "No architecture defined yet.")
    
    # Initialize repo if not already
    git.init()
    
    prompt = (
        f"You are CodeSmith 🔨. Implement the feature based on: {architecture}.\n"
        "Use `write_file` to save code.\n"
        "Use `commit_changes` (agent='codesmith') when done.\n"
        "OUTPUT JSON ONLY for tools:\n"
        "```json\n"
        "{\"tool\": \"write_file\", \"args\": {\"path\": \"...\", \"content\": \"...\"}}\n"
        "```"
    )
    
    # Simple invoke for now as CLI wrapper handling is complex
    # We rely on the CLI wrapper to return JSON if instructed
    response = coder_llm.invoke([SystemMessage(content=prompt)] + messages)
    
    # ... (Output parsing logic shared previously) ...
    # For brevity in this edit, I am just ensuring the function signature matches.
    return {"messages": [response]}
