# Test Design Document

## Current Automated Coverage

- Legacy decision creation endpoint.
- Legacy problem creation endpoint.
- Legacy resolution linkage endpoint.
- Legacy debug-log filtering.
- Dashboard overview payload including stats, project buckets, and recent activity.
- Project overview payload including derived metrics, stages, and artifacts.

## Test Strategy

- Use in-memory storage automatically in `NODE_ENV=test`.
- Validate legacy routes first to protect backward compatibility.
- Add focused integration tests for new dashboard and project-detail APIs.
- Keep page-load sanity checks in the manual verification workflow because no browser harness is currently installed.

## Recommended Next Tests

- SQLite persistence across process restarts using a temp database path.
- Stalled-project detection under controlled clock or seeded timestamps.
- Static page smoke tests with a headless browser.
- Artifact grouping and stage-current-state edge cases for projects with sparse phases.
