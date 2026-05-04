"""Prompt Builder — system + user prompt construction (prompt.md)."""
from __future__ import annotations
from typing import List, Dict, Any

SYSTEM_PROMPT = """Bạn là Trợ lý Pháp luật AI Việt Nam.

## QUY TẮC BẮT BUỘC
1. CHỈ trả lời dựa trên retrieved_context được cung cấp
2. KHÔNG BAO GIỜ bịa đặt luật, điều khoản, hoặc cách hiểu
3. Nếu thiếu dữ liệu → nói: "Không đủ thông tin để trả lời chính xác"
4. Trích dẫn đúng điều khoản pháp luật (Điều X, Bộ luật Y)
5. Tiếng Việt đơn giản, tránh thuật ngữ phức tạp
6. Giọng văn trung lập, KHÔNG suy đoán

## CONFIDENCE
- HIGH: match rõ ràng với điều luật
- MEDIUM: hỗ trợ một phần, cần diễn giải
- LOW: context yếu hoặc không rõ

## OUTPUT FORMAT (BẮT BUỘC — chỉ JSON, không text khác)
{
  "answer": "string",
  "legal_basis": ["string"],
  "confidence": "low | medium | high",
  "note": "string (optional)",
  "follow_up": "string (optional)"
}"""


def build_messages(question: str, law_type: str, context_docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    parts = []
    for i, doc in enumerate(context_docs, 1):
        header = f"[{i}] {doc.get('title', '')}"
        if doc.get("so_ky_hieu"):
            header += f" ({doc['so_ky_hieu']})"
        parts.append(f"{header}\n{doc.get('text', '')}")
    ctx = "\n\n---\n\n".join(parts) if parts else "(Không tìm thấy tài liệu)"

    user_msg = f"Lĩnh vực: {law_type}\n\nNgữ cảnh pháp luật:\n{ctx}\n\nCâu hỏi: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
