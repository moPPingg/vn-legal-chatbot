import logging
import os
import sys
import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.app.config import settings
from backend.pipeline.ingestor.embedder import embed_texts
from backend.app.schema import LegalChunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

class QdrantIngestor:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = settings.QDRANT_COLLECTION_DOCS
        self._ensure_collection()

    def _ensure_collection(self):
        # Determine dimension by embedding a dummy string
        dim = len(embed_texts(["dummy"], show_progress=False)[0])
        
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            logger.info(f"Creating collection '{self.collection_name}' with dim {dim}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            logger.info("Collection created.")
        else:
            logger.info(f"Collection '{self.collection_name}' already exists.")

    def ingest_chunks(self, chunks: List[LegalChunk], batch_size: int = 128):
        if not chunks:
            logger.warning("No chunks to ingest.")
            return

        logger.info(f"Ingesting {len(chunks)} chunks into Qdrant...")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.text for c in batch]
            metadatas = [c.metadata for c in batch]
            
            embeddings = embed_texts(texts, show_progress=False)
            
            points = []
            for j, emb in enumerate(embeddings):
                # We need a unique UUID for each point
                point_id = str(uuid.uuid4())
                
                payload = metadatas[j].copy()
                payload["text"] = texts[j]  # Ensure text is in payload for retrieval
                
                points.append(PointStruct(id=point_id, vector=emb.tolist(), payload=payload))
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted batch {i//batch_size + 1} ({len(batch)} points).")
            
        logger.info(f"Successfully ingested {len(chunks)} total chunks.")

def run_ingestor_test():
    # Mock some chunks to test
    dummy_chunks = [
        LegalChunk(
            text="Điều 5. Xử phạt người điều khiển xe ô tô: Phạt tiền từ 200.000 đồng đến 400.000 đồng...",
            metadata={"so_hieu": "100/2019/NĐ-CP", "domain": "giao_thong", "article_header": "Điều 5"}
        ),
        LegalChunk(
            text="Điều 6. Xử phạt người điều khiển xe mô tô, xe gắn máy...",
            metadata={"so_hieu": "100/2019/NĐ-CP", "domain": "giao_thong", "article_header": "Điều 6"}
        )
    ]
    
    ingestor = QdrantIngestor()
    ingestor.ingest_chunks(dummy_chunks)

if __name__ == "__main__":
    run_ingestor_test()
