from fastapi import APIRouter
from backend.retrieval.qdrant_client import QdrantRetriever

router = APIRouter()

@router.get("/health")
async def health_endpoint():
    try:
        retriever = QdrantRetriever()
        count = retriever.client.get_collection(retriever.collection_name).points_count
        return {"status": "ok", "qdrant_points": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
