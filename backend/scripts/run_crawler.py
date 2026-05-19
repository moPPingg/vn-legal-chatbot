"""CLI for crawling documents and normalizing stored source files into PDFs."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.pipeline.converter import DocumentConversionError, normalize_downloaded_document

STORAGE_PDF = Path("storage/pdfs")
STORAGE_DOWNLOADS = Path("storage/downloads")


def normalize_existing_files(domain: str, overwrite: bool = False) -> list[dict]:
    pdf_dir = STORAGE_PDF / domain
    download_dir = STORAGE_DOWNLOADS / domain
    pdf_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    supported = {".pdf", ".doc", ".docx", ".rtf", ".odt", ".txt", ".html", ".htm"}

    for source in sorted(pdf_dir.iterdir()):
        if not source.is_file() or source.suffix.lower() not in supported:
            continue
        if source.suffix.lower() == ".pdf":
            continue

        try:
            normalized = normalize_downloaded_document(
                temp_file=source,
                download_dir=download_dir,
                pdf_dir=pdf_dir,
                final_stem=source.stem,
                media_type="application/octet-stream",
                overwrite=overwrite,
            )
            source.unlink(missing_ok=True)
            results.append(
                {
                    "name": source.name,
                    "pdf": normalized.pdf_path.name,
                    "engine": normalized.engine,
                    "ok": True,
                }
            )
        except DocumentConversionError as exc:
            results.append(
                {
                    "name": source.name,
                    "error": str(exc),
                    "ok": False,
                }
            )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run crawler or normalize existing source files")
    parser.add_argument("--domain", default="giao_thong")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--normalize-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.normalize_only:
        results = normalize_existing_files(args.domain, overwrite=args.overwrite)
        print(f"Normalized {len(results)} files in {args.domain}")
        for result in results:
            if result["ok"]:
                print(f"- {result['name']} -> {result['pdf']} [{result['engine']}]")
            else:
                print(f"- {result['name']} FAILED: {result['error']}")
        return

    from backend.pipeline.crawler.vbpl_crawler import PRIORITY_DOCUMENTS, crawl_documents

    asyncio.run(crawl_documents(domain=args.domain, documents=PRIORITY_DOCUMENTS, limit=args.limit))


if __name__ == "__main__":
    main()
