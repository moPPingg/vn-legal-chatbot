"""
Data Loader — reads parquet files and prepares documents for ingestion.

Handles the legal document dataset from vietnamese-legal-documents/:
  - metadata.parquet  (153K rows)
  - content.parquet   (178K rows — HTML bodies)
  - relationships.parquet (897K rows)
"""

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional

import pandas as pd
from bs4 import BeautifulSoup

from app.config import DATA_DIR

logger = logging.getLogger(__name__)


# ── Vietnamese domain mapping ────────────────────────────────────────────────
# Maps linh_vuc (legal field) keywords to our law_type categories
_DOMAIN_MAP: Dict[str, str] = {
    "hình sự": "hình sự",
    "tố tụng hình sự": "hình sự",
    "dân sự": "dân sự",
    "tố tụng dân sự": "dân sự",
    "lao động": "lao động",
    "việc làm": "lao động",
    "hành chính": "hành chính",
    "xử lý vi phạm hành chính": "hành chính",
    "thương mại": "thương mại",
    "doanh nghiệp": "thương mại",
    "đất đai": "đất đai",
    "nhà ở": "đất đai",
    "bất động sản": "đất đai",
    "hôn nhân": "hôn nhân gia đình",
    "gia đình": "hôn nhân gia đình",
    "thuế": "thuế",
    "tài chính": "thuế",
    "giáo dục": "giáo dục",
    "đào tạo": "giáo dục",
    "y tế": "y tế",
    "dược": "y tế",
    "sức khỏe": "y tế",
}


def _clean_html(html: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    if not html or not isinstance(html, str):
        return ""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator="\n", strip=True)
    # collapse excessive whitespace / blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _classify_domain(row: pd.Series) -> str:
    """Classify a metadata row into a law_type using linh_vuc + nganh fields."""
    fields = []
    for col in ("linh_vuc", "nganh"):
        val = row.get(col)
        if isinstance(val, str) and val.strip():
            fields.append(val.strip().lower())
    combined = " ".join(fields)
    for keyword, domain in _DOMAIN_MAP.items():
        if keyword in combined:
            return domain
    return "khác"


def load_metadata() -> pd.DataFrame:
    """Load the metadata parquet and add a 'law_type' column."""
    path = DATA_DIR / "metadata.parquet"
    logger.info("Loading metadata from %s", path)
    df = pd.read_parquet(path)
    df["law_type"] = df.apply(_classify_domain, axis=1)
    logger.info("Loaded %d metadata rows", len(df))
    return df


def load_content() -> pd.DataFrame:
    """Load document content parquet and clean HTML → plain text."""
    path = DATA_DIR / "content.parquet"
    logger.info("Loading content from %s", path)
    df = pd.read_parquet(path)
    df["content_text"] = df["content_html"].apply(_clean_html)
    logger.info("Loaded %d content rows", len(df))
    return df


def prepare_documents(
    max_docs: Optional[int] = None,
    chunk_size: int = 1500,
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """
    Join metadata + content, chunk the text, and return a list of dicts
    ready for vector-store ingestion.

    Each dict has keys:
      - id:        unique chunk id
      - text:      chunk text
      - law_type:  classified domain
      - title:     document title
      - doc_id:    original document id
      - so_ky_hieu: document number
    """
    meta = load_metadata()
    content = load_content()

    # Ensure id columns have the same type for the join
    meta["id"] = meta["id"].astype(str)
    content["id"] = content["id"].astype(str)

    merged = meta.merge(content[["id", "content_text"]], on="id", how="inner")
    logger.info("Merged dataset: %d documents", len(merged))

    if max_docs:
        merged = merged.head(max_docs)

    docs: List[Dict[str, Any]] = []

    for _, row in merged.iterrows():
        text = row.get("content_text", "")
        if not text or len(text) < 50:
            continue

        # Simple chunking with overlap
        chunks = _chunk_text(text, chunk_size, chunk_overlap)
        title = row.get("title", "")
        so_ky_hieu = row.get("so_ky_hieu", "")
        law_type = row.get("law_type", "khác")
        doc_id = str(row["id"])

        for i, chunk in enumerate(chunks):
            docs.append(
                {
                    "id": f"{doc_id}_chunk_{i}",
                    "text": chunk,
                    "law_type": law_type,
                    "title": title,
                    "doc_id": doc_id,
                    "so_ky_hieu": so_ky_hieu,
                }
            )

    logger.info("Prepared %d chunks from %d documents", len(docs), len(merged))
    return docs


def _chunk_text(text: str, size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks of roughly `size` characters."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += size - overlap
    return chunks
