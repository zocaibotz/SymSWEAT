import json
import os
import sys
from pathlib import Path

REQUIRED_PATHS = [
    "docs/spec/spec.md",
    "docs/spec/plan.md",
    "docs/spec/tasks.md",
    "docs/architecture/system-design.md",
    "docs/ui/handoff_contract.json",
    "docs/tests/unit_test_plan.md",
]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_project1_dashboard.py <project-dir>")
        return 2

    pdir = Path(sys.argv[1])
    missing = []
    for rel in REQUIRED_PATHS:
        if not (pdir / rel).exists():
            missing.append(rel)

    # Optional but expected: live observability artifacts
    expected_any = [
        pdir / "state" / "run_events.jsonl",
        pdir / "state" / "project_state.json",
    ]
    if not any(x.exists() for x in expected_any):
        missing.append("state/{run_events.jsonl|project_state.json}")

    if missing:
        print("FAIL missing required dashboard project artifacts:")
        for m in missing:
            print("-", m)
        return 1

    print("PASS project1 dashboard requirement artifact baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
