from src.sweat_v2.e2e_classifier import classify_route


def test_classify_early_end() -> None:
    assert classify_route([{"node": "zocai"}], "__end__", 1) == "early_end"


def test_classify_review_loop() -> None:
    route = [
        {"node": "zocai"},
        {"node": "codesmith"},
        {"node": "gatekeeper"},
        {"node": "pipeline"},
    ]
    assert classify_route(route, "bughunter", 4) == "review_loop"


def test_classify_non_terminal_max_step() -> None:
    route = [{"node": "zocai"}] * 100
    assert classify_route(route, "codesmith", 100) == "non_terminal_max_step"
