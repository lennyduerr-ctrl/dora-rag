"""DORA Document Ingestion Pipeline.

Loads PDFs from docs/, chunks them by document type, generates embeddings via
OpenRouter, and writes a local vector store under data/:

    data/dora_vectors.npy      float32 matrix [N, dim]  (one row per chunk)
    data/dora_chunks.jsonl.gz  one {"content", "metadata"} per line (same order)

These two files are committed to the repo, so the app runs with no database.
Re-run this whenever the documents or the embedding model change.

Usage:
    python -m src.ingest
"""

import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings

from src.config import (
    CHUNKS_PATH,
    DATA_DIR,
    DOCS_DIR,
    EMBEDDING_MODEL,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    VECTORS_PATH,
    openrouter_configured,
)
from src.chunking import chunk_documents
from src.metadata import parse_filename

BATCH_SIZE = 50  # Chunks per embedding batch


def get_pdf_files() -> list[Path]:
    """Get all PDF files from the docs directory."""
    docs_path = Path(DOCS_DIR)
    if not docs_path.exists():
        print(f"ERROR: docs/ directory not found at {docs_path}")
        print("Unzip data/dora_docs.zip into docs/ first (38 PDFs).")
        sys.exit(1)

    pdfs = sorted(docs_path.glob("*.pdf"))
    if not pdfs:
        print("ERROR: No PDF files found in docs/")
        print("Unzip data/dora_docs.zip into docs/ first (38 PDFs).")
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

    results = []
    for i, chunk in enumerate(chunks):
        chunk_metadata = {**metadata, "chunk_index": i}
        chunk_metadata.pop("source", None)
        chunk_metadata.pop("page", None)
        results.append({
            "content": chunk.page_content,
            "metadata": chunk_metadata,
        })

    return results


def build_vector_store(chunks: list[dict], embeddings_model: OpenAIEmbeddings):
    """Embed all chunks and write data/dora_vectors.npy + data/dora_chunks.jsonl.gz."""
    os.makedirs(DATA_DIR, exist_ok=True)

    total = len(chunks)
    vectors: list[list[float]] = []

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["content"] for c in batch]
        print(f"  Embedding batch {i // BATCH_SIZE + 1} ({len(batch)} chunks)...")
        vectors.extend(embeddings_model.embed_documents(texts))
        print(f"  Embedded {min(i + BATCH_SIZE, total)}/{total} chunks")

    matrix = np.asarray(vectors, dtype=np.float32)
    np.save(VECTORS_PATH, matrix)

    with gzip.open(CHUNKS_PATH, "wt", encoding="utf-8") as fh:
        for c in chunks:
            fh.write(json.dumps(
                {"content": c["content"], "metadata": c["metadata"]},
                ensure_ascii=False,
            ) + "\n")

    return matrix.shape


def main():
    print("=" * 60)
    print("DORA RAG Ingestion Pipeline (OpenRouter embeddings -> local store)")
    print("=" * 60)

    if not openrouter_configured():
        sys.exit("ERROR: OPENAI_API_KEY (OpenRouter key) not set. See .env.example.")

    pdfs = get_pdf_files()
    print(f"\nFound {len(pdfs)} PDFs in docs/\n")

    print("--- Phase 1: Loading & Chunking ---")
    all_chunks = []
    for pdf in pdfs:
        chunks = load_and_chunk(pdf)
        all_chunks.extend(chunks)
        print(f"    -> {len(chunks)} chunks\n")

    print(f"Total: {len(all_chunks)} chunks from {len(pdfs)} documents\n")

    print(f"--- Phase 2: Embedding ({EMBEDDING_MODEL}) & Saving ---")
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        check_embedding_ctx_length=False,
    )

    shape = build_vector_store(all_chunks, embeddings)

    print(f"\nDone! Vector store written: {shape[0]} chunks x {shape[1]} dims")
    print(f"  {VECTORS_PATH}")
    print(f"  {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
