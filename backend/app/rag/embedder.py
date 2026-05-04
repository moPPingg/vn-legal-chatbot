"""Embedder — sentence-transformers embedding (data_processing.md §3)."""
from __future__ import annotations
import logging
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)
_model: Optional[SentenceTransformer] = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded ✓")
    return _model

def embed_texts(texts: List[str], show_progress: bool = True) -> np.ndarray:
    """Embed a list of texts → numpy array of shape (n, dim)."""
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=show_progress)

def embed_query(text: str) -> np.ndarray:
    """Embed a single query → numpy array of shape (dim,)."""
    model = get_model()
    return model.encode(text, normalize_embeddings=True)
