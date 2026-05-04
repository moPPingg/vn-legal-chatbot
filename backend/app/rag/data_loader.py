"""Data Loader — OPTIMIZED: reads only needed rows from parquet files."""
from __future__ import annotations
import logging, re
from typing import Dict
import pandas as pd
from bs4 import BeautifulSoup
from app.config import DATA_DIR

logger = logging.getLogger(__name__)

_DOMAIN_MAP: Dict[str, str] = {
    "hình sự": "hình sự", "tố tụng hình sự": "hình sự",
    "dân sự": "dân sự", "tố tụng dân sự": "dân sự",
    "lao động": "lao động", "việc làm": "lao động",
    "hành chính": "hành chính", "xử lý vi phạm hành chính": "hành chính",
    "thương mại": "thương mại", "doanh nghiệp": "thương mại",
    "đất đai": "đất đai", "nhà ở": "đất đai", "bất động sản": "đất đai",
    "hôn nhân": "hôn nhân gia đình", "gia đình": "hôn nhân gia đình",
    "thuế": "thuế", "tài chính": "thuế",
    "giáo dục": "giáo dục", "đào tạo": "giáo dục",
    "y tế": "y tế", "dược": "y tế", "sức khỏe": "y tế",
    "giao thông": "giao thông", "đường bộ": "giao thông",
}

def _clean_html(html: str) -> str:
    if not html or not isinstance(html, str):
        return ""
    text = BeautifulSoup(html, "lxml").get_text(separator="\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def _classify_domain(row: pd.Series) -> str:
    combined = " ".join(
        str(row.get(c, "")).strip().lower() for c in ("linh_vuc", "nganh") if row.get(c)
    )
    for kw, domain in _DOMAIN_MAP.items():
        if kw in combined:
            return domain
    return "khác"

def load_and_merge(max_docs: int | None = None) -> pd.DataFrame:
    """
    OPTIMIZED: Load metadata first (small file), limit rows,
    then load only matching content rows from the large parquet.
    """
    # Step 1: Load metadata (only 13MB)
    logger.info("Loading metadata...")
    meta = pd.read_parquet(DATA_DIR / "metadata.parquet")
    meta["law_type"] = meta.apply(_classify_domain, axis=1)
    meta["id"] = meta["id"].astype(str)

    # Step 2: Limit early (before loading 392MB content!)
    if max_docs:
        meta = meta.head(max_docs)

    logger.info("Metadata loaded: %d docs", len(meta))

    # Step 3 & 4: Load content efficiently using filters (pushdown to pyarrow)
    needed_ids = list(meta["id"])
    logger.info("Loading content efficiently with filters for %d IDs...", len(needed_ids))
    
    # Use filters to only load matching IDs from disk, preventing full RAM usage
    content = pd.read_parquet(
        DATA_DIR / "content.parquet",
        columns=["id", "content_html"],
        filters=[("id", "in", needed_ids)],
        engine="pyarrow"
    )
    content["id"] = content["id"].astype(str)
    
    logger.info("Loaded and filtered content to %d rows", len(content))

    # Step 5: Clean HTML
    logger.info("Cleaning HTML...")
    content["content_text"] = content["content_html"].apply(_clean_html)

    # Step 6: Merge
    merged = meta.merge(content[["id", "content_text"]], on="id", how="inner")
    logger.info("Final dataset: %d documents", len(merged))
    return merged
