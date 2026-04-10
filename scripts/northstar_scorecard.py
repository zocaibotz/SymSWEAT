import json
import os
import time
from pathlib import Path


def main():
    src = Path("reports/northstar/northstar_stability_runset.json")
    out_json = Path("reports/northstar/northstar_scorecard.json")
    out_md = Path("reports/northstar/northstar_scorecard.md")
    out_json.parent.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        payload = {
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "missing_runset",
            "note": "Run scripts/northstar_stability_runset.py first",
        }
        out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        out_md.write_text("# North-Star Scorecard\n\nRunset missing.\n", encoding="utf-8")
        print(str(out_json))
        print(str(out_md))
        return

    data = json.loads(src.read_text(encoding="utf-8"))
    pass_rate = float(data.get("pass_rate") or 0)
    median_steps = data.get("median_steps")
    top_fail = data.get("top_fail_reasons") or {}

    grade = "RED"
    if pass_rate >= 90:
        grade = "GREEN"
    elif pass_rate >= 80:
        grade = "YELLOW"

    payload = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "north_star_grade": grade,
        "pass_rate": pass_rate,
        "median_steps": median_steps,
        "top_fail_reasons": top_fail,
        "total_runs": data.get("total_runs"),
        "passed_runs": data.get("passed_runs"),
    }

    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = [
        "# North-Star Scorecard",
        "",
        f"- grade: **{grade}**",
        f"- pass_rate: **{pass_rate:.1f}%**",
        f"- median_steps: **{median_steps}**",
        f"- total_runs: {data.get('total_runs')}",
        f"- passed_runs: {data.get('passed_runs')}",
        "",
        "## Top fail reasons",
    ]
    for k, v in top_fail.items():
        md.append(f"- {k}: {v}")

    out_md.write_text("\n".join(md), encoding="utf-8")
    print(str(out_json))
    print(str(out_md))


if __name__ == "__main__":
    main()
