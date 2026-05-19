import logging
from typing import Dict, Any
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)

def run(state: AgentState) -> Dict[str, Any]:
    logger.info("--- NODE: legal_analyzer ---")
    doc_results = state.get("doc_results", [])
    wiki_results = state.get("wiki_results", [])
    
    # Merge context to feed to LLM
    merged_context = ""
    if wiki_results:
        merged_context += "--- WIKI KNOWLEDGE ---\n"
        for w in wiki_results:
            merged_context += f"{w}\n"
            
    if doc_results:
        merged_context += "\n--- LEGAL DOCUMENTS ---\n"
        for i, doc in enumerate(doc_results):
            header = doc.get("metadata", {}).get("article_header", "")
            so_hieu = doc.get("metadata", {}).get("so_hieu", "")
            merged_context += f"Document {i+1} [{so_hieu} - {header}]:\n{doc.get('text', '')}\n\n"
            
    if not merged_context.strip():
        merged_context = "No relevant legal context found."
        
    return {
        "merged_context": merged_context
    }
