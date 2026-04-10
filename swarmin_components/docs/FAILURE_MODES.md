# SWARMINSYM Failure Modes

## FM-01 Missing artifacts
- Symptom: exit `2`
- Detection: validator reason `missing_artifacts`
- Action: enforce artifact-first execution, re-run

## FM-02 No commits/material changes
- Symptom: exit `3`
- Detection: `commits_ahead=0`, `changed_files=0`, or validator reason `placeholder_only_changes`
- Action: tighten prompt and require real source/test edits before report

## FM-03 Status-only / refused agent output
- Symptom: exit `3`
- Detection: validator reason `agent_status_only` or `agent_launch_only`
- Action: re-run only after downstream agent capacity/refusal issue is resolved; do not accept queue/launch chatter as completion

## FM-04 PR creation failure
- Symptom: exit `4` or PR URL empty
- Action: verify branch divergence and `gh` auth

## FM-05 Repo resolution failure
- Symptom: `missing_repo_url` / clone failure
- Action: fix project description URL or repo heuristic fallback

## FM-06 Linear transition mismatch
- Symptom: target state not found
- Action: fallback mapping already enabled; audit team workflow states

## FM-07 Plugin noise
- Symptom: manifest `compression` warnings in logs
- Action: treat as non-blocking unless agent execution fails
