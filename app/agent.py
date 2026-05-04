"""
Agent Pipeline — orchestrates the full RAG pipeline.

Implements pipeline.md §2 (Pipeline Flow) and §4 (Agent Logic):
  User Input → Validate → Vector Search → Prompt Build → LLM → Validate → Response
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from app.models import QuestionRequest, LegalAnswer, AgentResponse
from app.vector_store import search
from app.prompt_builder import build_messages
from app.llm_client import call_llm
from app.config import RAG_TOP_K

logger = logging.getLogger(__name__)


def run_pipeline(request: QuestionRequest) -> AgentResponse:
    """
    Execute the full agent pipeline as defined in pipeline.md.

    Stage 1: Input Processing (§3.1)
    Stage 2: Retrieval — RAG (§3.2)
    Stage 3: Prompt Construction (§3.3)
    Stage 4: LLM Inference (§3.4)
    Stage 5: Validation & Response (§3.5)
    """

    # ── Stage 1: Input Processing ────────────────────────────────────────────
    question = request.question.strip()
    law_type = request.law_type.strip()

    if not question:
        return AgentResponse(
            success=False,
            error="Câu hỏi không được để trống.",
        )

    if not law_type:
        return AgentResponse(
            success=False,
            error="Vui lòng chọn lĩnh vực pháp luật.",
        )

    logger.info("Pipeline START — question=%r, law_type=%s", question[:80], law_type)

    # ── Stage 2: Retrieval (RAG) ─────────────────────────────────────────────
    context_docs = search(question=question, law_type=law_type, top_k=RAG_TOP_K)
    logger.info("Retrieved %d context documents", len(context_docs))

    # Agent logic (pipeline.md §4): no context → fallback
    if not context_docs:
        logger.warning("No context found — returning fallback")
        return AgentResponse(
            success=True,
            data=LegalAnswer(
                answer="Không tìm thấy thông tin phù hợp trong dữ liệu. Vui lòng thử lại với câu hỏi khác hoặc chọn lĩnh vực pháp luật phù hợp hơn.",
                legal_basis=[],
                confidence="low",
                follow_up="Bạn có thể mô tả cụ thể hơn vấn đề pháp lý cần tư vấn không?",
            ),
            sources=[],
        )

    # ── Stage 3: Prompt Construction ─────────────────────────────────────────
    messages = build_messages(
        question=question,
        law_type=law_type,
        context_docs=context_docs,
    )

    # ── Stage 4 & 5: LLM Inference + Validation ─────────────────────────────
    answer = call_llm(messages)

    # Collect source references for the frontend
    sources = []
    for doc in context_docs:
        title = doc.get("title", "")
        so_ky_hieu = doc.get("so_ky_hieu", "")
        ref = title
        if so_ky_hieu:
            ref = f"{so_ky_hieu} — {title}"
        if ref and ref not in sources:
            sources.append(ref)

    logger.info("Pipeline DONE — confidence=%s, sources=%d", answer.confidence, len(sources))

    return AgentResponse(
        success=True,
        data=answer,
        sources=sources,
    )
