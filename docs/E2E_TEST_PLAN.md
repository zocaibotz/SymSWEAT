# SWEAT End-to-End Pipeline Test Plan

**Date:** 2026-04-11  
**Author:** Zocai  
**Status:** Planning

---

## 1. What Is Being Tested

The full SWEAT pipeline: **5 stages × 2 entry paths**, driven through the monitoring UI.

| Stage | Node | What it does | HITL? | Typical runtime |
|-------|------|---------------|-------|-----------------|
| **Requirement Master** | `req_master_interview` | Asks 4 questions; human answers via monitoring UI | ✅ | Pauses here |
| **Specification** | `sdd_specify` + `sdd_plan` + `sdd_tasks` | SDD doc + tasks list generated | ❌ | 2–5 min |
| **Design** | `architect` + `pixel` + `frontman` | Architecture diagram + tech spec + UI spec | ❌ | 2–5 min |
| **Build & Test** | `codesmith` + `gatekeeper` + `tdd_orchestrator` | Code written, reviewed, tests pass | ❌ | 5–15 min |
| **Deploy & Ops** | `automator` + `deployer` + `scrumlord` | CI/CD live, Linear tickets, GitHub repo | ❌ | 5–10 min |

> Total elapsed time for a warm run (no cold start): **~15–35 min**  
> With cold/startup overhead: budget **up to 60 min**

---

## 2. Entry Points: Two Modes

### Mode A — Fresh Project (cold start)
```
Playwright → monitoring UI → answers 4 interview questions
           → pipeline advances automatically through all 5 stages
           → artifacts appear in UI at each stage boundary
```

### Mode B — Dry-Run / Isolated (fast)
```
scripts/run_strict_e2e_cycle.py --project-dir projects/test-e2e-01 --prompt "Build a..."
```
This drives the LangGraph directly without UI. No HITL polling needed since the interview is auto-completed via prompt injection. Used for **smoke testing** the graph itself.

---

## 3. Observable Stage Verification Points

For each stage `S`, the test asserts **at least one** of:

1. **Monitoring API** — `GET /api/monitoring/projects/{id}` shows `current_stage == S`
2. **State file** — `projects/{id}/state/project_state.json` has relevant fields set (e.g. `sdd_spec_path` after specify)
3. **Artifact files** — files exist on disk (e.g. `sdd_spec.md`, `plans/tasks.md`, `src/main.py`)
4. **UI** — Playwright verifies stage label in the pipeline progress bar
5. **GitHub** — repo exists at `https://github.com/zocaibotz/{project-slug}`

---

## 4. Credentials & Environment Audit

| Item | Status | Notes |
|------|--------|-------|
| `MINIMAX_API_KEY` | ⚠️ Real but rate-limited | Primary coder; funded account but 429s likely under load |
| `GEMINI_CLI_MODEL=gemini-3-pro-preview` | ❓ Unknown | Requires `gemini` CLI installed + auth |
| `LINEAR_API_KEY` | ✅ Configured | Team ZOC (ID: `4b6221eb-...`) |
| `GITHUB_TOKEN` | ✅ Inherited from git credentials | `~/.git-credentials` or `git config credential.helper` |
| `docker-compose` | ✅ Available | n8n + SIS services for full SIS mode |
| `ollama` | ❌ Disabled (`SWEAT_USE_OLLAMA=false`) | Not available |
| ACP runtime | ⏸️ Paused | Not available for this run |

**Key risk:** Gemini CLI is not confirmed installed or authenticated in this environment. If it is missing, SWEAT will cascade to `minimax_api` for coding, which is rate-limited.

---

## 5. Test Architecture

```
tests/
  test_pipeline_e2e.py       ← the main E2E test
  conftest.py                ← shared server fixtures (app_server, graph_server)

scripts/
  run_pipeline_e2e.py         ← one-shot script wrapper (runs graph + waits for stages)
```

### `conftest.py` fixtures:
- `app_server` — uvicorn server on port 18766, with auth env vars (`ADMIN_PASSWORD`, `SWEAT_USERS`)
- `graph_server` — background thread running `scripts/run_strict_e2e_cycle.py` with a dedicated project ID and SWEAT LLM BACKEND set to `minimax_api`
- `graph_process` — tears down the graph server when the test session ends

### `test_pipeline_e2e.py` stages:

#### Class `TestRequirementMaster`
- `test_interview_renders_4_questions` — verifies 4 textareas appear for a fresh `awaiting_human` project
- `test_answer_all_4_questions` — answers all 4 via `POST /interview/answer`, verifies `"pending_questions": []`
- `test_interview_complete_hides_section` — after all answered, interview section is `display:none`

#### Class `TestSpecificationStage`
- `test_specify_produces_sdd_doc` — after interview complete, poll `/api/monitoring/projects/{id}` until `current_stage == "sdd_specify"` or `sdd_spec_path` is set
- `test_plan_and_tasks_files_exist` — checks for `sdd_plan_path` and `sdd_tasks_path` in state

#### Class `TestDesignStage`
- `test_architect_produces_design_doc` — waits for `design_doc_path` in state / UI
- `test_pixel_produces_ui_spec` — waits for UI spec artifact
- `test_frontman_produces_acceptance_criteria` — waits for acceptance criteria in state

#### Class `TestBuildStage`
- `test_codesmith_produces_src_files` — checks `src/` directory is non-empty
- `test_gatekeeper_approves` — verifies no `lifecycle_fail_reason` in state
- `test_tdd_tests_exist_and_pass` — runs `pytest` in the generated project directory

#### Class `TestDeployStage`
- `test_github_repo_created` — checks `github_url` in state / monitoring API
- `test_deployer_reports_url` — verifies `deployment_url` is set (or staging URL in artifacts)
- `test_linear_sprint_created` — queries Linear API for issues in the team

---

## 6. Execution Flow

```
1. Start app_server (port 18766) with auth
2. Spawn graph_server in background thread
   - writes to projects/{test_project_id}/
   - uses MINIMAX_API_KEY for coding
   - uses LINEAR_API_KEY for ticket ops
3. Playwright page logs in at http://localhost:18766/ui/login
4. Navigate to /ui/project/{test_project_id}
5. For each stage boundary:
   a. Poll GET /api/monitoring/projects/{test_project_id} every 10s
   b. Assert expected fields are set
   c. If HITL stage → answer via POST /interview/answer
   d. If non-HITL stage → wait up to 5 min then assert
6. After pipeline completes (next_agent == "__end__"):
   a. Verify all stage artifacts present
   b. Assert no `lifecycle_fail_reason`
   c. Capture run_events.jsonl as test artifact
7. Tear down graph_server and app_server
```

---

## 7. Timeout Budget

| Stage | Timeout | Rationale |
|-------|---------|-----------|
| Interview answer propagation | 30s | Write to JSONL + state update |
| Interview → Specify transition | 60s | Orchestrator loop frequency |
| SDD specify/plan/tasks | 300s (5 min) | LLM generates 3 docs |
| Design (architect/pixel/frontman) | 300s (5 min) | Diagrams + specs |
| Build (codesmith + gatekeeper) | 600s (10 min) | Code write + review cycle |
| Deploy (automator + deployer) | 300s (5 min) | CI setup + Linear |
| **Total** | **25 min** | Plus 5 min buffer = 30 min hard cap |

---

## 8. What Zocai Needs from Zi

1. **Gemini CLI confirmation** — Is `gemini` CLI installed and authenticated on this machine? (`gemini --version` → if not found, SWEAT cascades to `minimax_api` which may hit rate limits)
2. **Which stages to test** — Full 5-stage pipeline takes ~30 min. Prefer Mode A (fresh + real UI) or Mode B (isolated cycle, faster)?
3. **Target project ID** — Fixed slug like `e2e-pipeline-test-01` or dynamically generated per run?
4. **GitHub token scope** — Confirm the `~/.git-credentials` GitHub token has `repo` scope (needed for repo creation + branch protection)
5. **Moonshot** — `sk-3ijCwGnxGtZiXwotpxvU2Ef9aN7k3gXtSImdVXytlqFkcD8M` is in `.env` but was previously rate-limited. Confirm if this should be kept as fallback or masked.

---

## 9. Known Gaps & Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| MiniMax 429 during coding stages | Medium | Add exponential backoff to polling; cap retries at 3 |
| Gemini CLI not installed | Medium | Detect at test startup; warn and skip to minimax_api |
| Interview not advancing to specify | Low | Check `_latest_route_stage` logic; `__end__` guard |
| GitHub repo creation fails (token perms) | Low | Catch exception; assert error is auth-related |
| docker-compose n8n not running | Low | Only needed for SIS/n8n webhook mode; not needed for this test |
| LangGraph state bloat (120 step cap) | Very Low | 5 stages × ~10 steps = 50 steps well within 120 |
| `requirements_open_questions` not cleared after POST | Low | Already fixed in monitoring_api.py; test covers it |

---

## 10. Deliverable Files

- [ ] `tests/conftest.py` — server fixtures
- [ ] `tests/test_pipeline_e2e.py` — 15+ stage-verification tests  
- [ ] `scripts/run_pipeline_e2e.py` — reusable script wrapper
- [ ] `docs/E2E_TEST_PLAN.md` — this document
