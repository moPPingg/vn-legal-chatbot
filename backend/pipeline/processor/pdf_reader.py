"""Read normalized PDF files with PyMuPDF."""

from __future__ import annotations

from pathlib import Path


class PdfReadError(RuntimeError):
    """Raised when a document cannot be read as PDF."""


def extract_text(pdf_path: str | Path, max_pages: int | None = None) -> str:
    path = Path(pdf_path)
    if path.suffix.lower() != ".pdf":
        raise PdfReadError(f"Expected a PDF file, got: {path.name}")

    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise PdfReadError("PyMuPDF is not installed. Run `pip install pymupdf`.") from exc

    try:
        doc = fitz.open(path)
    except Exception as exc:
        raise PdfReadError(f"Failed to open PDF {path}: {exc}") from exc

    texts: list[str] = []
    page_total = doc.page_count if max_pages is None else min(doc.page_count, max_pages)
    for page_index in range(page_total):
        texts.append(doc[page_index].get_text())
    doc.close()
    return "\n".join(texts).strip()
