# SWEAT Red-Flag Deep Audit (2026-02-28)

Source: Codex-assisted deep review of code + architecture docs.
Scope included:
- `docs/SWEAT_ARCHITECTURE_AS_BUILT.md`
- `docs/SWEAT_SYSTEM_DETAILED.md`
- `docs/SWEAT_SYSTEM_STAKEHOLDER_BRIEF.md`
- `reports/northstar/SWEAT_NORTHSTAR_EXECUTIVE_CLOSEOUT_2026-02-28.md`
- `src/**`, `scripts/**`, `.github/workflows/**`, tests

---

## Executive Summary
Codex identified **11 red flags**:
- **Critical:** 2
- **High:** 6
- **Medium:** 2
- **Low:** 1

Top blockers for reliable NL→E2E execution:
1. Run status can be incorrectly finalized (failure can be overwritten as completed).
2. CI security workflow snippets contain brittle/invalid assumptions.
3. Resume-state artifact exists but is not consumed for real recovery.
4. Several ops flows depend on local artifacts not guaranteed in CI/runtime environments.

---

## Severity-Ranked Findings

## Critical

### C1) Run-status overwrite risk after fail-fast
**Risk:** A run can be marked `failed` on version conflict and still later be marked `completed` in wrapper flow.
- Evidence areas: `src/main.py` telemetry wrapper fail-fast + end-run handling.
- Why this is bad: corrupts operational truth; can produce false PASS signals.
- Repro: trigger `VersionConflictError` during snapshot write and observe subsequent end-run handling.
- Minimal fix: guard final `end_run(completed)` behind non-failed state check.
- Robust fix: centralized run terminal-state machine (`running -> completed|failed|blocked`) with one-way transitions.

### C2) Resume-state not actually wired for restart semantics
**Risk:** `resume_state.json` is written but not used as canonical restore source when runs restart.
- Evidence areas: `src/utils/resume_state.py` exists; no authoritative load path in orchestration startup.
- Why this is bad: state continuity may diverge; loop regressions can reappear after restart.
- Repro: interrupt mid-run, restart with same project, compare effective state vs resume artifact.
- Minimal fix: load resume state at run start when present + valid.
- Robust fix: explicit resume protocol (`resume_token`, schema/version checks, deterministic replay pointer).

## High

### H1) CI workflow assumptions may fail on non-Node projects
- Evidence: workflow templates and strict pipeline behavior depend on Playwright/node setup in some paths.
- Risk: false negatives, noisy failures, wasted cycles.
- Fix: keep requirement-aware Playwright gate + ensure CI templates mirror that logic.

### H2) State schema gate validates one canonical project path only
- Evidence: `.github/workflows/state-schema.yml` currently validates `projects/overnight-e2e-01`.
- Risk: gives false confidence for other project folders.
- Fix: matrix over detected project dirs or targeted changed dirs.

### H3) Local-only artifacts in CI context
- Evidence: signoff/state scripts rely on local `projects/<id>/state/*` artifacts that may not exist in ephemeral CI.
- Risk: CI gate flakiness unrelated to code quality.
- Fix: generate synthetic test fixture or run an explicit pre-step to build artifacts in CI.

### H4) Contract enforcement coverage still partial
- Evidence: validator exists but not all node contracts are strict-schema-bound.
- Risk: ambiguous handoffs can leak through under provider variability.
- Fix: expand contract map and add hard schema checks for top-risk nodes.

### H5) Tool-call validation relies on soft parsing from model output
- Evidence: parser and tool-call extraction rely on model formatting conventions.
- Risk: non-JSON/prose outputs can still cause churn.
- Fix: enforce strict structured output mode + fallback parser hard limits.

### H6) Lifecycle loops still policy-heavy
- Evidence: multiple env-controlled fallback/forward flags can mask root issues.
- Risk: policy combinations may produce unexpected transitions.
- Fix: publish allowed policy matrix + add tests for each supported mode.

## Medium

### M1) Security/workflow scripts not uniformly portable
- Evidence: script assumptions around environment/tooling differ between local/CI.
- Risk: operator confusion and inconsistent outcomes.
- Fix: standardize bootstrap script used by all workflows.

### M2) Observability completeness gap
- Evidence: route telemetry improved, but some decisions still require log correlation.
- Risk: slower root-cause analysis in production incidents.
- Fix: emit normalized decision/reason codes at each gate.

## Low

### L1) Report freshness/process coupling
- Evidence: multiple report generators require explicit refresh ordering.
- Risk: stale report misuse if wrappers are bypassed.
- Fix: keep single canonical wrapper and deprecate direct report writes in runbooks.

---

## Risk Register (Likelihood × Impact)

| ID | Severity | Likelihood | Impact | Owner Suggestion |
|---|---|---|---|---|
| C1 | Critical | Med | High | Core orchestration owner |
| C2 | Critical | Med | High | State-management owner |
| H1 | High | High | Med | CI/DevOps owner |
| H2 | High | High | Med | CI/DevOps owner |
| H3 | High | Med | Med | CI/DevOps owner |
| H4 | High | Med | Med | Orchestration owner |
| H5 | High | Med | Med | LLM/runtime owner |
| H6 | High | Med | Med | Architecture owner |
| M1 | Medium | Med | Low | Platform owner |
| M2 | Medium | Med | Low | Observability owner |
| L1 | Low | Low | Low | Ops owner |

---

## Recommended Remediation Plan

### Phase P0 (Immediate)
1. Fix terminal run-state overwrite (C1).
2. Implement real resume-state load path (C2).
3. Harden CI state-schema gate scope (H2).

### Phase P1 (Near-term)
4. Expand strict contract coverage to all high-risk nodes (H4).
5. Enforce structured tool-call output and parser guardrails (H5).
6. Normalize lifecycle policy matrix + tests (H6).

### Phase P2 (Operational hardening)
7. Standardize CI/runtime bootstrap portability (M1).
8. Add reason-code telemetry for all gates/transitions (M2).

---

## Regression Tests to Add
- `test_run_terminal_state_not_overwritten_after_failure`
- `test_resume_state_loaded_on_restart`
- `test_state_schema_ci_matrix_over_projects`
- `test_toolcall_strict_json_contract_failure_paths`
- `test_policy_matrix_supported_modes`

---

## Auditor Note
Codex console summary for this pass:
- "2 Critical, 6 High, 2 Medium, 1 Low"
- Top blockers: run-status overwrite, CI security/script assumptions, missing full resume wiring.
