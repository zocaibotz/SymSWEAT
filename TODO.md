# SWEAT Project TODO (Master)

_Last updated: 2026-02-23 (UTC)_

## Mission (Factory Mode)
SWEAT should autonomously deliver full software lifecycle from prompt to production:

`ReqMaster Interview -> SDD (spec/plan/tasks) -> Design (Architect+Pixel+Frontman) -> TDD Gate -> Build/Review/CI -> Linear Sprint Ops -> GitHub Repo+Actions -> Deploy`

---

## Completed Foundations

- ✅ Memory integration + retrieval guards
- ✅ Automator reliability (retry/failover/health policy)
- ✅ Pixel/Frontman structured design contract
- ✅ CodeSmith tool-call hardening + sandbox + circuit breaker
- ✅ Phase-3 strict pre-code gates (SDD + Design Approval + TDD readiness)
- ✅ Linear integration (project/issue lifecycle + sync routines)
- ✅ Gatekeeper timeout fallback policy

---

## Factory Mode v1 Backlog (authoritative)

### A. GitHub Factory Bootstrap
- [x] Add node to create repo under `zocaibotz/<project-slug>` automatically (`github_bootstrap_node`)
- [x] Add node to initialize git, first commit, default branch, push remote
- [x] Add branch protection + PR strategy bootstrap (CODEOWNERS + PR template + protection API attempt)
- [x] Persist repo metadata in state (`github_repo`, `github_default_branch`, `github_url`)

### B. Production CI/CD via GitHub Actions
- [x] Replace basic CI workflow with strict multi-job workflow:
  - unit + coverage >=95
  - integration tests
  - Playwright e2e
- [x] Add artifact uploads (coverage report, test logs, e2e traces)
- [x] Add deploy job templates (staging/prod) with environment gates

### C. ScrumLord Autonomous Sprint Loop (Linear)
- [x] Add sprint executor loop: pick top ready issue -> implement -> update status -> close (v1)
- [x] Add policy for assignee/status transitions per phase (started -> completed for processed issue)
- [x] Add progress heartbeat/status summary to docs + Linear comments (issue comment on execution)

### D. SDD Tooling Integration
- [x] Integrate `specify` workflow (`specify/plan/tasks`) as first-class node operations (best-effort CLI + fallback)
- [x] Map ReqMaster interview outputs to SDD command inputs and artifacts
- [x] Add validation gate for spec completeness and ambiguity checks

### E. Reliability + Live Readiness
- [x] Finalize provider cascade policy (Gemini CLI -> Codex CLI -> MiniMax API -> Ollama)
- [x] Normalize non-OpenAI response/tool-call parsing (strip `<think>`, parse MiniMax wrappers)
- [x] Run one full live E2E to deploy+automator stage (with fallback flags)
- [x] Publish formal production-readiness report (go/no-go dossier)
- [x] Loop cleanup: stop deployer/automator repeat cycle after successful automation

---

## Factory Mode v2 Backlog (next phase)

### V2-A Governance Hardening
- [x] Enforce branch protection as hard requirement (fail bootstrap if not applied, with explicit override flag)
- [x] Add required checks policy alignment with generated workflow job names
- [x] Add PR auto-label + CODEOWNERS review policy validation

### V2-B CI/E2E Strictness
- [x] Remove permissive Playwright bootstrap fallbacks (`|| true`) in strict templates
- [x] Add reusable test matrix templates (python/node) and cache optimization
- [x] Add security scans (dependency + secret scanning) as required CI jobs

### V2-C Sprint Executor v2
- [x] Priority-aware issue selection (priority + state + labels)
- [x] WIP limits and dependency-aware sequencing
- [x] Multi-issue cycle with stop conditions and periodic status digest

### V2-D SDD Quality Controls
- [x] Enforce spec quality scoring (ambiguity/completeness rubric)
- [x] Block plan/tasks when acceptance criteria are non-testable
- [x] Add traceability map (requirement -> tests -> code artifacts)

### V2-E Observability & Ops
- [x] Add run telemetry (node timings, retries, failure reasons)
- [x] Add autonomous run dashboard/report artifact per execution
- [x] Add nightly healthcheck and drift report for critical integrations

### V2-F Security Scanning Automation
- [x] Integrate code security scans into SWEAT pipeline (Bandit + pip-audit + detect-secrets)
- [x] Persist scan artifacts (`reports/security/*`) and fail policy thresholds
- [x] Add PR security summary comment/check output

## State Hardening Program (Phase 1-3)

- [x] Phase 1: Add append-only run event log (`state/run_events.jsonl`) and run index (`state/run_index.json`)
- [x] Phase 2: Add canonical inter-node communication events + project snapshot (`state/project_state.json`)
- [x] Phase 3: Add idempotency keys + snapshot version checks + conflict events
- [ ] Add JSON schema validation hook for event/snapshot envelopes in CI (`scripts/validate_state.py` + workflow gate)
- [ ] Add migration utility for older projects missing `state/` artifacts

## V3 Backlog (continuous autonomy improvements)

### V3-A Security Auto-Remediation Loop
- [x] Add automated remediation stage after security scans in pipeline
- [x] Attempt safe auto-fixes for findings (dependency updates, config hardening, code fixes where deterministic)
- [x] Re-run security scans after remediation and compare before/after
- [x] Publish remediation + rescan report artifact per run
- [x] Auto-post remediation summary and evidence links into related Linear issue(s)

## Tracking Policy
- Linear project `SWEAT` is source-of-truth execution board.
- This TODO remains strategic summary; execution details tracked per Linear issue.
- Every completed issue should update:
  - docs artifact path(s)
  - test evidence
  - rollout notes
