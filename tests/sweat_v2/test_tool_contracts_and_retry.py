from src.sweat_v2.retry_policy import decide_retry
from src.sweat_v2.tool_contracts import ToolStatus, fatal_error, ok, retryable_error


def test_tool_contract_ok() -> None:
    result = ok("done", artifacts={"path": "x"})
    assert result.status == ToolStatus.success
    assert result.artifacts["path"] == "x"


def test_retry_policy_retryable() -> None:
    result = retryable_error("E_TIMEOUT", "timeout")
    decision = decide_retry(result, attempt=1, max_attempts=3)
    assert decision.should_retry is True
    assert decision.next_backoff_sec > 0


def test_retry_policy_fatal() -> None:
    result = fatal_error("E_AUTH", "unauthorized")
    decision = decide_retry(result, attempt=1, max_attempts=3)
    assert decision.should_retry is False
    assert decision.reason == "fatal_error"
