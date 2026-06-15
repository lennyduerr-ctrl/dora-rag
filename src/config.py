import os
from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str | None = None) -> str | None:
    """Read from env vars first, fall back to Streamlit secrets (for Cloud)."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# OpenRouter (one key for both the chat LLM and the embeddings)
# Get a free key at https://openrouter.ai/keys
# ---------------------------------------------------------------------------
OPENAI_API_KEY = _get("OPENAI_API_KEY")  # the OpenRouter key (sk-or-...)
OPENAI_API_BASE = _get("OPENAI_API_BASE", "https://openrouter.ai/api/v1")

# Chat model (DeepSeek V4 Flash — fast & cheap). Swap via env without code change.
OPENROUTER_MODEL = _get("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")

# Embedding model (must match the model used to build data/dora_vectors.npy).
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "openai/text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(_get("EMBEDDING_DIMENSIONS", "1536"))

# ---------------------------------------------------------------------------
# Local vector store (shipped in the repo, no external database required)
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(_ROOT, "data")
VECTORS_PATH = os.path.join(DATA_DIR, "dora_vectors.npy")
CHUNKS_PATH = os.path.join(DATA_DIR, "dora_chunks.jsonl.gz")
DOCS_DIR = os.path.join(_ROOT, "docs")

# ---------------------------------------------------------------------------
# LangSmith (optional, auto-detected by LangChain if set)
# ---------------------------------------------------------------------------
LANGSMITH_API_KEY = _get("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = _get("LANGSMITH_PROJECT", "dora-rag")


# ---------------------------------------------------------------------------
# Configuration guard
# ---------------------------------------------------------------------------
_PLACEHOLDERS = ("sk-or-...", "<", "xxx")


def openrouter_configured() -> bool:
    """True if a real OpenRouter key looks configured (not a placeholder)."""
    key = OPENAI_API_KEY
    if not key:
        return False
    return not any(p in key for p in _PLACEHOLDERS)
