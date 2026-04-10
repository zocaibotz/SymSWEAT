import json
import os
import sys
import time


def main():
    if len(sys.argv) < 3:
        print("usage: validate_latest_report.py <path> <expected_project_id>")
        return 2

    path = sys.argv[1]
    expected_project = sys.argv[2]
    if not os.path.exists(path):
        print(f"FAIL: report not found: {path}")
        return 1

    with open(path, "r", encoding="utf-8") as f:
        r = json.load(f)

    pid = r.get("project_id")
    if pid != expected_project:
        print(f"FAIL: stale/mismatched project_id: got={pid} expected={expected_project}")
        return 1

    ts = int(r.get("updated_at_epoch") or 0)
    if ts <= 0 or (time.time() - ts) > 6 * 3600:
        print("FAIL: stale report timestamp (>6h) or missing")
        return 1

    print("PASS: latest_run_report is fresh and project-matched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
