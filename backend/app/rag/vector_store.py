"""Vector Store — FAISS index with metadata (teckstack.md §3.4, pipeline.md §3.2)."""
from __future__ import annotations
import json, logging, pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from app.config import FAISS_DIR
from app.rag.embedder import embed_texts, embed_query

logger = logging.getLogger(__name__)

INDEX_FILE = "index.faiss"
META_FILE = "metadata.pkl"

_index: Optional[faiss.Index] = None
_metadata: Optional[List[Dict[str, Any]]] = None


def _ensure_dir():
    FAISS_DIR.mkdir(parents=True, exist_ok=True)


def save_index(index: faiss.Index, metadata: List[Dict[str, Any]]):
    """Persist FAISS index and metadata to disk."""
    _ensure_dir()
    faiss.write_index(index, str(FAISS_DIR / INDEX_FILE))
    with open(FAISS_DIR / META_FILE, "wb") as f:
        pickle.dump(metadata, f)
    logger.info("Saved FAISS index (%d vectors) + metadata", index.ntotal)


def load_index() -> tuple[faiss.Index, List[Dict[str, Any]]]:
    """Load persisted FAISS index and metadata."""
    global _index, _metadata
    if _index is not None and _metadata is not None:
        return _index, _metadata
    idx_path = FAISS_DIR / INDEX_FILE
    meta_path = FAISS_DIR / META_FILE
    if not idx_path.exists():
        raise FileNotFoundError(f"FAISS index not found at {idx_path}. Run ingest first.")
    _index = faiss.read_index(str(idx_path))
    with open(meta_path, "rb") as f:
        _metadata = pickle.load(f)
    logger.info("Loaded FAISS index (%d vectors)", _index.ntotal)
    return _index, _metadata


def build_index(docs: List[Dict[str, Any]], batch_size: int = 512) -> int:
    """Build FAISS index from document chunks. Returns number of vectors."""
    if (FAISS_DIR / INDEX_FILE).exists():
        idx, meta = load_index()
        logger.info("Index already exists with %d vectors. Skipping.", idx.ntotal)
        return idx.ntotal

    texts = [d["text"] for d in docs]
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embs = embed_texts(batch)
        all_embeddings.append(embs)
        logger.info("Embedded %d / %d", min(i + batch_size, len(texts)), len(texts))

    embeddings = np.vstack(all_embeddings).astype("float32")
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)  # Inner product (cosine with normalized vectors)
    index.add(embeddings)

    metadata = [
        {"law_type": d["law_type"], "title": d["title"], "doc_id": d["doc_id"],
         "so_ky_hieu": d.get("so_ky_hieu", ""), "text": d["text"]}
        for d in docs
    ]
    save_index(index, metadata)
    return index.ntotal


def get_stats() -> Dict[str, Any]:
    """Return index statistics."""
    try:
        idx, meta = load_index()
        return {"total_vectors": idx.ntotal, "status": "ready"}
    except FileNotFoundError:
        return {"total_vectors": 0, "status": "not_initialized"}
