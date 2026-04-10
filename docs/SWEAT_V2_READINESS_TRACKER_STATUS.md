# SWEAT v2 Readiness Tracker Status

Updated: 2026-03-22 17:14 UTC  
Scope: high-signal review of v2 checklist + current v2 code/artifacts only.

Status legend: `complete` | `in_progress` | `blocked` | `not_started`

## 1) Runtime Reality (core)
- **Overall:** `in_progress`
- direct worker bindings for all stages → `in_progress`  
  Evidence: `src/sweat_v2/bindings.py` (planning workers mapped), `src/sweat_v2/graph/*.py` (stage graph stubs)
- remove placeholder transitions; drive flow from real outputs → `blocked`  
  Evidence: `src/sweat_v2/graph/supervisor.py` uses deterministic `_next_stage` increment scaffold
- deterministic routing from real gate/state fields → `in_progress`  
  Evidence: `src/sweat_v2/bridge.py::_to_stage`, `_STAGE_TO_AGENT`

## 2) State & Contract Hardening
- **Overall:** `in_progress`
- canonical v2 schema + versioning policy → `in_progress`  
  Evidence: `src/sweat_v2/state.py` (typed schema present; no explicit schema_version field)
- migration handlers for schema evolution → `not_started`  
  Evidence: no v2 migration handler module found in `src/sweat_v2/`
- strict node-boundary contracts (ingress/egress) → `in_progress`  
  Evidence: `src/sweat_v2/stage_contracts.py`, `src/sweat_v2/contracts.py` (validators/models exist; full runtime enforcement incomplete)
- backward-compatible adapter for legacy `ProjectState` → `complete`  
  Evidence: `src/sweat_v2/bindings.py` (`v2_to_legacy`, `apply_legacy_patch`)

## 3) Reliability & Safety
- **Overall:** `in_progress`
- idempotency keys for side-effecting actions (Linear/GitHub/deploy) → `not_started` (v2-specific)  
  Evidence: no v2 side-effect idempotency layer; only legacy runtime idempotency in `src/main.py`
- retry policy with backoff + max attempts → `complete`  
  Evidence: `src/sweat_v2/retry_policy.py`
- circuit breaker for repeated external failures → `not_started` (v2-specific)  
  Evidence: no v2 circuit-breaker module for external integrations
- dead-letter / failed-run quarantine → `not_started`  
  Evidence: no quarantine/dead-letter artifact path in `src/sweat_v2/`
- human intervention checkpoints for high-risk failures → `in_progress`  
  Evidence: HITL exists in v1 runtime (`src/main.py`, req flow), not codified as v2 risk-class checkpoints

## 4) Quality Gates
- **Overall:** `in_progress`
- pre-completion evidence (tests executed + passed) → `in_progress`  
  Evidence: `src/sweat_v2/harness/middleware/pre_completion_checklist.py` checks `tests_executed`; `stage_contracts.py` checks `tests_passed` for deploy stage
- acceptance-criteria coverage threshold → `in_progress`  
  Evidence: `pre_completion_checklist.py` enforces `criteria_coverage >= 0.95` via policy violation
- policy checks before terminal state → `in_progress`  
  Evidence: `src/sweat_v2/harness/middleware/policy_guard.py`
- artifact sync to SWEAT-private before completion → `in_progress`  
  Evidence: `bridge.py` sets `artifact_sync_target`; policy only checks metadata presence
- false-complete detector before done → `in_progress`  
  Evidence: `src/sweat_v2/e2e_classifier.py`, `scripts/sweat_v2_e2e_failure_report.py`, `reports/runs/v2_e2e_failure_report.json`

## 5) Observability & Ops
- **Overall:** `in_progress`
- end-to-end stage trace correlation IDs → `in_progress`  
  Evidence: shadow/e2e records carry run/project references: `src/sweat_v2/shadow_runner.py`, `reports/runs/v2_shadow_report.jsonl`
- tool-call telemetry (latency/cost/error/type) → `in_progress`  
  Evidence: baseline telemetry in `src/main.py` (`run_telemetry`), v2-specific telemetry model still limited
- dashboard for success/failure/latency/cost/policy drift → `not_started` (v2-specific)  
  Evidence: existing dashboard docs are project-level (`docs/SWEAT_PROJECT1_MONITORING_DASHBOARD.md`), not v2 readiness KPIs
- incident runbook (triage/mitigate/recover) → `in_progress`  
  Evidence: `docs/SWEAT_PRODUCTION_OPERATOR_RUNBOOK.md` exists (not v2 incident-specific)
- replay + snapshot inspection workflow → `not_started`

## 6) Evaluation & Promotion System
- **Overall:** `in_progress`
- finalize benchmark suite → `in_progress`  
  Evidence: `scripts/northstar_stability_runset.py`, `src/sweat_v2/evals.py`
- A/B compare v2 vs v1 fixed runsets → `not_started` (insufficient shadow volume)
- promotion gate enforced in CI → `in_progress`  
  Evidence: gate logic exists `src/sweat_v2/promotion_gate.py`; evidence threshold script `scripts/sweat_v2_promotion_evidence_gate.py`
- regression thresholds encoded + blocking → `in_progress`  
  Evidence: threshold logic in `promotion_gate.py` (cost/latency/policy/success checks)
- weekly eval report automation → `complete`  
  Evidence: `scripts/sweat_v2_shadow_weekly_report.py`, outputs in `reports/runs/v2_shadow_weekly_report.{json,md}`

## 7) Security & Governance
- **Overall:** `not_started`
- secret redaction in logs/events/reports → `not_started`
- credential scope review (least privilege) → `not_started`
- policy audit trail completeness (who/what/when) → `not_started`
- blocklist/allowlist enforcement tests → `not_started` (v2)
- security signoff checklist per release → `not_started`

## 8) Release Engineering
- **Overall:** `in_progress`
- shadow → partial cutover → full cutover controls → `in_progress`  
  Evidence: `docs/SWEAT_V2_MIGRATION_PLAN.md`, `src/sweat_v2/config.py`, `reports/runs/v2_cutover_dry_run.json`
- one-command rollback validated → `complete`  
  Evidence: `scripts/sweat_v2_rollback_dry_run.py`, `reports/runs/v2_rollback_dry_run.json`
- rollback drill under load → `not_started`
- versioned migration notes per release → `in_progress`  
  Evidence: `docs/SWEAT_V2_MIGRATION_PLAN.md` (single plan; no release-by-release changelog yet)
- release checklist + signoff artifact → `in_progress`  
  Evidence: legacy signoff exists `reports/runs/milestone_signoff.{md,json}`; v2-specific signoff artifact incomplete

## 9) Productization Layer
- **Overall:** `not_started`
- operator config guide (model policy/budgets/gates/strictness) → `not_started` (partial env docs only)
- admin controls (pause/resume/kill/replay) → `not_started` (v2)
- troubleshooting FAQ + known failure modes → `not_started`
- onboarding guide for new operators → `not_started`
- example production config bundle → `in_progress`  
  Evidence: `src/sweat_v2/configs/feature_flags.yaml`, `.env.example`

## 10) Proven Readiness Criteria (Go/No-Go)
- **Overall:** `blocked`
- 7-day shadow run completed → `blocked`  
  Evidence: `reports/runs/v2_shadow_weekly_report.json` shows `total: 0` in 7-day window
- >= v1 success rate on E2E workloads → `blocked`
- >=20% false-complete reduction → `blocked`
- >=15% first-pass CI improvement → `blocked`
- policy compliance 100% → `blocked`
- rollback tested successfully → `complete`  
  Evidence: `reports/runs/v2_rollback_dry_run.json`
- final production readiness report published → `not_started`

---

## Current blockers
1. **Shadow evidence volume too low for promotion:** `reports/runs/v2_promotion_evidence_gate.json` => `shadow_rows: 1`, `ready: false`.
2. **Cutover not ready by flags/checks:** `reports/runs/v2_cutover_dry_run.json` => `enabled_is_true: false`, `shadow_is_false: false`, `ready: false`.
3. **E2E quality instability remains:** `reports/runs/v2_e2e_failure_report.json` => `review_loop: 12`, `early_end: 14`, `non_terminal_max_step: 1` (out of 43).
4. **Runtime still scaffold-heavy:** supervisor increments stages generically (`src/sweat_v2/graph/supervisor.py`) instead of real worker-output-driven transitions.

## Next 24h plan (targeted)
1. **Replace stage auto-increment with outcome-driven transitions** for planning/design/tdd/coding in `src/sweat_v2/graph/supervisor.py` + binding integration; add focused tests in `tests/sweat_v2/`.
2. **Increase shadow sample volume to promotion minimum** by running controlled shadow batches and appending to `reports/runs/v2_shadow_report.jsonl` (target >=20 rows).
3. **Tighten quality gates from “violation tagging” to hard blocking** (tests executed/passed + criteria coverage + artifact sync checks) before routing to `done`.
4. **Produce v2 incident/replay mini-runbook** (triage + replay steps + rollback triggers) under `docs/` to unblock observability/ops and release signoff.
5. **Generate refreshed evidence pack** by re-running:
   - `python3 scripts/sweat_v2_e2e_failure_report.py`
   - `python3 scripts/sweat_v2_shadow_weekly_report.py`
   - `python3 scripts/sweat_v2_promotion_evidence_gate.py`

## Fresh Check-in (2026-03-22 17:28 UTC)
- **Changed files since prior tracker timestamp (2026-03-22 17:14 UTC):**
  - `docs/SWEAT_V2_READINESS_TRACKER_STATUS.md` (self-update only)
  - `reports/runs/v2_readiness_tracker_status.json` (self-update only)
- **Other readiness evidence/report files changed:** none detected.
- **Readiness score:** unchanged at **10.0%** (`5/50` complete; summary unchanged).
- **Blockers:** unchanged (B1–B4 still active).
- **Next best action:** run the 3 evidence generators, then execute a controlled shadow batch to raise `v2_shadow_report.jsonl` to `>=20` rows before re-evaluating promotion/cutover readiness.
