# 📊 EVALUATION — LEGAL AI SYSTEM

## 1. GOAL

Measure:
- accuracy
- hallucination rate

---

## 2. METRICS

- Answer correctness
- Legal citation accuracy
- Confidence alignment

---

## 3. TEST SET

Manual dataset:

{
  "question": "...",
  "expected_answer": "...",
  "expected_law": "..."
}

---

## 4. METHOD

- run batch queries
- compare outputs

---

## 5. FAILURE ANALYSIS

- wrong law_type
- missing context
- hallucination

---

## 6. IMPROVEMENT LOOP

- adjust prompt
- adjust retrieval
- improve chunking