# 🔍 LegalAI — Audit Prompt & Logic Gap Checker

> **Mục đích:** Kiểm tra toàn bộ codebase hiện tại so với kiến trúc đã thiết kế
> **Dán toàn bộ file này vào opencode. Làm tuần tự, báo cáo từng phần.**

---

## PHẦN 1 — AUDIT TOÀN BỘ CODEBASE (Không sửa gì)

Đọc toàn bộ thư mục `D:\CHATBOT\` và báo cáo theo bảng sau:

### 1.1 Kiểm tra folder structure

So sánh folder thực tế với chuẩn sau và đánh dấu ✅/❌:

```
backend/
├── app/                        ✅/❌
│   ├── main.py                 ✅/❌
│   ├── config.py               ✅/❌
│   ├── routes/
│   │   ├── chat.py             ✅/❌
│   │   ├── documents.py        ✅/❌
│   │   └── health.py           ✅/❌
├── agents/                     ✅/❌
│   ├── graph.py                ✅/❌
│   ├── state.py                ✅/❌
│   ├── query_classifier.py     ✅/❌
│   ├── legal_retriever.py      ✅/❌
│   ├── legal_analyzer.py       ✅/❌
│   ├── fact_checker.py         ✅/❌
│   └── response_generator.py   ✅/❌
├── wiki/                       ✅/❌
│   ├── generator.py            ✅/❌
│   ├── validator.py            ✅/❌
│   └── schema.py               ✅/❌
├── pipeline/
│   ├── crawler/
│   │   └── vbpl_crawler.py     ✅/❌
│   └── processor/
│       ├── chunker.py          ✅/❌
│       └── metadata_extractor.py ✅/❌
├── retrieval/
│   ├── hybrid_search.py        ✅/❌
│   ├── reranker.py             ✅/❌
│   └── citation_builder.py     ✅/❌
├── storage/
│   ├── pdfs/giao_thong/        ✅/❌
│   └── raw/giao_thong/         ✅/❌
```

Liệt kê thêm các file/folder THỪA không có trong chuẩn.

---

### 1.2 Kiểm tra LangGraph pipeline

Đọc `agents/graph.py` và trả lời:

- [ ] Có đủ 5 nodes: `classify → retrieve → analyze → fact_check → generate`?
- [ ] `AgentState` trong `state.py` có các field: `question`, `rewritten_query`, `predicted_domain`, `wiki_results`, `doc_results`, `citations`, `answer`?
- [ ] LangGraph có được compile và gọi trong `app/routes/chat.py` không?
- [ ] Có streaming SSE response không hay vẫn trả JSON đồng bộ?

Paste toàn bộ nội dung `agents/graph.py` và `agents/state.py` ra.

---

### 1.3 Kiểm tra Retrieval

Đọc `retrieval/citation_builder.py` và trả lời:

- [ ] Hàm `build_citation()` có kiểm tra file PDF tồn tại trên disk không?
- [ ] `pdf_url` trả về có dạng `http://localhost:8000/api/document/{domain}/{filename}.pdf` không?
- [ ] Khi PDF không tồn tại, có trả `null` thay vì dummy URL không?

Paste toàn bộ nội dung `retrieval/citation_builder.py` ra.

---

### 1.4 Kiểm tra PDF serving

Đọc `app/routes/documents.py` và trả lời:

- [ ] Có endpoint `GET /api/document/{domain}/{filename}` không?
- [ ] Có dùng `FileResponse` với `media_type="application/pdf"` không?
- [ ] Có header `Access-Control-Allow-Origin: *` không?
- [ ] Có sanitize path để tránh `../` attack không?

Chạy lệnh test thật:
```powershell
curl.exe http://localhost:8000/api/document/giao_thong/168-2024-ND-CP.pdf --output test_download.pdf
python -c "import fitz; doc=fitz.open('test_download.pdf'); print(doc[0].get_text()[:300])"
```

Paste output ra.

---

### 1.5 Kiểm tra Embedding & Vector DB

Trả lời:

- [ ] Đang dùng Qdrant hay FAISS? (Thiết kế yêu cầu Qdrant)
- [ ] Embedding model là gì? (Phải là `keepitreal/vietnamese-sbert`)
- [ ] Collection trong Qdrant có tên `legal_docs` và `legal_wiki` không?
- [ ] Chunking dùng regex theo `Điều/Khoản` hay vẫn character-based?

Chạy:
```python
python -c "
from qdrant_client import QdrantClient
client = QdrantClient('localhost', port=6333)
collections = client.get_collections()
print('Collections:', collections)
for col in collections.collections:
    info = client.get_collection(col.name)
    print(f'{col.name}: {info.points_count} vectors')
"
```

Paste output ra.

---

### 1.6 Kiểm tra LLM Wiki

Trả lời:

- [ ] File `wiki/generator.py` có tồn tại không?
- [ ] Nếu có, nó đã được chạy chưa? (Kiểm tra `storage/wiki_entries/` có file nào không)
- [ ] Wiki entries có được index vào Qdrant collection `legal_wiki` không?

---

### 1.7 Kiểm tra LangSmith

Trả lời:

- [ ] `.env` có `LANGCHAIN_TRACING_V2=true` và `LANGCHAIN_API_KEY` không?
- [ ] `app/main.py` có import và set LangSmith env vars không?
- [ ] Khi gọi `/api/chat`, có trace xuất hiện trên app.langsmith.com không?

---

## PHẦN 2 — BÁO CÁO LỖ HỔNG LOGIC

Sau khi audit xong, tạo bảng báo cáo theo format:

```
| # | Thành phần | Vấn đề phát hiện | Mức độ | Nguyên nhân gốc |
|---|---|---|---|---|
| 1 | citation_builder | pdf_url trỏ sai port | 🔴 Critical | ... |
| 2 | ... | ... | ... | ... |
```

M��c độ:
- 🔴 Critical — người dùng thấy lỗi trực tiếp
- 🟠 High — ảnh hưởng chất lượng trả lời
- 🟡 Medium — thiếu feature nhưng không crash
- 🟢 Low — nice to have

---

## PHẦN 3 — FIX THEO THỨ TỰ ƯU TIÊN

Sau khi có bảng lỗ hổng, fix theo thứ tự 🔴 → 🟠 → 🟡.

**Quy tắc bắt buộc:**
1. Fix xong 1 lỗi → chạy test verify → báo cáo kết quả → mới fix lỗi tiếp theo
2. KHÔNG fix nhiều lỗi cùng lúc
3. KHÔNG báo "đã fix" mà không chạy lệnh verify thật
4. Nếu fix gây ra lỗi mới → revert ngay, báo cáo, hỏi hướng xử lý

---

## PHẦN 4 — VERIFY CUỐI (Chạy sau khi fix xong tất cả)

Chạy toàn bộ checklist này và báo cáo từng dòng ✅/❌:

```powershell
# Test 1: Backend khởi động không lỗi
curl.exe http://localhost:8000/health

# Test 2: API documents hoạt động
curl.exe http://localhost:8000/api/documents/giao_thong

# Test 3: PDF thật được serve
curl.exe http://localhost:8000/api/document/giao_thong/168-2024-ND-CP.pdf --output verify.pdf
python -c "import fitz; doc=fitz.open('verify.pdf'); print('Pages:', doc.page_count); print(doc[0].get_text()[:200])"

# Test 4: Chat trả về citation có pdf_url thật
curl.exe -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"uong ruou bia lai xe o to phat bao nhieu\", \"domain\": \"giao_thong\"}"
```

Với Test 4, kiểm tra response JSON:
- [ ] `citations` array có ít nhất 1 item
- [ ] Mỗi citation có `pdf_url` không null
- [ ] `pdf_url` trỏ đúng `http://localhost:8000/api/document/giao_thong/...`
- [ ] `still_valid` đúng với tình trạng hiệu lực thật

---

## PHẦN 5 — KIỂM TRA FRONTEND

Sau khi backend verify xong:

1. Mở `http://localhost:3000`
2. Chọn lĩnh vực Giao thông
3. Hỏi: **"uống rượu bia khi lái xe ô tô phạt bao nhiêu"**
4. Mở DevTools (F12) → tab Network
5. Click vào citation card bất kỳ
6. Kiểm tra request PDF trong Network tab:
   - URL có đúng không?
   - Status code có phải 200 không?
   - Content-Type có phải `application/pdf` không?

Chụp ảnh màn hình Network tab và PDF viewer bên phải gửi để xác nhận.

---

## GHI NHỚ — Các điểm kỹ thuật BẮT BUỘC phải đúng

| Yêu cầu | Đúng thì | Sai thì |
|---|---|---|
| Vector DB | Qdrant | Không dùng FAISS |
| Embedding | `keepitreal/vietnamese-sbert` | Không dùng MiniLM |
| LLM local | `gemma3:12b` qua Ollama | Không dùng mistral cho wiki |
| Chunking | Regex theo `Điều/Khoản` | Không character-based |
| Pipeline | LangGraph 5 agents | Không monolithic pipeline |
| Monitoring | LangSmith traces | Phải có trace cho mỗi request |
| PDF | File thật từ chinhphu.vn | Không dùng dummy/copy |
| Citation | `pdf_url` trỏ file thật | Không null, không fallback dummy |