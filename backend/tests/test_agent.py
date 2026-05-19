import sys
import os
import logging
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.agents.graph import build_graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def test_graph():
    graph = build_graph()
    
    initial_state = {
        "question": "nồng độ cồn ô tô phạt bao nhiêu?",
        "conversation_history": []
    }
    
    print("--- STARTING AGENT PIPELINE ---")
    final_state = graph.invoke(initial_state)
    
    print("\n--- FINAL ANSWER ---")
    print(final_state.get("answer"))
    print("\n--- CONFIDENCE ---")
    print(final_state.get("confidence"))
    print("\n--- CITATIONS ---")
    for cit in final_state.get("citations", []):
        print(cit)

if __name__ == "__main__":
    test_graph()
