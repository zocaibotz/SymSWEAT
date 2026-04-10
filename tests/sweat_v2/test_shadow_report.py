import json
from pathlib import Path

from src.sweat_v2.shadow_report import summarize_shadow_report


def test_shadow_report_summary(tmp_path: Path) -> None:
    report = tmp_path / "shadow.jsonl"
    rows = [
        {"v2_stage": "planning", "agreed": True},
        {"v2_stage": "planning", "agreed": False},
        {"v2_stage": "coding", "agreed": True},
    ]
    with report.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    out = summarize_shadow_report(str(report))
    assert out["total"] == 3
    assert out["agreed"] == 2
    assert out["disagreed"] == 1
    assert out["agreement_rate"] > 0.66
    assert out["by_stage"]["planning"] == 2
