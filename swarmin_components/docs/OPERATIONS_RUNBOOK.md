# SWARMINSYM Operations Runbook

## Standard Operator Flow
1. Generate project/tickets with `pm_agent.py`
2. Poll + dispatch via `symphony_poller.py`
3. Review adapter log at `projects/symphony/<ISSUE>/adapter_log.txt`
4. Review attempt ledger(s) at `projects/symphony/runs/attempts/<ISSUE>--<ATTEMPT_ID>.json`
5. Review issue summary ledger at `projects/symphony/runs/issues/<ISSUE>.json`
6. Review active-run registry at `projects/symphony/runs/active/<ISSUE>.current.json` when a ticket is currently owned by the poller
6. Confirm Linear comment/state updates

## If Run Fails (`exit 2`)
- Read `validation.missing_artifacts` in run ledger
- Re-run ticket with stricter constraints or fix repo prerequisites
- Confirm required files exist:
  - `docs/spec/<ISSUE>.md`
  - `reports/security_scan.txt`
  - architect-only docs

## If Run Fails (`exit 3`)
- No meaningful output landed in branch, or the adapter rejected status/refusal chatter
- Check `validation.reason` and `validation.agent_semantic_reason` in the attempt ledger
- Inspect `projects/symphony/<ISSUE>/agent_output.txt` for queue/refusal/concurrency-limit chatter
- Inspect `validation.meaningful_changed_files` vs `validation.placeholder_only_files`
- Re-run only after the branch contains real implementation/test changes or downstream agent capacity is healthy

## If PR Missing (`exit 4`)
- Verify remote branch exists and commits differ from main
- Run `gh pr view <ISSUE>` and `gh pr create ...` manually if needed

## Verification Commands
```bash
bash -n swarm-adapter/run_swarm.sh
cat projects/symphony/runs/attempts/<ISSUE>--<ATTEMPT_ID>.json | jq .
cat projects/symphony/runs/issues/<ISSUE>.json | jq .
cat projects/symphony/runs/active/<ISSUE>.current.json | jq .
```
