import argparse
import json
import os
import subprocess
import sys
import time
from typing import Optional


def _latest_run_id(state_dir: str) -> Optional[str]:
    idx = os.path.join(state_dir, "run_index.json")
    if not os.path.exists(idx):
        return None
    try:
        with open(idx, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("latest_run_id")
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Run strict E2E validator against latest run and emit report artifact")
    ap.add_argument("--project-dir", default="projects/overnight-e2e-01", help="Project workspace dir containing state/")
    ap.add_argument("--run-id", default=None, help="Optional explicit run_id")
    ap.add_argument("--out", default="reports/runs/strict_e2e_validation.json", help="Output report path")
    args = ap.parse_args()

    state_dir = os.path.join(args.project_dir, "state")
    events = os.path.join(state_dir, "run_events.jsonl")
    run_id = args.run_id or _latest_run_id(state_dir)

    report = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project_dir": args.project_dir,
        "state_dir": state_dir,
        "events_path": events,
        "run_id": run_id,
        "validator": "scripts/validate_strict_e2e.py",
        "success": False,
    }

    if not run_id:
        report["error"] = "No run_id found (missing/invalid run_index.json)"
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(args.out)
        return 1

    cmd = [sys.executable, "scripts/validate_strict_e2e.py", events, run_id]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    report["command"] = " ".join(cmd)
    report["exit_code"] = proc.returncode
    report["stdout"] = proc.stdout
    report["stderr"] = proc.stderr
    report["success"] = proc.returncode == 0

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(args.out)
    print("PASS" if report["success"] else "FAIL")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
