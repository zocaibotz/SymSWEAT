import json
import os
import subprocess
import sys
import time


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {"cmd": " ".join(cmd), "code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def _arg_value(flag: str, default: str) -> str:
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def main() -> int:
    project_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "projects/overnight-e2e-01"
    rerun = "--rerun" in sys.argv
    max_steps = _arg_value("--max-steps", "120")
    run_id_override = _arg_value("--run-id", "")
    project_id = os.path.basename(project_dir.rstrip("/"))

    os.makedirs("reports/runs", exist_ok=True)

    steps = []
    if rerun:
        steps.append(run([sys.executable, "scripts/run_strict_e2e_cycle.py", "--project-dir", project_dir, "--max-steps", str(max_steps)]))

    # Pre-step: refresh latest_run_report to target project/run to avoid stale-report false negatives.
    refresh_cmd = [sys.executable, "scripts/refresh_latest_run_report.py", "--project-dir", project_dir]
    validate_cmd = [sys.executable, "scripts/run_strict_e2e_check.py", "--project-dir", project_dir]
    if run_id_override:
        refresh_cmd += ["--run-id", run_id_override]
        validate_cmd += ["--run-id", run_id_override]

    steps.append(run(refresh_cmd))
    steps.append(run(validate_cmd))
    steps.append(run([sys.executable, "scripts/validate_latest_report.py", "reports/runs/latest_run_report.json", project_id]))

    # Requirement-specific gate: dashboard project must produce baseline artifacts.
    if project_id == "command-center-dashboard":
        steps.append(run([sys.executable, "scripts/validate_project1_dashboard.py", project_dir]))

    success = all(s["code"] == 0 for s in steps)
    payload = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project_dir": project_dir,
        "project_id": project_id,
        "success": success,
        "steps": steps,
    }

    json_out = "reports/runs/milestone_signoff.json"
    md_out = "reports/runs/milestone_signoff.md"

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    with open(md_out, "w", encoding="utf-8") as f:
        f.write(f"# Milestone Signoff\n\n")
        f.write(f"- timestamp_utc: {payload['timestamp_utc']}\n")
        f.write(f"- project_dir: {project_dir}\n")
        f.write(f"- project_id: {project_id}\n")
        f.write(f"- success: {success}\n\n")
        for i, s in enumerate(steps, start=1):
            f.write(f"## Step {i}\n")
            f.write(f"- cmd: `{s['cmd']}`\n")
            f.write(f"- exit_code: {s['code']}\n")
            if s.get("stdout"):
                f.write("\n### stdout\n```\n" + s["stdout"][:4000] + "\n```\n")
            if s.get("stderr"):
                f.write("\n### stderr\n```\n" + s["stderr"][:4000] + "\n```\n")
            f.write("\n")

    print(md_out)
    print(json_out)
    print("PASS" if success else "FAIL")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
