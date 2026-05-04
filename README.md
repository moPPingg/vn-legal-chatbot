# 🏛️ Vietnamese Legal AI Agent

Full-stack AI legal assistant: **FastAPI** + **Next.js** + **FAISS** + **TailwindCSS**

## Architecture

```
Frontend (Next.js + TailwindCSS)  →  /api/chat (Next.js API Route)  →  POST /chat (Python FastAPI)  →  FAISS Vector DB
```

## Project Structure

```
CHATBOT/
├── backend/                    # Python FastAPI
│   ├── app/
│   │   ├── main.py             # FastAPI server (POST /chat)
│   │   ├── config.py           # Environment config
│   │   ├── models.py           # Pydantic schemas
│   │   ├── pipeline.py         # 5-stage pipeline orchestrator
│   │   ├── prompt_builder.py   # System + user prompt
│   │   ├── llm_client.py       # OpenAI + JSON validation + retry
│   │   ├── classifier.py       # Law type classifier (sklearn)
│   │   ├── evaluator.py        # Batch evaluation script
│   │   └── rag/
│   │       ├── data_loader.py  # Parquet loading + cleaning
│   │       ├── chunker.py      # Text chunking
│   │       ├── embedder.py     # Sentence-transformers
│   │       ├── vector_store.py # FAISS index management
│   │       └── retriever.py    # Search + law_type filtering
│   ├── ingest.py               # Data ingestion CLI
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # Next.js (App Router)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Home — law selection
│   │   │   ├── chat/page.tsx   # Chat page
│   │   │   └── api/chat/route.ts # Proxy to Python
│   │   └── components/
│   │       ├── LawSelector.tsx
│   │       ├── ChatBox.tsx
│   │       └── MessageBubble.tsx
│   └── .env.local
├── docs/                       # Spec files
└── vietnamese-legal-documents/ # Dataset (parquet)
```

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env            # Edit: set OPENAI_API_KEY
python ingest.py --max-docs 2000  # Ingest data into FAISS
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev                     # → http://localhost:3000
```

### 3. Test

- Open http://localhost:3000
- Select a law category
- Ask a question in Vietnamese

### 4. Evaluate

```bash
cd backend
python -m app.evaluator
```

## API

| Method | Endpoint | Service |
|--------|----------|---------|
| POST | `/api/chat` | Next.js → proxies to Python |
| POST | `/chat` | Python FastAPI (AI processing) |
| POST | `/classify` | Python — predict law_type |
| GET | `/health` | Python — system status |
| GET | `/law-types` | Python — available categories |
