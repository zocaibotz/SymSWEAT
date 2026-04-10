import sys
import os
print("Starting test_ci.py...")

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    print("Importing workers...")
    from src.agents.workers import gatekeeper_node, pipeline_node
    print("Workers imported.")
    
    from src.state import ProjectState
    print("State imported.")
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_pipeline():
    print("\n--- TEST START ---")
    state = {
        "messages": [],
        "project_id": "test-ci"
    }
    
    # Mock Gatekeeper
    print("1. Calling Gatekeeper...")
    gatekeeper_result = gatekeeper_node(state)
    print("Gatekeeper Result:", gatekeeper_result["messages"][0].content)
    
    # Mock Pipeline
    print("\n2. Calling Pipeline...")
    pipeline_result = pipeline_node(state)
    print("Pipeline Result:", pipeline_result["messages"][0].content)

if __name__ == "__main__":
    test_pipeline()
