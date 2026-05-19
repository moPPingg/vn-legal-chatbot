"""Helpers to stage crawler downloads and normalize them into PDFs."""

from __future__ import annotations

import shutil
from pathlib import Path

from .file_converter import ConversionResult, convert_to_pdf


def normalize_downloaded_document(
    temp_file: Path,
    download_dir: Path,
    pdf_dir: Path,
    final_stem: str,
    media_type: str,
    overwrite: bool = False,
) -> ConversionResult:
    """Move a crawler-downloaded file into permanent storage and ensure a PDF exists."""
    download_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    download_path = download_dir / f"{final_stem}{temp_file.suffix.lower()}"
    pdf_path = pdf_dir / f"{final_stem}.pdf"

    if overwrite or not download_path.exists():
        shutil.copy2(temp_file, download_path)

    engine, converted = convert_to_pdf(download_path, pdf_path, overwrite=overwrite)
    return ConversionResult(
        source_path=temp_file.resolve(),
        download_path=download_path,
        pdf_path=pdf_path,
        media_type=media_type,
        engine=engine,
        converted=converted,
    )
