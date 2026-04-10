# SWEAT Redflag Recheck (2026-02-28)

## Scope
Post-remediation recheck of SWEAT codebase + architecture/process artifacts, focused on whether prior Critical/High/Medium/Low findings are closed and whether new reliability blockers were introduced.

Reference artifacts:
- `reports/audits/SWEAT_REDFLAG_DEEP_AUDIT_2026-02-28.md`
- `reports/audits/SWEAT_REDFLAG_EXECUTION_PLAN_2026-02-28.md`
- `docs/SWEAT_ARCHITECTURE_AS_BUILT.md`
- `reports/northstar/SWEAT_NORTHSTAR_EXECUTIVE_CLOSEOUT_2026-02-28.md`

---

## Prior findings status

### Critical
- **C1 Run terminal-state overwrite risk**: **Mostly remediated**
  - Status precedence guard added; verify no downstream path can emit conflicting terminal transitions in edge fallback chains.
- **C2 Resume-state load path missing**: **Remediated**
  - Resume bootstrap wiring exists with merge semantics.

### High
- **H1/H2 CI schema scope and project coverage**: **Remediated with caveats**
  - Multi-project validator exists; confirm workflow environment parity.
- **H3 Local-artifact dependency in CI**: **Partially remediated**
  - Better wrappers exist; still verify CI bootstrap assumptions.
- **H4/H5 Contract and tool-call hardening**: **Remediated**
  - Strict defaults + broader contract checks added.
- **H6 Lifecycle policy matrix ambiguity**: **Partially remediated**
  - Tests added; still keep policy combinations tightly bounded.

### Medium
- **M1 Bootstrap portability**: **Remediated**
  - Shared `ci_bootstrap.sh` adopted in workflows.
- **M2 Observability reason codes**: **Remediated**
  - Decision reason codes added across key gates/transitions.

### Low
- **L1 Stale-report process coupling**: **Remediated (operationally)**
  - Canonical wrapper policy documented and automation improved.

---

## Remaining / open red flags (severity-ranked)

## High

### R1) CI security workflow block mismatch
**Why it matters:** can produce false negatives/positives in governance gates and erode trust in CI evidence.
**Observed pattern:** security CI path assumptions not fully aligned with current runtime/project layout.
**Fix now:** normalize security workflow to shared bootstrap + explicit target matrix + deterministic artifact checks.

### R2) Unconditional Playwright behavior in at least one CI path
**Why it matters:** strict pipeline can fail non-Node or mixed projects unnecessarily.
**Observed pattern:** runtime gate is requirement-aware, but CI path parity is not guaranteed in every workflow.
**Fix now:** enforce same `_playwright_required` logic in CI invocation path and document `SWEAT_REQUIRE_PLAYWRIGHT` policy.

### R3) Terminal event/state truth edge case still possible
**Why it matters:** monitoring/signoff can disagree with actual outcome under specific fallback sequences.
**Observed pattern:** terminal status guard exists, but event-stream finalization consistency still needs one final invariant check.
**Fix now:** add a single terminal-state arbiter + test asserting final run_end event status matches persisted terminal status.

---

## New findings introduced by remediations
No new Critical findings identified. Residual risks are primarily integration/consistency class (CI parity + terminal truth alignment).

---

## Final recommendation
**Conditional-ready** (not full production-ready yet).

To reach production-ready:
1. Close R1 (CI security workflow parity)
2. Close R2 (Playwright parity across all CI paths)
3. Close R3 (terminal event/status invariant)
4. Re-run strict signoff + stability matrix and attach fresh evidence artifacts.

Once those are done with passing evidence, readiness can be upgraded to **production-ready**.
