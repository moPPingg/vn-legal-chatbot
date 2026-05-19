# 🏛️ LegalAI — Architecture & Implementation Blueprint

> **Stack:** Python · FastAPI · LangGraph · Qdrant · LLM Wiki · LangSmith  
> **Model:** gemma3:12b (Ollama local) · vietnamese-sbert (embedding)  
> **Frontend:** Giữ nguyên React hiện tại  
> **Mục tiêu:** Demo-ready → Production-ready với tài liệu nội bộ

---

## 1. Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (React)                    │
│  - Chat UI                                           │
│  - Document Viewer Panel (bên phải, như Claude)      │
│  - PDF Viewer với highlight điều luật                │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP / SSE (streaming)
┌─────────────────────▼───────────────────────────────┐
│              API Gateway (FastAPI)                   │
│  POST /api/chat          - câu hỏi người dùng        │
│  GET  /api/document/{id} - lấy PDF + metadata        │
│  GET  /api/domains       - danh sách lĩnh vực        │
│  WS   /api/stream        - streaming response        │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           LangGraph Orchestrator                     │
│                                                      │
│  START → [Query Classifier]                          │
│              ↓                                       │
│         [Legal Retriever] ←── Qdrant (Wiki Index)   │
│              ↓                 Qdrant (Doc Index)    │
│         [Legal Analyzer]                             │
│              ↓                                       │
│         [Fact Checker] ←── metadata: năm, hiệu lực  │
│              ↓                                       │
│         [Response Generator] → SSE stream            │
│              ↓                                       │
│            END                                       │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        ▼                            ▼
┌───────────────┐          ┌─────────────────────┐
│    Qdrant     │          │   LLM Wiki Store     │
│  Vector DB    │          │   (JSON + embedded)  │
│               │          │                      │
│  Collection:  │          │  wiki_entries/       │
│  legal_docs   │          │    giao_thong/       │
│  legal_wiki   │          │    hinh_su/          │
└───────────────┘          │    hon_nhan/...      │
                           └─────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              LangSmith (Monitoring)                  │
│  - Trace mọi LangGraph run                           │
│  - Eval retrieval quality                            │
│  - A/B test prompt versions                          │
└─────────────────────────────────────────────────────┘
```

---

## 2. Cấu trúc thư mục chuẩn

```
legalai/
│
├── backend/                        # Python backend
│   │
│   ├── app/                        # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, routes, CORS
│   │   ├── config.py               # Pydantic Settings, load .env
│   │   ├── dependencies.py         # Dependency injection (DB, LLM)
│   │   └── routes/
│   │       ├── chat.py             # POST /api/chat
│   │       ├── documents.py        # GET /api/document/{id}
│   │       └── health.py           # GET /health
│   │
│   ├── agents/                     # LangGraph agents
│   │   ├── __init__.py
│   │   ├── graph.py                # LangGraph StateGraph definition
│   │   ├── state.py                # AgentState TypedDict
│   │   ├── query_classifier.py     # Agent 1: phân loại domain
│   │   ├── legal_retriever.py      # Agent 2: tìm wiki + doc chunks
│   │   ├── legal_analyzer.py       # Agent 3: phân tích, tổng hợp
│   │   ├── fact_checker.py         # Agent 4: kiểm tra hiệu lực
│   │   └── response_generator.py  # Agent 5: sinh câu trả lời + SSE
│   │
│   ├── wiki/                       # LLM Wiki system
│   │   ├── __init__.py
│   │   ├── generator.py            # Generate wiki entries từ văn bản
│   │   ├── validator.py            # Validate JSON output của LLM
│   │   ├── ingestor.py             # Embed wiki entries → Qdrant
│   │   └── schema.py               # WikiEntry Pydantic model
│   │
│   ├── pipeline/                   # Data pipeline (offline)
│   │   ├── __init__.py
│   │   ├── crawler/
│   │   │   ├── vbpl_crawler.py     # Cào vbpl.vn (nguồn chính thống)
│   │   │   ├── thuvienphapluat.py  # Backup crawler
│   │   │   └── pdf_downloader.py   # Tải PDF gốc về
│   │   ├── processor/
│   │   │   ├── pdf_reader.py       # Đọc PDF → text (pdfplumber)
│   │   │   ├── html_cleaner.py     # Clean HTML từ crawler
│   │   │   ├── chunker.py          # Legal-aware chunking
│   │   │   └── metadata_extractor.py # Trích số hiệu, ngày, điều
│   │   └── ingestor/
│   │       ├── embedder.py         # vietnamese-sbert embedding
│   │       ├── qdrant_ingestor.py  # Upload lên Qdrant
│   │       └── run_pipeline.py     # Script chạy toàn bộ pipeline
│   │
│   ├── retrieval/                  # Retrieval logic
│   │   ├── __init__.py
│   │   ├── qdrant_client.py        # Wrapper Qdrant operations
│   │   ├── hybrid_search.py        # Dense + BM25 hybrid search
│   │   ├── reranker.py             # Year boost + keyword boost
│   │   └── citation_builder.py    # Build citation + PDF link
│   │
│   ├── llm/                        # LLM clients
│   │   ├── __init__.py
│   │   ├── ollama_client.py        # Ollama local (gemma3:12b)
│   │   ├── api_client.py           # Gemini/OpenAI (production)
│   │   └── prompt_templates.py     # Tất cả prompt templates
│   │
│   ├── storage/                    # File storage
│   │   ├── pdfs/                   # PDF gốc đã tải về
│   │   │   └── {domain}/{doc_id}.pdf
│   │   └── wiki_entries/           # Wiki JSON files
│   │       └── {domain}/{doc_id}.json
│   │
│   ├── tests/                      # Pytest test suite
│   │   ├── test_retrieval.py
│   │   ├── test_chunking.py
│   │   ├── test_wiki_generator.py
│   │   └── golden_dataset.json     # 100 câu hỏi + đáp án chuẩn
│   │
│   ├── scripts/                    # CLI scripts
│   │   ├── run_crawler.py
│   │   ├── run_wiki_generator.py
│   │   └── run_evaluation.py
│   │
│   ├── .env                        # Biến môi trường (không commit)
│   ├── .env.example                # Template .env
│   ├── pyproject.toml              # Dependencies (uv hoặc poetry)
│   └── Dockerfile
│
├── frontend/                       # React (giữ nguyên, chỉ thêm)
│   └── src/
│       └── components/
│           └── DocumentViewer/     # Panel PDF bên phải (thêm mới)
│               ├── PdfPanel.jsx
│               └── CitationCard.jsx
│
├── docker-compose.yml              # Qdrant + Backend + Ollama
├── .gitignore
└── README.md
```

---

## 3. Data Sources — Cào từ đâu

Dataset HuggingFace hiện tại **không đủ** vì:
- Không có file PDF gốc (chỉ có text, không link được)
- Thiếu nhiều văn bản cấp thông tư, quyết định địa phương
- Metadata không chuẩn (thiếu trạng thái hiệu lực)

### Nguồn chính thống nên cào:

| Nguồn | URL | Nội dung | Ưu tiên |
|---|---|---|---|
| **VBPL** (chính phủ) | vbpl.vn | Toàn bộ văn bản PL, có PDF gốc, có trạng thái hiệu lực | 🔴 Cao nhất |
| **Thư viện Pháp luật** | thuvienphapluat.vn | Đầy đủ, có full text, cập nhật nhanh | 🟠 Cao |
| **Cổng TTĐT Chính phủ** | chinhphu.vn | Nghị định, quyết định chính phủ | 🟡 Trung bình |
| **Bộ Tư pháp** | moj.gov.vn | Văn bản tư pháp, hôn nhân, hình sự | 🟡 Trung bình |

### Ưu tiên cào theo domain:

```python
CRAWL_PRIORITY = {
    "giao_thong":  ["vbpl.vn/giao-thong", "NĐ 168/2024"],
    "hinh_su":     ["vbpl.vn/hinh-su", "BLHS 2015 sửa đổi 2017"],
    "hon_nhan":    ["vbpl.vn/hon-nhan-gia-dinh", "Luật HN&GĐ 2014"],
    "lao_dong":    ["vbpl.vn/lao-dong", "BLLĐ 2019"],
    "dat_dai":     ["vbpl.vn/dat-dai", "Luật Đất đai 2024"],
    "doanh_nghiep":["vbpl.vn/doanh-nghiep", "Luật DN 2020"],
}
```

### Metadata cần lưu cho mỗi văn bản:

```python
class LegalDocument(BaseModel):
    id: str                    # UUID
    so_hieu: str               # "168/2024/NĐ-CP"
    ten_van_ban: str           # Tên đầy đủ
    loai_van_ban: str          # "Nghị định" | "Thông tư" | "Luật"...
    co_quan_ban_hanh: str      # "Chính phủ" | "Bộ GTVT"...
    ngay_ban_hanh: date
    ngay_hieu_luc: date
    ngay_het_hieu_luc: Optional[date]  # None = còn hiệu lực
    tinh_trang: str            # "Còn hiệu lực" | "Hết hiệu lực"
    thay_the: List[str]        # ["100/2019/NĐ-CP", "15/2003/NĐ-CP"]
    domain: str                # "giao_thong"
    pdf_url: str               # URL PDF gốc trên vbpl.vn
    pdf_local_path: str        # Đường dẫn local sau khi tải về
    full_text: str             # Nội dung text đã clean
```

---

## 4. Legal-aware Chunking

Không dùng character-based chunking. Tách theo cấu trúc văn bản pháp lý:

```python
# pipeline/processor/chunker.py

import re
from typing import List
from app.schema import LegalChunk

ARTICLE_PATTERN = re.compile(r'(?=Điều \d+[\.\:\s])')
CLAUSE_PATTERN  = re.compile(r'(?=\d+\.\s)')
POINT_PATTERN   = re.compile(r'(?=[a-zđ]\)\s)')

def chunk_legal_document(text: str, metadata: dict) -> List[LegalChunk]:
    chunks = []
    articles = ARTICLE_PATTERN.split(text)

    for article in articles:
        if not article.strip():
            continue

        article_header = article.split('\n')[0].strip()  # "Điều 5. Xử phạt..."

        # Nếu điều ngắn → giữ nguyên 1 chunk
        if len(article) <= 2000:
            chunks.append(LegalChunk(
                text=article.strip(),
                metadata={**metadata, "article_header": article_header}
            ))
            continue

        # Điều dài → tách theo Khoản, nhưng GIỮ header điều cha
        clauses = CLAUSE_PATTERN.split(article)
        header = clauses[0]  # "Điều 5. Xử phạt người điều khiển xe ô tô..."

        for clause in clauses[1:]:
            chunk_text = f"{article_header}\n{clause.strip()}"
            chunks.append(LegalChunk(
                text=chunk_text,
                metadata={**metadata, "article_header": article_header}
            ))

    return chunks
```

---

## 5. LLM Wiki Generator

```python
# wiki/generator.py

WIKI_PROMPT = """
Bạn là chuyên gia pháp lý Việt Nam. Đọc văn bản pháp luật sau và tạo wiki entry.

VĂN BẢN:
Tên: {ten_van_ban}
Số hiệu: {so_hieu}
Năm: {nam_ban_hanh}
Nội dung:
{noi_dung}

Tạo wiki entry JSON (không giải thích thêm):
{{
  "concept": "Tên khái niệm pháp lý chính",
  "summary": "Tóm tắt 2-3 câu",
  "keywords": ["từ khóa 1", "từ khóa 2"],
  "applies_to": ["ô tô", "xe máy"],
  "penalties": {{
    "o_to": {{"muc_1": "6-8 triệu", "muc_2": "...", "muc_3": "..."}},
    "xe_may": {{"muc_1": "2-3 triệu", "muc_2": "...", "muc_3": "..."}}
  }},
  "conditions": ["điều kiện áp dụng"],
  "legal_basis": ["Điều 5 NĐ 168/2024/NĐ-CP"],
  "supersedes": ["100/2019/NĐ-CP"],
  "effective_date": "2025-01-01",
  "still_valid": true
}}
"""
```

---

## 6. LangGraph Pipeline

```python
# agents/state.py
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    # Input
    question: str
    domain: Optional[str]
    conversation_history: List[dict]

    # Pipeline state
    rewritten_query: str
    predicted_domain: str
    wiki_results: List[dict]
    doc_results: List[dict]
    merged_context: str
    citations: List[dict]       # [{so_hieu, dieu, pdf_url, pdf_page}]

    # Output
    answer: str
    confidence: str             # "high" | "medium" | "low"
    follow_up: str
    error: Optional[str]
```

```python
# agents/graph.py
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents import (
    query_classifier,
    legal_retriever,
    legal_analyzer,
    fact_checker,
    response_generator
)

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("classify",   query_classifier.run)
    graph.add_node("retrieve",   legal_retriever.run)
    graph.add_node("analyze",    legal_analyzer.run)
    graph.add_node("fact_check", fact_checker.run)
    graph.add_node("generate",   response_generator.run)

    graph.set_entry_point("classify")
    graph.add_edge("classify",   "retrieve")
    graph.add_edge("retrieve",   "analyze")
    graph.add_edge("analyze",    "fact_check")
    graph.add_edge("fact_check", "generate")
    graph.add_edge("generate",   END)

    return graph.compile()
```

---

## 7. Citation + PDF Viewer

### Backend — Citation Builder:

```python
# retrieval/citation_builder.py

def build_citation(chunk: dict) -> dict:
    return {
        "so_hieu":    chunk["metadata"]["so_hieu"],       # "168/2024/NĐ-CP"
        "ten_van_ban":chunk["metadata"]["ten_van_ban"],
        "dieu":       chunk["metadata"]["article_header"], # "Điều 5. Xử phạt..."
        "trang":      chunk["metadata"].get("page_number"),
        "pdf_url":    chunk["metadata"]["pdf_local_path"], # serve qua /api/document
        "snippet":    chunk["text"][:300],                 # preview text
        "still_valid":chunk["metadata"]["tinh_trang"] == "Còn hiệu lực"
    }
```

### Frontend — Document Viewer Panel:

Thêm vào React (không đổi UI chính):

```
┌─────────────────────┬──────────────────────┐
│   Chat UI           │   Document Viewer    │
│                     │   (slide-in panel)   │
│  🤖 Theo NĐ 168/   │  ┌────────────────┐  │
│  2024, mức phạt... │  │ 📄 168/2024/   │  │
│                     │  │    NĐ-CP       │  │
│  Cơ sở pháp lý:    │  │                │  │
│  [📄 Điều 5 →]     │  │ [PDF rendered] │  │
│  [📄 Điều 6 →]     │  │                │  │
│                     │  │ Điều 5 được   │  │
│                     │  │ highlight     │  │
│                     │  └────────────────┘  │
└─────────────────────┴──────────────────────┘
```

Components cần thêm:
- `CitationCard.jsx` — card nhỏ hiển thị tên văn bản + điều khoản, click mở panel
- `PdfPanel.jsx` — panel bên phải, dùng `react-pdf` để render PDF, tự scroll đến trang có điều luật

---

## 8. LangSmith Integration

```python
# app/config.py
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"]    = settings.LANGSMITH_API_KEY
os.environ["LANGCHAIN_PROJECT"]    = "legalai-vietnam"
```

LangSmith tự động trace toàn bộ LangGraph runs — không cần code thêm.

Dùng LangSmith để:
- Xem từng bước agent làm gì
- So sánh retrieval quality giữa các version
- Tạo dataset evaluation từ các câu hỏi thực tế

---

## 9. Thứ tự triển khai (làm ngay)

```
Tuần này:
  [x] Bước 1: Dọn dẹp folder structure theo chuẩn trên
  [ ] Bước 2: Cài Qdrant local (docker run qdrant/qdrant)
  [ ] Bước 3: Viết crawler vbpl.vn — cào domain giao thông trước
  [ ] Bước 4: Chạy legal-aware chunker trên data đã cào
  [ ] Bước 5: Embed + ingest vào Qdrant
  [ ] Bước 6: Test retrieval — query "nồng độ cồn ô tô"

Tuần sau:
  [ ] Bước 7: Chạy LLM Wiki Generator cho domain giao thông
  [ ] Bước 8: Build LangGraph pipeline (5 agents)
  [ ] Bước 9: Tích hợp LangSmith
  [ ] Bước 10: Thêm CitationCard + PdfPanel vào React
  [ ] Bước 11: Test end-to-end, so sánh với version cũ
  [ ] Bước 12: Mở rộng sang domain hình sự, hôn nhân
```

---

## 10. .env chuẩn

```env
# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:12b
OLLAMA_WIKI_MODEL=gemma3:12b

# Embedding
EMBEDDING_MODEL=keepitreal/vietnamese-sbert

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_DOCS=legal_docs
QDRANT_COLLECTION_WIKI=legal_wiki

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=legalai-vietnam

# Storage
PDF_STORAGE_PATH=./storage/pdfs
WIKI_STORAGE_PATH=./storage/wiki_entries

# API
CORS_ORIGINS=http://localhost:3000
MAX_RETRIEVAL_RESULTS=10
```

---

## 11. Ghi chú cho production (tài liệu nội bộ công ty)

Khi chuyển từ demo luật công khai → tài liệu nội bộ công ty:

| Thay đổi | Demo (luật VN) | Production (công ty) |
|---|---|---|
| LLM | Ollama local | Giữ Ollama local (bảo mật) |
| Data source | vbpl.vn crawler | Upload PDF nội bộ |
| Auth | Không cần | JWT + role-based |
| Qdrant | Local Docker | Self-hosted server |
| LangSmith | Cloud (free tier) | Self-hosted hoặc tắt |
| PDF storage | Local `./storage/pdfs` | S3-compatible (MinIO) |

**Lý do giữ Ollama cho production:** Tài liệu công ty không được gửi lên API bên ngoài (Gemini/OpenAI). Ollama local đảm bảo data không rời khỏi server công ty.