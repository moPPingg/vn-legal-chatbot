"""
Pydantic models — request / response schemas following rule.md and prompt.md.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class LawType(str, Enum):
    """Supported legal domains (extendable)."""
    HINH_SU = "hình sự"
    DAN_SU = "dân sự"
    LAO_DONG = "lao động"
    HANH_CHINH = "hành chính"
    THUONG_MAI = "thương mại"
    DAT_DAI = "đất đai"
    HON_NHAN_GIA_DINH = "hôn nhân gia đình"
    THUE = "thuế"
    GIAO_DUC = "giáo dục"
    Y_TE = "y tế"
    KHAC = "khác"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Request ───────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    """User query coming from the frontend."""
    question: str = Field(..., min_length=1, description="User's legal question in Vietnamese")
    law_type: str = Field(..., min_length=1, description="Selected legal domain")


# ── LLM Response (structured JSON the LLM must return) ───────────────────────

class LegalAnswer(BaseModel):
    """Structured answer as defined in prompt.md / rule.md §2.4."""
    answer: str
    legal_basis: List[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.LOW
    note: Optional[str] = None
    follow_up: Optional[str] = None


# ── API Response wrapper ─────────────────────────────────────────────────────

class AgentResponse(BaseModel):
    """Full response returned by the API."""
    success: bool = True
    data: Optional[LegalAnswer] = None
    error: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
