from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import SweatRunState


@dataclass
class LocalContextMiddleware:
    name: str = "local_context"

    def before_stage(self, state: SweatRunState) -> SweatRunState:
        if "workspace_map" not in state.metadata:
            state.metadata["workspace_map"] = "pending-discovery"
        if "tooling_map" not in state.metadata:
            state.metadata["tooling_map"] = "pending-discovery"
        return state

    def before_complete(self, state: SweatRunState) -> SweatRunState:
        return state

    def after_stage(self, state: SweatRunState) -> SweatRunState:
        return state
