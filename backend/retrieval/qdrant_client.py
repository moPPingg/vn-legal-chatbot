import sys
import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.app.config import settings
from backend.pipeline.ingestor.embedder import embed_query

logger = logging.getLogger(__name__)

class QdrantRetriever:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = settings.QDRANT_COLLECTION_DOCS

    def dense_search(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query_vector = embed_query(query).tolist()
        
        # Build filter if provided
        qdrant_filter = None
        if filters:
            must_conditions = []
            for key, value in filters.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
            qdrant_filter = models.Filter(must=must_conditions)

        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True
        ).points
        
        results = []
        for hit in search_result:
            metadata = {k: v for k, v in hit.payload.items() if k != "text"}
            results.append({
                "id": hit.id,
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "metadata": metadata
            })
        return results

    def fetch_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        points = self.client.retrieve(
            collection_name=self.collection_name,
            ids=ids,
            with_payload=True
        )
        return [{
            "id": point.id,
            "text": point.payload.get("text", ""),
            "metadata": {k: v for k, v in point.payload.items() if k != "text"}
        } for point in points]
