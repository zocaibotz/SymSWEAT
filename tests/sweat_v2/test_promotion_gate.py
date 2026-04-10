from src.sweat_v2.promotion_gate import PromotionInput, evaluate_promotion


def test_promotion_pass() -> None:
    decision = evaluate_promotion(
        PromotionInput(
            baseline_success_rate=0.70,
            candidate_success_rate=0.72,
            baseline_cost_per_success=1.0,
            candidate_cost_per_success=1.10,
            baseline_latency_sec=100,
            candidate_latency_sec=110,
            baseline_policy_violations=2,
            candidate_policy_violations=2,
        )
    )
    assert decision.promote is True


def test_promotion_fail_on_policy_regression() -> None:
    decision = evaluate_promotion(
        PromotionInput(
            baseline_success_rate=0.70,
            candidate_success_rate=0.75,
            baseline_cost_per_success=1.0,
            candidate_cost_per_success=1.0,
            baseline_latency_sec=100,
            candidate_latency_sec=90,
            baseline_policy_violations=1,
            candidate_policy_violations=2,
        )
    )
    assert decision.promote is False
    assert decision.reason == "policy_regression"
