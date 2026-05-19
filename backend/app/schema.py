from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

class LegalChunk(BaseModel):
    text: str
    metadata: Dict[str, Any]

class WikiEntry(BaseModel):
    concept: str
    summary: str
    keywords: List[str]
    applies_to: List[str]
    penalties: Dict[str, Any]
    conditions: List[str]
    legal_basis: List[str]
    supersedes: List[str]
    effective_date: str
    still_valid: bool
