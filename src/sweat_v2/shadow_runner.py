from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.sweat_v2.bridge import V2RouterResult, route_with_v2
from src.sweat_v2.config import V2Flags


def build_shadow_record(state: Dict[str, Any], v1_next_agent: str | None, v2: V2RouterResult) -> Dict[str, Any]:
    agreed = v1_next_agent == v2.next_agent
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": state.get("project_id"),
        "v1_next_agent": v1_next_agent,
        "v2_next_agent": v2.next_agent,
        "v2_stage": v2.v2_stage,
        "v2_policy_violations": v2.policy_violations,
        "agreed": agreed,
    }


def run_shadow_once(state: Dict[str, Any]) -> Dict[str, Any]:
    from src.agents.orchestrator import orchestrator_node

    v1 = orchestrator_node(state)
    v2 = route_with_v2(state, V2Flags(enabled=True, shadow_mode=True))
    return build_shadow_record(state, v1.get("next_agent"), v2)


def append_shadow_record(record: Dict[str, Any], path: str = "reports/runs/v2_shadow_report.jsonl") -> Dict[str, Any]:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def append_shadow_report(state: Dict[str, Any], path: str = "reports/runs/v2_shadow_report.jsonl") -> Dict[str, Any]:
    record = run_shadow_once(state)
    return append_shadow_record(record, path)
