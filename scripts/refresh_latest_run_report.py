import argparse
import json
import os
import time


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh reports/runs/latest_run_report.json from run_events for a project")
    ap.add_argument("--project-dir", required=True, help="Project directory, e.g. projects/overnight-e2e-01")
    ap.add_argument("--run-id", default=None, help="Optional explicit run id; defaults to latest in run_index")
    args = ap.parse_args()

    state_dir = os.path.join(args.project_dir, "state")
    index_path = os.path.join(state_dir, "run_index.json")
    events_path = os.path.join(state_dir, "run_events.jsonl")

    if not os.path.exists(index_path) or not os.path.exists(events_path):
        print("FAIL missing state artifacts")
        return 1

    with open(index_path, "r", encoding="utf-8") as f:
        idx = json.load(f)

    run_id = args.run_id or idx.get("latest_run_id")
    if not run_id:
        print("FAIL no run_id")
        return 1

    events = []
    with open(events_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("run_id") != run_id:
                continue
            if e.get("event_type") == "route_decision":
                payload = e.get("payload") or {}
                events.append({
                    "node": e.get("node"),
                    "duration_ms": None,
                    "next_agent": payload.get("next_node"),
                })

    report = {
        "project_id": os.path.basename(args.project_dir.rstrip("/")),
        "run_id": run_id,
        "events": events,
        "updated_at_epoch": int(time.time()),
        "source": "refresh_latest_run_report.py",
    }

    out = "reports/runs/latest_run_report.json"
    os.makedirs("reports/runs", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(out)
    print(f"events={len(events)} run_id={run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
