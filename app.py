"""Chat DORA — Streamlit UI for the DORA Compliance Chatbot."""

import uuid

import streamlit as st

from src.chain import create_dora_agent

st.set_page_config(page_title="Chat DORA", page_icon="📋", layout="centered")

    st.write(f"API Base: {OPENAI_API_BASE or 'MISSING'}")
    st.write(f"Supabase: {'set' if SUPABASE_URL else 'MISSING'}")


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
if "agent" not in st.session_state:
    st.session_state.agent = create_dora_agent()
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []

config = {
    "configurable": {"thread_id": st.session_state.thread_id},
    "recursion_limit": 25,
}

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
        with st.spinner("Analysiere..."):
            result = st.session_state.agent.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config=config,
            )
            answer = result["messages"][-1].content
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
