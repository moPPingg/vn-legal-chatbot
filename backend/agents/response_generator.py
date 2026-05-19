import logging
import unicodedata
from typing import Any, Dict

from backend.agents.state import AgentState
from backend.app.config import settings
from backend.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


def _normalize_text(value: str) -> str:
    value = value.replace("Đ", "D").replace("đ", "d")
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    return " ".join(value.lower().split())


def _contains_phrase(text: str, phrase: str) -> bool:
    text_tokens = text.split()
    phrase_tokens = phrase.split()
    if not phrase_tokens or len(phrase_tokens) > len(text_tokens):
        return False
    window = len(phrase_tokens)
    return any(text_tokens[i : i + window] == phrase_tokens for i in range(len(text_tokens) - window + 1))


def _citation_score(question: str, citation: Dict[str, Any]) -> float:
    haystack = " ".join(
        [
            citation.get("dieu", ""),
            citation.get("ten_van_ban", ""),
            citation.get("snippet", ""),
        ]
    )
    normalized_question = _normalize_text(question)
    normalized_haystack = _normalize_text(haystack)
    haystack_tokens = set(normalized_haystack.split())

    score = 0.0
    for term in {term for term in normalized_question.split() if len(term) >= 2}:
        if term in haystack_tokens:
            score += 0.08

    if _contains_phrase(normalized_question, "o to") and _contains_phrase(normalized_haystack, "o to"):
        score += 0.4
    if _contains_phrase(normalized_question, "xe may") and _contains_phrase(normalized_haystack, "xe may"):
        score += 0.4

    return score


def _pick_best_citation(question: str, citations: list[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not citations:
        return None
    return max(citations, key=lambda citation: _citation_score(question, citation))


def _build_summary_from_citation(question: str, citations: list[Dict[str, Any]]) -> str:
    top = _pick_best_citation(question, citations) or (citations[0] if citations else None)
    if top is None:
        return "Hien tai toi chua tao duoc cau tra loi tu mo hinh va cung chua co du trich dan de tom tat an toan."

    so_hieu = top.get("so_hieu", "van ban lien quan")
    dieu = top.get("dieu", "dieu khoan lien quan")
    snippet = " ".join((top.get("snippet", "") or "").split())
    if len(snippet) > 320:
        snippet = snippet[:317].rstrip() + "..."

    return (
        f"Toi tam thoi tra loi theo trich dan tim duoc tu {so_hieu}, {dieu}. "
        f"Noi dung lien quan ghi nhan: {snippet}"
    )


def _build_note(citations: list[Dict[str, Any]], used_fallback: bool) -> str:
    if used_fallback:
        return "Cau tra loi duoc tom tat tu trich dan truy hoi vi mo hinh local khong phan hoi kip trong gioi han thoi gian."
    if any(not citation.get("still_valid", False) for citation in citations):
        return "Co it nhat mot trich dan da het hieu luc hoac can doi chieu them voi van ban moi hon."
    return ""


def run(state: AgentState) -> Dict[str, Any]:
    logger.info("--- NODE: response_generator ---")
    question = state.get("question", "")
    merged_context = state.get("merged_context", "")
    citations = state.get("citations", [])

    llm = OllamaClient(
        model=settings.OLLAMA_CHAT_MODEL,
        timeout_seconds=settings.OLLAMA_CHAT_TIMEOUT_SECONDS,
    )
    system_prompt = """You are a professional Vietnamese legal assistant.
Base your answer ONLY on the provided context. If the context does not contain the answer, say you don't know.
Write a concise Vietnamese summary for a non-lawyer.
Mention the practical penalty or legal consequence first when the context supports it."""

    prompt = f"Context:\n{merged_context}\n\nQuestion: {question}\n\nAnswer in Vietnamese:"

    used_fallback = False
    try:
        summary = llm.generate(prompt=prompt, system_prompt=system_prompt)
    except RuntimeError as exc:
        logger.warning("Falling back to retrieval-only answer: %s", exc)
        summary = _build_summary_from_citation(question, citations)
        used_fallback = True

    normalized_response = _normalize_text(summary)
    confidence = "medium"
    if "dieu" in normalized_response and ("nd-cp" in normalized_response or "so hieu" in normalized_response):
        confidence = "high"
    if "khong co thong tin" in normalized_response or "khong ro" in normalized_response:
        confidence = "low"
    if used_fallback and confidence == "high":
        confidence = "medium"

    note = _build_note(citations, used_fallback)

    return {
        "answer": summary,
        "summary": summary,
        "note": note,
        "confidence": confidence,
        "follow_up": "Ban co can hoi them ve muc phat nao khac khong?",
    }
