"""Chunker — splits documents into overlapping chunks with metadata (data_processing.md §2)."""
from __future__ import annotations
import logging
from typing import List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

def chunk_documents(
    df: pd.DataFrame,
    chunk_size: int = 1500,
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """
    Chunk each document's content_text. Returns list of dicts with:
      id, text, law_type, title, doc_id, so_ky_hieu
    """
    docs: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        text = row.get("content_text", "")
        if not text or len(text) < 50:
            continue
        title = str(row.get("title", ""))
        so_ky_hieu = str(row.get("so_ky_hieu", ""))
        law_type = str(row.get("law_type", "khác"))
        doc_id = str(row["id"])
        start = 0
        i = 0
        while start < len(text):
            chunk = text[start : start + chunk_size].strip()
            if chunk:
                docs.append({
                    "id": f"{doc_id}_c{i}",
                    "text": chunk,
                    "law_type": law_type,
                    "title": title,
                    "doc_id": doc_id,
                    "so_ky_hieu": so_ky_hieu,
                })
                i += 1
            start += chunk_size - chunk_overlap
    logger.info("Chunked into %d pieces", len(docs))
    return docs
