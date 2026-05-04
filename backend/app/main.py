"""FastAPI server — Vietnamese Legal AI Agent (teckstack.md §5.2)."""
from __future__ import annotations
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import ChatRequest, ChatResponse, LAW_TYPES
from app.pipeline import run_pipeline
from app.rag.vector_store import get_stats
from app.classifier import predict_law_type

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Vietnamese Legal AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok", "vector_store": get_stats()}

@app.get("/law-types")
async def law_types():
    return {"law_types": LAW_TYPES}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        return run_pipeline(req)
    except Exception as e:
        logger.exception("Pipeline error")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/classify")
async def classify(req: dict):
    question = req.get("question", "")
    if not question:
        raise HTTPException(400, "question required")
    return {"predicted_law_type": predict_law_type(question)}
