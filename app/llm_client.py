"""
LLM Client — handles inference via OpenAI API.

Implements pipeline.md §3.4 (LLM Inference) and §3.5 (Validation Layer).
"""

from __future__ import annotations

import json
import logging
from typing import Optional, Dict, Any, List

from openai import OpenAI

from app.config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from app.models import LegalAnswer

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Try to extract a JSON object from the LLM response text."""
    text = text.strip()

    # Attempt 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: find JSON block in markdown code fence
    import re
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Attempt 3: find first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def call_llm(
    messages: List[Dict[str, str]],
    max_retries: int = 2,
) -> LegalAnswer:
    """
    Call the LLM and validate the response.

    Implements:
    - pipeline.md §3.4: LLM call with low temperature
    - pipeline.md §3.5: JSON validation with retry
    - rule.md §12: validation before output
    """
    client = _get_client()
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            logger.info("LLM call attempt %d/%d (model=%s)", attempt + 1, max_retries + 1, LLM_MODEL)

            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content
            logger.debug("LLM raw response: %s", raw[:500])

            # Parse JSON (pipeline.md §3.5 — validation)
            parsed = _extract_json(raw)
            if parsed is None:
                last_error = "Invalid JSON in LLM response"
                logger.warning("Attempt %d: %s", attempt + 1, last_error)
                # On retry, add a stricter instruction (pipeline.md §5 — JSON Error)
                if attempt < max_retries:
                    messages = messages + [
                        {"role": "assistant", "content": raw},
                        {
                            "role": "user",
                            "content": "Phản hồi của bạn không phải JSON hợp lệ. Hãy trả lời LẠI chỉ với JSON theo đúng format đã quy định, KHÔNG có text nào khác.",
                        },
                    ]
                continue

            # Validate with Pydantic (rule.md §12)
            answer = LegalAnswer(**parsed)

            # Anti-hallucination check (rule.md §9):
            # If answer has legal_basis but confidence is low, flag it
            if answer.legal_basis and answer.confidence == "low":
                answer.note = (answer.note or "") + " [Cảnh báo: cơ sở pháp lý được trích dẫn nhưng độ tin cậy thấp]"

            logger.info("LLM response validated ✓ (confidence=%s)", answer.confidence)
            return answer

        except Exception as e:
            last_error = str(e)
            logger.error("LLM call error on attempt %d: %s", attempt + 1, last_error)

    # All retries failed — return fallback (pipeline.md §5 — LLM Failure)
    logger.error("All LLM attempts failed. Returning fallback.")
    return LegalAnswer(
        answer="Xin lỗi, hệ thống gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau.",
        legal_basis=[],
        confidence="low",
        note=f"Lỗi hệ thống: {last_error}",
    )
