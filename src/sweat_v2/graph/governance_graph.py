from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import SweatRunState


@dataclass
class GovernanceGraph:
    """Policy and gate annotation scaffold."""

    def run(self, state: SweatRunState) -> SweatRunState:
        state.metadata.setdefault("governance_checked", "true")
        return state
