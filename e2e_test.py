import sys
import os
import json
import time
from langchain_core.messages import HumanMessage
from src.main import build_graph

def run_e2e():
    graph = build_graph()
    
    # Novel Software Idea: "I want an automated CLI tool that checks the status of OpenClaw nodes and pings a webhook if any node is down. It should be written in Python using typer and httpx. I want proper testing and GitHub Actions."
    prompt = (
        "I want a Python CLI tool named 'claw-node-monitor' using Typer and httpx. "
        "It checks a list of OpenClaw node URLs from a local config file, verifies they return HTTP 200, "
        "and if any fail, it sends a JSON payload to a configurable webhook. "
        "Please ensure there is unit testing and GitHub Actions set up."
    )
    print(f"Starting E2E run with prompt: {prompt}")
    
    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "project_id": "claw-node-monitor-123",
        "next_agent": "req_master"
    }
    
    events = []
    # Stream the graph execution
    for event in graph.stream(initial_state):
        for node, value in event.items():
            print(f"--- Node {node.upper()} Finished ---")
            if "messages" in value and value["messages"]:
                last_msg = value["messages"][-1]
                print(f"[{node.upper()}]: {last_msg.content[:200]}...")
            events.append(node)
            
            # Since some loops are asynchronous/external, we stop at codesmith if it hangs, or continue
            if node == "sprint_executor" and value.get("sprint_executor_completed"):
                print("Sprint executor completed one cycle.")
                break

    print("\nGraph execution complete.")
    print(f"Nodes traversed: {events}")
    
    # Check telemetry
    telemetry_file = "projects/claw-node-monitor-123/state/run_events.jsonl"
    if os.path.exists(telemetry_file):
        print(f"\nTelemetry successfully captured in {telemetry_file}")
        with open(telemetry_file, "r") as f:
            lines = f.readlines()
            print(f"Total events recorded: {len(lines)}")
            if lines:
                print("Latest event:")
                print(lines[-1][:300])
    else:
        print("\nERROR: Telemetry file not found!")

if __name__ == "__main__":
    run_e2e()
