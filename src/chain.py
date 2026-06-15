"""DORA RAG Agent.

Retrieval-augmented agent that answers DORA compliance questions by searching a
local in-memory vector store (shipped in the repo) and generating responses via
OpenRouter (DeepSeek). Both the chat model and the embeddings go through a single
OpenRouter key — no external database required.

Uses 5 specialized search tools with metadata filtering for targeted retrieval
across regulations, BaFin guidance, ESA Q&As, and TIBER documents.

Usage:
    from src.chain import create_dora_agent
    agent = create_dora_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Was ist DORA?"}]},
        config={"configurable": {"thread_id": "session-1"}},
    )
"""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from src import vectorstore
from src.config import (
    EMBEDDING_MODEL,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    OPENROUTER_MODEL,
)

# Embeddings client, created on demand (keeps imports cheap and lets the app
# boot even before a key is configured).
_embeddings = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
            check_embedding_ctx_length=False,  # OpenRouter doesn't expose tokenizer
        )
    return _embeddings


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Du bist ein Senior DORA-Compliance-Berater, vergleichbar mit einem Partner \
einer Wirtschaftsprüfungsgesellschaft mit Spezialisierung auf IT-Regulierung \
im Finanzsektor. Du berätst das interne Compliance-Team zu allen Fragen rund \
um die DORA-Verordnung (EU) 2022/2554, die zugehörigen technischen Standards \
(RTS/ITS), BaFin-Aufsichtsmitteilungen und FAQs, ESA Q&As sowie \
TIBER-EU/TIBER-DE Guidance.

═══════════════════════════════════════════════════════════════
TOOL-NUTZUNG — PFLICHT
═══════════════════════════════════════════════════════════════
- Rufe IMMER mindestens 2 verschiedene Such-Tools auf, bevor du antwortest.
- Beginne mit search_regulations für den Gesetzestext, dann \
search_bafin_guidance für die deutsche Aufsichtsperspektive.
- Für TIBER/TLPT-Fragen: Nutze zusätzlich search_tiber.
- Für EU-weite Auslegungsfragen: Nutze search_esa_qa.
- Für übergreifende oder unklare Fragen: search_all als Ergänzung.
- Wenn die ersten Ergebnisse nicht ausreichen, suche erneut mit \
reformulierten Begriffen.
- Stütze deine Antworten AUSSCHLIESSLICH auf die gefundenen Dokumente. \
Sage NIE "laut meinem Wissen".

═══════════════════════════════════════════════════════════════
ANTWORTFORMAT — IMMER einhalten
═══════════════════════════════════════════════════════════════

## Zusammenfassung
2–3 Sätze: Kernaussage, wichtigste Pflicht oder Frist, direkter Bezug \
zur gestellten Frage. Dies ist die "Executive Summary" für eilige Leser.

## Detailanalyse
Strukturiert mit ### Unterüberschriften nach Themenaspekten:
- Zitiere konkrete Artikelnummern und Absätze \
(z. B. "Art. 5 Abs. 2 lit. a DORA", "Art. 3 Nr. 1 RTS 2024/1774").
- Nenne Fristen mit konkreten Daten oder Zeiträumen \
(z. B. "innerhalb von 4 Stunden", "bis zum 17.01.2025").
- Kennzeichne Pflichten klar als "Muss-Anforderung" vs. "Soll-Anforderung".
- Gib bei jedem Punkt die Quelle in [eckigen Klammern] an \
(z. B. [0100_DE_REG_DORA-Verordnung.pdf, Art. 5]).

## Praxishinweise
- Konkrete Umsetzungsempfehlungen für die Praxis.
- Typische Fallstricke und Risiken bei der Umsetzung.
- Wenn der User sein Unternehmen nennt (z. B. "KfW", "Deutsche Bank"), \
ordne die DORA-Anforderungen spezifisch in den Kontext dieses \
Unternehmenstyps ein (CRR-Kreditinstitut, Förderbank, \
Wertpapierfirma, Versicherung etc.).
- Nenne ggf. Wechselwirkungen mit anderen Regulierungen (MaRisk, BAIT, \
EBA-Leitlinien).

## Quellen
Nummerierte Liste aller verwendeten Quellen mit:
- Dokumentname (z. B. 0100_DE_REG_DORA-Verordnung.pdf)
- Spezifische Artikel-/Frage-/Abschnittsnummer
- Herausgebende Behörde (EU, BaFin, ECB, ESA)

═══════════════════════════════════════════════════════════════
QUALITÄTSREGELN
═══════════════════════════════════════════════════════════════
- Antworte IMMER auf Deutsch, auch wenn Quellen auf Englisch sind.
- Mindestlänge: 400 Wörter für Standardfragen. Kürzer nur bei \
einfachen Ja/Nein-Faktenfragen.
- Wenn die Dokumente keine ausreichende Antwort hergeben, sage das \
ehrlich und schlage eine alternative Suchstrategie oder Quelle vor.
- Vermeide Wiederholungen zwischen den Abschnitten.
- Nummeriere Pflichten und Anforderungen durch, damit sie als \
Checkliste verwendbar sind.
"""


# ---------------------------------------------------------------------------
# Search Helper
# ---------------------------------------------------------------------------

def _search_filtered(
    query: str,
    match_count: int = 8,
    doc_types: list[str] | None = None,
    authority: str | None = None,
    category: str | None = None,
) -> str:
    """Embed the query and search the in-memory store with optional filters."""
    query_vector = _get_embeddings().embed_query(query)

    rows = vectorstore.search(
        query_vector,
        match_count=match_count,
        match_threshold=0.3,
        doc_types=doc_types,
        authority=authority,
        category=category,
    )

    if not rows:
        return "Keine relevanten Dokumente gefunden."

    chunks = []
    for row in rows:
        meta = row["metadata"]
        source = meta.get("source_file", "Unbekannt")
        cat = meta.get("category", "")
        auth = meta.get("authority", "")
        article = meta.get("article", "")
        question = meta.get("question_number", "")
        qa_num = meta.get("qa_number", "")
        similarity = row.get("similarity", 0)

        # Build detailed source reference
        ref_parts = [f"Quelle: {source}"]
        if article:
            ref_parts.append(f"Artikel {article}")
        if question:
            ref_parts.append(f"Frage {question}")
        if qa_num:
            ref_parts.append(f"{qa_num}")
        ref_parts.append(f"{cat}")
        ref_parts.append(f"{auth}")
        ref_parts.append(f"Relevanz: {similarity:.2f}")

        header = "[" + " | ".join(ref_parts) + "]"
        chunks.append(f"{header}\n{row['content']}")

    return "\n\n---\n\n".join(chunks)


# ---------------------------------------------------------------------------
# 5 Specialized Search Tools
# ---------------------------------------------------------------------------

@tool
def search_regulations(query: str) -> str:
    """Durchsucht DORA-Verordnungstexte, RTS, ITS und Leitlinien (GL).

    Nutze dieses Tool für:
    - Konkreter Gesetzestext und Artikelreferenzen
    - Pflichten, Verbote, Definitionen aus der DORA-Verordnung
    - Technische Regulierungsstandards (RTS) und Durchführungsstandards (ITS)
    - EU-Leitlinien (GL) zu Kosten/Verlusten
    - Fristen und Übergangsbestimmungen
    - Berichtigungen (Corrigenda) zu Verordnungstexten

    Args:
        query: Suchbegriff zu Regulierung, Artikel, Pflichten oder Fristen
    """
    return _search_filtered(
        query, match_count=10, doc_types=["REG", "CORR", "GL"]
    )


@tool
def search_bafin_guidance(query: str) -> str:
    """Durchsucht BaFin-FAQs, Aufsichtsmitteilungen und Praxisleitfäden.

    Nutze dieses Tool für:
    - BaFin-Interpretation und Auslegung der DORA-Anforderungen
    - Praktische Hinweise zur Umsetzung in Deutschland
    - FAQ-Antworten zu IKT-Risikomanagement, Vorfallmeldung, Drittparteien
    - BaFin-Aufsichtsmitteilungen und Dokumentationsanforderungen
    - Deutsche aufsichtliche Erwartungen

    Args:
        query: Suchbegriff zu BaFin-Guidance, FAQs oder Aufsichtspraxis
    """
    return _search_filtered(query, match_count=8, authority="BaFin")


@tool
def search_esa_qa(query: str) -> str:
    """Durchsucht die ESA Q&A-Kompilation zu DORA.

    Nutze dieses Tool für:
    - EU-weite Auslegungsfragen der Europäischen Aufsichtsbehörden (EBA/ESMA/EIOPA)
    - Offizielle Antworten auf häufige DORA-Interpretationsfragen
    - Grenzüberschreitende Compliance-Fragen

    Args:
        query: Suchbegriff zu ESA/EBA/ESMA Q&A oder EU-Auslegung
    """
    return _search_filtered(query, match_count=6, doc_types=["QA"])


@tool
def search_tiber(query: str) -> str:
    """Durchsucht TIBER-EU und TIBER-DE Dokumente zu Penetrationstests.

    Nutze dieses Tool für:
    - TLPT (Threat-Led Penetration Testing) nach DORA Art. 26-27
    - TIBER-EU Framework und alle Subdokumente (Red Team, Blue Team, etc.)
    - TIBER-DE Implementierung der Bundesbank
    - ECB-Guidance zum Übergang TIBER-EU zu DORA-TLPT
    - Anforderungen an Testdienstleister und Testabläufe

    Args:
        query: Suchbegriff zu TLPT, TIBER, Penetrationstests oder Red/Blue Teaming
    """
    return _search_filtered(
        query, match_count=8, category="TLPT-Penetrationstests"
    )


@tool
def search_all(query: str) -> str:
    """Durchsucht die gesamte DORA-Dokumentenbasis ohne Filter.

    Nutze dieses Tool als Ergänzung oder Fallback:
    - Wenn die spezialisierten Tools nicht genug Ergebnisse liefern
    - Für übergreifende Fragen, die mehrere Themenbereiche betreffen
    - Für allgemeine DORA-Fragen ohne klaren Fokusbereich
    - Für EZB-Guidance zu Cloud-Dienstleistern

    Args:
        query: Allgemeiner Suchbegriff zum DORA-Thema
    """
    return _search_filtered(query, match_count=8)


# ---------------------------------------------------------------------------
# Agent Factory
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    search_regulations,
    search_bafin_guidance,
    search_esa_qa,
    search_tiber,
    search_all,
]


def create_dora_agent():
    """Create the DORA compliance agent with conversation memory."""
    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        temperature=0,
    )

    return create_agent(
        model=llm,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )
