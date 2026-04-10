# Deployment Guide

## Local Run

```bash
npm install
npm start
```

The service listens on `PORT` or `3000` by default and creates `data/tracker.db` automatically when SQLite mode is active.

## Production Run

```bash
npm ci --omit=dev
PORT=3000 TRACKER_DB=sqlite DB_PATH=/var/lib/swarminsym/tracker.db npm start
```

## Environment Variables

- `PORT`: Listener port.
- `TRACKER_DB`: `sqlite` by default, `memory` for ephemeral mode.
- `DB_PATH`: SQLite file location.
- `STALLED_THRESHOLD_DAYS`: Inactivity threshold for stalled detection.

## Reverse Proxy

- Terminate TLS at Nginx or Caddy.
- Forward traffic to the Node.js process.
- Restrict public access if the tracker contains internal project metadata.

## Deployment Notes

- Ensure the process user can write to the directory containing `DB_PATH`.
- Include the SQLite database file and WAL sidecars in backup plans.
- Prefer a process manager such as PM2 or systemd for restart handling.
