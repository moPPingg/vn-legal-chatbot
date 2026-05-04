"""Data ingestion CLI — load, chunk, embed, store in FAISS."""
import argparse, logging, sys
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Ingest Vietnamese legal documents")
    parser.add_argument("--max-docs", type=int, default=None)
    parser.add_argument("--chunk-size", type=int, default=1500)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    args = parser.parse_args()

    from app.rag.vector_store import get_stats, build_index
    from app.rag.data_loader import load_and_merge
    from app.rag.chunker import chunk_documents
    from app.classifier import train_classifier

    stats = get_stats()
    if stats["total_vectors"] > 0:
        print(f"Index already has {stats['total_vectors']} vectors. Delete faiss_index/ to re-ingest.")
        return

    print(f"Loading documents (max={args.max_docs})...")
    df = load_and_merge(max_docs=args.max_docs)
    print(f"Chunking ({args.chunk_size} chars, {args.chunk_overlap} overlap)...")
    docs = chunk_documents(df, args.chunk_size, args.chunk_overlap)
    print(f"Building FAISS index from {len(docs)} chunks...")
    n = build_index(docs)
    print(f"Index built with {n} vectors")

    print("Training classifier...")
    train_classifier()
    print("Classifier trained")
    print("\nDone! Start server with: uvicorn app.main:app --reload --port 8000")

if __name__ == "__main__":
    main()
