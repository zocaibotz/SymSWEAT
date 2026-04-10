import json
from pathlib import Path

from src.sweat_v2.shadow_diagnostics import summarize_disagreements


def test_disagreement_summary_counts_pairs(tmp_path: Path) -> None:
    p = tmp_path / "shadow.jsonl"
    rows = [
        {"agreed": True, "v1_next_agent": "a", "v2_next_agent": "a", "v2_stage": "planning"},
        {"agreed": False, "v1_next_agent": "a", "v2_next_agent": "b", "v2_stage": "coding"},
        {"agreed": False, "v1_next_agent": "a", "v2_next_agent": "b", "v2_stage": "coding"},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = summarize_disagreements(str(p))
    assert out["total"] == 3
    assert out["disagreed"] == 2
    assert out["pairs"]["a -> b"] == 2
