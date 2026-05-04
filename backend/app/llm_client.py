"""LLM Client — Ollama local inference + JSON validation + retry (100% offline)."""
from __future__ import annotations
import json, re, logging
from typing import Optional, Dict, Any, List
import ollama
from app.config import OLLAMA_MODEL, LLM_TEMPERATURE, OLLAMA_BASE_URL
from app.models import LegalAnswer

logger = logging.getLogger(__name__)

# Initialize explicit client with increased timeout for slow local generation
client = ollama.Client(host=OLLAMA_BASE_URL, timeout=120.0)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Try multiple strategies to extract JSON from LLM output."""
    text = text.strip()
    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strategy 2: markdown code block
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Strategy 3: find first { ... last }
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e > s:
        try:
            return json.loads(text[s : e + 1])
        except json.JSONDecodeError:
            pass
    return None


def call_llm(messages: List[Dict[str, str]], max_retries: int = 2) -> LegalAnswer:
    """Call Ollama local model, validate JSON output, retry if needed."""
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            logger.info("Ollama call attempt %d/%d (model=%s)", attempt + 1, max_retries + 1, OLLAMA_MODEL)

            response = client.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                options={
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": 1024,
                },
                format="json",
            )

            raw = response.message.content
            logger.info("Ollama raw response length: %d chars", len(raw))

            parsed = _extract_json(raw)
            if parsed is None:
                last_error = "LLM returned invalid JSON"
                logger.warning("Attempt %d: %s — raw: %s", attempt + 1, last_error, raw[:200])
                if attempt < max_retries:
                    messages = messages + [
                        {"role": "assistant", "content": raw},
                        {"role": "user", "content": "Phản hồi không phải JSON hợp lệ. Trả lời LẠI chỉ bằng JSON theo đúng format yêu cầu."},
                    ]
                continue

            # Validate with Pydantic
            answer = LegalAnswer(**parsed)

            # Add warning for low confidence
            if answer.legal_basis and answer.confidence == "low":
                answer.note = (answer.note or "") + " [Cảnh báo: độ tin cậy thấp]"

            return answer

        except Exception as e:
            last_error = str(e)
            logger.error("Ollama error attempt %d: %s", attempt + 1, last_error)

    # All retries exhausted
    return LegalAnswer(
        answer="Xin lỗi, hệ thống gặp sự cố khi xử lý câu hỏi. Vui lòng thử lại.",
        legal_basis=[],
        confidence="low",
        note=f"Lỗi: {last_error}",
    )


def generate_text(prompt: str, system_prompt: Optional[str] = None) -> str:
    """General purpose text generation (no JSON enforcement)."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"temperature": 0.0, "num_predict": 256},
        )
        return response.message.content.strip()
    except Exception as e:
        logger.error("Error in generate_text: %s", e)
        return ""


def rewrite_query(original_query: str) -> str:
    """Rewrite a casual query into a formal legal query for better retrieval."""
    system_prompt = """Bạn là một chuyên gia phân tích ngôn ngữ pháp lý. 
Nhiệm vụ của bạn là chuyển đổi câu hỏi dân dã của người dùng thành các từ khóa hoặc câu truy vấn mang tính pháp lý chuẩn mực (Query Expansion/Rewriting) để tối ưu hóa việc tìm kiếm trong cơ sở dữ liệu Vector (Vector Database Search).

Quy tắc:
1. Giữ nguyên ý định cốt lõi của người dùng.
2. Trả về đúng 1 câu truy vấn đã được viết lại, không giải thích gì thêm."""

    prompt = f"Câu hỏi gốc: \"{original_query}\"\nTruy vấn pháp lý tối ưu:"
    
    rewritten = generate_text(prompt, system_prompt)
    if rewritten:
        # Remove quotes if the LLM added them
        rewritten = rewritten.replace('"', '').replace("'", "")
        logger.info("Rewritten query: %r -> %r", original_query, rewritten)
        return rewritten
    return original_query

