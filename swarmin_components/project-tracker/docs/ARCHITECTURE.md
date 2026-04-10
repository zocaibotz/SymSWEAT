# Architecture

## Runtime Topology

- Single Node.js process serves both API and static assets.
- Express routes generate raw CRUD-style responses for legacy consumers and aggregated view models for the dashboard UI.
- SQLite runs in-process using `node:sqlite`; test mode falls back to an in-memory adapter with the same method contract.

## Request Flow

1. Browser requests `/index.html` or `/project.html`.
2. Frontend JavaScript fetches dashboard or project-overview endpoints.
3. `src/app.js` reads entities from the selected store.
4. The backend derives portfolio stats, stage groupings, and activity feed entries.
5. JSON is returned to the frontend and rendered into cards, lists, and timeline components.

## Storage Strategy

- Projects are durable records and are never deleted by the current application flow.
- Decisions, problems, resolutions, and artifacts are append-oriented records.
- Historical project visibility is achieved by keeping completed project records available in the same dataset as active projects.
- Stalled status is not stored; it is derived dynamically from `updatedAt`.

## UI Architecture

- Dashboard page emphasizes portfolio scanning with a large stats row and two project buckets.
- Detail page emphasizes stage comprehension with a vertical timeline and adjacent stage-content pane.
- Styling is centralized in a single CSS file to keep deployment simple.
