from __future__ import annotations

from dataclasses import dataclass, field

from src.sweat_v2.graph.delivery_graph import DeliveryGraph
from src.sweat_v2.graph.execution_graph import ExecutionGraph
from src.sweat_v2.graph.governance_graph import GovernanceGraph
from src.sweat_v2.graph.planning_graph import PlanningGraph
from src.sweat_v2.graph.pm_graph import PMGraph
from src.sweat_v2.stage_contracts import validate_stage_contract
from src.sweat_v2.state import Stage, SweatRunState


@dataclass
class RuntimeGraph:
    planning: PlanningGraph = field(default_factory=PlanningGraph)
    execution: ExecutionGraph = field(default_factory=ExecutionGraph)
    governance: GovernanceGraph = field(default_factory=GovernanceGraph)
    delivery: DeliveryGraph = field(default_factory=DeliveryGraph)
    pm: PMGraph = field(default_factory=PMGraph)

    def run_to_terminal(self, state: SweatRunState, max_steps: int = 20) -> SweatRunState:
        for _ in range(max_steps):
            if state.stage in {Stage.done, Stage.blocked}:
                break

            violations = validate_stage_contract(state)
            if violations:
                state.quality.policy_violations.extend(violations)
                state.stage = Stage.blocked
                break

            state = self.governance.run(state)
            state = self.pm.run(state)
            if state.stage in {Stage.planning, Stage.design, Stage.tdd}:
                state = self.planning.run(state)
            else:
                state = self.execution.run(state)
            state = self.delivery.run(state)
        return state
