import argparse
import json
import os
import time
from pathlib import Path


def ensure_file(path: Path, data: dict):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return True


def backfill_project(project_dir: Path, apply: bool):
    state_dir = project_dir / "state"
    pid = project_dir.name
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    project_state = {
        "schema_version": "1.0.0",
        "state_version": 1,
        "project_id": pid,
        "project_slug": pid,
        "lifecycle": {"phase": "unknown", "status": "backfilled", "current_run_id": None, "last_updated_utc": now},
        "gates": {"design_approved": False, "tdd_ready": False, "ci_passed": False, "deployment_approved": False},
        "artifacts": {},
    }
    run_index = {
        "schema_version": "1.0.0",
        "project_id": pid,
        "runs": {},
        "latest_run_id": None,
        "updated_at_utc": now,
    }

    targets = {
        "project_state.json": state_dir / "project_state.json",
        "run_index.json": state_dir / "run_index.json",
        "run_events.jsonl": state_dir / "run_events.jsonl",
    }

    created = []
    if apply:
        if ensure_file(targets["project_state.json"], project_state):
            created.append("project_state.json")
        if ensure_file(targets["run_index.json"], run_index):
            created.append("run_index.json")
        if not targets["run_events.jsonl"].exists():
            targets["run_events.jsonl"].parent.mkdir(parents=True, exist_ok=True)
            targets["run_events.jsonl"].write_text("", encoding="utf-8")
            created.append("run_events.jsonl")
    else:
        for k, p in targets.items():
            if not p.exists():
                created.append(k)

    return {
        "project": str(project_dir),
        "created_or_missing": created,
    }


def main():
    ap = argparse.ArgumentParser(description="Backfill missing SWEAT state artifacts for legacy projects")
    ap.add_argument("--root", default="projects")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", default="reports/northstar/state_backfill_report.json")
    args = ap.parse_args()

    root = Path(args.root)
    rows = []
    for p in sorted(root.glob("*")):
        if not p.is_dir():
            continue
        rows.append(backfill_project(p, args.apply))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"apply": args.apply, "rows": rows}, indent=2), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
