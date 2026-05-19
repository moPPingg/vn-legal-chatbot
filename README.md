# LegalAI

LegalAI la chatbot phap ly tieng Viet voi kien truc `FastAPI + LangGraph + Qdrant + Ollama + Next.js`.

## Stack

- Backend: FastAPI, LangGraph
- Retrieval: Qdrant, `keepitreal/vietnamese-sbert`
- LLM local: Ollama
- Frontend: Next.js, React, `react-pdf`
- Monitoring: LangSmith

## Kien truc hien tai

Luong chinh:

`Frontend -> /api/chat (Next.js route) -> /api/chat (FastAPI) -> LangGraph -> Qdrant -> citations + PDF viewer`

LangGraph hien tai gom 5 node:

1. `query_classifier`
2. `legal_retriever`
3. `legal_analyzer`
4. `fact_checker`
5. `response_generator`

## Cau truc thu muc chinh

```text
backend/
  app/
    main.py
    config.py
    schema.py
    routes/
      chat.py
      documents.py
      health.py
  agents/
    graph.py
    state.py
    query_classifier.py
    legal_retriever.py
    legal_analyzer.py
    fact_checker.py
    response_generator.py
  retrieval/
    qdrant_client.py
    hybrid_search.py
    citation_builder.py
  pipeline/
    crawler/
      vbpl_crawler.py
      pdf_downloader.py
    converter/
      file_converter.py
      crawler_integration.py
    processor/
      pdf_reader.py
      chunker.py
    ingestor/
      embedder.py
      qdrant_ingestor.py
  wiki/
    generator.py
  storage/
    pdfs/
    raw/
    downloads/

frontend/
  src/
    app/
      page.tsx
      api/chat/route.ts
    components/
      DocumentViewer/
        CitationCard.tsx
        PdfPanel.tsx
```

## Tinh nang dang co

- Chat phap ly theo domain
- Retrieval theo Qdrant
- Citation co `pdf_url` tro den file PDF that
- Document Viewer ben phai bang `react-pdf`
- Tu dong normalize file tai lieu ve PDF trong pipeline crawler

## Chay local

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
```

Can cac dich vu:

- Qdrant tai `http://localhost:6333`
- Ollama tai `http://localhost:11434`

Chay backend:

```bash
cd ..
D:\CHATBOT\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend mac dinh chay tai `http://localhost:3000` va goi backend qua `PYTHON_API_URL=http://localhost:8000`.

## API chinh

- `GET /health`
- `POST /api/chat`
- `GET /api/documents/{domain}`
- `GET /api/document/{domain}/{filename}`
- `GET /api/document/{domain}/{filename}/metadata`

## Ghi chu

- README nay da duoc cap nhat theo `LEGALAI_ARCHITECTURE.md`.
- Tai lieu huong dan crawler cu da bi loai bo de tranh lech voi codebase hien tai.
