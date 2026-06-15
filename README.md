# Chat DORA

**KI-gestützter Compliance-Assistent für die DORA-Verordnung (EU) 2022/2554**

Ein RAG-Chatbot (Retrieval-Augmented Generation), der **38 offizielle DORA-Dokumente** durchsucht und strukturierte Compliance-Analysen mit konkreten Artikelverweisen liefert.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![LangChain](https://img.shields.io/badge/LangChain-1.x-green)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)
![OpenRouter](https://img.shields.io/badge/OpenRouter-DeepSeek%20V4-8A2BE2)

👉 **Live-Demo:** https://dora-chat.streamlit.app

> **Kein externer Datenbank-Dienst nötig.** Die Vektoren liegen vorgerechnet im
> Repo (`data/`), die App lädt sie in den Speicher und sucht lokal. Du brauchst
> nur **einen kostenlosen OpenRouter-Key** — der treibt sowohl das Chat-Modell
> als auch die Embeddings.

---

## Was ist DORA?

Der **Digital Operational Resilience Act** (DORA) ist eine EU-Verordnung, die seit Januar 2025 einheitliche Anforderungen an die digitale Betriebsstabilität im Finanzsektor vorschreibt — von IKT-Risikomanagement über Vorfallmeldung bis hin zu Penetrationstests (TLPT). Die Regulierungslandschaft ist komplex: Verordnungstext, technische Standards (RTS/ITS), BaFin-FAQs, ESA Q&As und TIBER-Leitlinien verteilen sich auf Dutzende Dokumente.

**Chat DORA** macht diese Dokumente durchsuchbar und liefert strukturierte Analysen mit Artikelverweisen, Praxishinweisen und Quellenangaben.

---

## Architektur

```
                          ┌──────────────┐
                          │  Streamlit   │
                          │   Chat UI    │
                          └──────┬───────┘
                                 │
                          ┌──────▼───────────┐
                          │   LangGraph      │
                          │     Agent        │
                          │ DeepSeek V4 Flash│
                          │  (via OpenRouter)│
                          └──────┬───────────┘
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
                    ┌────────────▼─────────────┐
                    │  Embeddings (OpenRouter) │
                    │ openai/text-embedding-3- │
                    │   small · 1536 Dim.      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  In-Memory Vektor-Store  │
                    │  data/dora_vectors.npy   │
                    │  1.406 Chunks · NumPy    │
                    └──────────────────────────┘
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

Jeder Chunk wird mit Metadaten angereichert: Behörde, Kategorie, Dokumenttyp, Quelldatei.

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

## Quickstart (lokal in 3 Minuten)

Die vorgerechneten Vektoren liegen schon im Repo (`data/`) — du musst **nichts neu indexieren**.

```bash
git clone https://github.com/lennyduerr-ctrl/dora-rag.git
cd dora-rag
pip install -r requirements.txt

cp .env.example .env        # dann OPENAI_API_KEY = dein OpenRouter-Key eintragen
streamlit run app.py        # öffnet http://localhost:8501
```

Du brauchst nur einen **kostenlosen OpenRouter-Key** von https://openrouter.ai/keys.
Alternativ ein CLI-Test ohne UI: `python -m src.chat`.

---

## Deployment auf Streamlit Community Cloud (kostenlos)

1. Repo zu GitHub pushen und auf https://share.streamlit.io eine neue App aus
   dem Repo erstellen (`app.py` als Entry-Point).
2. Unter **Settings → Secrets** eintragen (TOML-Format):

   ```toml
   OPENAI_API_KEY = "sk-or-DEIN-OPENROUTER-KEY"
   OPENAI_API_BASE = "https://openrouter.ai/api/v1"
   OPENROUTER_MODEL = "deepseek/deepseek-v4-flash"
   EMBEDDING_MODEL = "openai/text-embedding-3-small"
   ```

3. Speichern → die App startet (bzw. startet neu). Der Key liegt **nur** in den
   Streamlit-Secrets, nie im Repo.

---

## Selbst bauen / Dokumente aktualisieren

Die 38 Quell-PDFs liegen als ZIP im Repo: **`data/dora_docs.zip`**. So baust du den
Vektor-Store neu (z.B. nach Doku-Updates oder mit einem anderen Embedding-Modell):

```bash
unzip data/dora_docs.zip -d docs/      # 38 PDFs nach docs/
python -m src.ingest                   # PDF -> Chunks -> Embeddings -> data/
```

`src/ingest.py` schreibt `data/dora_vectors.npy` (Embedding-Matrix) und
`data/dora_chunks.jsonl.gz` (Texte + Metadaten). Beide Dateien werden committet,
damit die App ohne Datenbank läuft.

---

## Tech-Stack

| Komponente | Technologie | Warum |
|-----------|-------------|-------|
| **LLM** | DeepSeek V4 Flash via OpenRouter | Schnell, günstig, gutes Reasoning |
| **Embeddings** | `openai/text-embedding-3-small` via OpenRouter (1536 Dim.) | Ein Key für LLM **und** Embeddings |
| **Vector Store** | In-Memory (NumPy, Cosine) aus `data/` | Kein externer Dienst, läuft kostenlos auf Streamlit Cloud |
| **Agent Framework** | LangChain + LangGraph | Tool-Calling, Memory, Checkpointing |
| **UI** | Streamlit | Schnell deployt, native Chat-Komponenten |

### Warum OpenRouter?

**Ein API-Key für Chat und Embeddings.** Das Chat-Modell ist über `OPENROUTER_MODEL`
jederzeit tauschbar (z.B. `anthropic/claude-...`, `google/gemini-...`), ohne
Code-Änderung. Standard: `deepseek/deepseek-v4-flash`.

### Warum ein In-Memory-Store statt einer Datenbank?

Bei ~1.400 Chunks ist eine Vektor-Datenbank überdimensioniert. Eine NumPy-Matrix
im Speicher beantwortet jede Suche in Millisekunden, kommt ohne externen Dienst
aus und macht das Repo **vollständig selbst-baubar** — perfekt für eine kostenlose
Demo.

---

## Projektstruktur

```
dora-rag/
├── app.py                 # Streamlit Chat-UI
├── src/
│   ├── config.py          # Env-Variablen / OpenRouter-Settings
│   ├── metadata.py        # Metadaten aus Dateinamen extrahieren
│   ├── chunking.py        # Dokumenttyp-basiertes Chunking
│   ├── ingest.py          # PDF -> Chunks -> Embeddings -> data/
│   ├── vectorstore.py     # In-Memory Cosine-Suche + Metadaten-Filter
│   ├── chain.py           # RAG Agent mit 5 Such-Tools + System-Prompt
│   └── chat.py            # CLI-Chat zum Testen
├── data/
│   ├── dora_vectors.npy       # Embedding-Matrix (1406 x 1536)
│   ├── dora_chunks.jsonl.gz   # Chunk-Texte + Metadaten
│   └── dora_docs.zip          # 38 Quell-PDFs (zum Selbstbauen)
├── docs/                  # entpackte PDFs (nicht in Git)
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

## Lizenz / Hinweis

Der **Code** dieses Projekts steht unter der **MIT-Lizenz** (siehe [LICENSE](LICENSE))
— frei nutzbar, anpassbar und weitergebbar.

Die **DORA-Dokumente** in `data/dora_docs.zip` sind davon **ausgenommen**: Sie
unterliegen dem Urheberrecht der jeweiligen Herausgeber (EU, BaFin, EBA/ESMA/EIOPA,
ECB/BBK) und sind nur zur Demonstration beigefügt.

Dieses Projekt ist eine Demonstration; die Antworten stellen **keine Rechtsberatung** dar.
