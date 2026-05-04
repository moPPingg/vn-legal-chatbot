# 📚 DATA PROCESSING — LEGAL DATASET

## 1. DATA SOURCE

Vietnamese legal documents dataset

---

## 2. PREPROCESSING

### Step 1: Cleaning
- remove noise
- normalize text

---

### Step 2: Chunking

Split into:

{
  "law_type": "hình sự",
  "article": "Điều 123",
  "content": "..."
}

---

### Step 3: Metadata tagging

Add:
- law_type
- article
- keywords

---

## 3. EMBEDDING

Convert text → vector

---

## 4. STORAGE

Store:
- vector
- metadata

---

## 5. RETRIEVAL STRATEGY

- similarity search
- filter by law_type

---

## 6. IMPROVEMENTS

- chunk size tuning
- overlap chunks
- keyword boosting

---

## 7. COMMON ISSUES

- chunk too large → mất chính xác
- chunk quá nhỏ → mất context