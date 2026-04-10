import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate state artifacts for all discovered project dirs")
    ap.add_argument("--root", default="projects")
    args = ap.parse_args()

    root = Path(args.root)
    projects = [p for p in sorted(root.glob("*")) if p.is_dir() and (p / "state" / "project_state.json").exists()]
    if not projects:
        print("PASS no project_state artifacts discovered")
        return 0

    failed = 0
    for p in projects:
        cmd = [sys.executable, "scripts/validate_state.py", "--project-dir", str(p)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"[{p}] exit={r.returncode}")
        if r.stdout:
            print(r.stdout.strip())
        if r.stderr:
            print(r.stderr.strip())
        if r.returncode != 0:
            failed += 1

    if failed:
        print(f"FAIL state validation failed for {failed} project(s)")
        return 1

    print(f"PASS validated {len(projects)} project(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
