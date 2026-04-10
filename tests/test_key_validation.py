import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.llm import _is_likely_real_key as llm_key_ok
from src.utils.memory import _is_likely_real_key as mem_key_ok


def test_key_validation_rejects_placeholders():
    for fn in (llm_key_ok, mem_key_ok):
        assert fn("sk-proj-FAKE") is False
        assert fn("your_api_key_here") is False
        assert fn("dummy-token") is False


def test_key_validation_accepts_non_placeholder():
    for fn in (llm_key_ok, mem_key_ok):
        assert fn("sk-proj-abc123-real-looking") is True
