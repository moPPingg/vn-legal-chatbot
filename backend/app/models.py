"""Pydantic models — request/response schemas per rule.md & prompt.md."""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    lawType: str = Field(..., min_length=1)

class LegalAnswer(BaseModel):
    answer: str
    legal_basis: List[str] = Field(default_factory=list)
    confidence: str = "low"
    note: Optional[str] = None
    follow_up: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool = True
    data: Optional[LegalAnswer] = None
    error: Optional[str] = None
    sources: List[str] = Field(default_factory=list)

LAW_TYPES = [
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
    {"value": "giao thông", "label": "Giao thông"},
    {"value": "khác", "label": "Khác"},
]
