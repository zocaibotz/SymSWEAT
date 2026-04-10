from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from src.sweat_v2.harness.middleware.base import Middleware
from src.sweat_v2.state import Stage, SweatRunState


@dataclass
class SupervisorGraph:
    """Minimal v2 supervisor scaffold.

    This intentionally starts small: middleware hooks + deterministic stage advance.
    It is meant to be integrated behind a feature flag while v1 remains active.
    """

    middleware: List[Middleware] = field(default_factory=list)

    def run_stage(self, state: SweatRunState) -> SweatRunState:
        for mw in self.middleware:
            state = mw.before_stage(state)

        state.stage = self._next_stage(state.stage)

        for mw in self.middleware:
            state = mw.after_stage(state)

        return state

    def finalize(self, state: SweatRunState) -> SweatRunState:
        for mw in self.middleware:
            state = mw.before_complete(state)
        return state

    @staticmethod
    def _next_stage(stage: Stage) -> Stage:
        order: Iterable[Stage] = (
            Stage.planning,
            Stage.design,
            Stage.tdd,
            Stage.coding,
            Stage.qa,
            Stage.deploy,
            Stage.done,
        )
        order_list = list(order)
        if stage == Stage.blocked:
            return Stage.blocked
        idx = order_list.index(stage)
        return order_list[min(idx + 1, len(order_list) - 1)]
