from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromotionInput:
    baseline_success_rate: float
    candidate_success_rate: float
    baseline_cost_per_success: float
    candidate_cost_per_success: float
    baseline_latency_sec: float
    candidate_latency_sec: float
    baseline_policy_violations: int
    candidate_policy_violations: int


@dataclass
class PromotionDecision:
    promote: bool
    reason: str


def evaluate_promotion(inp: PromotionInput) -> PromotionDecision:
    if inp.candidate_policy_violations > inp.baseline_policy_violations:
        return PromotionDecision(False, "policy_regression")

    if inp.candidate_success_rate + 1e-9 < inp.baseline_success_rate:
        return PromotionDecision(False, "success_rate_regression")

    latency_regression = inp.candidate_latency_sec > inp.baseline_latency_sec * 1.15
    cost_regression = inp.candidate_cost_per_success > inp.baseline_cost_per_success * 1.15

    if latency_regression and cost_regression:
        return PromotionDecision(False, "cost_and_latency_regression")

    return PromotionDecision(True, "gate_pass")
