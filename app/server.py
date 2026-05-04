"""
FastAPI server — serves the Vietnamese Legal AI Agent API + static frontend.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.models import QuestionRequest, AgentResponse
from app.agent import run_pipeline
from app.vector_store import get_stats

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Vietnamese Legal AI Agent",
    description="RAG-powered legal assistant for Vietnamese law",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    stats = get_stats()
    return {"status": "ok", "vector_store": stats}


@app.post("/api/ask", response_model=AgentResponse)
async def ask_question(request: QuestionRequest):
    """
    Main endpoint — accepts a legal question and returns a structured answer.
    """
    try:
        result = run_pipeline(request)
        return result
    except Exception as e:
        logger.exception("Pipeline error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/law-types")
async def get_law_types():
    """Return the list of supported law_type categories."""
    return {
        "law_types": [
            {"value": "hình sự", "label": "Hình sự"},
            {"value": "dân sự", "label": "Dân sự"},
            {"value": "lao động", "label": "Lao động"},
            {"value": "hành chính", "label": "Hành chính"},
            {"value": "thương mại", "label": "Thương mại"},
            {"value": "đất đai", "label": "Đất đai"},
            {"value": "hôn nhân gia đình", "label": "Hôn nhân & Gia đình"},
            {"value": "thuế", "label": "Thuế"},
            {"value": "giáo dục", "label": "Giáo dục"},
            {"value": "y tế", "label": "Y tế"},
            {"value": "khác", "label": "Khác"},
        ]
    }


# ── Serve Frontend ───────────────────────────────────────────────────────────

@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    return FileResponse(FRONTEND_DIR / "index.html")


# Mount static after all API routes
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
