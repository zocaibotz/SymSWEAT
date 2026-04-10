from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


@dataclass
class WeeklySummary:
    total: int
    agreed: int
    disagreed: int
    agreement_rate: float
    by_stage: Dict[str, int]


def summarize_week(path: str = "reports/runs/v2_shadow_report.jsonl", now: datetime | None = None) -> WeeklySummary:
    p = Path(path)
    if not p.exists():
        return WeeklySummary(0, 0, 0, 0.0, {})

    now = now or datetime.now(timezone.utc)
    threshold = now - timedelta(days=7)

    total = 0
    agreed = 0
    by_stage: Counter[str] = Counter()

    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            ts = _parse_ts(row.get("timestamp_utc"))
            if ts and ts < threshold:
                continue
            total += 1
            if bool(row.get("agreed")):
                agreed += 1
            by_stage[str(row.get("v2_stage") or "unknown")] += 1

    disagreed = total - agreed
    return WeeklySummary(total, agreed, disagreed, (agreed / total) if total else 0.0, dict(by_stage))


def write_weekly_report(out_json: str = "reports/runs/v2_shadow_weekly_report.json", out_md: str = "reports/runs/v2_shadow_weekly_report.md", source: str = "reports/runs/v2_shadow_report.jsonl") -> Dict[str, Any]:
    summary = summarize_week(source)
    payload = {
        "window_days": 7,
        "total": summary.total,
        "agreed": summary.agreed,
        "disagreed": summary.disagreed,
        "agreement_rate": summary.agreement_rate,
        "by_stage": summary.by_stage,
    }

    j = Path(out_json)
    m = Path(out_md)
    j.parent.mkdir(parents=True, exist_ok=True)
    m.parent.mkdir(parents=True, exist_ok=True)

    j.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    m.write_text(
        "\n".join(
            [
                "# SWEAT v2 Shadow Weekly Report",
                "",
                f"- Window: 7 days",
                f"- Total runs: {summary.total}",
                f"- Agreed: {summary.agreed}",
                f"- Disagreed: {summary.disagreed}",
                f"- Agreement rate: {summary.agreement_rate:.2%}",
                "",
                "## By Stage",
                *[f"- {k}: {v}" for k, v in sorted(summary.by_stage.items())],
            ]
        ),
        encoding="utf-8",
    )
    return payload
