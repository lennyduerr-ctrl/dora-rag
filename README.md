# Chat DORA

**KI-gestützter Compliance-Assistent für die DORA-Verordnung (EU) 2022/2554**

Ein RAG-Chatbot (Retrieval-Augmented Generation), der 38 offizielle DORA-Dokumente durchsucht und strukturierte Compliance-Analysen mit konkreten Artikelverweisen liefert.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangChain](https://img.shields.io/badge/LangChain-0.3-green)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)
![Supabase](https://img.shields.io/badge/Supabase-pgvector-orange)

---

## Was ist DORA?

Der **Digital Operational Resilience Act** (DORA) ist eine EU-Verordnung, die ab Januar 2025 einheitliche Anforderungen an die digitale Betriebsstabilität im Finanzsektor vorschreibt — von IKT-Risikomanagement über Vorfallmeldung bis hin zu Penetrationstests (TLPT). Die Regulierungslandschaft ist komplex: Verordnungstext, technische Standards (RTS/ITS), BaFin-FAQs, ESA Q&As und TIBER-Leitlinien verteilen sich auf Dutzende Dokumente.

**Chat DORA** macht diese Dokumente durchsuchbar und liefert strukturierte Analysen mit Artikelverweisen, Praxishinweisen und Quellenangaben.

---

## Architektur

```
                          ┌──────────────┐
                          │  Streamlit   │
                          │   Chat UI    │
                          └──────┬───────┘
                                 │
                          ┌──────▼───────┐
                          │  LangGraph   │
                          │    Agent     │
                          │  (Gemini 2)  │
                          └──────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
     ┌────────▼───────┐  ┌──────▼───────┐  ┌───────▼──────┐
     │ search_         │  │ search_      │  │ search_      │
     │ regulations     │  │ bafin_       │  │ tiber        │
     │ (REG/CORR/GL)  │  │ guidance     │  │ (TLPT)       │
     └────────┬───────┘  └──────┬───────┘  └───────┬──────┘
              │                  │                   │
              └──────────────────┼──────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   OpenAI Embeddings     │
                    │  text-embedding-3-large │
                    │     (via OpenRouter)    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Supabase pgvector     │
                    │   1.406 Chunks / HNSW   │
                    └─────────────────────────┘
```

### Warum 5 spezialisierte Such-Tools?

Statt einer generischen Suche nutzt der Agent **Metadaten-Filter**, um zielgerichtet in den richtigen Dokumenten zu suchen:

| Tool | Filtert auf | Anwendungsfall |
|------|-------------|----------------|
| `search_regulations` | REG, CORR, GL | Gesetzestext, RTS/ITS, Leitlinien |
| `search_bafin_guidance` | authority=BaFin | Deutsche Aufsichtsperspektive, FAQs |
| `search_esa_qa` | QA | EU-weite Auslegungsfragen |
| `search_tiber` | category=TLPT | Penetrationstests (Art. 26-27) |
| `search_all` | kein Filter | Fallback / übergreifende Fragen |

Der Agent muss **mindestens 2 Tools** pro Frage aufrufen (durch den System-Prompt erzwungen) — das kombiniert z.B. den Gesetzestext mit der BaFin-Interpretation.

---

## Dokumenttyp-basiertes Chunking

Nicht jedes Dokument lässt sich gleich aufteilen. Die Ingestion-Pipeline erkennt den Dokumenttyp aus dem Dateinamen und wendet eine passende Strategie an:

| Dokumenttyp | Chunking-Strategie | Separatoren |
|-------------|-------------------|-------------|
| REG / CORR | Artikel-basiert | `Artikel`, `Abschnitt`, `Kapitel` |
| FAQ | Frage-basiert | `Frage 1:`, `Q1:` |
| QA | Q&A-ID-basiert | `DORA001`, `DORA002`, ... |
| GL / GUIDE | Standard | Markdown-Headings, Absätze |

Jeder Chunk wird mit Metadaten angereichert: Artikelnummer, Frage-Nr., Behörde, Kategorie, Quelldatei.

---

## Dateinamen-Schema

Die 38 PDFs folgen einem standardisierten Namensschema, aus dem automatisch Metadaten extrahiert werden:

```
{CODE}_{LANG}_{TYP}_{Thema}.pdf
```

| Feld | Beispiel | Bedeutung |
|------|----------|-----------|
| CODE | `0100` | Kategorie (01=DORA-VO, 02=IKT-Risiko, 03=Vorfall, 04=Drittparteien, 05=TLPT) |
| LANG | `DE` | Sprache (DE/EN) |
| TYP | `REG` | Dokumenttyp (REG, CORR, FAQ, GL, GUIDE, QA) |
| Thema | `DORA-Verordnung` | Kurzbezeichnung |

Beispiel: `0100_DE_REG_DORA-Verordnung.pdf` = Deutsche DORA-Verordnung, Kategorie DORA-VO

---

## Antwortformat

Jede Antwort folgt einer festen Struktur (durch den System-Prompt erzwungen):

1. **Zusammenfassung** — Executive Summary in 2-3 Sätzen
2. **Detailanalyse** — Artikelverweise, Pflichten, Fristen (mit `[Quelle, Art. X]`)
3. **Praxishinweise** — Umsetzungstipps, Fallstricke, Wechselwirkungen mit MaRisk/BAIT
4. **Quellen** — Nummerierte Liste mit Dokument, Artikel, Behörde

---

## Quickstart

### Voraussetzungen

- Python 3.11+
- [Supabase](https://supabase.com)-Projekt mit pgvector
- [OpenRouter](https://openrouter.ai)-API-Key (für Embeddings + LLM)

### 1. Repo klonen & Dependencies installieren

```bash
git clone https://github.com/lennyduerr-ctrl/dora-rag.git
cd dora-rag
pip install -r requirements.txt
```

### 2. Umgebungsvariablen setzen

```bash
cp .env.example .env
```

`.env` ausfüllen:

```env
OPENAI_API_KEY=sk-or-...          # OpenRouter API Key
OPENAI_API_BASE=https://openrouter.ai/api/v1
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
LANGSMITH_API_KEY=ls__...         # Optional: LangSmith Tracing
LANGSMITH_PROJECT=dora-rag
LANGSMITH_TRACING=true
```

### 3. Supabase einrichten

Den Inhalt von `supabase_setup.sql` im [Supabase SQL Editor](https://supabase.com/dashboard) ausführen. Das erstellt:
- `dora_chunks`-Tabelle mit pgvector (1536 Dimensionen)
- HNSW-Index für Cosine Similarity
- `match_dora_chunks`- und `match_dora_chunks_filtered`-Funktionen

### 4. PDFs laden (Ingestion)

Die 38 DORA-PDFs in den `docs/`-Ordner legen (Dateinamen-Schema beachten), dann:

```bash
python -m src.ingest
```

Das erzeugt ~1.400 Chunks mit Embeddings in Supabase.

### 5. App starten

```bash
streamlit run app.py
```

Öffnet die Chat-UI unter `http://localhost:8501`.

Alternativ CLI-Modus zum Testen:

```bash
python -m src.chat
```

---

## Tech-Stack

| Komponente | Technologie | Warum |
|-----------|-------------|-------|
| **LLM** | Gemini 2.0 Flash via OpenRouter | Schnell, günstig, guter Kontext |
| **Embeddings** | OpenAI `text-embedding-3-large` (1536 Dim.) | State-of-the-Art Semantic Search |
| **Vector Store** | Supabase pgvector + HNSW | Managed, SQL-basiert, RPC-Funktionen |
| **Agent Framework** | LangChain + LangGraph | Tool-Calling, Memory, Checkpointing |
| **UI** | Streamlit | Schnell deployt, native Chat-Komponenten |
| **Tracing** | LangSmith | Optional: Debugging von Agent-Entscheidungen |

### Warum OpenRouter?

Ein API-Key für **Embeddings und LLM**. Modell jederzeit tauschbar (`OPENROUTER_MODEL` in `.env`), ohne Code-Änderung. Standard: `google/gemini-2.0-flash-001`.

### Warum 1536 statt 3072 Dimensionen?

OpenAI `text-embedding-3-large` unterstützt bis zu 3072 Dimensionen, aber Supabase pgvector hat ein praktisches Limit bei 2000 für HNSW-Indexierung. 1536 Dimensionen bieten einen guten Kompromiss aus Suchqualität und Performance.

---

## Projektstruktur

```
dora-rag/
├── app.py                 # Streamlit Chat-UI
├── src/
│   ├── config.py          # Env-Variablen und Settings
│   ├── metadata.py        # Metadaten aus Dateinamen extrahieren
│   ├── chunking.py        # Dokumenttyp-basiertes Chunking
│   ├── ingest.py          # PDF -> Chunks -> Embeddings -> Supabase
│   ├── chain.py           # RAG Agent mit 5 Such-Tools + System-Prompt
│   └── chat.py            # CLI-Chat zum Testen
├── docs/                  # 38 DORA-PDFs (nicht in Git)
├── supabase_setup.sql     # SQL Setup (Tabelle, Index, RPC-Funktionen)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Beispielfragen

```
Was sind die Kernpflichten unter DORA Art. 5-16 zum IKT-Risikomanagement?

Welche Fristen gelten für die Meldung schwerwiegender IKT-Vorfälle?

Was sind die Anforderungen an TLPT nach Art. 26-27 DORA?

Wie interpretiert die BaFin die Anforderungen an das IKT-Drittparteienrisikomanagement?

Welche Übergangsfristen gelten für bestehende IKT-Drittparteienverträge?
```

---

## Lizenz

Dieses Projekt dient ausschließlich internen Compliance-Zwecken. Die DORA-Dokumente unterliegen dem Urheberrecht der jeweiligen Herausgeber (EU, BaFin, EBA/ESMA/EIOPA, ECB/BBK).
