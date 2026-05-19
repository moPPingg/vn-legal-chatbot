"""API endpoints for serving stored PDF documents and upload conversions."""

from pathlib import Path
import json

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from backend.pipeline.converter import is_valid_pdf
from backend.pipeline.processor.file_converter import (
    convert_uploaded_file,
    get_pdf_info,
    save_upload,
)

router = APIRouter(tags=["documents"])

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PDF_BASE = BACKEND_ROOT / "storage" / "pdfs"
META_BASE = BACKEND_ROOT / "storage" / "raw"


@router.get("/document/{domain}/{filename}")
async def serve_pdf(domain: str, filename: str):
    """Serve a PDF file by domain and filename."""
    if ".." in domain or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid path")

    pdf_path = PDF_BASE / domain / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found: {domain}/{filename}")
    if not is_valid_pdf(pdf_path):
        raise HTTPException(
            status_code=422,
            detail=f"Stored file is not a valid PDF: {domain}/{filename}",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@router.get("/document/{domain}/{filename}/metadata")
async def get_document_metadata(domain: str, filename: str):
    """Return metadata for a stored document."""
    stem = filename.replace(".pdf", "")
    meta_path = META_BASE / domain / f"{stem}.json"

    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Metadata not found")

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    return JSONResponse(content=data)


@router.get("/documents/{domain}")
async def list_documents(domain: str):
    """List crawled documents for one domain."""
    domain_path = META_BASE / domain
    if not domain_path.exists():
        return {"domain": domain, "documents": [], "total": 0}

    docs = []
    for meta_file in domain_path.glob("*.json"):
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            docs.append(
                {
                    "so_hieu": data.get("so_hieu", ""),
                    "ten_van_ban": data.get("ten_van_ban", ""),
                    "tinh_trang": data.get("tinh_trang", ""),
                    "pdf_api_url": data.get("pdf_api_url", ""),
                    "ngay_ban_hanh": data.get("ngay_ban_hanh", ""),
                }
            )
        except Exception:
            continue

    return {"domain": domain, "documents": docs, "total": len(docs)}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    saved_path = await save_upload(file)
    pdf_path = convert_uploaded_file(saved_path)
    info = get_pdf_info(pdf_path)

    return {
        "success": True,
        "original_filename": file.filename,
        "pdf_filename": pdf_path.name,
        "pdf_url": f"/api/document/uploaded/{pdf_path.name}",
        "page_count": info["page_count"],
        "preview": info["first_page_preview"],
        "message": f"Da convert thanh cong sang PDF ({info['page_count']} trang)",
    }
