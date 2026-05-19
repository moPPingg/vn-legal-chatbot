import requests
import json
import logging
import sys
import os
from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.app.config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, model: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    def generate(self, prompt: str, system_prompt: Optional[str] = None, format: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if format == "json":
            payload["format"] = "json"
            
        try:
            logger.info(f"Sending request to Ollama ({self.model})...")
            response = requests.post(url, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation failed: {str(e)}")
            raise RuntimeError(f"Ollama generation failed for model {self.model}: {e}") from e
