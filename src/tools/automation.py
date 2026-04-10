from typing import Dict, Any, List, Optional
import requests
import os
import time
from urllib.parse import urlparse
from src.utils.logger import logger


class N8NTool:
    """
    Real n8n automation tool.

    Behavior:
    - If webhook URL(s) configured: sends workflow data with retries.
    - Supports endpoint failover via N8N_WEBHOOK_URLS (comma-separated).
    - If all endpoints fail: returns local draft payload with error metadata.

    Env knobs:
    - N8N_WEBHOOK_URL: primary webhook endpoint
    - N8N_WEBHOOK_URLS: optional comma-separated fallback endpoints
    - N8N_TIMEOUT_SECONDS: per-request timeout (default: 10)
    - N8N_MAX_RETRIES: retry attempts after first try per endpoint (default: 2)
    - N8N_RETRY_BACKOFF_SECONDS: base backoff between retries (default: 1.0)
    - N8N_HEALTHCHECK_ENABLED: when true, probe endpoint host health before send
    """

    def __init__(self):
        self.webhook_url = os.getenv("N8N_WEBHOOK_URL", "").strip()
        urls_raw = os.getenv("N8N_WEBHOOK_URLS", "").strip()
        extra_urls = [u.strip() for u in urls_raw.split(",") if u.strip()] if urls_raw else []
        self.webhook_candidates = [u for u in [self.webhook_url, *extra_urls] if u]

        # dedupe while preserving order
        seen = set()
        self.webhook_candidates = [u for u in self.webhook_candidates if not (u in seen or seen.add(u))]

        self.timeout_seconds = float(os.getenv("N8N_TIMEOUT_SECONDS", "10"))
        self.max_retries = int(os.getenv("N8N_MAX_RETRIES", "2"))
        self.retry_backoff_seconds = float(os.getenv("N8N_RETRY_BACKOFF_SECONDS", "1"))
        self.healthcheck_enabled = os.getenv("N8N_HEALTHCHECK_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

    def _base_workflow_payload(self, name: str, trigger: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "name": name,
            "trigger": trigger,
            "actions": actions,
            "status": "active" if self.webhook_candidates else "draft",
        }

    @staticmethod
    def _extract_error_text(response: Optional[requests.Response]) -> str:
        if response is None:
            return "No response received"
        body = ""
        try:
            body = response.text or ""
        except Exception:
            body = ""
        return f"HTTP {response.status_code}: {body[:300]}".strip()

    def _probe_base_health(self, webhook_url: str) -> Dict[str, Any]:
        """Best-effort host health probe for n8n endpoint selection."""
        if not self.healthcheck_enabled:
            return {"ok": True, "checked": False, "reason": "healthcheck disabled"}

        parsed = urlparse(webhook_url)
        if not parsed.scheme or not parsed.netloc:
            return {"ok": False, "checked": False, "reason": "invalid webhook url"}

        base = f"{parsed.scheme}://{parsed.netloc}"
        candidates = [f"{base}/healthz", f"{base}/healthz/readiness", base]
        probe_timeout = 3.0 if self.timeout_seconds > 3.0 else float(self.timeout_seconds)
        for target in candidates:
            try:
                r = requests.get(target, timeout=probe_timeout)
                if 200 <= r.status_code < 500:
                    return {"ok": True, "checked": True, "url": target, "status": r.status_code}
            except requests.RequestException:
                continue
        return {"ok": False, "checked": True, "reason": "health probe failed", "base": base}

    def _post_with_retries(self, webhook_url: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes webhook call with retry on network/5xx/429 errors."""
        last_error = ""
        last_response: Optional[requests.Response] = None

        total_attempts = 1 + max(0, self.max_retries)

        for attempt in range(1, total_attempts + 1):
            try:
                logger.info(
                    "N8N: Triggering webhook %s (attempt %s/%s)...",
                    webhook_url,
                    attempt,
                    total_attempts,
                )
                response = requests.post(
                    webhook_url,
                    json=workflow_data,
                    timeout=self.timeout_seconds,
                )
                last_response = response

                if 200 <= response.status_code < 300:
                    logger.info("N8N: Webhook successful.")
                    payload = response.json() if response.content else "ok"
                    return {
                        **workflow_data,
                        "remote_status": "synced",
                        "attempts": attempt,
                        "selected_webhook": webhook_url,
                        "response": payload,
                    }

                if response.status_code in {429, 500, 502, 503, 504} and attempt < total_attempts:
                    last_error = self._extract_error_text(response)
                    sleep_for = self.retry_backoff_seconds * attempt
                    logger.warning("N8N transient failure, retrying in %.2fs: %s", sleep_for, last_error)
                    time.sleep(sleep_for)
                    continue

                last_error = self._extract_error_text(response)
                break

            except requests.RequestException as e:
                last_error = f"Request error: {e}"
                if attempt < total_attempts:
                    sleep_for = self.retry_backoff_seconds * attempt
                    logger.warning("N8N request failed, retrying in %.2fs: %s", sleep_for, last_error)
                    time.sleep(sleep_for)
                    continue
                break

        return {
            **workflow_data,
            "status": "draft",
            "remote_status": "failed",
            "fallback": "local_draft",
            "attempts": total_attempts,
            "selected_webhook": webhook_url,
            "error": last_error or self._extract_error_text(last_response),
        }

    def create_workflow(self, name: str, trigger: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        workflow_data = self._base_workflow_payload(name=name, trigger=trigger, actions=actions)

        if not self.webhook_candidates:
            return workflow_data

        errors = []
        attempts_total = 0
        for webhook in self.webhook_candidates:
            probe = self._probe_base_health(webhook)
            if probe.get("checked") and not probe.get("ok"):
                errors.append({"webhook": webhook, "error": "healthcheck failed", "probe": probe, "attempts": 0})
                continue

            result = self._post_with_retries(webhook, workflow_data)
            attempts_total += int(result.get("attempts", 0) or 0)
            if result.get("remote_status") == "synced":
                result["health_probe"] = probe
                return result
            errors.append({"webhook": webhook, "error": result.get("error"), "probe": probe, "attempts": result.get("attempts")})

        return {
            **workflow_data,
            "status": "draft",
            "remote_status": "failed",
            "fallback": "local_draft",
            "attempts": attempts_total,
            "error": "All configured webhook endpoints failed",
            "endpoint_errors": errors,
        }


_n8n_tool = N8NTool()


def get_n8n_tool() -> N8NTool:
    return _n8n_tool
