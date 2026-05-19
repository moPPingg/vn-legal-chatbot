"""Helpers for uploaded files that need to become viewer-ready PDFs."""

from __future__ import annotations

from pathlib import Path

import fitz
from fastapi import HTTPException, UploadFile

from backend.pipeline.converter.file_converter import (
    DocumentConversionError,
    convert_to_pdf,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_ROOT / "storage" / "uploads"
PDF_DIR = BACKEND_ROOT / "storage" / "pdfs" / "uploaded"

SUPPORTED_UPLOAD_SUFFIXES = {
    ".pdf",
    ".docx",
    ".doc",
    ".rtf",
    ".odt",
    ".xlsx",
    ".xls",
    ".ods",
    ".pptx",
    ".ppt",
    ".odp",
    ".txt",
    ".html",
    ".htm",
}


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload(file: UploadFile) -> Path:
    ensure_dirs()
    filename = Path(file.filename or "upload.bin").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dinh dang {suffix or '<none>'} khong duoc ho tro. "
                f"Ho tro: {', '.join(sorted(SUPPORTED_UPLOAD_SUFFIXES))}"
            ),
        )

    save_path = UPLOAD_DIR / filename
    content = await file.read()
    save_path.write_bytes(content)
    return save_path


def convert_uploaded_file(source_path: Path) -> Path:
    ensure_dirs()
    output_path = PDF_DIR / f"{source_path.stem}.pdf"
    try:
        convert_to_pdf(source_path, output_path, overwrite=True)
    except DocumentConversionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return output_path


def get_pdf_info(pdf_path: Path) -> dict:
    doc = fitz.open(str(pdf_path))
    try:
        preview = doc[0].get_text()[:300] if doc.page_count else ""
        return {
            "filename": pdf_path.name,
            "page_count": doc.page_count,
            "file_size": pdf_path.stat().st_size,
            "first_page_preview": preview,
        }
    finally:
        doc.close()
