# Product Requirements Document

## Product Summary

SWARMINSYM Project Tracker provides a professional operations dashboard for monitoring active and historical projects across the full delivery lifecycle. The product combines portfolio-level visibility with project-level inspection of stages, decisions, problems, resolutions, and linked artifacts.

## Users

- Operators monitoring multiple in-flight SWARMINSYM projects.
- Technical leads reviewing stage progress and unresolved delivery risks.
- Auditors and reviewers validating historical decision trails and artifacts.

## Goals

- Surface the health of the entire project portfolio from one landing page.
- Preserve historical projects and make them searchable alongside active work.
- Show stage progression clearly for each project, including the current stage for active work.
- Provide stage-level evidence through decisions, problem logs, resolutions, and artifacts.
- Maintain backward compatibility for existing automation and tests.

## Functional Requirements

- Dashboard landing page must show portfolio stats.
- Dashboard must separate current and historical projects while supporting tabs and search.
- Dashboard must show a recent activity feed built from backend data.
- Project detail page must show status, metadata, stage timeline, stage detail, and artifact links.
- Backend must expose dedicated overview endpoints for dashboard and project detail experiences.
- Storage must persist in SQLite by default and support in-memory operation in tests.
- Stalled projects must be derived when active projects exceed an inactivity threshold.

## Non-Goals

- Authentication and role-based access control.
- Multi-tenant isolation.
- Rich editing workflows for every entity in the UI.

## Success Criteria

- Users can identify project health from the dashboard without visiting individual records.
- Project detail page accurately reflects current stage and linked artifacts.
- Historical projects remain queryable after process restarts in SQLite mode.
- Legacy API tests remain green after the rewrite.
