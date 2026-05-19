"""
Crawler for legal documents from vbpl.vn.

The current VBPL site has moved away from the old static pages that the legacy
scraper expected. This crawler therefore uses a stricter pipeline:

1. Prefer explicit `item_id` or `document_url` seeds.
2. Download the authoritative source page or file.
3. Validate whether the downloaded payload is a real PDF.
4. If the source is HTML, convert it into a viewer-friendly PDF so the frontend
   can still render citations reliably.
"""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from backend.pipeline.converter import (
    DocumentConversionError,
    infer_extension,
    is_valid_pdf,
    normalize_downloaded_document,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
STORAGE_PDF = BACKEND_ROOT / "storage" / "pdfs"
STORAGE_DOWNLOADS = BACKEND_ROOT / "storage" / "downloads"
STORAGE_RAW = BACKEND_ROOT / "storage" / "raw"

DELAY_SECONDS = 2
VBPL_BASE_URL = "https://vbpl.vn"
VBPL_CENTRAL_PAGE = "https://vbpl.vn/TW/Pages/vbpq-van-ban-goc.aspx?ItemID={item_id}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9",
}

# The old search endpoint is no longer reliable. Seed documents should include
# either `item_id` or `document_url` whenever possible.
PRIORITY_DOCUMENTS = [
    {
        "so_hieu": "168/2024/ND-CP",
        "slug": "168-2024-ND-CP",
        "item_id": "173920",
        "ten_van_ban": "Nghi dinh 168/2024/ND-CP",
        "ngay_ban_hanh": "31/12/2024",
        "tinh_trang": "Con hieu luc",
    },
    {
        "so_hieu": "100/2019/ND-CP",
        "slug": "100-2019-ND-CP",
        "item_id": "140152",
        "ten_van_ban": "Nghi dinh 100/2019/ND-CP",
        "ngay_ban_hanh": "30/12/2019",
        "tinh_trang": "Con hieu luc",
    },
    {"so_hieu": "123/2021/ND-CP", "slug": "123-2021-ND-CP"},
    {"so_hieu": "46/2016/ND-CP", "slug": "46-2016-ND-CP"},
    {"so_hieu": "15/2003/ND-CP", "slug": "15-2003-ND-CP"},
]


def sanitize_filename(so_hieu: str) -> str:
    normalized = so_hieu.replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r'[/\\:*?"<>|]', "-", normalized).strip("-")
    return normalized or "document"


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_only.lower().split())


def ensure_dirs(domain: str) -> None:
    (STORAGE_PDF / domain).mkdir(parents=True, exist_ok=True)
    (STORAGE_DOWNLOADS / domain).mkdir(parents=True, exist_ok=True)
    (STORAGE_RAW / domain).mkdir(parents=True, exist_ok=True)


def build_document_url(seed: dict) -> str | None:
    if seed.get("document_url"):
        return str(seed["document_url"])
    if seed.get("item_id"):
        return VBPL_CENTRAL_PAGE.format(item_id=seed["item_id"])
    return None


async def search_document(client: httpx.AsyncClient, so_hieu: str) -> dict | None:
    # Legacy fallback kept for completeness. It currently returns 404 on VBPL
    # for many requests, so `item_id` / `document_url` should be preferred.
    search_url = "https://vbpl.vn/pages/vbpq-toanvan.aspx"
    params = {"dvid": "13", "Keyword": so_hieu}

    try:
        resp = await client.get(search_url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        result = soup.select_one(".van-ban-item a, .result-item a, h3 a")
        if not result:
            print(f"  [WARN] Khong tim thay bang endpoint cu: {so_hieu}")
            return None

        href = result.get("href", "")
        title = result.get_text(strip=True)
        full_url = urljoin(VBPL_BASE_URL, href)
        return {"url": full_url, "title": title}
    except Exception as exc:
        print(f"  [WARN] Search endpoint cu that bai cho {so_hieu}: {exc}")
        return None


async def resolve_document(client: httpx.AsyncClient, seed: dict) -> dict | None:
    direct_url = build_document_url(seed)
    if direct_url:
        return {
            "url": direct_url,
            "title": seed.get("ten_van_ban", seed.get("so_hieu", "")),
            "item_id": seed.get("item_id"),
        }
    return await search_document(client, seed["so_hieu"])


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup.select("script, style, noscript"):
        element.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


async def extract_document_info(client: httpx.AsyncClient, seed: dict, url: str) -> dict:
    metadata = {
        "url": url,
        "ten_van_ban": seed.get("ten_van_ban", ""),
        "so_hieu": seed.get("so_hieu", ""),
        "ngay_ban_hanh": seed.get("ngay_ban_hanh", ""),
        "tinh_trang": seed.get("tinh_trang", "Khong xac dinh"),
        "pdf_url": seed.get("pdf_url"),
        "full_text": "",
        "item_id": seed.get("item_id"),
        "crawled_at": datetime.now().isoformat(),
        "source_kind": "seed",
    }

    try:
        resp = await client.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("title, h1")
        if title_el and not metadata["ten_van_ban"]:
            metadata["ten_van_ban"] = title_el.get_text(strip=True)

        text = _extract_text_from_html(html)
        metadata["full_text"] = text

        # If there is a direct PDF link in the rendered HTML, prefer it.
        pdf_link = soup.select_one("a[href$='.pdf'], a[href*='.pdf?'], a[download]")
        if pdf_link:
            href = pdf_link.get("href", "").strip()
            if href:
                metadata["pdf_url"] = urljoin(VBPL_BASE_URL, href)
                metadata["source_kind"] = "direct-pdf-link"
        else:
            # If no direct PDF is exposed, fall back to the page HTML itself.
            metadata["pdf_url"] = metadata["pdf_url"] or url
            metadata["source_kind"] = "html-fallback"

        return metadata
    except Exception as exc:
        print(f"  [ERR] Loi extract {url}: {exc}")
        return metadata


async def download_document(
    client: httpx.AsyncClient,
    document_url: str,
    domain: str,
    filename_stem: str,
) -> dict | None:
    pdf_path = STORAGE_PDF / domain / f"{filename_stem}.pdf"
    if pdf_path.exists() and is_valid_pdf(pdf_path):
        print(f"  [SKIP] PDF da ton tai: {pdf_path.name}")
        return {
            "pdf_path": str(pdf_path),
            "download_path": str(pdf_path),
            "engine": "cached",
            "source_url": document_url,
        }
    if pdf_path.exists():
        print(f"  [REPAIR] PDF ton tai nhung khong hop le: {pdf_path.name}")

    try:
        resp = await client.get(document_url, headers=HEADERS, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        extension = infer_extension(document_url, content_type, filename_stem)
        size_kb = len(resp.content) // 1024

        with tempfile.TemporaryDirectory(prefix="legalai-download-") as temp_name:
            temp_path = Path(temp_name) / f"{filename_stem}{extension}"
            temp_path.write_bytes(resp.content)
            normalized = normalize_downloaded_document(
                temp_file=temp_path,
                download_dir=STORAGE_DOWNLOADS / domain,
                pdf_dir=STORAGE_PDF / domain,
                final_stem=filename_stem,
                media_type=content_type,
                overwrite=True,
            )

        print(
            f"  [OK] Chuan hoa: {normalized.download_path.name} -> "
            f"{normalized.pdf_path.name} [{normalized.engine}] ({size_kb}KB)"
        )
        return {
            "pdf_path": str(normalized.pdf_path),
            "download_path": str(normalized.download_path),
            "engine": normalized.engine,
            "source_url": document_url,
        }
    except DocumentConversionError as exc:
        print(f"  [ERR] Loi convert tai lieu {document_url}: {exc}")
        return None
    except Exception as exc:
        print(f"  [ERR] Loi tai tai lieu {document_url}: {exc}")
        return None


async def crawl_documents(domain: str, documents: list[dict], limit: int = 5):
    ensure_dirs(domain)
    results = []

    async with httpx.AsyncClient(verify=False) as client:
        for seed in documents[:limit]:
            so_hieu = seed["so_hieu"]
            filename = sanitize_filename(seed.get("slug", so_hieu))
            print(f"\n{'=' * 60}")
            print(f"[DOC] Dang xu ly: {so_hieu}")

            resolved = await resolve_document(client, seed)
            await asyncio.sleep(DELAY_SECONDS)
            if not resolved:
                print(f"  [WARN] Khong resolve duoc tai lieu cho {so_hieu}")
                continue

            metadata = await extract_document_info(client, seed, resolved["url"])
            metadata["domain"] = domain
            metadata["resolved_url"] = resolved["url"]
            await asyncio.sleep(DELAY_SECONDS)

            pdf_saved_path = None
            source_to_download = metadata.get("pdf_url") or resolved["url"]
            normalized = await download_document(client, source_to_download, domain, filename)
            if normalized:
                pdf_saved_path = normalized["pdf_path"]
                metadata["pdf_local_path"] = pdf_saved_path
                metadata["download_local_path"] = normalized["download_path"]
                metadata["pdf_api_url"] = f"/api/document/{domain}/{filename}.pdf"
                metadata["conversion_engine"] = normalized["engine"]
                metadata["download_source_url"] = normalized["source_url"]
            else:
                print(f"  [WARN] Khong tao duoc PDF cho {so_hieu}")

            raw_path = STORAGE_RAW / domain / f"{filename}.json"
            raw_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  [SAVE] Da luu metadata: {raw_path.name}")

            results.append(
                {
                    "so_hieu": so_hieu,
                    "pdf_ok": pdf_saved_path is not None,
                    "metadata_ok": True,
                    "source_kind": metadata.get("source_kind"),
                }
            )

    print(f"\n{'=' * 60}")
    print(f"[SUMMARY] KET QUA CRAWL DOMAIN: {domain}")
    print(f"{'=' * 60}")
    for result in results:
        pdf_status = "OK PDF" if result["pdf_ok"] else "NO PDF"
        print(f"  {pdf_status} | {result['so_hieu']} | {result['source_kind']}")
    print(f"\nTong: {len(results)}/{len(documents[:limit])} van ban")
    return results


if __name__ == "__main__":
    asyncio.run(crawl_documents(domain="giao_thong", documents=PRIORITY_DOCUMENTS, limit=5))
