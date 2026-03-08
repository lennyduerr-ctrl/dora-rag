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


OPENAI_API_KEY = _get("OPENAI_API_KEY")
OPENAI_API_BASE = _get("OPENAI_API_BASE")
SUPABASE_URL = _get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = _get("SUPABASE_SERVICE_KEY")

# LangSmith (optional, auto-detected by LangChain if set)
LANGSMITH_API_KEY = _get("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = _get("LANGSMITH_PROJECT", "dora-rag")

OPENROUTER_MODEL = _get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
