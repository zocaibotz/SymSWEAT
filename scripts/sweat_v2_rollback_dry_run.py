#!/usr/bin/env python3
import json
import os
from pathlib import Path


def main() -> int:
    out = {
        "mode": "rollback_dry_run",
        "rollback_target": {
            "SWEAT_V2_ENABLED": "false",
            "SWEAT_V2_SHADOW_MODE": "true",
        },
        "current": {
            "SWEAT_V2_ENABLED": os.getenv("SWEAT_V2_ENABLED", "false"),
            "SWEAT_V2_SHADOW_MODE": os.getenv("SWEAT_V2_SHADOW_MODE", "true"),
        },
        "instruction": "Set SWEAT_V2_ENABLED=false and restart runtime to revert routing to v1.",
    }
    p = Path("reports/runs/v2_rollback_dry_run.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
