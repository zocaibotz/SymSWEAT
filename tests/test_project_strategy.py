import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.workers import _decide_project_strategy


def test_project_strategy_large_initiative():
    req = {
        "name": "Payments V1 Launch",
        "initiative": "multi-phase",
        "estimated_tasks": 12,
        "stakeholder": "ops",
    }
    out = _decide_project_strategy(req)
    assert out["should_create_linear_project"] is True
    assert out["linear_project_name"] == "Payments V1 Launch"


def test_project_strategy_small_fix():
    req = {
        "name": "Typo fix",
        "description": "small quick fix",
        "estimated_tasks": 1,
    }
    out = _decide_project_strategy(req)
    assert out["should_create_linear_project"] is False
