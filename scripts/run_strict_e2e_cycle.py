import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import HumanMessage
from src.main import build_graph


def _load_prompt(args):
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    return (
        "Build a production-ready MVP for a task manager app. "
        "Include auth, CRUD tasks, tags, due dates, and dashboard. "
        "Provide testable acceptance criteria and architecture-ready requirements."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Run one strict E2E SWEAT cycle and emit route trace artifacts")
    ap.add_argument("--project-dir", default="projects/overnight-e2e-01")
    ap.add_argument("--project-id", default=None)
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--prompt-file", default=None)
    ap.add_argument("--max-steps", type=int, default=120)
    args = ap.parse_args()

    os.environ.setdefault("SWEAT_STRICT_CONTRACTS", "true")
    os.environ.setdefault("SWEAT_STRICT_TEST_GATE", "true")
    os.environ.setdefault("SWEAT_CODER_PRIMARY", "gemini_cli")
    os.environ.setdefault("SWEAT_CODER_SECONDARY", "minimax_api")
    os.environ.setdefault("SWEAT_CODER_TERTIARY", "ollama")
    os.environ.setdefault("SWEAT_CODEX_STRICT_TOOLS", "true")

    project_dir = args.project_dir
    project_id = args.project_id or os.path.basename(project_dir.rstrip("/"))
    Path(project_dir).mkdir(parents=True, exist_ok=True)

    prompt = _load_prompt(args)
    graph = build_graph()
    state = {
        "messages": [HumanMessage(content=prompt)],
        "project_id": project_id,
        "project_workspace_path": project_dir,
        "next_agent": None,
    }

    route = []
    for i, event in enumerate(graph.stream(state), start=1):
        for node, value in event.items():
            if isinstance(value, dict):
                nxt = value.get("next_agent")
                route.append({"step": i, "node": node, "next_agent": nxt})
                state.update(value)
        if state.get("next_agent") == "__end__" or i >= args.max_steps:
            break

    out_dir = Path("reports/runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    trace_path = out_dir / f"strict_e2e_cycle_{ts}.json"
    trace_path.write_text(json.dumps({
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project_id": project_id,
        "project_dir": project_dir,
        "steps": len(route),
        "route": route,
        "final_next_agent": state.get("next_agent"),
        "run_id": state.get("run_id"),
    }, indent=2), encoding="utf-8")

    latest = out_dir / "strict_e2e_cycle_latest.json"
    latest.write_text(trace_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(str(trace_path))
    print(f"run_id={state.get('run_id')} steps={len(route)} final_next_agent={state.get('next_agent')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
