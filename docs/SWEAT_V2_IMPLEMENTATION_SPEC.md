# SWEAT v2 — Implementation Spec + Execution Breakdown

Last updated: 2026-03-21
Owner: Zocai

## 1) Objective
Rebuild SWEAT orchestration around LangGraph/Deep-Agent harness engineering so that reliability improves via:
- deterministic verification before completion
- stronger context injection and policy enforcement
- trace-driven outer-loop improvements

## 2) Architecture Delta (v1 → v2)

### Keep
- Existing SWEAT lifecycle semantics (requirements → SDD → design → TDD → code/review/CI → deploy/automation)
- Existing governance expectations (Linear discipline, artifact discipline, CI quality)

### Replace / Add
- Replace ad-hoc orchestration glue with typed v2 graph contracts
- Add harness middleware stack:
  1. LocalContextMiddleware
  2. PreCompletionChecklistMiddleware
  3. LoopDetectionMiddleware
  4. ReasoningBudgetMiddleware
  5. PolicyGuardMiddleware
- Add evaluation contract + trace-first improvement loop

---

## 3) Linear Issue Set (Epics, stories, dependencies, estimates)

## Epic E1 — SWEAT-v2 Runtime Foundation
**Goal:** Typed graph skeleton + run-state contracts.

1. E1-1: Create `src/sweat_v2` package skeleton
   - Est: 2h
   - Depends: none
2. E1-2: Implement canonical run-state models (`state.py`)
   - Est: 3h
   - Depends: E1-1
3. E1-3: Implement handoff contracts (`contracts.py`)
   - Est: 2h
   - Depends: E1-2
4. E1-4: Add feature flags + config wiring for v2/shadow/cutover
   - Est: 3h
   - Depends: E1-2
5. E1-5: Supervisor graph skeleton + stage routing
   - Est: 4h
   - Depends: E1-3

## Epic E2 — Harness Middleware
**Goal:** Reliable autonomous behavior by default.

1. E2-1: LocalContextMiddleware v1
   - Est: 4h
   - Depends: E1-2
2. E2-2: PreCompletionChecklistMiddleware v1
   - Est: 4h
   - Depends: E1-3
3. E2-3: LoopDetectionMiddleware v1
   - Est: 3h
   - Depends: E1-3
4. E2-4: ReasoningBudgetMiddleware v1
   - Est: 3h
   - Depends: E1-2
5. E2-5: PolicyGuardMiddleware v1
   - Est: 5h
   - Depends: E1-3

## Epic E3 — Tool/Action Contracts
**Goal:** Normalize tool outputs and error taxonomy.

1. E3-1: Tool result schema (`status`, `summary`, `artifacts`, `errors`)
   - Est: 3h
   - Depends: E1-3
2. E3-2: Adapt high-value actions (tests, CI, Linear update)
   - Est: 6h
   - Depends: E3-1
3. E3-3: Retry + escalation policy
   - Est: 3h
   - Depends: E3-1

## Epic E4 — Eval/Trace Loop
**Goal:** Measurable harness iteration.

1. E4-1: LangSmith trace tagging strategy
   - Est: 2h
   - Depends: E1-5
2. E4-2: Failure taxonomy v1
   - Est: 3h
   - Depends: E4-1
3. E4-3: SWEAT benchmark suite scaffold
   - Est: 5h
   - Depends: E1-2
4. E4-4: Harness promotion gate script (regression guard)
   - Est: 4h
   - Depends: E4-3

## Epic E5 — Migration + Cutover
**Goal:** Low-risk transition from v1 to v2.

1. E5-1: Shadow runner (v1/v2 side-by-side)
   - Est: 5h
   - Depends: E1-5, E2-2
2. E5-2: Stage-wise cutover plan (planning→execution→delivery)
   - Est: 3h
   - Depends: E5-1
3. E5-3: Rollback runbook + kill switches
   - Est: 3h
   - Depends: E5-2
4. E5-4: 7-day shadow validation report
   - Est: 6h
   - Depends: E5-1, E4-3

---

## 4) First 10 Working Days (Execution Calendar)

### Day 1
- E1-1 package scaffold
- E1-2 canonical state
- E1-3 contract schema

### Day 2
- E1-4 feature flags
- E1-5 supervisor skeleton
- smoke tests for imports

### Day 3
- E2-1 LocalContextMiddleware
- E2-2 PreCompletionChecklistMiddleware (core checks)

### Day 4
- E2-3 LoopDetectionMiddleware
- E2-4 ReasoningBudgetMiddleware

### Day 5
- E2-5 PolicyGuardMiddleware
- policy configuration schema

### Day 6
- E3-1 tool result schema
- E3-2 adapt tests/CI actions

### Day 7
- E3-2 adapt Linear action contract
- E3-3 retry/escalation policy

### Day 8
- E4-1 trace tags
- E4-2 failure taxonomy

### Day 9
- E4-3 benchmark scaffold
- E4-4 promotion gate prototype

### Day 10
- E5-1 shadow runner initial
- E5-2 cutover draft + rollback draft

---

## 5) Acceptance Criteria for this milestone
- `src/sweat_v2` exists with typed state + contracts + middleware v1 scaffolds
- docs capture linearized task plan + dependencies + 10-day schedule
- basic tests verify middleware contract behavior and import integrity

## 6) Risks and Controls
- Risk: Overfitting harness to isolated tasks
  - Control: promotion gate requires benchmark pass across mixed suite
- Risk: Silent false-complete
  - Control: pre-completion middleware blocks completion without evidence
- Risk: Cost blowups
  - Control: reasoning budget middleware + trace cost telemetry

## 7) Immediate next coding step
Implement runtime skeleton + middleware contract stubs now (done in this session), then wire to existing orchestrator behind feature flags.
