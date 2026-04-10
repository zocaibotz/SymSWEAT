# SWARMINSYM review — 2026-04-03

Scope reviewed:
- `swarm-adapter/run_swarm.sh`
- `swarm-adapter/validate_artifacts.sh`
- `poller/symphony_poller.py`
- sample ledgers/logs under `../symphony/runs/` and `../symphony/*/adapter_log.txt`

## Executive summary

There are **two main failure mechanisms**:

1. **Confirmed async / stalled-run race in the poller**
   - The poller only knows which runs are active inside its own current process memory.
   - If the poller restarts, `active_by_issue` is empty on boot.
   - Any ticket still sitting in Linear `In Progress` and older than `STALL_MINUTES` is treated as stalled and moved back to `Todo`/`Backlog`, even if a detached adapter is still running.
   - That re-queues live work and causes duplicate/repeated runs.

2. **Confirmed false-positive adapter success path when the downstream agent only says “started / queued / can’t start now”**
   - `run_swarm.sh` treats `openclaw agent ...` exit code `0` as success, regardless of whether the agent actually completed the requested repo work.
   - The adapter then creates fallback docs/security artifacts, commits them, and may even pass validation.
   - This can turn a “run never really executed” outcome into a superficially valid branch.

Those two combine badly:
- the poller can re-queue a still-running or recently-detached job,
- then the adapter can accept a status-only/non-executing agent response as if useful work happened,
- producing noisy retries, duplicate attempts, and ledger history that looks like the system is working when it is partly self-healing around broken execution.

---

## Confirmed findings

### 1) Poller stall detection is not durable across poller restarts

In `poller/symphony_poller.py`:
- adapters are launched detached with `start_new_session=True` (`dispatch_swarm_adapter`, lines ~425-431)
- active runs are tracked only in `active_by_issue` RAM (`main`, lines ~461-482)
- stalled detection excludes only issues present in that in-memory set (`handle_stalled_issues`, lines ~197-201)

That means after any poller restart:
- `active_by_issue = {}`
- any old `In Progress` ticket is now invisible as active
- if `updatedAt` is older than `STALL_MINUTES`, the poller does:
  - increment attempts
  - append `reason: stalled`
  - transition issue back to `Todo`/`Backlog`

This is the core async race.

### 2) Existing retry history already shows the race happened

`../symphony/runs/retry_state.json` contains multiple tickets with:
- prior `stalled` entries
- followed later by `success`

Examples:
- `ZOC-83`
- `ZOC-84`
- `ZOC-85`
- `ZOC-81`
- `ZOC-69`
- `ZOC-55`

That pattern is exactly what you would expect from:
- poller forgetting a detached running adapter
- marking it stalled / re-queueing it
- a later run eventually succeeding

It is not proof of the specific restart moment, but it is strong evidence the stall detector is firing on work that later completes successfully.

### 3) Adapter validation is artifact-only and can be satisfied by fallback placeholders

In `run_swarm.sh`:
- after agent invocation, adapter creates fallback docs if missing (`ensure_minimum_docs`, lines ~278-387)
- it creates `reports/security_scan.txt` if missing (`ensure_security_scan_report`, lines ~390-441)
- then stages/commits everything and validates (`git add`, `git commit`, validation at lines ~447-490)

In `validate_artifacts.sh`:
- it only checks presence of:
  - `reports/security_scan.txt`
  - `docs/spec/<ISSUE>.md`
  - architect docs when applicable
- plus `COMMITS_AHEAD > 0`

So validation can pass even when:
- the agent never performed meaningful implementation work,
- only fallback placeholder artifacts were created,
- the resulting commit is mostly adapter-generated scaffolding.

### 4) The adapter accepts status-only agent output as successful execution

In `run_swarm.sh`, lines ~263-274:
- it runs `timeout ... openclaw agent --agent main --message ...`
- if command exits `0`, adapter logs `SWARM execution finished.` and proceeds

But the logs show agent outputs like:
- `Started ✅`
- `I’ve launched the ... run ...`
- `I can’t start ... right now because the session is at the subagent concurrency limit (5/5 active).`

Despite that, the adapter still proceeds to fallback artifact generation and commit/validation.

This is visible in:
- `../symphony/ZOC-81/adapter_log.txt`
- `../symphony/ZOC-60/adapter_log.txt`
- `../symphony/ZOC-91/adapter_log.txt`

That is a confirmed semantic failure: shell success is being mistaken for task success.

### 5) The adapter can record `agent_failed` exit code incorrectly because of `if ! ...; then` + `$?`

In `run_swarm.sh`:
```bash
if ! timeout "$AGENT_TIMEOUT_SEC" openclaw agent ...; then
  AGENT_EXIT=$?
```

Inside that `then` block, `$?` is the exit status of the negated `if` test, not reliably the original agent/timeout exit code you want. Same bug pattern appears in `run_with_timeout()` call sites where logs show failures like:
- `Failed: npm audit (exit=0)`
- `Failed: gh pr view (exit=0)`
- `Failed: gh pr url lookup (exit=0)`

So some logged/recorded failure codes are untrustworthy.

### 6) Reconciliation logic reads one ledger file per issue, so overlapping attempts overwrite evidence

`RUN_LEDGER` is fixed per issue:
- `RUN_LEDGER="$RUNS_DIR/${ISSUE_IDENTIFIER}.json"`

So multiple attempts for the same issue overwrite the same ledger file.

Effects:
- the poller loses per-attempt durability
- `reconcile_failed_attempts()` only sees the latest state snapshot for that issue file
- duplicate runs can erase evidence of the attempt sequence
- postmortems become ambiguous

This makes the async race harder to debug and easier to mis-handle.

---

## Most likely concrete failure path

### Primary path: poller restart -> false stall -> duplicate dispatch

1. Poller dispatches adapter and marks ticket `In Progress`.
2. Adapter is running detached.
3. Poller process restarts/crashes/redeploys.
4. New poller process starts with empty `active_by_issue`.
5. Ticket is still `In Progress` in Linear, and `updatedAt` is older than `STALL_MINUTES`.
6. `handle_stalled_issues()` marks it stalled and moves it back to `Todo`/`Backlog`.
7. Next candidate poll picks it up again and dispatches another adapter.
8. One of the attempts later succeeds; retry state shows both `stalled` and later `success`.

Why this is the most likely known race:
- detached adapter processes are intentionally decoupled from the poller
- poller has no durable active-run registry
- stall logic trusts Linear timestamps more than local run ownership
- retry history already contains `stalled -> success` sequences

### Secondary path: agent says “started/queued/can’t start” -> adapter fabricates enough artifacts to look valid

1. Adapter calls `openclaw agent --agent main --message ...`.
2. Agent responds with status chatter or refusal/queue notice, but exits `0`.
3. Adapter interprets that as successful execution completion.
4. Adapter creates fallback spec/security artifacts.
5. Adapter commits and pushes those artifacts.
6. Validator passes because required files now exist and commits are ahead.
7. System may create/update PR with low-value or placeholder-only changes.

This is also confirmed by adapter logs.

---

## Likely hypotheses (not fully proven from static review alone)

### H1) Some historical `stalled` events were caused by poller restarts rather than truly hung adapters

Very likely, but not fully proven without PM2/service logs aligned to run times.

### H2) Some “success” runs may contain mainly adapter-generated placeholder docs rather than genuine implementation output

Very plausible because the validator allows it and the adapter explicitly synthesizes required docs/security artifacts. Needs per-PR diff review to quantify how often.

### H3) `updatedAt` in Linear may not be refreshed often enough during long runs, making false stall detection possible even without poller restart

Possible. The code does not heartbeat/update the issue while a run is active. If a real run exceeds `STALL_MINUTES` and the poller loses active visibility for any reason, false-stall risk rises further.

---

## Current state snapshot

- Repo code for SWARMINSYM is present and coherent enough to inspect.
- Poller has a single-instance file lock, project filters, retry-state persistence, and stall handling.
- Adapter has better structured ledgers and explicit validation than an earlier naive version.
- But the success criteria are still too weak semantically.
- The most important remaining gap is **durable run ownership / liveness tracking**.
- The second major gap is **distinguishing real implementation completion from agent status chatter**.
- Historical artifacts strongly suggest the system has already hit these issues in practice.

---

## Safest next actions checklist

### Before resuming end-to-end runs
- [ ] **Do not resume broad unattended SWARMINSYM processing yet.**
- [ ] Freeze on analysis/patching first; avoid another full queue run until the race and false-success path are fixed.

### Fix the race first
- [ ] Add a **durable active-run registry** written before adapter launch and cleared only on terminal completion.
- [ ] Make `handle_stalled_issues()` consult that registry, not just in-memory `active_by_issue`.
- [ ] Store **attempt-level ledgers** (`ISSUE_IDENTIFIER + timestamp/attempt id`) instead of one mutable JSON per issue.
- [ ] Only re-queue as stalled when there is **no active registry entry** *and* the latest attempt is older than threshold.

### Fix false-success validation next
- [ ] Treat agent output as failed unless it proves completion or produces expected repo changes.
- [ ] Add a semantic guard: reject outputs containing patterns like `Started`, `launched`, `queued`, `can’t start`, `concurrency limit`, unless there are real repo diffs/tests/PR evidence.
- [ ] Strengthen validator to require more than artifact presence:
  - actual non-placeholder diffs outside generated fallback docs,
  - optionally test evidence/logs,
  - maybe forbid success when only adapter fallback files changed.
- [ ] Consider disabling fallback doc generation during normal runs or marking fallback artifacts so validation can fail when they are the only deliverables.

### Fix observability / correctness bugs
- [ ] Fix exit-code capture around `if ! cmd; then code=$?` patterns.
- [ ] Log/store original command exit statuses correctly.
- [ ] Include attempt id / pid / dispatch timestamp in ledger and comments.
- [ ] Add a small run-state heartbeat (timestamp touch/json update) from adapter while long steps are running.

### Then do a narrow verification run
- [ ] Run one controlled ticket end-to-end after patches.
- [ ] Verify:
  - no duplicate dispatch on poller restart,
  - no false `stalled` transition during active work,
  - no success when agent only returns launch chatter,
  - ledgers preserve all attempts.
- [ ] Inspect resulting PR diff to confirm it contains real issue work, not just fallback artifacts.

---

## Bottom line

The known async execution/validation race is real, but it is actually a **durability/liveness race in the poller**, not just a validator bug.

The adapter/validator layer then makes recovery look healthier than it is by allowing fallback artifacts plus any commit to satisfy success preconditions.

If SWARMINSYM work is resumed without fixing those two layers together, the safest expectation is:
- duplicate retries,
- misleading ledgers,
- placeholder-heavy PRs,
- and hard-to-trust run state.
