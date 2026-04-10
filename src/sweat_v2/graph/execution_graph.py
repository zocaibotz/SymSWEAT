from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.state import Stage, SweatRunState


@dataclass
class ExecutionGraph:
    """Coding/QA/deploy scaffold for SWEAT v2."""

    def run(self, state: SweatRunState) -> SweatRunState:
        if state.stage == Stage.coding:
            state.metadata["coding_status"] = "implemented"
            state.stage = Stage.qa
        elif state.stage == Stage.qa:
            state.metadata["qa_status"] = "approved"
            state.stage = Stage.deploy
        elif state.stage == Stage.deploy:
            state.metadata["deploy_status"] = "released"
            state.stage = Stage.done
        return state
