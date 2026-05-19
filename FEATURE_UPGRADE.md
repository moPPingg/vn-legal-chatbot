# 🚀 LegalAI — Feature Upgrade Prompt

> **3 tính năng cần bổ sung:**
> 1. Auto convert Word/Excel/các định dạng khác → PDF khi upload
> 2. Verify PDF viewer hiển thị đúng văn bản thật (không phải Hello World)
> 3. Cấu trúc câu trả lời mới: Tóm tắt AI + Điều khoản có thể expand

---

## TÍNH NĂNG 1 — Auto Convert sang PDF khi upload

### Backend: Tạo `backend/pipeline/processor/file_converter.py`

```python
"""
Auto convert các định dạng file → PDF
Hỗ trợ: .docx, .doc, .xlsx, .xls, .pptx, .ppt, .txt, .html
"""

import subprocess
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
import fitz  # pymupdf

SUPPORTED_FORMATS = {
    ".docx": "word",
    ".doc":  "word",3
    ".xlsx": "excel",
    ".xls":  "excel",
    ".pptx": "powerpoint",
    ".ppt":  "powerpoint",
    ".txt":  "text",
    ".html": "html",
    ".pdf":  "pdf",  # đã là PDF, không cần convert
}

UPLOAD_DIR = Path("storage/uploads")
PDF_DIR    = Path("storage/pdfs/uploaded")


def ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload(file: UploadFile) -> Path:
    """Lưu file upload vào thư mục tạm"""
    ensure_dirs()
    save_path = UPLOAD_DIR / file.filename
    content = await file.read()
    save_path.write_bytes(content)
    return save_path


def convert_to_pdf(input_path: Path) -> Path:
    """
    Convert file sang PDF.
    Trả về Path của file PDF đã convert.
    """
    suffix = input_path.suffix.lower()

    if suffix not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng {suffix} không được hỗ trợ. "
                   f"Hỗ trợ: {', '.join(SUPPORTED_FORMATS.keys())}"
        )

    # Đã là PDF — copy thẳng sang thư mục đích
    if suffix == ".pdf":
        output_path = PDF_DIR / input_path.name
        shutil.copy2(input_path, output_path)
        return output_path

    output_path = PDF_DIR / (input_path.stem + ".pdf")

    # Dùng LibreOffice để convert (hỗ trợ tất cả định dạng Office)
    # Cài: winget install TheDocumentFoundation.LibreOffice
    libreoffice_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "soffice",  # nếu đã add vào PATH
    ]

    soffice = None
    for path in libreoffice_paths:
        if shutil.which(path) or Path(path).exists():
            soffice = path
            break

    if suffix in [".txt", ".html"] and not soffice:
        # Fallback: convert txt/html bằng Python thuần
        return _convert_text_to_pdf(input_path, output_path)

    if not soffice:
        raise HTTPException(
            status_code=500,
            detail="LibreOffice chưa được cài. Chạy: winget install TheDocumentFoundation.LibreOffice"
        )

    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf",
         "--outdir", str(PDF_DIR), str(input_path)],
        capture_output=True, text=True, timeout=60
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Convert thất bại: {result.stderr}"
        )

    return output_path


def _convert_text_to_pdf(input_path: Path, output_path: Path) -> Path:
    """Fallback: convert .txt hoặc .html sang PDF bằng pymupdf"""
    text = input_path.read_text(encoding="utf-8", errors="ignore")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50), text,
        fontsize=11,
        fontname="helv",
    )
    doc.save(str(output_path))
    doc.close()
    return output_path


def get_pdf_info(pdf_path: Path) -> dict:
    """Lấy thông tin cơ bản của PDF sau khi convert"""
    doc = fitz.open(str(pdf_path))
    return {
        "filename":   pdf_path.name,
        "page_count": doc.page_count,
        "file_size":  pdf_path.stat().st_size,
        "first_page_preview": doc[0].get_text()[:300],
    }
```

### Backend: Thêm endpoint upload vào `app/routes/documents.py`

```python
from fastapi import UploadFile, File
from pipeline.processor.file_converter import save_upload, convert_to_pdf, get_pdf_info

@router.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload file bất kỳ → tự động convert sang PDF
    Hỗ trợ: .docx, .xlsx, .pptx, .txt, .html, .pdf
    """
    # Lưu file upload
    saved_path = await save_upload(file)

    # Convert sang PDF
    pdf_path = convert_to_pdf(saved_path)

    # Lấy thông tin PDF
    info = get_pdf_info(pdf_path)

    return {
        "success": True,
        "original_filename": file.filename,
        "pdf_filename": pdf_path.name,
        "pdf_url": f"/api/document/uploaded/{pdf_path.name}",
        "page_count": info["page_count"],
        "preview": info["first_page_preview"],
        "message": f"Đã convert thành công sang PDF ({info['page_count']} trang)"
    }
```

### Cài LibreOffice (chạy 1 lần trong PowerShell):
```powershell
winget install TheDocumentFoundation.LibreOffice
```

### Test upload:
```powershell
# Tạo file test
echo "Day la van ban test" > test_upload.txt

# Upload và convert
curl.exe -X POST http://localhost:8000/api/upload ^
  -F "file=@test_upload.txt" ^
  -H "Accept: application/json"
```

**Kết quả mong đợi:**
```json
{
  "success": true,
  "original_filename": "test_upload.txt",
  "pdf_filename": "test_upload.pdf",
  "pdf_url": "/api/document/uploaded/test_upload.pdf",
  "page_count": 1,
  "message": "Đã convert thành công sang PDF (1 trang)"
}
```

---

## TÍNH NĂNG 2 — Verify PDF Viewer không còn Hello World

### Chạy lệnh verify này TRƯỚC KHI làm gì khác:

```powershell
# Bước 1: Kiểm tra 3 file PDF thật đã có chưa
python -c "
import fitz, os
folder = r'D:\CHATBOT\backend\storage\pdfs\giao_thong'
files = os.listdir(folder)
print(f'So file PDF: {len(files)}')
for f in files:
    path = os.path.join(folder, f)
    doc = fitz.open(path)
    text = doc[0].get_text()[:150].strip()
    size = os.path.getsize(path) // 1024
    print(f'--- {f} ({size}KB, {doc.page_count} trang) ---')
    print(text[:100])
    print()
"
```

**Nếu thấy nội dung khác nhau cho mỗi file → PASS**
**Nếu thấy "Hello, world!" hoặc nội dung giống nhau → FAIL, báo cáo ngay**

```powershell
# Bước 2: Test API serve PDF
curl.exe http://localhost:8000/api/document/giao_thong/168-2024-ND-CP.pdf --output verify_168.pdf
python -c "
import fitz
doc = fitz.open('verify_168.pdf')
print('NĐ 168 - Trang 1:')
print(doc[0].get_text()[:300])
"
```

**Phải thấy nội dung về NĐ 168/2024, không phải NĐ 100/2019**

```powershell
# Bước 3: Kiểm tra frontend gọi đúng URL
# Mở trình duyệt → F12 → tab Network → lọc "pdf"
# Hỏi chatbot: "uống rượu bia lái xe phạt bao nhiêu"
# Click vào citation card
# Paste URL của request PDF vào đây để xác nhận
```

**Checklist cuối:**
- [ ] PDF viewer bên phải hiện nội dung văn bản luật thật
- [ ] Tiêu đề panel đúng tên văn bản (VD: "168/2024/NĐ-CP — Điều 5")
- [ ] Số trang hiển thị đúng (VD: "Trang 1 / 47")
- [ ] Không còn "Hello, world!" nữa

---

## TÍNH NĂNG 3 — Cấu trúc câu trả lời mới

### Mục tiêu: Câu trả lời có 2 phần rõ ràng

```
┌─────────────────────────────────────────────┐
│  🤖 LegalAI                                  │
│                                             │
│  [PHẦN 1 — TÓM TẮT AI]                     │
│  Theo NĐ 168/2024, người lái ô tô có        │
│  nồng độ cồn sẽ bị phạt từ 6 đến 40        │
│  triệu đồng tùy mức vi phạm, kèm tước       │
│  GPLX 10–24 tháng...                        │
│                                             │
│  [PHẦN 2 — ĐIỀU KHOẢN LIÊN QUAN]           │
│  ┌─────────────────────────────┐            │
│  │ 📄 168/2024/NĐ-CP  [Còn HLực] →│        │
│  │ Điều 5. Xử phạt lái xe ô tô    │        │
│  │ Phạt 30–40 triệu đồng...        │        │
│  └─────────────────────────────┘            │
│  ┌─────────────────────────────┐            │
│  │ 📄 168/2024/NĐ-CP  [Còn HLực] →│        │
│  │ Điều 6. Xử phạt lái xe máy     │        │
│  │ Phạt 6–8 triệu đồng...          │        │
│  └─────────────────────────────┘            │
└─────────────────────────────────────────────┘
```

### Backend: Cập nhật `agents/response_generator.py`

```python
RESPONSE_PROMPT = """
Bạn là LegalAI, chuyên gia tư vấn pháp luật Việt Nam.
LUÔN trả lời bằng tiếng Việt.

Dựa trên các điều khoản pháp luật được cung cấp, hãy trả lời theo đúng cấu trúc JSON sau:

{
  "summary": "Đoạn tóm tắt 3-5 câu bằng ngôn ngữ dễ hiểu. KHÔNG dùng thuật ngữ kỹ thuật. Nêu rõ: ai bị phạt, phạt bao nhiêu, hình thức phạt bổ sung. Ưu tiên thông tin từ văn bản MỚI NHẤT.",
  "citations": [
    {
      "so_hieu": "168/2024/NĐ-CP",
      "ten_van_ban": "Tên đầy đủ của văn bản",
      "dieu": "Điều 5. Xử phạt người điều khiển xe ô tô...",
      "snippet": "Trích dẫn nguyên văn điều khoản liên quan, tối đa 200 ký tự",
      "still_valid": true,
      "pdf_url": "{pdf_url_từ_metadata}"
    }
  ],
  "confidence": "high | medium | low",
  "note": "Lưu ý quan trọng nếu có (VD: luật mới thay luật cũ, cần tham khảo luật sư...)"
}

QUY TẮC:
1. summary PHẢI phân biệt rõ ô tô vs xe máy nếu mức phạt khác nhau
2. Chỉ đưa vào citations những điều khoản TRỰC TIẾP trả lời câu hỏi
3. Ưu tiên văn bản năm MỚI HƠN nếu có nhiều văn bản cùng chủ đề
4. Không bịa đặt số tiền hoặc điều khoản không có trong context
5. still_valid = false nếu văn bản đã bị thay thế hoặc hết hiệu lực

CONTEXT (các điều khoản pháp luật):
{context}

CÂU HỎI: {question}
"""
```

### Backend: Cập nhật `app/routes/chat.py`

Đảm bảo response trả về đúng cấu trúc:

```python
@router.post("/api/chat")
async def chat(request: ChatRequest):
    result = await graph.ainvoke({
        "question": request.question,
        "domain": request.domain,
        "conversation_history": request.history or [],
    })

    return {
        "summary":    result["answer"]["summary"],
        "citations":  result["answer"]["citations"],
        "confidence": result["answer"]["confidence"],
        "note":       result["answer"].get("note", ""),
        "domain":     result["predicted_domain"],
    }
```

### Frontend: Cập nhật component chat để render 2 phần

Tìm component hiển thị câu trả lời của bot (thường là `ChatMessage.jsx` hoặc tương tự).
Sửa lại render logic:

```jsx
function BotMessage({ message }) {
  const { summary, citations, confidence, note } = message;

  return (
    <div className="bot-message">
      {/* PHẦN 1: Tóm tắt AI */}
      <div className="summary-section">
        <p>{summary}</p>
        {note && (
          <div className="note-box">
            ⚠️ {note}
          </div>
        )}
      </div>

      {/* PHẦN 2: Điều khoản liên quan */}
      {citations && citations.length > 0 && (
        <div className="citations-section">
          <p className="citations-label">Cơ sở pháp lý:</p>
          {citations.map((citation, index) => (
            <CitationCard
              key={index}
              citation={citation}
              onClick={() => openPdfPanel(citation)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## VERIFY CUỐI — Chạy sau khi làm xong cả 3 tính năng

```
Checklist tổng:

TÍNH NĂNG 1 — Auto Convert:
  [ ] Upload file .docx → API trả về pdf_url hợp lệ
  [ ] Upload file .txt → convert thành công
  [ ] Upload file .pdf → giữ nguyên, không convert
  [ ] Upload file .xyz → trả lỗi 400 rõ ràng

TÍNH NĂNG 2 — PDF thật:
  [ ] Click citation "168/2024/NĐ-CP" → PDF bên phải hiện NĐ 168, không phải Hello World
  [ ] Click citation "100/2019/NĐ-CP" → PDF bên phải hiện NĐ 100 khác NĐ 168
  [ ] Tiêu đề panel hiện đúng tên văn bản
  [ ] Số trang > 1

TÍNH NĂNG 3 — Cấu trúc câu trả lời:
  [ ] Câu trả lời có phần tóm tắt AI ở trên
  [ ] Phần tóm tắt phân biệt rõ ô tô vs xe máy
  [ ] Phần điều khoản ở dưới có thể click
  [ ] Click điều khoản → PDF mở đúng trang
  [ ] Không còn hiển thị JSON raw
```

---

## LƯU Ý QUAN TRỌNG CHO codex

1. **Làm tuần tự:** Tính năng 2 → Tính năng 3 → Tính năng 1
   - Tính năng 2 phải xong trước (PDF thật) vì Tính năng 3 phụ thuộc vào nó
   - Tính năng 1 làm cuối vì cần LibreOffice cài sẵn

2. **Không báo cáo thành công nếu chưa chạy verify**
   - Sau mỗi tính năng PHẢI chạy lệnh kiểm tra
   - Paste output thật ra, không tự ý viết "đã thành công"

3. **PDF thật là ưu tiên số 1**
   - Nếu verify PDF vẫn ra "Hello World" → dừng lại, báo cáo ngay
   - Không tiếp tục làm tính năng khác khi PDF chưa đúng