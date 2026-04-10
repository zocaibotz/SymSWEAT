from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def classify_route(route: List[Dict[str, Any]], final_next_agent: str | None, steps: int, max_steps: int = 100) -> str:
    if steps <= 1 and final_next_agent == "__end__":
        return "early_end"

    triplet = ["codesmith", "gatekeeper", "pipeline"]
    nodes = [str(r.get("node")) for r in route]
    for i in range(0, max(0, len(nodes) - 2)):
        if nodes[i : i + 3] == triplet:
            return "review_loop"

    if steps >= max_steps and final_next_agent != "__end__":
        return "non_terminal_max_step"

    return "ok"


def classify_cycle_report(path: str, max_steps: int = 100) -> Dict[str, Any]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    route = data.get("route") or []
    steps = int(data.get("steps") or len(route))
    final_next_agent = data.get("final_next_agent")
    klass = classify_route(route, final_next_agent, steps, max_steps=max_steps)
    return {
        "path": str(p),
        "project_id": data.get("project_id"),
        "run_id": data.get("run_id"),
        "steps": steps,
        "final_next_agent": final_next_agent,
        "classification": klass,
    }
