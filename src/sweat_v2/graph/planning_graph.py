from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.bindings import apply_legacy_patch, map_stage_after_planning, run_planning_worker
from src.sweat_v2.state import Stage, SweatRunState


@dataclass
class PlanningGraph:
    """Planning/design/tdd handoff scaffold for SWEAT v2."""

    def run(self, state: SweatRunState) -> SweatRunState:
        if state.stage == Stage.planning:
            use_bindings = state.metadata.get("use_real_workers", "true") == "true"
            if use_bindings:
                route = state.metadata.get("planning_next_worker", "req_master_interview")
                if route in {"req_master_interview", "sdd_specify", "sdd_plan", "sdd_tasks"}:
                    patch = run_planning_worker(state, route)
                    state = apply_legacy_patch(state, patch)
                    state.metadata["planning_next_worker"] = patch.get("next_agent", route)
                state = map_stage_after_planning(state)
            else:
                state.metadata["planning_status"] = "specified"
                state.stage = Stage.design
        elif state.stage == Stage.design:
            state.metadata["design_status"] = "approved"
            state.stage = Stage.tdd
        elif state.stage == Stage.tdd:
            state.metadata["tdd_status"] = "ready"
            state.stage = Stage.coding
        return state
