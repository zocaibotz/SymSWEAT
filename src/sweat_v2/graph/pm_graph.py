from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import SweatRunState


@dataclass
class PMGraph:
    """Linear/project management sync scaffold."""

    def run(self, state: SweatRunState) -> SweatRunState:
        state.metadata.setdefault("pm_synced", "true")
        return state
