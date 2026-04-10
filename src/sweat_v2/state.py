from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Stage(str, Enum):
    planning = "planning"
    design = "design"
    tdd = "tdd"
    coding = "coding"
    qa = "qa"
    deploy = "deploy"
    done = "done"
    blocked = "blocked"


class ReasoningMode(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    xhigh = "xhigh"


class ArtifactBundle(BaseModel):
    spec_path: Optional[str] = None
    tests_path: Optional[str] = None
    diff_summary: Optional[str] = None
    ci_url: Optional[HttpUrl] = None


class QualitySignals(BaseModel):
    tests_executed: bool = False
    tests_passed: bool = False
    criteria_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    policy_violations: List[str] = Field(default_factory=list)


class BudgetSignals(BaseModel):
    elapsed_sec: int = Field(default=0, ge=0)
    token_used: int = Field(default=0, ge=0)
    reasoning_mode: ReasoningMode = ReasoningMode.medium


class TraceSignals(BaseModel):
    langsmith_run_url: Optional[HttpUrl] = None
    tags: List[str] = Field(default_factory=list)


class SweatRunState(BaseModel):
    run_id: str
    project_id: str
    task_id: str
    stage: Stage = Stage.planning
    acceptance_criteria: List[str] = Field(default_factory=list)
    artifacts: ArtifactBundle = Field(default_factory=ArtifactBundle)
    quality: QualitySignals = Field(default_factory=QualitySignals)
    budget: BudgetSignals = Field(default_factory=BudgetSignals)
    trace: TraceSignals = Field(default_factory=TraceSignals)
    metadata: Dict[str, str] = Field(default_factory=dict)
