from typing import TypedDict, List, Optional, Dict, Any

class AgentState(TypedDict):
    # Input
    question: str
    domain: Optional[str]
    conversation_history: List[Dict[str, str]]

    # Pipeline state
    rewritten_query: str
    predicted_domain: str
    wiki_results: List[Dict[str, Any]]
    doc_results: List[Dict[str, Any]]
    merged_context: str
    citations: List[Dict[str, Any]]

    # Output
    answer: str
    confidence: str             # "high" | "medium" | "low"
    follow_up: str
    error: Optional[str]
