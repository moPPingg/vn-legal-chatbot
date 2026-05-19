from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from backend.agents.graph import build_graph

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize graph once
graph = build_graph()

class ChatRequest(BaseModel):
    question: str
    lawType: str = ""

class ChatResponseData(BaseModel):
    answer: str
    summary: str = ""
    legal_basis: list = []
    citations: list = []
    confidence: str = ""
    note: str = ""
    follow_up: str = ""

class ChatResponse(BaseModel):
    success: bool
    data: ChatResponseData | None = None
    sources: list = []
    error: str | None = None

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        initial_state = {
            "question": req.question,
            "domain": req.lawType,
            "conversation_history": []
        }
        
        # Invoke LangGraph
        final_state = graph.invoke(initial_state)
        
        citations = final_state.get("citations", [])
        
        # Deduplicate sources for a simpler view
        sources = list(set([f"{c['so_hieu']} - {c['dieu']}" for c in citations if c.get('so_hieu')]))
        
        return ChatResponse(
            success=True,
            data=ChatResponseData(
                answer=final_state.get("answer", ""),
                summary=final_state.get("summary", final_state.get("answer", "")),
                citations=citations,
                confidence=final_state.get("confidence", "low"),
                note=final_state.get("note", ""),
                follow_up=final_state.get("follow_up", "")
            ),
            sources=sources
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return ChatResponse(success=False, error=str(e))
