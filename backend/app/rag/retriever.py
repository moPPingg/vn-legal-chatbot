"""Retriever — search FAISS with law_type filtering (pipeline.md §3.2)."""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.config import RAG_TOP_K
from app.rag.embedder import embed_query
from app.rag.vector_store import load_index

logger = logging.getLogger(__name__)


def search(
    question: str,
    law_type: Optional[str] = None,
    top_k: int = RAG_TOP_K,
) -> List[Dict[str, Any]]:
    """
    Embed question → search FAISS → filter by law_type → return top-k results.
    Each result has: text, title, doc_id, so_ky_hieu, law_type, score.
    """
    try:
        index, metadata = load_index()
    except FileNotFoundError:
        logger.warning("FAISS index not found")
        return []

    if index.ntotal == 0:
        return []

    query_vec = embed_query(question).astype("float32").reshape(1, -1)

    # Search more than needed so we can filter by law_type
    search_k = min(top_k * 5, index.ntotal)
    scores, indices = index.search(query_vec, search_k)

    hits: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        meta = metadata[idx]
        # Filter by law_type if specified
        if law_type and law_type != "khác" and meta["law_type"] != law_type:
            continue
        hits.append({
            "text": meta["text"],
            "title": meta["title"],
            "doc_id": meta["doc_id"],
            "so_ky_hieu": meta.get("so_ky_hieu", ""),
            "law_type": meta["law_type"],
            "score": float(score),
        })
        if len(hits) >= top_k:
            break

    logger.info("Retrieved %d documents (law_type=%s)", len(hits), law_type)
    return hits
