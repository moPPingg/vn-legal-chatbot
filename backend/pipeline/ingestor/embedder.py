import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.app.config import settings

logger = logging.getLogger(__name__)
_model: Optional[SentenceTransformer] = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully.")
    return _model

def embed_texts(texts: List[str], show_progress: bool = True) -> np.ndarray:
    """Embed a list of texts into numpy arrays."""
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=show_progress)

def embed_query(text: str) -> np.ndarray:
    """Embed a single query."""
    model = get_model()
    return model.encode(text, normalize_embeddings=True)
