# SWARMINSYM Governance

## Phase Definitions
- **P1**: Contract stabilization (profiles + validator + structured failures)
- **P2**: Observability/state (run ledger + Linear transitions)
- **P3**: Behavior hardening (work-first prompt, timeout, quality gates)
- **P4**: Docs/governance/runbooks aligned to runtime behavior

## Exit Codes
- `0`: success
- `2`: missing artifacts (hard contract violation)
- `3`: semantic/material gate failure (`no_commits`, `no_material_changes`, `placeholder_only_changes`, `agent_status_only`, `agent_launch_only`)
- `4`: PR missing despite valid preconditions
- `5+`: other adapter failures

## Required Success Conditions
1. Artifact validator returns `valid=true`
2. `commits_ahead > 0`
3. `changed_files > 0`
4. `meaningful_changed_files` is non-empty (not only adapter fallback artifacts)
5. No semantic refusal/status-only agent signal was detected
6. PR exists
7. Linear comment + state transition attempted

## State Mapping Policy (Linear)
- Success: `In Review` -> `Review` -> `Done` (first available)
- Failure: `Blocked` -> `Backlog` -> `Todo` (first available)

## Change Control
Any adapter change must include:
- shell syntax check (`bash -n`)
- one verification run
- ledger and log evidence
- TODO + MASTER_TODO update
