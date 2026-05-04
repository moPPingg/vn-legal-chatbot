# 🔗 AI PIPELINE — VIETNAM LEGAL ASSISTANT

## 1. OVERVIEW

Pipeline gồm 5 stage:

1. Input Processing
2. Retrieval (RAG)
3. Prompt Construction
4. LLM Inference
5. Validation & Response

---

## 2. PIPELINE FLOW

User Input
  ↓
Validate Input
  ↓
Check law_type
  ↓
Vector Search (filter by law_type)
  ↓
Top-K Context Retrieval
  ↓
Prompt Builder
  ↓
LLM
  ↓
JSON Validator
  ↓
Response to User

---

## 3. STAGE DETAILS

### 3.1 Input Processing

- Validate:
  - question != empty
  - law_type exists

---

### 3.2 Retrieval (RAG)

- Input:
  - question
  - law_type

- Process:
  - embedding(question)
  - search vector DB
  - filter by law_type

- Output:
  - top_k documents

---

### 3.3 Prompt Construction

Combine:

- system prompt
- retrieved_context
- user question

---

### 3.4 LLM Inference

- Call model (OpenAI / local)
- temperature: low (0–0.3)
- max_tokens: controlled

---

### 3.5 Validation Layer (VERY IMPORTANT)

Check:

- Is valid JSON?
- Missing fields?
- legal_basis empty but answer strong? → flag
- hallucination detection (basic)

If fail:
→ retry or fallback response

---

## 4. AGENT LOGIC (BASIC)

IF no context found:
→ return fallback

IF low confidence:
→ suggest user refine question

IF domain mismatch:
→ suggest new law_type

---

## 5. ERROR HANDLING

### JSON Error
→ retry with stricter prompt

### Empty Answer
→ fallback message

### LLM Failure
→ return safe error message

---

## 6. EXTENSIONS (FOR FUTURE)

- Multi-agent:
  - Retriever agent
  - Answer agent
  - Validator agent

- RAG improvement:
  - re-ranking
  - hybrid search

- Tools:
  - search API
  - legal database

---

## 7. LOGGING (OPTIONAL BUT STRONG)

Store:

- question
- law_type
- retrieved docs
- response
- confidence

→ dùng để debug + improve

---

## 8. PERFORMANCE OPTIMIZATION

- cache embeddings
- cache frequent queries
- limit top_k

---

## 9. INTERVIEW TALKING POINT

Explain:

- Why RAG instead of fine-tune
- Why law_type filtering
- Why validation layer exists
- How you reduce hallucination