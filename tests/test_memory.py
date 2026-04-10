import sys
import os
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.memory import get_memory

def test_vector_memory():
    print("Initializing Vector Memory...")
    try:
        memory = get_memory()
        print(f"Memory initialized with embeddings: {memory.embeddings}")
    except Exception as e:
        print(f"Failed to initialize memory: {e}")
        return

    # Test Data
    test_fact = "The project codename is Titan Genesis."
    metadata = {"source": "test_script", "importance": "high"}

    print(f"\nSaving fact: '{test_fact}'")
    try:
        memory.save_context(test_fact, metadata)
        print("Fact saved.")
    except Exception as e:
        print(f"Failed to save context: {e}")
        return

    # Retrieval
    query = "What is the project codename?"
    print(f"\nQuerying: '{query}'")
    try:
        results = memory.retrieve_context(query, k=1)
        print(f"Retrieved: {results}")
        
        if results and "Titan Genesis" in results[0]:
            print("\n✅ SUCCESS: Memory retrieval verified.")
        else:
            print("\n❌ FAILURE: retrieved content did not match expected fact.")
            
    except Exception as e:
        print(f"Failed to retrieve context: {e}")

if __name__ == "__main__":
    test_vector_memory()
