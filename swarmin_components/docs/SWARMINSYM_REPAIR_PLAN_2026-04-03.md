# SWARMINSYM repair plan — 2026-04-03

Based on: `docs/SWARMINSYM_REVIEW_2026-04-03.md`

## Goal

Resume SWARMINSYM safely by fixing the **confirmed** failure paths first:

1. poller restart / stalled-run race
2. adapter false-success path on status-only agent output
3. weak attempt durability / observability that hides or clobbers evidence

This plan intentionally avoids broad end-to-end resumption until the system can distinguish:
- **active vs actually stalled work**
- **real repo work vs status chatter / placeholder artifacts**
- **one attempt vs overlapping duplicate attempts**

---

## Confirmed failure paths this plan targets

### FP1 — Poller restart causes false stall and duplicate dispatch
Confirmed in review:
- detached adapters are launched with `start_new_session=True`
- active runs live only in poller RAM (`active_by_issue`)
- after poller restart, old `In Progress` issues are no longer recognized as active
- `handle_stalled_issues()` can move a still-running issue back to `Todo`/`Backlog`
- next poll can dispatch another adapter for the same issue

Observed evidence:
- retry history shows `stalled -> success` sequences for multiple issues (`ZOC-83`, `ZOC-84`, `ZOC-85`, `ZOC-81`, `ZOC-69`, `ZOC-55`)

### FP2 — Adapter treats launch/queue/refusal chatter as execution success
Confirmed in review:
- `run_swarm.sh` treats `openclaw agent ...` exit `0` as success
- logs include outputs like `Started`, `launched`, or `can't start ... concurrency limit`
- adapter still proceeds to fallback artifacts, commit, validation, and possible PR flow

Observed evidence:
- `../symphony/ZOC-81/adapter_log.txt`
- `../symphony/ZOC-60/adapter_log.txt`
- `../symphony/ZOC-91/adapter_log.txt`

### FP3 — Validation can pass on placeholder-only adapter output
Confirmed in review:
- adapter synthesizes fallback docs and `reports/security_scan.txt`
- validator checks artifact presence + commits ahead
- meaningful implementation can be absent while validation still passes

### FP4 — One mutable ledger per issue hides overlapping attempts
Confirmed in review:
- `RUN_LEDGER="$RUNS_DIR/${ISSUE_IDENTIFIER}.json"`
- overlapping attempts overwrite the same issue ledger
- evidence of ordering and duplication gets lost

### FP5 — Exit-code recording is unreliable in some failure branches
Confirmed in review:
- `if ! timeout ...; then AGENT_EXIT=$?` captures the wrong status in this pattern
- same bug shape appears in other timeout-wrapped command paths

---

## Repair strategy

### Ordering principle
Fix in this order:
1. **run ownership / liveness durability**
2. **semantic success gating**
3. **attempt-level evidence and observability**
4. **controlled verification**
5. only then **resume broader unattended processing**

Why this order:
- If FP1 remains, every later fix can still be masked by duplicate dispatch.
- If FP2 remains, the system can still manufacture fake wins after FP1 is fixed.
- If FP4/FP5 remain, debugging validation becomes slow and ambiguous.

---

## Phase 0 — Freeze + baseline capture

### Objective
Preserve current evidence and avoid creating new misleading runs.

### Work
- Keep broad unattended SWARMINSYM processing paused.
- Do not run a full queue or multi-ticket catch-up pass.
- Snapshot current runtime artifacts before code changes:
  - `../symphony/runs/retry_state.json`
  - current per-issue ledgers under `../symphony/runs/`
  - sample `adapter_log.txt` files already cited in the review
- Add a short note in docs / TODO that resumption is blocked on FP1 + FP2 repair.

### Expected impact
- Prevents new duplicate attempts and more ambiguous ledgers during repair.

### Validation
- Evidence files preserved and referenced in repair PR.

### Safe resume criterion for this phase
- Not a resume phase. This is a hold-the-line phase.

---

## Phase 1 — Durable active-run registry (minimum viable first slice)

## Slice 1A — Persist active ownership before launch

### Objective
Stop the poller from forgetting live detached adapters after restart.

### Work
Implement a durable active-run registry, separate from the mutable issue ledger.

Suggested shape:
- directory: `../symphony/runs/active/`
- file per active attempt: `<ISSUE_IDENTIFIER>--<ATTEMPT_ID>.json`
- optional pointer file for latest active issue owner: `<ISSUE_IDENTIFIER>.current.json`

Minimum fields:
- `issue_id`
- `issue_identifier`
- `attempt_id`
- `poller_dispatch_ts`
- `adapter_pid` if known
- `status` (`dispatched`, `running`, `completed`, `failed`, `stalled`)
- `last_heartbeat_ts`
- `ledger_path`
- `branch`

Poller behavior change:
- write registry entry **before** or atomically with detached adapter launch
- on startup, rebuild in-memory active state from registry
- treat registry as source of truth, RAM as cache

### Rationale
This directly addresses FP1. A restarted poller can only make correct stall decisions if it has durable run ownership.

### Expected impact
- Prevents immediate false-stall requeue after poller restart.
- Makes detached adapters visible across poller process lifetimes.

### Validation
- Unit/integration test: dispatch adapter, restart poller, verify issue is still treated as active.
- Boot test: poller startup loads active registry and does not enqueue same issue again.

### Safe resume criterion
- Poller restart no longer causes duplicate dispatch for an active issue in a controlled test.

---

## Slice 1B — Make stall logic consult durable state, not just Linear age

### Objective
Prevent `updatedAt` + missing RAM state from being enough to requeue live work.

### Work
Change `handle_stalled_issues()` decision rules:
- only classify issue as stalled if **no active registry entry exists** for that issue
- and latest known attempt heartbeat/dispatch age exceeds threshold
- and latest attempt is not already terminal (`success`, `failed`, `abandoned`)

Recommended logic:
1. look for active registry owner for issue
2. if found and fresh heartbeat/dispatch exists -> skip stall action
3. if found but heartbeat very old -> mark `suspect_stalled`, not immediate requeue
4. only after a stronger threshold or explicit reconciliation mark `stalled`

Optional but good:
- split thresholds:
  - `RUN_SUSPECT_MINUTES`
  - `RUN_STALL_MINUTES`

### Rationale
Linear `updatedAt` is not a reliable liveness source for detached local work.

### Expected impact
- Greatly reduces false `stalled -> requeued` transitions.

### Validation
- Controlled test where issue remains `In Progress` without Linear updates while active registry remains fresh.
- Poller should not requeue it.

### Safe resume criterion
- No false `stalled` transition in restart + aged-Linear-ticket test.

---

## Phase 2 — Attempt-level ledgers and heartbeats

## Slice 2A — Replace one-ledger-per-issue with one-ledger-per-attempt

### Objective
Stop overlapping attempts from erasing each other.

### Work
Replace:
- `runs/<ISSUE_IDENTIFIER>.json`

With something like:
- `runs/attempts/<ISSUE_IDENTIFIER>--<ATTEMPT_ID>.json`
- optional summary pointer:
  - `runs/issues/<ISSUE_IDENTIFIER>.json`

Attempt id can be:
- UTC timestamp + random suffix
- or poller-generated monotonic retry attempt id

The issue summary file can point to:
- latest attempt
- all attempt ids
- current state
- retry count

### Rationale
This fixes FP4 and makes future postmortems honest.

### Expected impact
- Duplicate dispatch no longer hides prior attempt evidence.
- `reconcile_failed_attempts()` can reason about ordered history instead of a single overwritten snapshot.

### Validation
- Two attempts for same issue produce two distinct ledger files.
- Summary file references both in order.

### Safe resume criterion
- Attempt history survives duplicate/overlap scenarios without overwrite.

---

## Slice 2B — Add adapter heartbeats into registry/ledger

### Objective
Give the poller a better liveness signal than issue timestamp alone.

### Work
Have the adapter touch/update heartbeat state at key steps:
- clone start/end
- branch ready
- agent invoke start/end
- validation start/end
- PR create/view start/end
- final completion

Persist heartbeat updates to:
- active registry entry
- attempt ledger

### Rationale
Without heartbeats, any long step can still look dead.

### Expected impact
- Better stall decisions.
- Better incident debugging.

### Validation
- Long-running adapter updates `last_heartbeat_ts` during execution.
- Poller respects heartbeat freshness.

### Safe resume criterion
- In a deliberately long run, heartbeat freshness prevents false stall classification.

---

## Phase 3 — Semantic success gating in the adapter (second minimum viable slice)

## Slice 3A — Fail closed on status-only / launch-only agent responses

### Objective
Stop treating `exit 0` as proof that requested repo work happened.

### Work
After `openclaw agent ...`, inspect both:
- command exit status
- agent output semantics
- resulting repo state

Add a semantic failure classifier for patterns like:
- `Started`
- `launched`
- `queued`
- `can't start`
- `concurrency limit`
- `I’ve launched`
- `try again later`

If such patterns appear **without** corroborating repo work, fail the run.

Minimum corroboration examples:
- non-placeholder diff in repo
- tests added/changed where appropriate
- explicit PR creation evidence
- meaningful changed files beyond adapter fallbacks

### Rationale
This directly fixes FP2.

### Expected impact
- Status chatter becomes `failed`/`incomplete`, not fake `success`.
- Placeholder-only branches stop looking healthy.

### Validation
- Replay/log fixture test using known status-only outputs from reviewed adapter logs.
- Adapter must exit failure and avoid validation-success path.

### Safe resume criterion
- Reviewed bad outputs from ZOC-81/ZOC-60/ZOC-91 are rejected in tests.

---

## Slice 3B — Strengthen validation beyond artifact presence

### Objective
Prevent fallback artifacts alone from satisfying success.

### Work
Upgrade `validate_artifacts.sh` or replace it with richer validation logic.

Required checks for success:
- required artifacts exist
- commits exist ahead of base
- changed files include at least one non-fallback meaningful file
- success is rejected if all changed files are only:
  - generated spec fallback docs
  - generated architecture fallback docs
  - generated security report fallback output
- optionally require one of:
  - modified source code
  - modified tests
  - meaningful docs intentionally tied to architect/test ticket type

Recommended explicit outputs in validation JSON:
- `used_fallback_spec`
- `used_fallback_architecture_docs`
- `used_fallback_security_report`
- `meaningful_changes_present`
- `status_only_agent_output_detected`

### Rationale
This fixes FP3 and makes the validator reflect actual task completion.

### Expected impact
- Placeholder-only branches fail fast.
- Reviewers trust green runs more.

### Validation
- Test case: only fallback files changed -> invalid.
- Test case: real source/test diff + required artifacts -> valid.

### Safe resume criterion
- Placeholder-only run cannot pass validation.

---

## Phase 4 — Exit-status correctness and reconciliation cleanup

## Slice 4A — Fix exit-code capture everywhere timeout wrappers are used

### Objective
Make failures diagnosable again.

### Work
Replace patterns like:
```bash
if ! timeout ... cmd; then
  code=$?
fi
```
with a form that preserves the actual command exit status, for example:
```bash
timeout ... cmd
code=$?
if [ "$code" -ne 0 ]; then
  ...
fi
```

Audit at least:
- main `openclaw agent` call
- `run_with_timeout()` consumers
- `gh` command paths
- security scan command paths

### Rationale
This fixes FP5 and removes fake `exit=0` failure logs.

### Expected impact
- Logs and ledgers become trustworthy for debugging.

### Validation
- Small shell-level regression tests for timeout failure, command failure, and success.

### Safe resume criterion
- Deliberately failing commands record correct non-zero exit codes.

---

## Slice 4B — Reconciliation logic should use attempt history

### Objective
Make retry and recovery logic operate on full history rather than latest overwritten snapshot.

### Work
Update reconciliation to:
- read ordered attempts for an issue
- distinguish `active`, `failed`, `stalled`, `superseded`, `success`
- avoid requeue if there is already an active live attempt
- preserve prior evidence when a later attempt succeeds

### Rationale
This closes the loop after Phases 1 and 2.

### Expected impact
- Cleaner recovery behavior.
- Better operator trust.

### Validation
- Test sequence: attempt1 stalled, attempt2 success, attempt3 prevented while attempt2 active.

### Safe resume criterion
- Reconciliation behaves correctly on multi-attempt fixture history.

---

## Phase 5 — Controlled verification before broader resume

## Slice 5A — Single-ticket destructive-confidence test

### Objective
Prove the repaired system survives the known failure paths.

### Work
Use exactly one controlled issue.

Verification scenarios:
1. **poller restart while adapter active**
   - expected: no false stall, no duplicate dispatch
2. **agent status-only response fixture / simulated refusal**
   - expected: adapter fails closed, no fake success
3. **placeholder-only artifact path**
   - expected: validation fails
4. **normal successful run**
   - expected: attempt ledger complete, registry cleared on terminal success, PR reflects real work

### Expected impact
- Produces trustworthy evidence that the repair addresses reviewed failures.

### Validation artifacts to save
- test logs
- resulting attempt ledger(s)
- active registry snapshots before/after restart
- resulting PR diff or branch diff

### Safe resume criterion
All must hold:
- restart test passes
- status-only agent output is rejected
- placeholder-only run is rejected
- one real end-to-end run succeeds cleanly
- no duplicate attempts created during verification

---

## Phase 6 — Narrow resume, then broad resume

## Slice 6A — Narrow unattended resume

### Objective
Resume carefully without reopening the whole queue.

### Work
- Allow only 1 issue at a time initially.
- Monitor active registry + attempt ledgers manually for the first few runs.
- Keep stronger logging enabled.

### Expected impact
- Limits blast radius if another hidden failure path appears.

### Validation
- First 3-5 issues complete without duplicate dispatch or placeholder-only success.

### Safe resume criterion
- No FP1/FP2 regression seen across the first narrow batch.

## Slice 6B — Broader unattended resume

### Work
- Return concurrency gradually only after narrow-run stability.
- Keep registry/heartbeat/reconciliation instrumentation in place permanently.

### Safe resume criterion
- Narrow batch stable; no unexplained `stalled -> success` anomalies; no fake-success PRs.

---

## Minimum viable implementation boundary

If work has to resume in the smallest safe slices, do **not** jump straight to a full refactor.

### Minimum viable slice required before any new real run
Implement these first:
1. durable active-run registry
2. stall logic consulting registry
3. semantic rejection of status-only agent output
4. validator rejection when only fallback artifacts changed

That is the minimum safe boundary.

### Strongly recommended next slice before unattended resume
5. per-attempt ledgers
6. adapter heartbeats
7. exit-code fixups

### Can wait until after first controlled verification if needed
8. reconciliation/history polish
9. broader operator/reporting cleanup
10. threshold tuning and nicer dashboards

---

## Suggested work breakdown for implementation tickets

1. **Poller durability slice**
   - active registry write/load
   - stall logic reads registry
   - restart regression tests

2. **Adapter semantic gate slice**
   - parse agent output
   - detect status-only/refusal patterns
   - fail closed without meaningful diffs
   - replay-log tests from reviewed failures

3. **Validator hardening slice**
   - fallback-only change detection
   - richer validation JSON
   - placeholder-only rejection tests

4. **Attempt ledger + heartbeat slice**
   - unique attempt ids
   - per-attempt files
   - summary file
   - heartbeat updates

5. **Exit-status + reconciliation slice**
   - shell bug fixups
   - multi-attempt reconcile behavior
   - failure-code regression tests

6. **Controlled verification slice**
   - one-ticket restart test
   - one-ticket normal success test
   - evidence capture doc

---

## Resume decision

### Do not resume broad SWARMINSYM processing yet
Safe resumption requires proof that the system now:
- preserves active run ownership across poller restarts
- rejects status-only agent responses
- rejects placeholder-only artifact success
- preserves attempt history without overwrite

### Earliest safe resume point
After Phase 1 + Phase 3 minimum slice passes controlled verification.

### Preferred safe resume point
After Phases 1 through 5 all pass, then resume with one-at-a-time narrow processing.

---

## Bottom line

This is not mainly a cosmetic validator issue. The repair must treat SWARMINSYM as a **durable orchestration problem** plus a **semantic success-classification problem**.

If only the validator is tightened, duplicate dispatch can still corrupt runs.
If only the poller race is fixed, the adapter can still manufacture fake wins.

So the first real repair boundary is:
- durable active registry
- stall logic based on durable liveness
- semantic adapter success gate
- validator rejection of fallback-only work

Everything else improves trust and debuggability, but those four are the line between “paused for good reason” and “safe to start testing again.”
