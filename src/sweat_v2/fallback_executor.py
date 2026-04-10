from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class ExecutionResult:
    ok: bool
    mode: str
    detail: str = ""
    data: Dict[str, str] = field(default_factory=dict)


@dataclass
class SpawnAttempt:
    mode: str
    run: Callable[[], ExecutionResult]


THREAD_HOOK_ERROR = "subagent_spawning hooks"


def execute_with_fallback(*, attempts: list[SpawnAttempt]) -> ExecutionResult:
    """Run attempts in order and auto-fallback on known thread/session limitations.

    Intended order:
    1) thread session mode
    2) non-thread one-shot/run mode
    3) in-session local executor
    """
    last: Optional[ExecutionResult] = None
    for attempt in attempts:
        result = attempt.run()
        if result.ok:
            return result

        last = result
        # fallback trigger: known thread-binding limitation
        if THREAD_HOOK_ERROR in (result.detail or ""):
            continue

        # Unknown hard error: stop fast
        return result

    return last or ExecutionResult(ok=False, mode="none", detail="no attempts provided")
