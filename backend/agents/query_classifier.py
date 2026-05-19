import logging
from typing import Dict, Any
from backend.agents.state import AgentState
from backend.llm.ollama_client import OllamaClient
from backend.app.config import settings
import json

logger = logging.getLogger(__name__)

def run(state: AgentState) -> Dict[str, Any]:
    logger.info("--- NODE: query_classifier ---")
    question = state.get("question", "")
    selected_domain = state.get("domain")

    if selected_domain:
        return {
            "predicted_domain": selected_domain,
            "rewritten_query": question,
        }
    
    llm = OllamaClient(
        model=settings.OLLAMA_CHAT_MODEL,
        timeout_seconds=settings.OLLAMA_CHAT_TIMEOUT_SECONDS,
    )
    system_prompt = """You are a Legal AI router. Categorize the user's question into one of the following domains:
- giao_thong (traffic law)
- hinh_su (criminal law)
- hon_nhan (marriage & family law)
- lao_dong (labor law)
- dat_dai (land & real estate law)
- doanh_nghiep (business law)
- khac (other)

Output valid JSON ONLY: {"domain": "domain_name", "rewritten_query": "clearer version of the query if needed"}"""

    prompt = f"Question: {question}"
    
    response = llm.generate(prompt=prompt, system_prompt=system_prompt, format="json")
    
    predicted_domain = "khac"
    rewritten_query = question
    
    try:
        data = json.loads(response)
        predicted_domain = data.get("domain", "khac")
        rewritten_query = data.get("rewritten_query", question)
    except Exception as e:
        logger.error(f"Failed to parse classifier output: {str(e)}")
        
    return {
        "predicted_domain": predicted_domain,
        "rewritten_query": rewritten_query
    }
