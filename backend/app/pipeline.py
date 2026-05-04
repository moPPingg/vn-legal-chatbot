"""Pipeline — full 5-stage orchestrator (pipeline.md §2)."""
from __future__ import annotations
import logging, time
from app.models import ChatRequest, ChatResponse, LegalAnswer
from app.rag.retriever import search
from app.prompt_builder import build_messages
from app.llm_client import call_llm, rewrite_query
from app.config import RAG_TOP_K

logger = logging.getLogger(__name__)

def run_pipeline(req: ChatRequest) -> ChatResponse:
    start_time = time.time()
    question = req.question.strip()
    law_type = req.lawType.strip()

    if not question:
        return ChatResponse(success=False, error="Câu hỏi không được để trống.")
    if not law_type:
        return ChatResponse(success=False, error="Vui lòng chọn lĩnh vực pháp luật.")

    logger.info("Pipeline: q=%r, law=%s", question[:60], law_type)

    # Stage 1: Query Expansion
    rewritten_query = rewrite_query(question)
    
    # Stage 2: Retrieval
    t0 = time.time()
    docs = search(question=rewritten_query, law_type=law_type, top_k=RAG_TOP_K)
    retrieval_time = time.time() - t0
    logger.info("Retrieved %d documents in %.2fs", len(docs), retrieval_time)

    if not docs:
        return ChatResponse(
            success=True,
            data=LegalAnswer(
                answer="Không tìm thấy thông tin phù hợp. Vui lòng thử câu hỏi khác hoặc chọn lĩnh vực phù hợp hơn.",
                legal_basis=[], confidence="low",
                follow_up="Bạn có thể mô tả cụ thể hơn vấn đề pháp lý không?",
            ),
        )

    # Stage 3: Prompt
    messages = build_messages(question, law_type, docs)

    # Stage 4-5: LLM + Validation
    t1 = time.time()
    answer = call_llm(messages)
    llm_time = time.time() - t1
    logger.info("LLM generation + validation took %.2fs", llm_time)

    sources = []
    for d in docs:
        ref = f"{d.get('so_ky_hieu','')} — {d.get('title','')}" if d.get("so_ky_hieu") else d.get("title","")
        if ref and ref not in sources:
            sources.append(ref)

    total_time = time.time() - start_time
    logger.info("Total pipeline time: %.2fs", total_time)
    
    return ChatResponse(success=True, data=answer, sources=sources)
