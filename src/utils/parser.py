import re
import json
from typing import Any, Dict, Optional, Tuple

def strip_think_blocks(text: str) -> str:
    if not text:
        return text
    return re.sub(r"<think>[\s\S]*?</think>\s*", "", text, flags=re.IGNORECASE).strip()


def extract_tool_call_from_markup(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse non-OpenAI wrapper formats, e.g. MiniMax:
    <minimax:tool_call><invoke name="write_file"><param name="path">src/a.py</param>...</invoke></minimax:tool_call>
    """
    if not text:
        return None

    cleaned = strip_think_blocks(text)
    m = re.search(r"<invoke\s+name=\"([^\"]+)\"\s*>([\s\S]*?)</invoke>", cleaned, re.IGNORECASE)
    if not m:
        return None

    tool_name = m.group(1).strip()
    inner = m.group(2)
    args = {}
    for pm in re.finditer(r"<param\s+name=\"([^\"]+)\"\s*>([\s\S]*?)</param>", inner, re.IGNORECASE):
        key = pm.group(1).strip()
        val = pm.group(2).strip()
        args[key] = val

    if not tool_name:
        return None
    return {"tool": tool_name, "args": args}


def extract_json_content(text: str) -> Any:
    """
    Robustly extracts JSON from a string, handling markdown code blocks
    and potential chatter.

    Args:
        text (str): The raw LLM output.

    Returns:
        dict: The parsed JSON object.

    Raises:
        ValueError: If no valid JSON structure is found or parsing fails.
    """
    if not text:
        raise ValueError("Empty input text.")

    text = strip_think_blocks(text.strip())

    # 1. Try to find a markdown JSON code block
    # Matches ```json { ... } ```
    json_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Robust decode scan: find first valid JSON object/array in mixed text
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            obj, _end = decoder.raw_decode(text[i:])
            return obj
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Could not extract valid JSON from response: {text[:100]}...")


def extract_coverage_percent(output: str) -> Optional[float]:
    """Extract line coverage percentage from common pytest-cov output."""
    if not output:
        return None

    patterns = [
        r"TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%",
        r"coverage\D+(\d+(?:\.\d+)?)%",
    ]

    for p in patterns:
        m = re.search(p, output, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                return None

    return None
