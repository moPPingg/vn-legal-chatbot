# Converter Installation

The backend now normalizes downloaded legal documents into PDF before they are exposed to the frontend viewer.

## Storage layout

- `backend/storage/downloads/<domain>/` keeps the original downloaded files
- `backend/storage/pdfs/<domain>/` keeps only viewer-ready PDFs
- `backend/storage/raw/<domain>/` keeps metadata JSON

## Supported conversion backends

Preferred order:

1. LibreOffice headless
2. `docx2pdf` for `.docx` on Windows

## Windows setup

### Option 1: LibreOffice

Install LibreOffice and ensure one of these exists:

- `C:\Program Files\LibreOffice\program\soffice.exe`
- `C:\Program Files (x86)\LibreOffice\program\soffice.exe`

Or add `soffice` to `PATH`.

### Option 2: docx2pdf

```powershell
pip install docx2pdf
```

This helps only for `.docx`. Legacy `.doc` still needs LibreOffice.
