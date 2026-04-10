#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
from collections import Counter
from pathlib import Path

from src.sweat_v2.e2e_classifier import classify_cycle_report


def main() -> int:
    files = sorted(glob.glob("reports/runs/strict_e2e_cycle_*.json"))
    counter: Counter[str] = Counter()
    samples = []
    for f in files[-200:]:
        try:
            row = classify_cycle_report(f)
        except Exception:
            continue
        counter[row["classification"]] += 1
        samples.append(row)

    out = {
        "total": len(samples),
        "counts": dict(counter),
        "recent": samples[-30:],
    }
    p = Path("reports/runs/v2_e2e_failure_report.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
