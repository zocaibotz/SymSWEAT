import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import AIMessage
from src.agents.workers import (
    _validate_tool_call,
    _is_path_in_workspace,
    _validate_pixel_package,
    _build_frontman_prompt,
    _extract_structured_tool_call,
)
from src.utils.parser import strip_think_blocks, extract_tool_call_from_markup


def test_validate_tool_call_accepts_valid_tool():
    ok, reason = _validate_tool_call(
        {"tool": "write_file", "args": {"path": "src/a.py", "content": "print(1)"}},
        {"write_file"},
    )
    assert ok is True
    assert reason == "ok"


def test_validate_tool_call_rejects_unknown_tool():
    ok, reason = _validate_tool_call(
        {"tool": "shell_exec", "args": {}},
        {"write_file", "read_file"},
    )
    assert ok is False
    assert "not allowed" in reason


def test_validate_tool_call_rejects_non_dict_args():
    ok, reason = _validate_tool_call(
        {"tool": "write_file", "args": "bad"},
        {"write_file"},
    )
    assert ok is False
    assert "args" in reason.lower()


def test_path_guard_rejects_escape_attempt():
    assert _is_path_in_workspace("src/app.py") is True
    assert _is_path_in_workspace("../../etc/passwd") is False

    ok, reason = _validate_tool_call(
        {"tool": "write_file", "args": {"path": "../../etc/passwd", "content": "x"}},
        {"write_file"},
    )
    assert ok is False
    assert "escapes workspace sandbox" in reason


def test_validate_pixel_package_schema():
    valid_payload = {
        "personas": [{"name": "Dev"}],
        "user_journey": ["Open app", "Click create"],
        "screens": [{"name": "Home"}],
        "style_tokens": {"primary": "#000"},
    }
    ok, reason = _validate_pixel_package(valid_payload)
    assert ok is True
    assert reason == "ok"

    bad_payload = {
        "personas": [],
        "screens": [],
        "style_tokens": {},
    }
    ok, reason = _validate_pixel_package(bad_payload)
    assert ok is False
    assert "Missing Pixel field" in reason


def test_frontman_prompt_contains_contract_requirements():
    prompt = _build_frontman_prompt({"screens": [{"name": "Home"}]})
    assert "write_file" in prompt
    assert "src/App.jsx" in prompt
    assert "exported default function App()" in prompt


def test_extract_structured_tool_call_from_tool_calls():
    msg = AIMessage(
        content="",
        additional_kwargs={
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "arguments": '{"path":"src/a.py","content":"print(1)"}',
                    },
                }
            ]
        },
    )
    out = _extract_structured_tool_call(msg, allow_json_fallback=False)
    assert out["tool"] == "write_file"
    assert out["args"]["path"] == "src/a.py"


def test_extract_structured_tool_call_rejects_when_strict_and_no_tool_calls():
    msg = AIMessage(content='{"tool":"write_file","args":{"path":"src/a.py","content":"x"}}')
    try:
        _extract_structured_tool_call(msg, allow_json_fallback=False)
        assert False, "expected strict mode failure"
    except ValueError:
        assert True


def test_strip_think_blocks_and_markup_tool_call_parser():
    raw = """
<think>
internal reasoning
</think>
<minimax:tool_call>
<invoke name=\"write_file\">
  <param name=\"path\">src/app.py</param>
  <param name=\"content\">print('ok')</param>
</invoke>
</minimax:tool_call>
"""
    cleaned = strip_think_blocks(raw)
    assert "<think>" not in cleaned
    tc = extract_tool_call_from_markup(cleaned)
    assert tc is not None
    assert tc["tool"] == "write_file"
    assert tc["args"]["path"] == "src/app.py"


def test_extract_structured_tool_call_from_minimax_markup():
    raw = """
<think>...</think>
<minimax:tool_call>
<invoke name=\"write_file\">
  <param name=\"path\">src/a.py</param>
  <param name=\"content\">print(1)</param>
</invoke>
</minimax:tool_call>
"""
    msg = AIMessage(content=raw)
    out = _extract_structured_tool_call(msg, allow_json_fallback=True)
    assert out["tool"] == "write_file"
    assert out["args"]["path"] == "src/a.py"
