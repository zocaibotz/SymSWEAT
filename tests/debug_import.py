print("Start debug")
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.utils.llm import get_llm, get_coder_llm
    print("Imported llm getters")
    llm = get_llm()
    print(f"Got LLM: {llm}")
    coder = get_coder_llm()
    print(f"Got Coder: {coder}")
    
    from src.tools.git import get_git_tool
    git = get_git_tool()
    print(f"Got Git: {git}")

    from src.tools.definitions import write_file
    print("Imported definitions")
    from src.agents.workers import gatekeeper_node
    print("Imported workers")
except Exception as e:
    print(f"Error: {e}")
print("End debug")
