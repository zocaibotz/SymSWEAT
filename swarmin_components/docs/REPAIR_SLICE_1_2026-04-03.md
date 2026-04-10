# SWARMINSYM repair slice 1 — 2026-04-03

## What this slice implements

Minimum-safe Phase 1 repair from `docs/SWARMINSYM_REPAIR_PLAN_2026-04-03.md`:

- durable active-run registry under `projects/symphony/runs/active/`
- poller boot-time reload of active detached adapters
- stall logic that consults durable local run ownership/state before re-queueing `In Progress` Linear issues
- candidate filtering that avoids redispatching tickets already owned by the durable registry
- cleanup of active registry entries once the existing run ledger reaches a terminal state

## Registry shape

Current implementation writes:

- attempt record: `projects/symphony/runs/active/<ISSUE_IDENTIFIER>--<ATTEMPT_ID>.json`
- current owner pointer: `projects/symphony/runs/active/<ISSUE_IDENTIFIER>.current.json`

Fields include:

- `issue_id`
- `issue_identifier`
- `attempt_id`
- `poller_dispatch_ts`
- `last_heartbeat_ts`
- `adapter_pid`
- `status`
- `ledger_path`
- `branch`

## Boundaries / intentional non-goals for this slice

This slice does **not** yet do the later repair-plan work:

- no per-attempt adapter ledger migration yet
- no adapter heartbeat writes during long steps yet
- no semantic success gating on status-only downstream agent output yet
- no deeper multi-attempt reconciliation yet

Those remain follow-up slices.

## Operational notes

- The poller now treats the on-disk active registry as the source of truth across restarts.
- If an active registry entry exists and its adapter PID is still alive, stall requeue is skipped even when the Linear issue looks old.
- If the ledger becomes terminal (`success`, `failed`, `stalled`, `abandoned`, `completed`), the active registry entry is cleared.
- If the adapter PID is gone and the registry activity timestamp is older than `STALL_MINUTES`, the issue can still be considered stalled; this is the conservative fallback until adapter heartbeats land.
