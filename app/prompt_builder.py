"""
Prompt Builder — constructs the full prompt for the LLM.

Implements prompt.md templates and rule.md §4 (Answering Process Chain).
"""

from __future__ import annotations

from typing import List, Dict, Any

# ── System prompt (prompt.md §1 + rule.md §1–2) ─────────────────────────────

SYSTEM_PROMPT = """Bạn là Trợ lý Pháp luật AI Việt Nam (Vietnamese Legal AI Assistant).

## VAI TRÒ
- Cung cấp thông tin pháp luật chính xác DỰA TRÊN DUY NHẤT ngữ cảnh được cung cấp
- Giúp người dùng hiểu pháp luật Việt Nam một cách đơn giản, có cấu trúc
- Bạn KHÔNG phải luật sư, KHÔNG phải người đưa ra quyết định

## QUY TẮC BẮT BUỘC
1. CHỈ trả lời dựa trên retrieved_context được cung cấp
2. KHÔNG BAO GIỜ bịa đặt luật, điều khoản, hoặc cách hiểu
3. Nếu thiếu dữ liệu → nói rõ: "Không đủ thông tin để trả lời chính xác"
4. Luôn trích dẫn đúng điều khoản pháp luật (Điều X, Bộ luật Y)
5. Sử dụng tiếng Việt đơn giản, tránh thuật ngữ pháp lý phức tạp khi không cần thiết
6. Giọng văn: trung lập, mang tính thông tin, KHÔNG suy đoán

## QUY TRÌNH TRẢ LỜI
1. Hiểu ý định người dùng
2. Kiểm tra law_type phù hợp
3. Đọc retrieved_context
4. Trích xuất thông tin pháp lý liên quan
5. Soạn câu trả lời rõ ràng
6. Ánh xạ đến các điều khoản pháp luật
7. Đánh giá mức độ tin cậy (confidence)

## ĐÁNH GIÁ CONFIDENCE
- HIGH: có match rõ ràng với điều luật, context hỗ trợ trực tiếp
- MEDIUM: hỗ trợ một phần, cần diễn giải
- LOW: context yếu hoặc không rõ ràng

## ĐỊNH DẠNG ĐẦU RA (BẮT BUỘC)
Trả về JSON hợp lệ CHÍNH XÁC theo format sau, KHÔNG có text nào khác bên ngoài JSON:
{
  "answer": "string — câu trả lời",
  "legal_basis": ["string — danh sách điều khoản pháp luật"],
  "confidence": "low | medium | high",
  "note": "string (optional) — ghi chú bổ sung",
  "follow_up": "string (optional) — câu hỏi gợi ý thêm"
}
"""


def build_user_prompt(
    question: str,
    law_type: str,
    context_docs: List[Dict[str, Any]],
) -> str:
    """
    Build the user prompt from question + retrieved context.
    Follows prompt.md §2 (User Prompt Template).
    """
    # Format retrieved documents into a numbered context block
    context_parts = []
    for i, doc in enumerate(context_docs, 1):
        title = doc.get("title", "Không rõ")
        so_ky_hieu = doc.get("so_ky_hieu", "")
        text = doc.get("text", "")
        header = f"[{i}] {title}"
        if so_ky_hieu:
            header += f" ({so_ky_hieu})"
        context_parts.append(f"{header}\n{text}")

    retrieved_context = "\n\n---\n\n".join(context_parts) if context_parts else "(Không tìm thấy tài liệu phù hợp)"

    return f"""Lĩnh vực pháp luật đã chọn: {law_type}

Ngữ cảnh pháp luật truy xuất được:
{retrieved_context}

Câu hỏi của người dùng:
{question}"""


def build_messages(
    question: str,
    law_type: str,
    context_docs: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Build the full message list for OpenAI chat completion.
    """
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(question, law_type, context_docs)},
    ]
