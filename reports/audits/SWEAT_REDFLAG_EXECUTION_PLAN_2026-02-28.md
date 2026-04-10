# SWEAT Redflag Execution Plan (2026-02-28)

Source report: `reports/audits/SWEAT_REDFLAG_DEEP_AUDIT_2026-02-28.md`

## Priority order

### Critical
1. C1 — Prevent terminal run-status overwrite after failure
2. C2 — Wire real resume-state load path at run start

### High
3. H1/H2 — CI gate robustness (state schema over project matrix + artifact bootstrap)
4. H3 — Local artifact dependency hardening in CI paths
5. H4 — Expand strict contract coverage to remaining lifecycle nodes
6. H5 — Structured tool-call output hardening
7. H6 — Lifecycle policy matrix + test suite

## Delivery mode
- One issue per risk cluster in Linear
- For each: patch + tests + docs + evidence comment + state transition
- Strict order: Criticals first, then Highs

## Success criteria
- Criticals both merged and validated same day
- Highs tracked with reproducible tests and CI checks
- Weekly scorecard reflects improved pass-rate and reduced fail reasons
