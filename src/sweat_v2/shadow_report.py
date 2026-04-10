from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict


def summarize_shadow_report(path: str = "reports/runs/v2_shadow_report.jsonl") -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {
            "total": 0,
            "agreed": 0,
            "disagreed": 0,
            "agreement_rate": 0.0,
            "by_stage": {},
        }

    total = 0
    agreed = 0
    by_stage = Counter()

    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            total += 1
            if bool(row.get("agreed")):
                agreed += 1
            by_stage[str(row.get("v2_stage") or "unknown")] += 1

    disagreed = total - agreed
    agreement_rate = (agreed / total) if total else 0.0
    return {
        "total": total,
        "agreed": agreed,
        "disagreed": disagreed,
        "agreement_rate": agreement_rate,
        "by_stage": dict(by_stage),
    }
