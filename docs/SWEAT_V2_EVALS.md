# SWEAT v2 Evaluation Scaffold

Last updated: 2026-03-21

## KPIs (v1)
Computed by `src/sweat_v2/evals.py`:
- requirements_complete
- design_approved
- tdd_ready
- ci_passed
- deployed
- overall (mean)

## Shadow disagreement tracking
Use `src/sweat_v2/shadow_runner.py` and append records to:
- `reports/runs/v2_shadow_report.jsonl`

Each record includes:
- `v1_next_agent`
- `v2_next_agent`
- `v2_stage`
- `v2_policy_violations`
- `agreed`

## Promotion gate (implemented scaffold)
Implemented in `src/sweat_v2/promotion_gate.py`.

Current gate logic:
- reject on policy regression
- reject on success-rate regression
- reject when both cost and latency regress >15%
- otherwise allow promotion

Promote v2 cutover only if:
- disagreement rate trends down over time
- no increase in blocked/failed runs
- no policy compliance regression
