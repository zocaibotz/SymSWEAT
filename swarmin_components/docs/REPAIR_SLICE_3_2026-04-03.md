# SWARMINSYM Repair Slice 3 — Semantic Success Gating

## Implemented
- adapter now captures downstream agent output to `projects/symphony/<ISSUE>/agent_output.txt`
- adapter classifies queue/refusal/concurrency-limit/launch-only chatter and records semantic failure reasons (`agent_status_only`, `agent_launch_only`)
- validator now fails closed when an agent semantic failure reason is present
- validator now computes `changed_files`, `meaningful_changed_files`, and `placeholder_only_files`
- validator rejects runs where every changed file is only adapter fallback output (`placeholder_only_changes`)
- governance/runbook/failure-mode docs updated to describe the stronger success contract
- added shell regression test `tests/validate_semantic_gates.sh`

## Notes
- this keeps Slice 3 aligned with earlier registry / attempt-ledger / heartbeat work by putting semantic rejection into the same attempt ledger `validation` envelope
- exit code mapping stays conservative: semantic/material failures remain exit `3`

## Remaining assumptions
- launch/status-only detection is pattern-based, not a structured downstream protocol yet
- placeholder-only rejection currently treats these files as adapter-placeholder-only classes: `docs/spec/<ISSUE>.md`, architecture fallback docs, `reports/security_scan.txt`, and `swarm_prompt.txt`
- if future ticket types intentionally succeed with docs-only output, the validator allowlist will need a profile-aware expansion rather than a global relaxation

## Next
1. move from regex-based agent semantic detection to structured downstream completion metadata if OpenClaw can emit it
2. add an end-to-end adapter fixture test that exercises `run_swarm.sh` with mocked `openclaw agent` output and ledger assertions
3. optionally mark fallback-generated files explicitly in metadata so validation does not depend on path classification alone
4. review whether docs-only ticket classes need a separate success profile distinct from implementation/test tickets
