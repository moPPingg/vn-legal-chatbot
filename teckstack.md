# 🚀 TECH STACK & IMPLEMENTATION SPEC
## Vietnam Legal AI Assistant

---

# 1. OVERVIEW

This system is a full-stack AI-powered legal assistant with:

- Python (FastAPI) → AI processing (RAG, prompt, validation)
- NextJS → Frontend + Backend API layer
- TailwindCSS → UI styling
- Vector DB (FAISS) → document retrieval

---

# 2. SYSTEM ARCHITECTURE

Frontend (NextJS + Tailwind)
        ↓
Backend API (NextJS API Routes)
        ↓
AI Service (Python FastAPI)
        ↓
Vector DB (FAISS) + Legal Dataset

---

# 3. TECH STACK

## 3.1 Frontend

- Framework: NextJS (App Router)
- Styling: TailwindCSS
- State: React useState / useReducer
- API: fetch (call internal API routes)

---

## 3.2 Backend (Gateway Layer)

- NextJS API Routes
- Acts as proxy between frontend and Python service

Responsibilities:
- Receive user input
- Forward request to Python API
- Return response

---

## 3.3 AI Backend

- Language: Python
- Framework: FastAPI
- Libraries:
  - openai OR transformers
  - sentence-transformers (embedding)
  - faiss (vector search)
  - pydantic (validation)

---

## 3.4 Database

- Vector DB: FAISS (local)
- Data: Vietnamese legal documents

---

# 4. FRONTEND REQUIREMENTS

## 4.1 Law Selection UI

- Display list of law categories:
  - Criminal (Hình sự)
  - Civil (Dân sự)
  - Labor (Lao động)
  - Traffic (Giao thông)

- User must select before chatting

---

## 4.2 Chat Interface

- Input box for user question
- Display:
  - Answer
  - Legal basis
  - Confidence level

---

## 4.3 UI Constraints

- Must use TailwindCSS
- Responsive layout
- Clean, minimal design

---

# 5. API DESIGN

## 5.1 NextJS API Route

Endpoint:
POST /api/chat

Input:
{
  "question": "string",
  "lawType": "string"
}

Process:
- Forward request to Python API

---

## 5.2 Python API

Endpoint:
POST /chat

Input:
{
  "question": "string",
  "lawType": "string"
}

Output:
{
  "answer": "string",
  "legal_basis": ["string"],
  "confidence": "low | medium | high"
}

---

# 6. AI PIPELINE

## Step 1: Input Validation

- Ensure question exists
- Ensure lawType exists

---

## Step 2: Retrieval (RAG)

- Convert question → embedding
- Search FAISS index
- Filter by lawType
- Return top_k documents

---

## Step 3: Prompt Construction

Combine:
- system prompt
- retrieved documents
- user question

---

## Step 4: LLM Call

- temperature: 0–0.3
- ensure deterministic output

---

## Step 5: Validation

- Ensure JSON format
- Ensure no missing fields
- Ensure no hallucination

---

# 7. RAG IMPLEMENTATION

## 7.1 Data Processing

- Load dataset
- Chunk into small pieces
- Add metadata:
  - law_type
  - article

---

## 7.2 Embedding

- Use sentence-transformers OR OpenAI embeddings

---

## 7.3 Vector Store

- Use FAISS
- Store embeddings + metadata

---

## 7.4 Retrieval

- similarity search
- filter by law_type

---

# 8. PROJECT STRUCTURE

/project
  /frontend (NextJS)
  /backend (FastAPI)
  /docs (rule.md, prompt.md, pipeline.md)
  /data

---

# 9. DEVELOPMENT RULES

- Separate frontend and AI logic
- Never call LLM directly from frontend
- Always go through backend

---

# 10. ERROR HANDLING

- If Python API fails → return safe error
- If no context → fallback response
- If invalid JSON → retry

---

# 11. EXTENSION (OPTIONAL)

- Add streaming response
- Add chat history
- Add document highlighting
- Add multi-agent system

---

# 12. FINAL REQUIREMENTS

The system MUST:

- Use NextJS + TailwindCSS for frontend
- Use Python for AI processing
- Implement RAG
- Support law selection filtering
- Return structured JSON output
- Avoid hallucination

---

# END