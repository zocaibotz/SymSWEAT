# Automator ↔ n8n Contract

_Last updated: 2026-02-23 UTC_

## 1) Purpose
Defines the payload and response contract between SWEAT `Automator` and n8n webhook workflows.

---

## 2) Request Payload (Automator → n8n)

Automator sends `POST $N8N_WEBHOOK_URL` with JSON body:

```json
{
  "name": "sweat-build-notify",
  "trigger": "webhook",
  "actions": [
    {"type": "http", "name": "trigger-ci"},
    {"type": "notify", "name": "send-status"}
  ],
  "status": "active"
}
```

### Field definitions
- `name` (string, required): workflow instance name
- `trigger` (string, required): top-level trigger strategy
- `actions` (array<object>, required): ordered action descriptors
- `status` (string, required): `active` when webhook configured, else `draft`

---

## 3) Expected Success Response (n8n → Automator)

Any HTTP `2xx` is treated as success.

Automator normalization:

```json
{
  "name": "sweat-build-notify",
  "trigger": "webhook",
  "actions": [...],
  "status": "active",
  "remote_status": "synced",
  "attempts": 1,
  "response": {"...": "raw n8n response body if present, else 'ok'"}
}
```

---

## 4) Retry / Fallback Policy

Automator retries webhook POST when:
- network/request exceptions
- HTTP `429`, `500`, `502`, `503`, `504`

Configurable via env:
- `N8N_TIMEOUT_SECONDS` (default `10`)
- `N8N_MAX_RETRIES` (default `2`, i.e. total attempts = 1 + retries)
- `N8N_RETRY_BACKOFF_SECONDS` (default `1.0`, linear backoff by attempt index)

If all attempts fail, Automator falls back to local-draft status and returns:

```json
{
  "status": "draft",
  "remote_status": "failed",
  "fallback": "local_draft",
  "attempts": 3,
  "error": "HTTP 503: Service unavailable"
}
```

---

## 5) Error Map

| Condition | Retries? | Final `remote_status` | Notes |
|---|---:|---|---|
| 2xx | No | `synced` | success path |
| 4xx (except 429) | No | `failed` | treated as non-transient request/content/auth error |
| 429 | Yes | `failed` if exhausted | transient/rate-limit |
| 5xx | Yes | `failed` if exhausted | transient upstream/server |
| request timeout/connection/DNS | Yes | `failed` if exhausted | request exception |

---

## 6) n8n Summarizer Output Hygiene

In the Page Analyzer workflow, summary output is sanitized to remove hidden reasoning blocks:

```js
summary = rawSummary
  .replace(/<think>[\s\S]*?<\/think>\s*/gi, "")
  .trim()
```

This prevents accidental leakage of `<think>...</think>` content.

<!-- DOC_SYNC: 2026-02-24 -->
