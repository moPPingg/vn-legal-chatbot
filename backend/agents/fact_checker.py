import logging
from typing import Dict, Any
from backend.agents.state import AgentState
from backend.retrieval.citation_builder import build_citation

logger = logging.getLogger(__name__)

def run(state: AgentState) -> Dict[str, Any]:
    logger.info("--- NODE: fact_checker ---")
    doc_results = state.get("doc_results", [])
    
    citations = []
    
    # Check if the retrieved documents are still valid.
    # We will build citations and append validity info.
    for doc in doc_results:
        citation = build_citation(doc)
        citations.append(citation)
        
        # If any major document is invalid, we might want to flag it or add a warning to the LLM context.
        # For simplicity, we just pass the citations to the state.
        
    return {
        "citations": citations
    }
