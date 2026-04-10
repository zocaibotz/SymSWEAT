# SWEAT v2 Migration Plan (Shadow → Cutover)

Last updated: 2026-03-21

## Runtime flags
- `SWEAT_V2_ENABLED=false` (default)
- `SWEAT_V2_SHADOW_MODE=true` (default)
- `SWEAT_V2_CUTOVER_STAGE=planning` (reserved for staged cutover control)

## Modes
1. **Off**: `SWEAT_V2_ENABLED=false`
   - v1 orchestrator routing only.
2. **Shadow**: `SWEAT_V2_ENABLED=true`, `SWEAT_V2_SHADOW_MODE=true`
   - v1 routing executes.
   - v2 recommendation recorded in state + run events.
3. **Cutover**: `SWEAT_V2_ENABLED=true`, `SWEAT_V2_SHADOW_MODE=false`
   - v2 routing decisions become authoritative.

## Recommended rollout
1. Run shadow for 7 days (minimum mixed workload)
2. Review disagreements from `reports/runs/v2_shadow_report.jsonl`
3. Enable cutover first for planning stage workflows
4. Expand to execution and delivery after KPI stability

## Operational dry-runs (implemented)
- Weekly shadow report generator:
  - `python3 scripts/sweat_v2_shadow_weekly_report.py`
  - outputs:
    - `reports/runs/v2_shadow_weekly_report.json`
    - `reports/runs/v2_shadow_weekly_report.md`
- Cutover dry-run check:
  - `python3 scripts/sweat_v2_cutover_dry_run.py`
  - output: `reports/runs/v2_cutover_dry_run.json`
- Rollback dry-run check:
  - `python3 scripts/sweat_v2_rollback_dry_run.py`
  - output: `reports/runs/v2_rollback_dry_run.json`

## Rollback
- Set `SWEAT_V2_ENABLED=false`
- Restart SWEAT runtime
- Existing v1 routing resumes immediately
