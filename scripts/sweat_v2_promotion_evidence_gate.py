#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def main() -> int:
    shadow_path = Path("reports/runs/v2_shadow_report.jsonl")
    shadow_rows = _count_jsonl(shadow_path)

    e2e_report = Path("reports/runs/v2_e2e_failure_report.json")
    e2e_total = 0
    if e2e_report.exists():
        try:
            e2e_total = int(json.loads(e2e_report.read_text(encoding="utf-8")).get("total") or 0)
        except Exception:
            e2e_total = 0

    min_shadow = 20
    min_e2e = 5

    out = {
        "shadow_rows": shadow_rows,
        "e2e_total": e2e_total,
        "min_shadow": min_shadow,
        "min_e2e": min_e2e,
        "ready": shadow_rows >= min_shadow and e2e_total >= min_e2e,
    }
    p = Path("reports/runs/v2_promotion_evidence_gate.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(str(p))
    return 0 if out["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
