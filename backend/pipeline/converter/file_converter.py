"""Convert downloaded legal documents into viewer-ready PDF files."""

from __future__ import annotations

import logging
import mimetypes
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import fitz
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PDF_SUFFIX = ".pdf"
WORD_SUFFIXES = {".doc", ".docx", ".rtf", ".odt"}
SPREADSHEET_SUFFIXES = {".xlsx", ".xls", ".ods"}
PRESENTATION_SUFFIXES = {".pptx", ".ppt", ".odp"}
TEXT_SUFFIXES = {".txt", ".html", ".htm"}
CONVERTIBLE_SUFFIXES = WORD_SUFFIXES | SPREADSHEET_SUFFIXES | PRESENTATION_SUFFIXES | TEXT_SUFFIXES


class DocumentConversionError(RuntimeError):
    """Raised when a source document cannot be converted into PDF."""


@dataclass(slots=True)
class ConversionResult:
    source_path: Path
    download_path: Path
    pdf_path: Path
    media_type: str
    engine: str
    converted: bool


def is_valid_pdf(pdf_path: Path) -> bool:
    """Return True when the file is a readable PDF, not just a `.pdf` filename."""
    try:
        with pdf_path.open("rb") as handle:
            header = handle.read(5)
        if header != b"%PDF-":
            return False

        doc = fitz.open(str(pdf_path))
        try:
            return doc.page_count >= 1
        finally:
            doc.close()
    except Exception:
        return False


def infer_extension(url: str, content_type: str | None, fallback_name: str) -> str:
    """Infer a source extension from response metadata."""
    parsed = urlparse(url)
    url_ext = Path(parsed.path).suffix.lower()
    if url_ext:
        return url_ext

    if content_type:
        mime = content_type.split(";", 1)[0].strip().lower()
        mime_map = {
            "application/pdf": ".pdf",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/rtf": ".rtf",
            "text/rtf": ".rtf",
            "text/plain": ".txt",
            "text/html": ".html",
        }
        if mime in mime_map:
            return mime_map[mime]
        guessed = mimetypes.guess_extension(mime)
        if guessed:
            return guessed.lower()

    fallback_ext = Path(fallback_name).suffix.lower()
    return fallback_ext or ".bin"


def convert_to_pdf(source_path: Path, output_pdf_path: Path, overwrite: bool = False) -> tuple[str, bool]:
    """Ensure `output_pdf_path` exists as a PDF representation of `source_path`."""
    source = source_path.resolve()
    target = output_pdf_path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not overwrite:
        return "cached", source.suffix.lower() != PDF_SUFFIX

    suffix = source.suffix.lower()
    if suffix == PDF_SUFFIX:
        if not is_valid_pdf(source):
            if _looks_like_html(source):
                _convert_html_like_file(source, target)
                return "html-fallback", True
            raise DocumentConversionError(f"Downloaded file is not a valid PDF: {source.name}")
        if source != target:
            shutil.copy2(source, target)
        return "copied-pdf", False

    if suffix == ".docx":
        try:
            _convert_with_docx2pdf(source, target)
            return "docx2pdf", True
        except DocumentConversionError:
            logger.warning("docx2pdf failed for %s; falling back to LibreOffice", source)

    if suffix in TEXT_SUFFIXES and _find_libreoffice_binary() is None:
        if suffix in {".html", ".htm"}:
            _convert_html_like_file(source, target)
            return "html-fallback", True
        _convert_text_like_file(source, target)
        return "pymupdf-text", True

    if suffix in CONVERTIBLE_SUFFIXES:
        _convert_with_libreoffice(source, target.parent)
        expected = target.parent / f"{source.stem}.pdf"
        if expected != target:
            if not expected.exists():
                raise DocumentConversionError(
                    f"Expected PDF was not created for {source.name}: {expected}"
                )
            shutil.move(str(expected), str(target))
        elif not target.exists():
            raise DocumentConversionError(
                f"LibreOffice reported success but PDF was not created: {target}"
            )
        return "libreoffice", True

    raise DocumentConversionError(
        f"Unsupported file type for PDF conversion: {source.suffix or '<no extension>'}"
    )


def _convert_with_docx2pdf(source: Path, target: Path) -> None:
    try:
        from docx2pdf import convert  # type: ignore
    except ImportError as exc:
        raise DocumentConversionError("docx2pdf is not installed.") from exc

    try:
        convert(str(source), str(target))
    except Exception as exc:
        raise DocumentConversionError(f"docx2pdf failed for {source.name}: {exc}") from exc

    if not target.exists():
        raise DocumentConversionError(f"docx2pdf did not create {target}")


def _convert_with_libreoffice(source: Path, output_dir: Path) -> None:
    soffice = _find_libreoffice_binary()
    if soffice is None:
        raise DocumentConversionError(
            "LibreOffice was not found. Install LibreOffice and expose `soffice` in PATH."
        )

    with tempfile.TemporaryDirectory(prefix="legalai-convert-") as temp_name:
        temp_dir = Path(temp_name)
        temp_source = temp_dir / source.name
        shutil.copy2(source, temp_source)
        command = [
            str(soffice),
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(temp_source),
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip() or "no output"
            raise DocumentConversionError(
                f"LibreOffice failed for {source.name} with exit code {completed.returncode}: {details}"
            )


def _find_libreoffice_binary() -> Path | None:
    candidates: Iterable[str | Path | None] = (
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        Path("C:/Program Files/LibreOffice/program/soffice.exe"),
        Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
    )
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            return path
    return None


def _convert_text_like_file(source: Path, target: Path) -> None:
    text = source.read_text(encoding="utf-8", errors="ignore")
    text = " ".join(text.split()) or f"Converted from {source.name}"

    _write_text_pdf(text, target)


def _looks_like_html(source: Path) -> bool:
    sample = source.read_text(encoding="utf-8", errors="ignore")[:2048].lower()
    return "<html" in sample or "<!doctype html" in sample


def _convert_html_like_file(source: Path, target: Path) -> None:
    raw_html = source.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    text = text or f"Converted from HTML source {source.name}"

    _write_text_pdf(text, target)


def _write_text_pdf(text: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open()
    page_width = 595
    page_height = 842
    margin = 50
    line_height = 14
    max_chars = 90

    lines: list[str] = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        while len(paragraph) > max_chars:
            split_at = paragraph.rfind(" ", 0, max_chars)
            if split_at <= 0:
                split_at = max_chars
            lines.append(paragraph[:split_at].strip())
            paragraph = paragraph[split_at:].strip()
        lines.append(paragraph)

    y = margin
    page = doc.new_page(width=page_width, height=page_height)
    for line in lines:
        if y > page_height - margin:
            page = doc.new_page(width=page_width, height=page_height)
            y = margin
        page.insert_text((margin, y), line, fontsize=11, fontname="helv")
        y += line_height

    doc.save(str(target))
    doc.close()
