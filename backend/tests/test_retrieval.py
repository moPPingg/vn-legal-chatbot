import sys
import os
import logging
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.retrieval.hybrid_search import LegalSearcher
from backend.pipeline.ingestor.qdrant_ingestor import QdrantIngestor
from backend.app.schema import LegalChunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def inject_mock_data():
    ingestor = QdrantIngestor()
    # The constructor ensures collection exists
    
    mock_chunks = [
        LegalChunk(
            text="Điều 5. Xử phạt người điều khiển xe ô tô và các loại xe tương tự xe ô tô vi phạm quy tắc giao thông đường bộ.\n"
                 "Phạt tiền từ 30.000.000 đồng đến 40.000.000 đồng đối với người điều khiển xe trên đường mà trong máu "
                 "hoặc hơi thở có nồng độ cồn vượt quá 80 miligam/100 mililít máu hoặc vượt quá 0,4 miligam/1 lít khí thở.",
            metadata={
                "so_hieu": "100/2019/NĐ-CP",
                "ten_van_ban": "Nghị định 100/2019/NĐ-CP",
                "loai_van_ban": "Nghị định",
                "co_quan_ban_hanh": "Chính phủ",
                "domain": "giao_thong",
                "article_header": "Điều 5. Xử phạt người điều khiển xe ô tô",
                "tinh_trang": "Còn hiệu lực"
            }
        ),
        LegalChunk(
            text="Điều 6. Xử phạt người điều khiển xe mô tô, xe gắn máy (kể cả xe máy điện) vi phạm quy tắc giao thông.\n"
                 "Phạt tiền từ 6.000.000 đồng đến 8.000.000 đồng đối với người điều khiển xe trên đường mà trong máu "
                 "hoặc hơi thở có nồng độ cồn vượt quá 80 miligam/100 mililít máu hoặc vượt quá 0,4 miligam/1 lít khí thở.",
            metadata={
                "so_hieu": "100/2019/NĐ-CP",
                "ten_van_ban": "Nghị định 100/2019/NĐ-CP",
                "loai_van_ban": "Nghị định",
                "co_quan_ban_hanh": "Chính phủ",
                "domain": "giao_thong",
                "article_header": "Điều 6. Xử phạt người điều khiển xe mô tô, xe gắn máy",
                "tinh_trang": "Còn hiệu lực"
            }
        )
    ]
    
    ingestor.ingest_chunks(mock_chunks)
    logging.info("Mock data injected.")

def test_search():
    searcher = LegalSearcher()
    query = "nồng độ cồn ô tô"
    
    logging.info(f"--- Testing retrieval with query: {query} ---")
    results = searcher.search(query=query, limit=2)
    
    for i, res in enumerate(results):
        print(f"\nResult {i+1} (Score: {res['score']:.4f}):")
        print(f"Header: {res['metadata'].get('article_header')}")
        print(f"Text snippet: {res['text'][:150]}...")

if __name__ == "__main__":
    # Inject data first to ensure we have the results we want to retrieve
    inject_mock_data()
    # Test the retrieval
    test_search()
