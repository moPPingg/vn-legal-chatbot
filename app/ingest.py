"""
Data ingestion script — loads legal documents into ChromaDB.

Run this once before starting the server:
  python -m app.ingest --max-docs 5000

Use --max-docs to limit the number of documents for faster startup during development.
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)


def main():
    parser = argparse.ArgumentParser(description="Ingest Vietnamese legal documents into ChromaDB")
    parser.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="Max number of documents to process (default: all)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1500,
        help="Chunk size in characters (default: 1500)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between chunks (default: 200)",
    )
    args = parser.parse_args()

    from app.data_loader import prepare_documents
    from app.vector_store import ingest_documents, get_stats

    stats = get_stats()
    if stats["total_chunks"] > 0:
        print(f"✓ Vector store already has {stats['total_chunks']} chunks. Skipping ingestion.")
        print("  Delete the chroma_db/ directory to re-ingest.")
        return

    print(f"Preparing documents (max_docs={args.max_docs}, chunk_size={args.chunk_size})...")
    docs = prepare_documents(
        max_docs=args.max_docs,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    if not docs:
        print("⚠ No documents prepared. Check the data directory.")
        sys.exit(1)

    print(f"Ingesting {len(docs)} chunks into ChromaDB...")
    added = ingest_documents(docs)
    print(f"✓ Done! Added {added} chunks to the vector store.")


if __name__ == "__main__":
    main()
