from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import SweatRunState


@dataclass
class PolicyGuardMiddleware:
    name: str = "policy_guard"

    def before_stage(self, state: SweatRunState) -> SweatRunState:
        required = ["linear_issue_key", "artifact_sync_target"]
        missing = [key for key in required if key not in state.metadata]
        if missing:
            state.quality.policy_violations.extend([f"missing_{k}" for k in missing])
        return state

    def before_complete(self, state: SweatRunState) -> SweatRunState:
        state.quality.policy_violations = list(dict.fromkeys(state.quality.policy_violations))
        return state

    def after_stage(self, state: SweatRunState) -> SweatRunState:
        return state
