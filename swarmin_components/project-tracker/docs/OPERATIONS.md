# Operations Guide

## Health Checks

- `GET /api/projects`
- `GET /api/dashboard/stats`
- `GET /index.html`
- `GET /project.html?id=<projectId>` for a known project during smoke tests

## Backups

- Snapshot the SQLite database file on a schedule.
- Capture associated `-wal` and `-shm` files when snapshotting a live database.

## Routine Tasks

- Review stalled projects from the dashboard.
- Verify open problem counts and recent activity after deployments.
- Archive screenshots and release notes into the docs placeholders as the UI evolves.

## Incident Response

- Check application logs for startup or SQLite access failures.
- Confirm the database path is writable and not exhausted on disk.
- Validate the dashboard API payload before debugging frontend rendering.
- Restore the SQLite database from the latest known-good snapshot if corruption is suspected.
