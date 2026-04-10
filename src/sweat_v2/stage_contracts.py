from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.sweat_v2.state import Stage, SweatRunState


@dataclass(frozen=True)
class StageContract:
    stage: Stage
    required_metadata: List[str]
    required_quality_flags: List[str]


CONTRACTS: Dict[Stage, StageContract] = {
    Stage.planning: StageContract(Stage.planning, ["linear_issue_key"], []),
    Stage.design: StageContract(Stage.design, ["planning_status"], []),
    Stage.tdd: StageContract(Stage.tdd, ["design_status"], []),
    Stage.coding: StageContract(Stage.coding, ["tdd_status"], []),
    Stage.qa: StageContract(Stage.qa, ["coding_status"], ["tests_executed"]),
    Stage.deploy: StageContract(Stage.deploy, ["qa_status"], ["tests_passed"]),
}


def validate_stage_contract(state: SweatRunState) -> list[str]:
    contract = CONTRACTS.get(state.stage)
    if not contract:
        return []

    violations: list[str] = []
    for key in contract.required_metadata:
        if key not in state.metadata or not str(state.metadata.get(key)).strip():
            violations.append(f"missing_metadata:{key}")

    for flag in contract.required_quality_flags:
        if not bool(getattr(state.quality, flag, False)):
            violations.append(f"missing_quality_flag:{flag}")

    return violations
