from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import SweatRunState


@dataclass
class DeliveryGraph:
    """Delivery/post-release artifacts scaffold."""

    def run(self, state: SweatRunState) -> SweatRunState:
        state.metadata.setdefault("delivery_artifacts_published", "true")
        return state
