"""Chat DORA — Streamlit UI for the DORA Compliance Chatbot."""

import uuid

import streamlit as st

from src.chain import create_dora_agent
from src.config import openrouter_configured

st.set_page_config(page_title="Chat DORA", page_icon="📋", layout="centered")


@st.dialog("How it works")
def show_how_it_works():
    st.markdown(
        """
**Chat DORA** ist ein KI-gestützter Assistent für Fragen rund um die
DORA-Verordnung (Digital Operational Resilience Act).

### Quellengrundlage
Der Chatbot durchsucht **38 offizielle Dokumente**, darunter:
- DORA-Verordnung (EU) 2022/2554 inkl. Berichtigungen
- Technische Regulierungsstandards (RTS) und Durchführungsstandards (ITS)
- BaFin-FAQs und Rundschreiben
- ESA Q&A-Kompendien
- TIBER-EU / TLPT-Leitlinien

### Analyse-Aufbau
Jede Antwort folgt einer festen Struktur:
1. **Zusammenfassung** — Kernaussage in wenigen Sätzen
2. **Detailanalyse** — Relevante Artikel und Vorschriften
3. **Praxishinweise** — Umsetzungstipps für das Compliance-Team
4. **Quellen** — Genaue Artikelverweise und Dokumentennamen

### Hinweis
Chat DORA dient ausschließlich der **internen Unterstützung** des
Compliance-Teams. Die Antworten stellen **keine Rechtsberatung** dar.
"""
    )


# --- Header ---
col1, col2 = st.columns([4, 1])
with col1:
    st.title("Chat DORA")
with col2:
    st.write("")  # vertical spacing
    if st.button("How it works"):
        show_how_it_works()

# --- Session State ---
# Built defensively so the UI still renders if the OpenRouter key is missing
# (e.g. before the Streamlit secret is set) instead of crashing on a stack trace.
if "agent" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    try:
        st.session_state.agent = create_dora_agent()
        st.session_state.agent_error = None
    except Exception as exc:  # noqa: BLE001 - keep the UI alive
        st.session_state.agent = None
        st.session_state.agent_error = f"{type(exc).__name__}: {exc}"

config = {
    "configurable": {"thread_id": st.session_state.thread_id},
    "recursion_limit": 25,
}

# --- Status banner ---
if not openrouter_configured():
    st.warning(
        "⚠️ Kein OpenRouter-Key gefunden. Setze in den **Streamlit-Secrets** "
        "(bzw. lokal in `.env`) `OPENAI_API_KEY` auf deinen OpenRouter-Key "
        "(`sk-or-...`). Einen kostenlosen Key gibt es auf openrouter.ai/keys.",
        icon="⚠️",
    )

# --- Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Input ---
if question := st.chat_input("Stelle eine Frage zur DORA-Verordnung..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        if st.session_state.agent is None:
            answer = (
                "Die Chat-Funktion ist nicht verfügbar — es ist kein gültiger "
                "OpenRouter-Key konfiguriert. Bitte `OPENAI_API_KEY` in den "
                "Streamlit-Secrets hinterlegen."
            )
            st.markdown(answer)
        else:
            with st.spinner("Analysiere..."):
                try:
                    result = st.session_state.agent.invoke(
                        {"messages": [{"role": "user", "content": question}]},
                        config=config,
                    )
                    answer = result["messages"][-1].content
                except Exception as exc:  # noqa: BLE001 - keep the UI alive
                    answer = (
                        "Es ist ein Fehler bei der Verarbeitung aufgetreten "
                        f"({type(exc).__name__}). Bitte prüfe den OpenRouter-Key "
                        "und das Modell."
                    )
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
