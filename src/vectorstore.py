"""In-memory vector store for the DORA chunks.

The embeddings (one row per chunk) and the chunk texts/metadata are shipped in
the repo under data/, so the app needs no external database — it loads them once
and does a cosine-similarity search in NumPy. This is what lets the public demo
run for free on Streamlit Cloud.

Build the data files with `python -m src.ingest` (see that module).
"""

import gzip
import json
import os

import numpy as np

from src.config import CHUNKS_PATH, VECTORS_PATH

_store = None  # lazily-loaded singleton: (matrix, contents, metadatas)


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def load_store():
    """Load (and cache) the normalized embedding matrix + chunk payloads."""
    global _store
    if _store is not None:
        return _store

    if not (os.path.exists(VECTORS_PATH) and os.path.exists(CHUNKS_PATH)):
        raise FileNotFoundError(
            "Vector data not found. Build it with `python -m src.ingest` "
            f"(expected {VECTORS_PATH} and {CHUNKS_PATH})."
        )

    matrix = np.load(VECTORS_PATH).astype(np.float32)
    matrix = _l2_normalize(matrix)

    contents, metadatas = [], []
    with gzip.open(CHUNKS_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            contents.append(row["content"])
            metadatas.append(row["metadata"])

    _store = (matrix, contents, metadatas)
    return _store


def search(
    query_vector: list[float],
    match_count: int = 8,
    match_threshold: float = 0.3,
    doc_types: list[str] | None = None,
    authority: str | None = None,
    category: str | None = None,
) -> list[dict]:
    """Cosine-similarity search with optional metadata filtering.

    Mirrors the old Supabase ``match_dora_chunks_filtered`` RPC: filter by
    metadata, keep hits above ``match_threshold``, return the top ``match_count``
    as dicts with content, metadata and similarity.
    """
    matrix, contents, metadatas = load_store()

    q = np.asarray(query_vector, dtype=np.float32)
    n = np.linalg.norm(q)
    if n:
        q = q / n
    sims = matrix @ q  # cosine similarity (matrix is L2-normalized)

    results = []
    for idx in np.argsort(-sims):
        score = float(sims[idx])
        if score <= match_threshold:
            break  # sorted descending -> nothing better follows
        meta = metadatas[idx]
        if doc_types is not None and meta.get("document_type") not in doc_types:
            continue
        if authority is not None and meta.get("authority") != authority:
            continue
        if category is not None and meta.get("category") != category:
            continue
        results.append(
            {"content": contents[idx], "metadata": meta, "similarity": score}
        )
        if len(results) >= match_count:
            break
    return results
