import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

PROMPTS = [
    "Build an MVP note-taking app with auth, notes CRUD, search, and tag filters. Provide testable acceptance criteria.",
    "Create a simple expense tracker with categories, monthly summary dashboard, and CSV export. Include clear acceptance criteria.",
    "Build a habit tracker with daily check-ins, streaks, weekly view, and reminders hook. Include testable acceptance criteria.",
    "Create a lightweight project task board with columns, drag/drop status changes, and assignee filters. Include acceptance criteria.",
    "Build a personal knowledge base app with markdown notes, backlinks, and quick search. Include acceptance criteria.",
]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def main():
    project_root = Path("projects/northstar-runset")
    project_root.mkdir(parents=True, exist_ok=True)
    out_dir = Path("reports/northstar")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, prompt in enumerate(PROMPTS, start=1):
        proj = project_root / f"runset-{i:02d}"
        proj.mkdir(parents=True, exist_ok=True)
        prompt_file = out_dir / f"prompt_{i:02d}.txt"
        prompt_file.write_text(prompt, encoding="utf-8")

        c1 = [sys.executable, "scripts/run_strict_e2e_cycle.py", "--project-dir", str(proj), "--prompt-file", str(prompt_file), "--max-steps", "80"]
        code1, out1, err1 = run(c1)

        run_id = None
        for line in (out1 or "").splitlines():
            if line.startswith("run_id="):
                run_id = line.split("run_id=", 1)[1].split()[0]
                break

        c2 = [sys.executable, "scripts/milestone_signoff.py", str(proj), "--run-id", run_id] if run_id else [sys.executable, "scripts/milestone_signoff.py", str(proj)]
        code2, out2, err2 = run(c2)

        signoff_path = Path("reports/runs/milestone_signoff.json")
        success = False
        steps_count = None
        fail_reasons = []
        if signoff_path.exists():
            try:
                s = json.loads(signoff_path.read_text(encoding="utf-8"))
                success = bool(s.get("success"))
                # best effort parse fail reason from stdout of steps
                for st in s.get("steps", []):
                    so = st.get("stdout") or ""
                    if "FAIL" in so:
                        fail_reasons.append(so.strip().splitlines()[-1])
            except Exception:
                pass

        trace_latest = Path("reports/runs/strict_e2e_cycle_latest.json")
        if trace_latest.exists():
            try:
                t = json.loads(trace_latest.read_text(encoding="utf-8"))
                steps_count = t.get("steps")
            except Exception:
                pass

        rows.append({
            "run": i,
            "project_dir": str(proj),
            "run_id": run_id,
            "cycle_exit": code1,
            "signoff_exit": code2,
            "success": success,
            "steps": steps_count,
            "fail_reasons": fail_reasons,
        })

    total = len(rows)
    passed = sum(1 for r in rows if r["success"])
    pass_rate = (passed / total) * 100 if total else 0
    steps_values = [r["steps"] for r in rows if isinstance(r["steps"], int)]
    median_steps = statistics.median(steps_values) if steps_values else None

    top_fail = {}
    for r in rows:
        for fr in r.get("fail_reasons", []):
            top_fail[fr] = top_fail.get(fr, 0) + 1

    report = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_runs": total,
        "passed_runs": passed,
        "pass_rate": pass_rate,
        "median_steps": median_steps,
        "top_fail_reasons": dict(sorted(top_fail.items(), key=lambda x: x[1], reverse=True)[:10]),
        "rows": rows,
    }

    json_path = out_dir / "northstar_stability_runset.json"
    md_path = out_dir / "northstar_stability_runset.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# North-Star Stability Runset",
        "",
        f"- total_runs: {total}",
        f"- passed_runs: {passed}",
        f"- pass_rate: {pass_rate:.1f}%",
        f"- median_steps: {median_steps}",
        "",
        "## Top fail reasons",
    ]
    for k, v in report["top_fail_reasons"].items():
        lines.append(f"- {k}: {v}")
    lines.append("\n## Runs")
    for r in rows:
        lines.append(f"- run {r['run']}: success={r['success']} run_id={r['run_id']} steps={r['steps']} fail_reasons={r['fail_reasons']}")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(str(json_path))
    print(str(md_path))
    print(f"pass_rate={pass_rate:.1f}%")


if __name__ == "__main__":
    main()
