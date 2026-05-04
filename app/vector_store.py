"""
Vector Store — manages ChromaDB collection with sentence-transformer embeddings.

Implements pipeline.md §3.2 (Retrieval / RAG):
  - Embedding generation
  - Vector search with law_type filtering
  - Top-K context retrieval
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.config import CHROMA_DIR, EMBEDDING_MODEL, RAG_TOP_K

logger = logging.getLogger(__name__)

# ── Singleton instances ───────────────────────────────────────────────────────
_embedder: Optional[SentenceTransformer] = None
_client: Optional[chromadb.ClientAPI] = None
_collection: Optional[chromadb.Collection] = None

COLLECTION_NAME = "vietnamese_legal"


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded ✓")
    return _embedder


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection() -> chromadb.Collection:
    """Return (or create) the ChromaDB collection."""
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def embed_text(text: str) -> List[float]:
    """Generate an embedding vector for a single text."""
    model = _get_embedder()
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Batch-embed a list of texts."""
    model = _get_embedder()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=True).tolist()


# ── Ingestion ─────────────────────────────────────────────────────────────────

def ingest_documents(docs: List[Dict[str, Any]], batch_size: int = 256) -> int:
    """
    Ingest prepared documents into ChromaDB.
    Skips documents that are already in the collection.
    Returns the number of newly added documents.
    """
    collection = get_collection()
    existing_count = collection.count()

    if existing_count > 0:
        logger.info("Collection already has %d documents, skipping ingestion.", existing_count)
        return 0

    total_added = 0
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        ids = [d["id"] for d in batch]
        texts = [d["text"] for d in batch]
        metadatas = [
            {
                "law_type": d["law_type"],
                "title": d["title"],
                "doc_id": d["doc_id"],
                "so_ky_hieu": d.get("so_ky_hieu", ""),
            }
            for d in batch
        ]

        embeddings = embed_texts(texts)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total_added += len(batch)
        logger.info("Ingested %d / %d chunks", total_added, len(docs))

    logger.info("Ingestion complete. Total chunks: %d", total_added)
    return total_added


# ── Search (pipeline.md §3.2) ────────────────────────────────────────────────

def search(
    question: str,
    law_type: Optional[str] = None,
    top_k: int = RAG_TOP_K,
) -> List[Dict[str, Any]]:
    """
    Vector search with optional law_type filter.

    Returns a list of dicts with keys: text, title, doc_id, so_ky_hieu, law_type, score.
    """
    collection = get_collection()

    if collection.count() == 0:
        logger.warning("Collection is empty — no documents to search.")
        return []

    query_embedding = embed_text(question)

    where_filter = None
    if law_type and law_type != "khác":
        where_filter = {"law_type": law_type}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    hits: List[Dict[str, Any]] = []
    if results and results["documents"]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append(
                {
                    "text": doc,
                    "title": meta.get("title", ""),
                    "doc_id": meta.get("doc_id", ""),
                    "so_ky_hieu": meta.get("so_ky_hieu", ""),
                    "law_type": meta.get("law_type", ""),
                    "score": 1 - dist,  # cosine distance → similarity
                }
            )

    return hits


def get_stats() -> Dict[str, Any]:
    """Return basic collection statistics."""
    collection = get_collection()
    return {
        "total_chunks": collection.count(),
        "collection_name": COLLECTION_NAME,
    }
