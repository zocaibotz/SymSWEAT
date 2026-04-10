# SWEAT SDD + TDD Workflow

1. ReqMaster interview loop captures detailed requirements.
2. SDD artifacts generated in sequence:
   - `docs/spec/spec.md`
   - `docs/spec/plan.md`
   - `docs/spec/tasks.md`
3. Design artifacts generated and approved:
   - Architect output
   - Pixel UX package
   - Frontman UI contract
4. TDD gate prepares test assets before coding:
   - `docs/tests/unit_test_plan.md`
   - `docs/tests/integration_test_plan.md`
   - `docs/tests/playwright_test_plan.md`
5. Coverage policy is set to >=95% and enforced in pipeline.
6. Implementation starts only after test readiness gate passes.

<!-- DOC_SYNC: 2026-02-24 -->
