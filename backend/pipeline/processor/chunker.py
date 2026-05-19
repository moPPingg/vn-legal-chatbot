import re
import json
import os
import logging
from typing import List

# Fix import path for schema
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.app.schema import LegalChunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Regex patterns for Vietnamese legal documents
ARTICLE_PATTERN = re.compile(r'(?=Điều \d+[\.\:\s])')
CLAUSE_PATTERN  = re.compile(r'(?=\n\d+\.\s)')  # Khoản: 1. , 2. 
POINT_PATTERN   = re.compile(r'(?=\n[a-zđ]\)\s)') # Điểm: a) , b) , đ)

def chunk_legal_document(text: str, metadata: dict) -> List[LegalChunk]:
    chunks = []
    
    # Split by Article (Điều)
    articles = ARTICLE_PATTERN.split(text)

    for article in articles:
        if not article.strip():
            continue

        lines = article.strip().split('\n')
        article_header = lines[0].strip()  # e.g., "Điều 5. Xử phạt..."

        # If article is short enough, keep it as one chunk
        if len(article) <= 2000:
            chunks.append(LegalChunk(
                text=article.strip(),
                metadata={**metadata, "article_header": article_header}
            ))
            continue

        # If article is long, split by Clause (Khoản)
        clauses = CLAUSE_PATTERN.split(article)
        
        # clauses[0] usually contains the Article header and intro text
        header_text = clauses[0].strip()
        
        # If there are no clauses but it's long, we might need to split by points, but for now we fallback
        if len(clauses) == 1:
             chunks.append(LegalChunk(
                text=article.strip(),
                metadata={**metadata, "article_header": article_header}
            ))
             continue

        for clause in clauses[1:]:
            chunk_text = f"{header_text}\n{clause.strip()}"
            chunks.append(LegalChunk(
                text=chunk_text,
                metadata={**metadata, "article_header": article_header}
            ))

    return chunks

def run_chunking_test():
    # Simulate a raw crawled document
    sample_text = """
Điều 5. Xử phạt người điều khiển xe ô tô và các loại xe tương tự xe ô tô vi phạm quy tắc giao thông đường bộ
1. Phạt tiền từ 200.000 đồng đến 400.000 đồng đối với một trong các hành vi vi phạm sau đây:
a) Không chấp hành hiệu lệnh, chỉ dẫn của biển báo hiệu, vạch kẻ đường;
b) Chuyển hướng không nhường quyền đi trước cho: Người đi bộ, xe lăn của người khuyết tật.

2. Phạt tiền từ 400.000 đồng đến 600.000 đồng đối với người điều khiển xe thực hiện một trong các hành vi vi phạm sau đây:
a) Chuyển làn đường không đúng nơi cho phép hoặc không có tín hiệu báo trước;
b) Điều khiển xe chạy tốc độ thấp hơn các xe khác đi cùng chiều mà không đi về bên phải phần đường xe chạy.
    """
    metadata = {
        "so_hieu": "100/2019/NĐ-CP",
        "domain": "giao_thong"
    }
    
    logger.info("Starting chunking process on sample text...")
    chunks = chunk_legal_document(sample_text, metadata)
    
    for i, chunk in enumerate(chunks):
        logger.info(f"--- CHUNK {i+1} ---")
        logger.info(f"Metadata: {chunk.metadata}")
        logger.info(f"Text:\n{chunk.text}\n")
        
if __name__ == "__main__":
    run_chunking_test()
