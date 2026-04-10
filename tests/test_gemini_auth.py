# Test Gemini integration with API key
import sys
import os
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.llm import get_llm
from langchain_core.messages import HumanMessage

def test_gemini():
    print("Checking environment...")
    if "GEMINI_API_KEY" in os.environ:
        print("GEMINI_API_KEY is set (GOOD)")
    else:
        print("GEMINI_API_KEY is MISSING (BAD)")
        
    print(f"Gemini binary: {shutil.which('gemini')}")
    
    print("\nInitializing LLM...")
    llm = get_llm()
    print(f"LLM Type: {llm}")
    
    print("\nSending prompt: 'What is 2+2?'")
    try:
        response = llm.invoke([HumanMessage(content="What is 2+2?")])
        print(f"Response: {response.content}")
        print("SUCCESS!")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    test_gemini()
