import re
import unicodedata
from pathlib import Path

from backend.pipeline.converter import is_valid_pdf

PDF_BASE = Path(__file__).resolve().parents[1] / "storage" / "pdfs"


def sanitize_filename(so_hieu: str) -> str:
    normalized = so_hieu.replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r'[/\\:*?"<>|]', "-", normalized).strip("-")


def build_citation(chunk: dict, base_url: str = "http://localhost:8000") -> dict:
    meta = chunk.get("metadata", {})
    so_hieu = meta.get("so_hieu", "")
    domain = meta.get("domain", "giao_thong")
    filename = sanitize_filename(so_hieu) + ".pdf"

    pdf_local = PDF_BASE / domain / filename
    pdf_api_url = None
    if pdf_local.exists() and is_valid_pdf(pdf_local):
        pdf_api_url = f"{base_url}/api/document/{domain}/{filename}"

    return {
        "so_hieu": so_hieu,
        "ten_van_ban": meta.get("ten_van_ban", ""),
        "dieu": meta.get("article_header", ""),
        "trang": meta.get("page_number", 1),
        "pdf_url": pdf_api_url,
        "snippet": chunk.get("text", "")[:300],
        "still_valid": meta.get("tinh_trang", "") == "Còn hiệu lực",
        "domain": domain,
    }
