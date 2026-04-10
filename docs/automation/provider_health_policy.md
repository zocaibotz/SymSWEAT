# Automator Provider Health & Selection Policy

_Last updated: 2026-02-23 UTC_

## Goal
Keep Automator reliable under host/network failures by selecting healthy n8n webhook endpoints and failing over safely.

## Endpoint configuration
- `N8N_WEBHOOK_URL`: primary endpoint
- `N8N_WEBHOOK_URLS`: comma-separated fallback endpoints

Selection order is deterministic: primary first, then fallbacks in listed order.

## Health probing
When `N8N_HEALTHCHECK_ENABLED=true` (default), Automator probes endpoint host before send:
1. `GET <base>/healthz`
2. `GET <base>/healthz/readiness`
3. `GET <base>/`

If all probes fail for an endpoint, endpoint is skipped and next candidate is tried.

## Delivery behavior
For each candidate endpoint:
- retry transient failures (`429`, `5xx`, request exceptions)
- retries per endpoint controlled by `N8N_MAX_RETRIES`
- backoff controlled by `N8N_RETRY_BACKOFF_SECONDS`

If an endpoint succeeds, return immediately with:
- `remote_status: synced`
- `selected_webhook`
- `health_probe`

If all endpoints fail, return local fallback with:
- `remote_status: failed`
- `fallback: local_draft`
- `endpoint_errors`
- `attempts`

## Operational recommendation
- Keep at least 2 webhook endpoints when possible.
- Prefer same-region endpoint as primary.
- Use fallback endpoint on separate host/network path for resilience.

<!-- DOC_SYNC: 2026-02-24 -->
