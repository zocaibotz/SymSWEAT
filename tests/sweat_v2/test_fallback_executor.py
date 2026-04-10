from src.sweat_v2.fallback_executor import (
    ExecutionResult,
    SpawnAttempt,
    execute_with_fallback,
)


def test_fallback_on_thread_hook_error() -> None:
    calls = []

    def thread_attempt() -> ExecutionResult:
        calls.append("thread")
        return ExecutionResult(
            ok=False,
            mode="session-thread",
            detail="thread=true is unavailable because no channel plugin registered subagent_spawning hooks",
        )

    def run_attempt() -> ExecutionResult:
        calls.append("run")
        return ExecutionResult(ok=True, mode="run", detail="fallback succeeded")

    result = execute_with_fallback(
        attempts=[
            SpawnAttempt(mode="session-thread", run=thread_attempt),
            SpawnAttempt(mode="run", run=run_attempt),
        ]
    )

    assert result.ok is True
    assert result.mode == "run"
    assert calls == ["thread", "run"]


def test_stop_on_unknown_error() -> None:
    def bad_attempt() -> ExecutionResult:
        return ExecutionResult(ok=False, mode="session-thread", detail="permission denied")

    def should_not_run() -> ExecutionResult:
        raise AssertionError("should not run")

    result = execute_with_fallback(
        attempts=[
            SpawnAttempt(mode="session-thread", run=bad_attempt),
            SpawnAttempt(mode="run", run=should_not_run),
        ]
    )

    assert result.ok is False
    assert result.detail == "permission denied"
