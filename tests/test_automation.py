import sys
import os
from unittest.mock import patch, Mock
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.automation import N8NTool


def _resp(status_code=200, json_payload=None, text=""):
    m = Mock()
    m.status_code = status_code
    m.content = b"1" if json_payload is not None else b""
    m.json.return_value = json_payload
    m.text = text
    return m


def test_create_workflow_local_draft_when_no_webhook(monkeypatch):
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    tool = N8NTool()

    result = tool.create_workflow("wf", "webhook", [{"type": "http"}])

    assert result["status"] == "draft"
    assert result["name"] == "wf"
    assert "remote_status" not in result


@patch("src.tools.automation.requests.post")
def test_create_workflow_success_first_attempt(mock_post, monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://example.test/webhook")
    monkeypatch.setenv("N8N_MAX_RETRIES", "2")
    monkeypatch.setenv("N8N_HEALTHCHECK_ENABLED", "false")

    mock_post.return_value = _resp(200, {"ok": True})

    tool = N8NTool()
    result = tool.create_workflow("wf", "webhook", [{"type": "http"}])

    assert result["remote_status"] == "synced"
    assert result["attempts"] == 1
    assert result["response"] == {"ok": True}


@patch("src.tools.automation.time.sleep", return_value=None)
@patch("src.tools.automation.requests.post")
def test_create_workflow_retries_then_succeeds(mock_post, _sleep, monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://example.test/webhook")
    monkeypatch.setenv("N8N_MAX_RETRIES", "2")
    monkeypatch.setenv("N8N_HEALTHCHECK_ENABLED", "false")

    mock_post.side_effect = [
        _resp(503, text="Service unavailable"),
        _resp(200, {"ok": True}),
    ]

    tool = N8NTool()
    result = tool.create_workflow("wf", "webhook", [{"type": "http"}])

    assert result["remote_status"] == "synced"
    assert result["attempts"] == 2


@patch("src.tools.automation.time.sleep", return_value=None)
@patch("src.tools.automation.requests.post")
def test_create_workflow_falls_back_after_retries(mock_post, _sleep, monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://example.test/webhook")
    monkeypatch.setenv("N8N_MAX_RETRIES", "1")
    monkeypatch.setenv("N8N_HEALTHCHECK_ENABLED", "false")

    mock_post.side_effect = [
        _resp(503, text="Service unavailable"),
        _resp(503, text="Still unavailable"),
    ]

    tool = N8NTool()
    result = tool.create_workflow("wf", "webhook", [{"type": "http"}])

    assert result["remote_status"] == "failed"
    assert result["fallback"] == "local_draft"
    assert result["status"] == "draft"
    assert result["attempts"] == 2
    assert result["error"] == "All configured webhook endpoints failed"
    assert "HTTP 503" in str(result["endpoint_errors"])

@patch("src.tools.automation.requests.get")
@patch("src.tools.automation.requests.post")
def test_create_workflow_failover_to_secondary_webhook(mock_post, mock_get, monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://primary.test/webhook")
    monkeypatch.setenv("N8N_WEBHOOK_URLS", "http://secondary.test/webhook")
    monkeypatch.setenv("N8N_MAX_RETRIES", "0")

    mock_get.return_value = _resp(200, text="ok")
    mock_post.side_effect = [
        _resp(503, text="Primary down"),
        _resp(200, {"ok": True, "via": "secondary"}),
    ]

    tool = N8NTool()
    result = tool.create_workflow("wf", "webhook", [{"type": "http"}])

    assert result["remote_status"] == "synced"
    assert result["selected_webhook"] == "http://secondary.test/webhook"
    assert result["response"]["via"] == "secondary"


@patch("src.tools.automation.requests.get")
@patch("src.tools.automation.requests.post")
def test_create_workflow_skips_endpoint_on_failed_healthcheck(mock_post, mock_get, monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://bad.test/webhook")
    monkeypatch.setenv("N8N_WEBHOOK_URLS", "http://good.test/webhook")
    monkeypatch.setenv("N8N_MAX_RETRIES", "0")

    # bad endpoint fails all probes, good endpoint passes
    mock_get.side_effect = [
        requests.RequestException("conn"), requests.RequestException("conn"), requests.RequestException("conn"),
        _resp(200, text="ok")
    ]
    mock_post.return_value = _resp(200, {"ok": True})

    tool = N8NTool()
    result = tool.create_workflow("wf", "webhook", [{"type": "http"}])

    assert result["remote_status"] == "synced"
    assert result["selected_webhook"] == "http://good.test/webhook"
