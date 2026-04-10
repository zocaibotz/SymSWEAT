# SWEAT V2 Production Readiness Checklist

Last updated: 2026-03-22
Owner: Zocai
Status legend: `[ ]` not started · `[-]` in progress · `[x]` complete

---

## 1) Runtime Reality (core)
- [-] Complete direct worker bindings for all stages (planning, design, tdd, coding, qa, delivery, pm)
- [-] Remove placeholder transitions and drive stage flow from real worker outputs
- [-] Deterministic routing based on real gate/state fields

## 2) State & Contract Hardening
- [-] Finalize canonical v2 schema + schema versioning policy
- [ ] Add migration handlers for schema evolution
- [-] Enforce strict node-boundary contracts (ingress + egress)
- [x] Maintain backward-compatible adapter for legacy `ProjectState` during transition

## 3) Reliability & Safety
- [ ] Idempotency keys for side-effecting actions (Linear/GitHub/deploy)
- [x] Retry policy with backoff + max-attempt caps
- [ ] Circuit breaker for repeated external failures
- [ ] Dead-letter / failed-run quarantine path
- [ ] Human intervention checkpoints for high-risk failure classes

## 4) Quality Gates
- [ ] Enforce pre-completion evidence (tests executed + passed)
- [ ] Enforce acceptance-criteria coverage threshold
- [-] Enforce policy checks before terminal state
- [ ] Enforce artifact sync to SWEAT-private before completion
- [ ] Add false-complete detector before `done`

## 5) Observability & Ops
- [-] End-to-end stage trace correlation IDs
- [-] Tool-call telemetry (latency/cost/error/type)
- [ ] Dashboard for success/failure/latency/cost/policy drift
- [ ] Incident runbook (triage/mitigate/recover)
- [ ] Replay + snapshot inspection workflow

## 6) Evaluation & Promotion System
- [-] Finalize SWEAT benchmark suite (representative workloads)
- [ ] A/B compare v2 vs v1 on fixed runsets
- [-] Promotion gate enforced in CI
- [ ] Regression thresholds encoded + blocking
- [x] Weekly eval report automation

## 7) Security & Governance
- [ ] Secret redaction coverage in logs/events/reports
- [ ] Credential scope review (least privilege)
- [ ] Policy audit trail completeness (who/what/when)
- [ ] Blocklist/allowlist enforcement tests
- [ ] Security signoff checklist per release

## 8) Release Engineering
- [-] Shadow → partial cutover → full cutover rollout controls
- [x] One-command rollback validated
- [ ] Rollback drill under load
- [-] Versioned migration notes per release
- [ ] Release checklist + signoff artifact

## 9) Productization Layer
- [ ] Operator config guide (model policy, budgets, gates, strictness)
- [ ] Admin controls (pause/resume/kill/replay)
- [ ] Troubleshooting FAQ + known failure modes
- [ ] Onboarding guide for new operators
- [ ] Example production config bundle

## 10) Proven Readiness Criteria (Go/No-Go)
- [ ] 7-day shadow run completed
- [ ] >= v1 success rate on E2E workloads
- [ ] >= 20% reduction in false-complete outcomes
- [ ] >= 15% first-pass CI improvement (target)
- [ ] Policy compliance 100%
- [ ] Rollback tested successfully
- [ ] Final production readiness report published

---

## Progress Tracking Rules
- Update this checklist at every milestone completion.
- Include file/report evidence in milestone updates.
- Any blocker must include: root cause, impact, workaround, ETA.

## Current Snapshot
- Runtime scaffolding + middleware + bridge + shadow reporting + dry-run scripts are implemented.
- Full direct worker binding and production hardening are in progress.
