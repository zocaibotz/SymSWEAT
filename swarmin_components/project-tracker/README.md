# SWARMINSYM Project Tracker

SWARMINSYM Project Tracker is a lightweight Node.js dashboard for monitoring live and historical delivery across the full project lifecycle. It combines a professional two-page UI with a backward-compatible API that captures project decisions, problems, resolutions, stage progress, and linked artifacts.

## Features

- Landing dashboard with portfolio stats, current vs. historical projects, search, and recent activity.
- Project detail page with status header, clickable stage timeline, stage-specific detail panes, and artifact coverage.
- SQLite persistence by default, with automatic in-memory mode for tests.
- Backward-compatible legacy routes for decisions, problems, resolutions, timelines, and debug-log filters.
- Derived metrics for total artifacts, open problems, decision volume, average duration, and stalled-project detection.

## Screenshots

- Placeholder guidance lives in [docs/assets/README.md](/home/claw-admin/.openclaw/workspace/projects/swarminsym-project-tracker-fix/docs/assets/README.md).

## Architecture

- `src/server.js` starts the HTTP server.
- `src/app.js` contains the Express app, storage adapters, derived metrics, and API routes.
- `public/index.html` is the landing dashboard.
- `public/project.html` is the project detail page.
- `public/styles.css`, `public/dashboard.js`, and `public/project.js` provide the UI styling and behavior.
- `data/tracker.db` is the default SQLite database file in local runs.

## API Overview

Core legacy routes:

- `POST /api/projects`
- `GET /api/projects`
- `POST /api/projects/:id/decisions`
- `POST /api/projects/:id/problems`
- `POST /api/problems/:id/resolutions`
- `GET /api/projects/:id/timeline`
- `GET /api/projects/:id/debug-logs`

Dashboard and detail routes:

- `GET /api/dashboard`
- `GET /api/dashboard/stats`
- `GET /api/dashboard/projects`
- `GET /api/dashboard/recent-events`
- `GET /api/projects/:id/overview`
- `GET /api/projects/:id/stages`
- `GET /api/projects/:id/artifacts`
- `GET /api/projects/:id/recent-events`
- `POST /api/projects/:id/artifacts`

## Local Development

### Prerequisites

- Node.js 22+

### Install

```bash
npm install
```

### Run

```bash
npm start
```

Open `http://localhost:3000/index.html` for the dashboard or `http://localhost:3000/project.html?id=<projectId>` for a project detail page.

### Test

```bash
# API/unit tests (Jest)
npm test

# Browser E2E tests (Playwright)
npx playwright install chromium
npm run test:e2e

# Full gate
npm run test:all
```

## Environment Variables

- `PORT`: HTTP port. Default `3000`.
- `TRACKER_DB`: Storage mode. Default SQLite; set to `memory` for ephemeral runs.
- `DB_PATH`: SQLite database path. Default `./data/tracker.db`.
- `STALLED_THRESHOLD_DAYS`: Number of inactive days before an active project is marked stalled. Default `7`.

## Deployment

### Bare Node.js

```bash
npm ci --omit=dev
PORT=3000 TRACKER_DB=sqlite DB_PATH=/var/lib/swarminsym/tracker.db npm start
```

### Process Manager

```bash
pm2 start "npm start" --name swarminsym-tracker
pm2 save
```

Use Nginx or Caddy in front of the app for TLS termination and host-level access control.

## Repository Docs

- [PRD](/home/claw-admin/.openclaw/workspace/projects/swarminsym-project-tracker-fix/docs/PRD.md)
- [SDD](/home/claw-admin/.openclaw/workspace/projects/swarminsym-project-tracker-fix/docs/SDD.md)
- [TDD](/home/claw-admin/.openclaw/workspace/projects/swarminsym-project-tracker-fix/docs/TDD.md)
- [Architecture](/home/claw-admin/.openclaw/workspace/projects/swarminsym-project-tracker-fix/docs/ARCHITECTURE.md)
- [Deployment](/home/claw-admin/.openclaw/workspace/projects/swarminsym-project-tracker-fix/docs/DEPLOYMENT.md)
- [Operations](/home/claw-admin/.openclaw/workspace/projects/swarminsym-project-tracker-fix/docs/OPERATIONS.md)

## License

MIT
