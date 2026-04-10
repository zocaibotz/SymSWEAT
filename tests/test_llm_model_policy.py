import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.llm import _resolve_main_alias_order


def test_main_llm_defaults_follow_coder_policy(monkeypatch):
    monkeypatch.delenv("SWEAT_LLM_PRIMARY", raising=False)
    monkeypatch.delenv("SWEAT_LLM_SECONDARY", raising=False)
    monkeypatch.delenv("SWEAT_LLM_TERTIARY", raising=False)
    monkeypatch.setenv("SWEAT_CODER_PRIMARY", "codex_cli")
    monkeypatch.setenv("SWEAT_CODER_SECONDARY", "gemini_cli")
    monkeypatch.setenv("SWEAT_CODER_TERTIARY", "ollama")
    order = _resolve_main_alias_order()
    assert order[:3] == ["codex_cli", "gemini_cli", "ollama"]


def test_main_llm_explicit_policy_overrides(monkeypatch):
    monkeypatch.setenv("SWEAT_LLM_PRIMARY", "gemini_cli")
    monkeypatch.setenv("SWEAT_LLM_SECONDARY", "minimax_api")
    monkeypatch.setenv("SWEAT_LLM_TERTIARY", "ollama")
    order = _resolve_main_alias_order()
    assert order[:3] == ["gemini_cli", "minimax_api", "ollama"]
