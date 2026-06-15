# DORA RAG — Projekt-Kontext

## Was ist das?
RAG-Chatbot für das interne Compliance-Team. Beantwortet Fragen zur DORA-Verordnung basierend auf 38 bereinigten PDF-Dokumenten (Verordnungstexte, BaFin-FAQs, TIBER-EU Guidance, ESA Q&As).

## Tech-Stack
- **Python 3.11+** mit LangChain / LangGraph
- **LLM:** OpenRouter `deepseek/deepseek-v4-flash` (über `OPENROUTER_MODEL` tauschbar)
- **Embeddings:** OpenRouter `openai/text-embedding-3-small` (1536 Dim.)
- **Vector Store:** In-Memory (NumPy Cosine) aus `data/dora_vectors.npy` — **kein** externer DB-Dienst
- **Tracing:** LangSmith (optional)
- **UI:** Streamlit (gehostet auf Streamlit Community Cloud)

> **Ein OpenRouter-Key** (`OPENAI_API_KEY`, base `https://openrouter.ai/api/v1`)
> treibt Chat **und** Embeddings. Kein Supabase/Azure mehr.

## Projektstruktur
```
src/config.py      — Env-Variablen und Settings (OpenRouter)
src/metadata.py    — Metadaten aus Dateinamen extrahieren
src/chunking.py    — Dokumenttyp-basiertes Chunking (REG, FAQ, GUIDE, QA)
src/ingest.py      — Pipeline: PDF → Chunks → Embeddings → data/ (npy + jsonl.gz)
src/vectorstore.py — In-Memory Cosine-Suche + Metadaten-Filter
src/chain.py       — RAG Agent mit 5 spezialisierten Such-Tools + Experten-Prompt
src/chat.py        — CLI-Chat zum Testen
data/              — vorgerechnete Vektoren + dora_docs.zip (committed)
docs/              — entpackte PDFs (nicht in Git)
```

## Dateinamen-Schema der PDFs
`{CODE}_{LANG}_{TYP}_{Thema}.pdf` — z.B. `0100_DE_REG_DORA-Verordnung.pdf`

Typen: REG (Verordnung), CORR (Berichtigung), FAQ, GL (Leitlinie), GUIDE, QA

## Status
- [x] Dokumentenbasis bereinigt (38 PDFs)
- [x] Projektstruktur angelegt
- [x] LangChain Skills installiert
- [x] Ingestion-Code geschrieben
- [x] .env mit API-Key (OpenRouter; LangSmith optional)
- [x] PDFs in docs/ (Quelle: data/dora_docs.zip)
- [x] Ingestion erfolgreich: 1.406 Chunks → data/dora_vectors.npy (1536 Dim.)
- [x] In-Memory-Vektorstore (NumPy Cosine) statt Supabase
- [x] Retrieval-Chain mit 5 spezialisierten Such-Tools (Regulierung, BaFin, ESA, TIBER, Alles)
- [x] Experten-System-Prompt (Zusammenfassung → Detailanalyse → Praxishinweise → Quellen)
- [x] MemorySaver für Gesprächskontext
- [x] CLI-Chat (src/chat.py)
- [x] Streamlit UI (app.py) — live auf Streamlit Community Cloud

## Nächste Session: Streamlit UI "Chat DORA"
App-Name: **Chat DORA**

Anforderungen:
- Chat-Interface mit Eingabefeld (Streamlit `st.chat_input` / `st.chat_message`)
- "How it works"-Button oben → öffnet Popup/Modal mit Erklärung (was Chat DORA kann, welche Quellen, wie die Analyse aufgebaut ist)
- Agent aus `src/chain.py` (`create_dora_agent()`) anbinden
- MemorySaver pro Session (thread_id = Streamlit session_state)
- `streamlit` zu requirements.txt hinzufügen
- Datei: `app.py` im Projekt-Root

## Konventionen
- Deutsche Dokumente bevorzugt (EN nur wo kein DE existiert)
- Chunking-Strategie hängt vom Dokumenttyp ab (siehe chunking.py)
- Metadaten werden automatisch aus dem Dateinamen geparst

## Pflicht: LangChain Skills benutzen
**IMMER** die installierten LangChain-Skills konsultieren, BEVOR LangChain-Code geschrieben oder geändert wird:
- `langchain-rag` — für Loader, Splitter, Embeddings, Vector Stores, Retrieval
- `langchain-fundamentals` — für Agents, Tools, Middleware
- `langchain-dependencies` — für Imports, Paketversionen, Kompatibilität

Diese Skills enthalten die aktuellen Imports und Best Practices. Eigenes Wissen zu LangChain-Versionen kann veraltet sein.
