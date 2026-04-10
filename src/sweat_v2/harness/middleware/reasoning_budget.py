from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import ReasoningMode, Stage, SweatRunState


@dataclass
class ReasoningBudgetMiddleware:
    name: str = "reasoning_budget"

    def before_stage(self, state: SweatRunState) -> SweatRunState:
        mapping = {
            Stage.planning: ReasoningMode.xhigh,
            Stage.design: ReasoningMode.high,
            Stage.tdd: ReasoningMode.high,
            Stage.coding: ReasoningMode.medium,
            Stage.qa: ReasoningMode.high,
            Stage.deploy: ReasoningMode.medium,
            Stage.done: ReasoningMode.low,
            Stage.blocked: ReasoningMode.low,
        }
        state.budget.reasoning_mode = mapping[state.stage]
        return state

    def before_complete(self, state: SweatRunState) -> SweatRunState:
        return state

    def after_stage(self, state: SweatRunState) -> SweatRunState:
        return state
