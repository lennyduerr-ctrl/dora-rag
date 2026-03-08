"""DORA Document Ingestion Pipeline.

Loads PDFs from docs/, chunks them intelligently by document type,
generates embeddings via OpenAI, and stores in Supabase pgvector.

Usage:
    python -m src.ingest
"""

import os
import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from supabase import create_client

from src.config import DOCS_DIR, OPENAI_API_BASE, OPENAI_API_KEY, SUPABASE_SERVICE_KEY, SUPABASE_URL
from src.chunking import chunk_documents
from src.metadata import parse_filename

BATCH_SIZE = 50  # Chunks per embedding batch


def get_pdf_files() -> list[Path]:
    """Get all PDF files from the docs directory."""
    docs_path = Path(DOCS_DIR)
    if not docs_path.exists():
        print(f"ERROR: docs/ directory not found at {docs_path}")
        print("Copy the 38 DORA PDFs into the docs/ folder first.")
        sys.exit(1)

    pdfs = sorted(docs_path.glob("*.pdf"))
    if not pdfs:
        print("ERROR: No PDF files found in docs/")
        sys.exit(1)

    return pdfs


def load_and_chunk(pdf_path: Path) -> list[dict]:
    """Load a PDF, extract metadata, and chunk it.

    Returns list of dicts with 'content' and 'metadata' keys.
    """
    metadata = parse_filename(pdf_path)
    doc_type = metadata["document_type"]

    print(f"  Loading: {pdf_path.name} (type={doc_type})")

    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()

    if not pages:
        print(f"  WARNING: No text extracted from {pdf_path.name}")
        return []

    chunks = chunk_documents(pages, doc_type)

    # Merge file metadata into each chunk
    results = []
    for i, chunk in enumerate(chunks):
        chunk_metadata = {**metadata, "chunk_index": i}
        # Remove loader-specific metadata that doesn't belong in the DB
        chunk_metadata.pop("source", None)
        chunk_metadata.pop("page", None)
        results.append({
            "content": chunk.page_content,
            "metadata": chunk_metadata,
        })

    return results


def store_in_supabase(chunks: list[dict], embeddings_model: OpenAIEmbeddings):
    """Generate embeddings and store chunks in Supabase."""
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    total = len(chunks)
    stored = 0

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["content"] for c in batch]

        print(f"  Embedding batch {i // BATCH_SIZE + 1} ({len(batch)} chunks)...")
        vectors = embeddings_model.embed_documents(texts)

        rows = [
            {
                "content": chunk["content"],
                "metadata": chunk["metadata"],
                "embedding": vector,
            }
            for chunk, vector in zip(batch, vectors)
        ]

        supabase.table("dora_chunks").insert(rows).execute()
        stored += len(rows)
        print(f"  Stored {stored}/{total} chunks")

    return stored


def main():
    print("=" * 60)
    print("DORA RAG Ingestion Pipeline")
    print("=" * 60)

    # 1. Find PDFs
    pdfs = get_pdf_files()
    print(f"\nFound {len(pdfs)} PDFs in docs/\n")

    # 2. Load and chunk all documents
    print("--- Phase 1: Loading & Chunking ---")
    all_chunks = []
    for pdf in pdfs:
        chunks = load_and_chunk(pdf)
        all_chunks.extend(chunks)
        print(f"    -> {len(chunks)} chunks\n")

    print(f"Total: {len(all_chunks)} chunks from {len(pdfs)} documents\n")

    # 3. Embed and store
    print("--- Phase 2: Embedding & Storing ---")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        dimensions=1536,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
    )

    stored = store_in_supabase(all_chunks, embeddings)

    print(f"\nDone! {stored} chunks stored in Supabase.")
    print("Check your Supabase dashboard: dora_chunks table")
    print("Check LangSmith dashboard for tracing (if configured)")


if __name__ == "__main__":
    main()
