from __future__ import annotations

from dataclasses import dataclass

from src.sweat_v2.tool_contracts import ToolResult, ToolStatus


@dataclass
class RetryDecision:
    should_retry: bool
    reason: str
    next_backoff_sec: int = 0


def decide_retry(result: ToolResult, attempt: int, max_attempts: int = 3) -> RetryDecision:
    if result.status == ToolStatus.success:
        return RetryDecision(False, "success")

    if attempt >= max_attempts:
        return RetryDecision(False, "max_attempts_reached")

    if result.status == ToolStatus.retryable_error:
        backoff = min(60, 2 ** attempt)
        return RetryDecision(True, "retryable_error", backoff)

    return RetryDecision(False, "fatal_error")
