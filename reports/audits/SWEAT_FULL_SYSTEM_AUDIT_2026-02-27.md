# SWEAT Full-System Audit (2026-02-27)

North Star audited: **A user provides one natural-language requirement; SWEAT reliably delivers end-to-end through agents + lifecycle automations.**

## Executive Summary — Top Risks (Impact × Likelihood)

1. **Workspace split-brain**: bootstrap path not consistently used by downstream nodes.
2. **Potential lifecycle infinite loop**: `automator -> pipeline -> deployer -> automator`.
3. **Path guard weakness**: prefix-based path checks (`startswith`) are bypass-prone.
4. **Coder model alias integrity**: alias factories referenced undefined model builders.
5. **Zocai terminal routing gap**: zocai conditional map lacked explicit `__end__` route.
6. **Snapshot truth mismatch**: CI/deploy gate semantics can become inaccurate.
7. **Pipeline environment coupling**: strict test path + runtime assumptions can dead-loop retries.
8. **Prompt/schema ambiguity**: soft JSON contracts and semantic string routing triggers.
9. **CI config mismatch**: Playwright job expects root Node setup not always present.
10. **Coverage gap**: mocked/placeholder tests miss true autonomous failure modes.

---

## Key Findings (file-level)

- `src/main.py`: zocai edge map did not include terminal route (`__end__`) while worker map did.
- `src/agents/workers.py`: req/spec convergence logic improved but still relies on strict contract and live model stability.
- `src/agents/workers.py` + `src/tools/filesystem.py`: path safety checks used prefix semantics.
- `src/utils/llm.py`: alias factory referred to undefined helper functions for codex/gemini_cli/ollama builders.
- `src/utils/state_store.py`: persisted gate truth can diverge from runtime semantics if status normalization is inconsistent.
- `.github/workflows/ci.yml`, deploy artifacts: operational assumptions need alignment with actual runtime mode.

---

## Concrete Fix Plan

### P0 (Immediate)
1. Route hardening
   - Add explicit `__end__` in zocai conditional edges (`src/main.py`).
2. Path guard hardening
   - Replace prefix checks with `os.path.commonpath` in:
     - `src/tools/filesystem.py`
     - `src/agents/workers.py` (`_is_path_in_workspace`)
3. LLM factory integrity
   - Define missing helper builders:
     - `_codex_cli_model`
     - `_gemini_cli_model`
     - `_ollama_model`
   - (`src/utils/llm.py`)
4. Workspace affinity enforcement
   - Ensure all lifecycle writes/subprocesses consistently respect `project_workspace_path`.
5. Retry/loop budget
   - Add bounded retry budgets and terminal fail state on persistent lifecycle failure loops.

### P1
- Strong schema enforcement for node contracts (pydantic-level validation).
- Explicit structured gate outputs (avoid semantic string matching like "approved" heuristic).
- Resume-state completeness for deterministic continuation.

### P2
- Service-mode deploy path consistency (runtime + Docker + K8s alignment).
- Production-grade automation reliability (n8n dead-letter/poison-run handling).
- End-to-end replayability + governance telemetry SLOs.

---

## Validation Plan

### Deterministic tests to add
- `test_graph_route_terminal.py`
- `test_workspace_affinity.py`
- `test_loop_budget.py`
- `test_state_snapshot_truth.py`
- `test_path_guard_commonpath.py`
- `test_llm_coder_factory_integrity.py`
- `test_resume_semantics.py`
- `test_ci_config_consistency.py`

### Strict E2E acceptance checklist
1. Single NL requirement intake in clean workspace.
2. Req interview yields machine-valid requirements.
3. SDD spec/plan/tasks produced + traceable.
4. Design/TDD gates pass with explicit evidence.
5. Bootstrap repo + workspace affinity preserved.
6. Code/test pipeline bounded with deterministic pass/fail exits.
7. Deploy/automate path reaches success or explicit terminal fail.
8. State snapshot + resume remain coherent.
9. Final report includes full route/tool/gate evidence.
10. Re-run from same requirement produces equivalent lifecycle behavior (idempotency tolerance defined).

---

## Definition of Done (North-Star)

A run is compliant only when:
- no unbounded loops,
- node contracts are schema-validated,
- all operations are workspace-consistent,
- persistence truth matches runtime truth,
- integrations are success or fail-fast with clear diagnostics,
- deterministic E2E evidence is captured and reproducible.
