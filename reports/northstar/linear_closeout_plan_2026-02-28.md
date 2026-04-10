# SWEAT Linear Closeout Plan (2026-02-28)

Target pending issues:
- ZOC-29 — Enforce JSON schemas for state artifacts in CI
- ZOC-30 — Backfill state artifacts for legacy projects
- ZOC-32 — Concurrency lock enforcement

## Execution order

1) ZOC-29 (schema+CI gate)
- Add JSON schema files for `project_state.json` and `run_events` entries.
- Add validator script and CI workflow check.
- Add tests for schema pass/fail cases.
- Close when CI check is required and green.

2) ZOC-30 (legacy backfill)
- Add migration script to discover old project dirs and seed minimal state artifacts.
- Dry-run + apply modes.
- Write migration report artifact.
- Close after migration tested on sample legacy projects.

3) ZOC-32 (concurrency locks)
- Add lock acquisition/release primitives (project/run scope).
- Enforce lock in write paths + conflict failure event.
- Add tests for lock contention and stale lock recovery.
- Close when contention is deterministic and safe-fail.

## Reporting discipline
- Every sub-task gets Linear comment updates with commit hash + validation evidence.
- Transition issue states: started -> completed only with evidence.
