import logging
from typing import Dict, Any
from backend.agents.state import AgentState
from backend.retrieval.hybrid_search import LegalSearcher

logger = logging.getLogger(__name__)

def run(state: AgentState) -> Dict[str, Any]:
    logger.info("--- NODE: legal_retriever ---")
    query = state.get("rewritten_query", state.get("question", ""))
    domain = state.get("predicted_domain")
    
    searcher = LegalSearcher()
    
    # We could search a wiki collection if it existed.
    # For now, we only have legal_docs, so wiki_results is empty or mocked.
    wiki_results = [] 
    
    # Search document chunks
    doc_results = searcher.search(query=query, domain_filter=domain, limit=3)
    
    return {
        "wiki_results": wiki_results,
        "doc_results": doc_results
    }
