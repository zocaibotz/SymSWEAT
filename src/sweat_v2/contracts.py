from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class VerificationPlan(BaseModel):
    checks: List[str] = Field(default_factory=list)
    commands: List[str] = Field(default_factory=list)
    required_evidence: List[str] = Field(default_factory=list)


class ConstraintSet(BaseModel):
    time_budget_sec: int = Field(default=0, ge=0)
    policy_constraints: List[str] = Field(default_factory=list)
    environment_constraints: List[str] = Field(default_factory=list)


class HandoffContract(BaseModel):
    intent: str
    inputs: List[str] = Field(default_factory=list)
    expected_outputs: List[str] = Field(default_factory=list)
    verification_plan: VerificationPlan = Field(default_factory=VerificationPlan)
    constraints: ConstraintSet = Field(default_factory=ConstraintSet)
    done_definition: List[str] = Field(default_factory=list)

    def is_complete(self) -> bool:
        return all(
            [
                bool(self.intent.strip()),
                bool(self.inputs),
                bool(self.expected_outputs),
                bool(self.verification_plan.checks),
                bool(self.done_definition),
            ]
        )
