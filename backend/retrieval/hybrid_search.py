import logging
import unicodedata
from typing import List, Dict, Any, Optional
from .qdrant_client import QdrantRetriever

logger = logging.getLogger(__name__)


def _normalize_text(value: str) -> str:
    value = value.replace("Đ", "D").replace("đ", "d")
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    return " ".join(value.lower().split())


def _contains_phrase(text: str, phrase: str) -> bool:
    text_tokens = text.split()
    phrase_tokens = phrase.split()
    if not phrase_tokens or len(phrase_tokens) > len(text_tokens):
        return False
    window = len(phrase_tokens)
    return any(text_tokens[i : i + window] == phrase_tokens for i in range(len(text_tokens) - window + 1))


def _lexical_boost(query: str, result: Dict[str, Any]) -> float:
    metadata = result.get("metadata", {})
    haystack = " ".join(
        [
            metadata.get("article_header", ""),
            metadata.get("ten_van_ban", ""),
            result.get("text", ""),
        ]
    )
    normalized_query = _normalize_text(query)
    normalized_haystack = _normalize_text(haystack)
    haystack_tokens = set(normalized_haystack.split())

    boost = 0.0
    query_terms = [term for term in normalized_query.split() if len(term) >= 2]
    unique_terms = set(query_terms)

    for term in unique_terms:
        if term in haystack_tokens:
            boost += 0.08

    # Vehicle-specific hinting helps split Article 5 (o to) from Article 6 (xe may).
    if _contains_phrase(normalized_query, "o to") and _contains_phrase(normalized_haystack, "o to"):
        boost += 0.35
    if _contains_phrase(normalized_query, "xe may") and _contains_phrase(normalized_haystack, "xe may"):
        boost += 0.35

    return boost

class LegalSearcher:
    def __init__(self):
        self.retriever = QdrantRetriever()

    def search(self, query: str, domain_filter: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a search. For now, it's a dense vector search.
        In the future, this can combine BM25 and use a Cross-Encoder for reranking.
        """
        logger.info(f"Searching for '{query}' with domain filter '{domain_filter}'...")
        
        filters = {}
        if domain_filter:
            filters["domain"] = domain_filter
            
        # Dense search
        results = self.retriever.dense_search(query, limit=limit, filters=filters)
        
        for result in results:
            result["score"] = result.get("score", 0.0) + _lexical_boost(query, result)
        results.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        
        return results
