from pathlib import Path

from backend.pipeline.converter import is_valid_pdf
from backend.pipeline.converter.file_converter import convert_to_pdf


def main() -> None:
    pdf_root = Path(__file__).resolve().parents[1] / "storage" / "pdfs"

    repaired = 0
    skipped = 0
    failed = 0

    for pdf_path in pdf_root.rglob("*.pdf"):
        if is_valid_pdf(pdf_path):
            skipped += 1
            continue

        try:
            engine, _ = convert_to_pdf(pdf_path, pdf_path, overwrite=True)
            print(f"REPAIRED {pdf_path} [{engine}]")
            repaired += 1
        except Exception as exc:
            print(f"FAILED   {pdf_path} :: {exc}")
            failed += 1

    print(f"\nSummary: repaired={repaired} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()
