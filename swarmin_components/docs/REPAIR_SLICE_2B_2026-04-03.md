# SWARMINSYM repair slice 2B — 2026-04-03

## What this slice implements

Focused Phase 2B repair from `docs/SWARMINSYM_REPAIR_PLAN_2026-04-03.md`:

- adapter heartbeats now update both the durable active-run registry and the per-attempt ledger
- heartbeat metadata now includes `last_heartbeat_ts`, `current_phase`, `phase_started_at`, and `last_event`
- long-running adapter commands now emit periodic keepalive heartbeats while work is still in flight
- the poller now preserves the new heartbeat-phase metadata when persisting/loading active-run records

## Heartbeat coverage

This pass adds heartbeat updates around the main long phases called out in the repair plan:

- adapter bootstrap / initial ledger creation
- clone
- branch setup
- agent invocation
- artifact prep / security scan
- git publish
- validation
- PR lookup / creation / URL resolution
- final success/failure completion

For commands routed through `run_with_timeout`, the adapter now starts a background heartbeat loop that refreshes liveness every `HEARTBEAT_INTERVAL_SEC` seconds (default `60`) until the command exits.

## Data shape updates

Active registry and attempt ledger records can now carry:

- `last_heartbeat_ts`
- `current_phase`
- `phase_started_at`
- `last_event`

These fields are intended for operator debugging and for future stall/recovery policy refinements.

## Boundaries / intentional non-goals for this slice

This slice does **not** yet do the later repair-plan work:

- no semantic success gating for status-only downstream agent output yet
- no redesigned retry/backoff policy yet
- no registry cleanup owned directly by the adapter; terminal cleanup still happens through poller reconciliation
- no migration/removal of the legacy top-level run ledger mirror yet

## Validation performed

- `pytest -q poller/test_symphony_poller.py`
- `bash -n swarm-adapter/run_swarm.sh`
