# Test CLI wrappers
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.llm import get_llm, get_coder_llm

def test_wrappers():
    print("Testing get_llm()...")
    llm = get_llm()
    print(f"LLM Type: {llm._llm_type}")
    
    print("\nTesting get_coder_llm()...")
    coder = get_coder_llm()
    print(f"Coder Type: {coder._llm_type}")
    
    # We won't actually invoke them in CI/test environment to avoid subprocess calls hanging 
    # or failing auth, but this confirms the factory logic works.

if __name__ == "__main__":
    test_wrappers()
