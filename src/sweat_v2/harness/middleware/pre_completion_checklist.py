from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import SweatRunState


@dataclass
class PreCompletionChecklistMiddleware:
    name: str = "pre_completion_checklist"

    def before_stage(self, state: SweatRunState) -> SweatRunState:
        return state

    def before_complete(self, state: SweatRunState) -> SweatRunState:
        violations = state.quality.policy_violations

        if not state.quality.tests_executed:
            violations.append("tests_not_executed")
        if state.acceptance_criteria and state.quality.criteria_coverage < 0.95:
            violations.append("insufficient_criteria_coverage")

        state.quality.policy_violations = list(dict.fromkeys(violations))
        return state

    def after_stage(self, state: SweatRunState) -> SweatRunState:
        return state
