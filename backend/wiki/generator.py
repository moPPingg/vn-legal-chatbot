import json
import logging
import sys
import os
from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.llm.ollama_client import OllamaClient
from backend.app.config import settings
from backend.app.schema import WikiEntry

logger = logging.getLogger(__name__)

WIKI_PROMPT = """
Bạn là chuyên gia pháp lý Việt Nam. Đọc văn bản pháp luật sau và tạo wiki entry.

VĂN BẢN:
Tên: {ten_van_ban}
Số hiệu: {so_hieu}
Lĩnh vực: {domain}
Nội dung:
{noi_dung}

Tạo wiki entry JSON (không giải thích thêm):
{{
  "concept": "Tên khái niệm pháp lý chính",
  "summary": "Tóm tắt 2-3 câu",
  "keywords": ["từ khóa 1", "từ khóa 2"],
  "applies_to": ["đối tượng áp dụng 1"],
  "penalties": {{"muc_1": "phạt bao nhiêu", "muc_2": "..."}},
  "conditions": ["điều kiện áp dụng"],
  "legal_basis": ["Điều 5 NĐ 168/2024/NĐ-CP"],
  "supersedes": [],
  "effective_date": "2025-01-01",
  "still_valid": true
}}
"""

class WikiGenerator:
    def __init__(self):
        self.llm = OllamaClient(model=settings.OLLAMA_WIKI_MODEL)

    def generate_entry(self, chunk: Dict[str, Any]) -> Optional[WikiEntry]:
        prompt = WIKI_PROMPT.format(
            ten_van_ban=chunk.get("metadata", {}).get("ten_van_ban", ""),
            so_hieu=chunk.get("metadata", {}).get("so_hieu", ""),
            domain=chunk.get("metadata", {}).get("domain", ""),
            noi_dung=chunk.get("text", "")
        )
        
        system_prompt = "You are a Vietnamese legal assistant. Always output valid JSON."
        
        response = self.llm.generate(prompt=prompt, system_prompt=system_prompt, format="json")
        
        if not response:
            return None
            
        try:
            # Parse the JSON
            data = json.loads(response)
            return WikiEntry(**data)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM: {response}")
            return None
        except Exception as e:
            logger.error(f"Failed to validate WikiEntry: {str(e)}")
            return None
