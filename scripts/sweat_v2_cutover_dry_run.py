#!/usr/bin/env python3
import json
import os
from pathlib import Path


def main() -> int:
    flags = {
        "SWEAT_V2_ENABLED": os.getenv("SWEAT_V2_ENABLED", "false"),
        "SWEAT_V2_SHADOW_MODE": os.getenv("SWEAT_V2_SHADOW_MODE", "true"),
        "SWEAT_V2_CUTOVER_STAGE": os.getenv("SWEAT_V2_CUTOVER_STAGE", "planning"),
    }
    checks = {
        "enabled_is_true": flags["SWEAT_V2_ENABLED"].lower() in {"1", "true", "yes", "on"},
        "shadow_is_false": flags["SWEAT_V2_SHADOW_MODE"].lower() in {"0", "false", "no", "off"},
    }
    out = {
        "mode": "cutover_dry_run",
        "flags": flags,
        "checks": checks,
        "ready": all(checks.values()),
    }
    p = Path("reports/runs/v2_cutover_dry_run.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(str(p))
    return 0 if out["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
