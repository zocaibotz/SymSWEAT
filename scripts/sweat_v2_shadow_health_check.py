#!/usr/bin/env python3
import json
import os
from pathlib import Path


def main() -> int:
    enabled = os.getenv("SWEAT_V2_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    shadow = os.getenv("SWEAT_V2_SHADOW_MODE", "true").lower() in {"1", "true", "yes", "on"}
    p = Path("reports/runs/v2_shadow_report.jsonl")
    rows = 0
    if p.exists():
        with p.open("r", encoding="utf-8") as f:
            rows = sum(1 for line in f if line.strip())

    out = {
        "enabled": enabled,
        "shadow_mode": shadow,
        "shadow_report_path": str(p),
        "rows": rows,
        "ok": (not (enabled and shadow)) or rows > 0,
    }
    out_path = Path("reports/runs/v2_shadow_health_check.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(str(out_path))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
