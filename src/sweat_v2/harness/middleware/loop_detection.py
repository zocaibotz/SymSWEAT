from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import SweatRunState


@dataclass
class LoopDetectionMiddleware:
    max_retries_per_stage: int = 3
    name: str = "loop_detection"

    def before_stage(self, state: SweatRunState) -> SweatRunState:
        key = f"retry_count_{state.stage.value}"
        retries = int(state.metadata.get(key, "0"))
        if retries >= self.max_retries_per_stage:
            state.metadata["replan_required"] = "true"
        return state

    def before_complete(self, state: SweatRunState) -> SweatRunState:
        return state

    def after_stage(self, state: SweatRunState) -> SweatRunState:
        key = f"retry_count_{state.stage.value}"
        retries = int(state.metadata.get(key, "0"))
        state.metadata[key] = str(retries + 1)
        return state
