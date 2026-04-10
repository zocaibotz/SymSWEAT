from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict


def summarize_disagreements(path: str = "reports/runs/v2_shadow_report.jsonl") -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"total": 0, "disagreed": 0, "rate": 0.0, "pairs": {}, "by_stage": {}}

    total = 0
    disagreed = 0
    pairs = Counter()
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
            if not bool(row.get("agreed")):
                disagreed += 1
                pair = f"{row.get('v1_next_agent')} -> {row.get('v2_next_agent')}"
                pairs[pair] += 1
                by_stage[str(row.get("v2_stage") or "unknown")] += 1

    return {
        "total": total,
        "disagreed": disagreed,
        "rate": (disagreed / total) if total else 0.0,
        "pairs": dict(pairs.most_common(20)),
        "by_stage": dict(by_stage),
    }


def write_disagreement_report(out_json: str = "reports/runs/v2_shadow_disagreements.json") -> Dict[str, Any]:
    payload = summarize_disagreements()
    p = Path(out_json)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
