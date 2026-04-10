import json
from datetime import datetime, timezone
from pathlib import Path

from src.sweat_v2.shadow_weekly import summarize_week, write_weekly_report


def test_summarize_week_filters_old_rows(tmp_path: Path) -> None:
    p = tmp_path / "shadow.jsonl"
    rows = [
        {"timestamp_utc": "2026-03-01T00:00:00+00:00", "agreed": True, "v2_stage": "planning"},
        {"timestamp_utc": "2026-03-22T00:00:00+00:00", "agreed": False, "v2_stage": "coding"},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = summarize_week(str(p), now=datetime(2026, 3, 22, 1, 0, 0, tzinfo=timezone.utc))
    assert out.total == 1
    assert out.disagreed == 1


def test_write_weekly_report_outputs_files(tmp_path: Path) -> None:
    source = tmp_path / "shadow.jsonl"
    source.write_text(json.dumps({"timestamp_utc": "2026-03-22T00:00:00+00:00", "agreed": True, "v2_stage": "planning"}) + "\n")
    out_json = tmp_path / "out.json"
    out_md = tmp_path / "out.md"
    payload = write_weekly_report(str(out_json), str(out_md), str(source))
    assert payload["total"] == 1
    assert out_json.exists()
    assert out_md.exists()
