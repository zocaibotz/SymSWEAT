# Software Design Document

## Overview

The application is a single Node.js service serving both the API and static frontend. The backend aggregates raw entities into derived dashboard and project-detail views so the frontend can remain simple and fast.

## Major Components

- Express application in `src/app.js`.
- Storage adapters for `MemoryStore` and `SqliteStore`.
- Static frontend assets in `public/`.
- SQLite file storage under `data/` in non-test environments.

## Data Model

### Projects

- `id`
- `name`
- `prompt`
- `status`
- `createdAt`
- `updatedAt`

### Decisions

- Project-linked events with `phase`, `context`, `reasoning`, and `outcome`.

### Problems

- Project-linked issues with `phase`, `title`, `description`, `status`, and attempted resolutions.

### Resolutions

- Problem-linked resolution attempts with `phase`, `description`, and `outcome`.

### Artifacts

- Project-linked stage artifacts with `phase`, `name`, `url`, and `kind`.

## Derived Models

- Dashboard stats aggregate portfolio-wide project and event counts.
- Project metrics compute current stage, total artifacts, open problems, and duration.
- Stage detail groups decisions, problems, resolutions, and artifacts by lifecycle phase.
- Recent activity normalizes all event types into a feed-friendly payload.
- Stalled projects are identified when the project is not completed and `updatedAt` is older than `STALLED_THRESHOLD_DAYS`.

## Frontend Design

- `index.html` renders the dashboard layout.
- `dashboard.js` loads dashboard stats, filters projects, and creates new projects.
- `project.html` renders the detail layout.
- `project.js` loads overview data, renders the stage timeline, and swaps stage detail content on click.
- `styles.css` defines the responsive dashboard visual system.

## Compatibility Notes

- Existing legacy endpoints remain unchanged in status codes and response semantics.
- New routes are additive and power the rewritten frontend.
