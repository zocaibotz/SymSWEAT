# SWARMINSYM repair slice 2A — 2026-04-03

## What this slice implements

Focused Phase 2A repair from `docs/SWARMINSYM_REPAIR_PLAN_2026-04-03.md`:

- new adapter ledgers now write per attempt under `projects/symphony/runs/attempts/`
- each attempt ledger includes `attempt_id`, `ledger_path`, and `issue_summary_path`
- per-issue summary/index files now live under `projects/symphony/runs/issues/`
- active-run registry records now point at the per-attempt ledger path instead of a mutable per-issue ledger
- retry reconciliation now reads ordered attempt ledgers instead of only one mutable issue snapshot
- compatibility fallback remains in place for older top-level ledgers already written before this slice

## Ledger layout

Current run artifacts now look like:

- attempt ledger: `projects/symphony/runs/attempts/<ISSUE_IDENTIFIER>--<ATTEMPT_ID>.json`
- issue summary: `projects/symphony/runs/issues/<ISSUE_IDENTIFIER>.json`
- active registry attempt record: `projects/symphony/runs/active/<ISSUE_IDENTIFIER>--<ATTEMPT_ID>.json`
- active registry current pointer: `projects/symphony/runs/active/<ISSUE_IDENTIFIER>.current.json`

The issue summary stores the latest attempt plus an ordered `attempts[]` list with attempt id, status, reason, timestamps, and ledger path.

## Boundaries / intentional non-goals for this slice

This slice does **not** yet do the later repair-plan work:

- no adapter heartbeat updates during long-running steps yet
- no semantic success classification improvements yet
- no full multi-attempt policy/requeue redesign yet
- no cleanup/removal of the legacy compatibility mirror yet

## Compatibility notes

- `reconcile_failed_attempts()` still falls back to legacy top-level `projects/symphony/runs/*.json` ledgers so old evidence is not ignored.
- The adapter also mirrors the latest attempt ledger to the old `projects/symphony/runs/<ISSUE>.json` path for operators/scripts that have not yet been updated.
- New active runs, however, now use the per-attempt ledger path as the primary source of truth.

## Validation performed

- `pytest -q poller/test_symphony_poller.py`
- `bash -n swarm-adapter/run_swarm.sh`
