# Chat DORA — Projektvorstellung

**Ein KI-Assistent, der die DORA-Verordnung für das Compliance-Team durchsuchbar macht.**

---

## Das Problem

Mit dem **Digital Operational Resilience Act (DORA)** gelten seit Januar 2025 umfassende neue Anforderungen an die IT-Sicherheit im Finanzsektor. Die Herausforderung: Die relevanten Vorgaben verteilen sich auf **38 verschiedene Dokumente** — EU-Verordnungstexte, technische Standards, BaFin-FAQs, europäische Auslegungsfragen und Leitlinien zu Penetrationstests.

Für das Compliance-Team bedeutet das: Jede Frage erfordert die manuelle Suche durch mehrere Dokumente, den Abgleich verschiedener Quellen und die Einordnung in den deutschen Aufsichtskontext. Das kostet Zeit und birgt das Risiko, relevante Vorgaben zu übersehen.

---

## Die Lösung

**Chat DORA** ist ein interner KI-Assistent, der alle 38 DORA-Dokumente kennt und Fragen in natürlicher Sprache beantwortet — mit konkreten Artikelverweisen, Fristen und Praxishinweisen.

### So funktioniert es

1. Das Compliance-Team stellt eine Frage im Chat-Interface
2. Chat DORA durchsucht automatisch die **relevanten Dokumentenkategorien** (Verordnungstext + BaFin-Interpretation + ggf. weitere)
3. Die Antwort kommt in einer festen, prüfbaren Struktur:

| Abschnitt | Inhalt |
|-----------|--------|
| **Zusammenfassung** | Kernaussage in 2-3 Sätzen |
| **Detailanalyse** | Konkrete Artikel, Pflichten und Fristen |
| **Praxishinweise** | Umsetzungstipps und typische Fallstricke |
| **Quellen** | Genaue Dokumenten- und Artikelverweise |

Jede Aussage ist mit einer Quelle belegt. Es werden keine Informationen erfunden.

---

## Welche Dokumente sind enthalten?

| Kategorie | Beispiele | Anzahl |
|-----------|-----------|--------|
| DORA-Verordnung & Berichtigungen | EU-Verordnung 2022/2554 | 4 |
| Technische Standards (RTS/ITS) | IKT-Risikomanagement, Vorfallmeldung, Drittparteien | 12 |
| BaFin-Guidance | FAQs, Aufsichtsmitteilungen | 6 |
| ESA Q&As | Europäische Auslegungsfragen (EBA/ESMA/EIOPA) | 2 |
| TIBER / Penetrationstests | TIBER-EU Framework, TIBER-DE, ECB-Guidance | 8 |
| EU-Leitlinien | Kosten/Verluste, Cloud-Auslagerung | 6 |

**Gesamt: 38 Dokumente, ~1.400 durchsuchbare Textabschnitte**

---

## Beispiel

**Frage:** *Welche Fristen gelten für die Meldung schwerwiegender IKT-Vorfälle?*

**Chat DORA liefert:**
- Die exakten Fristen aus der Verordnung (4 Stunden Erstmeldung, 72 Stunden Zwischenmeldung, 1 Monat Abschlussbericht — mit Artikelverweis)
- Die BaFin-Interpretation und zusätzliche Anforderungen für den deutschen Markt
- Praxishinweise zur internen Prozessgestaltung
- Alle Quellen zum Nachschlagen

---

## Mehrwert

**Zeitersparnis** — Recherche, die sonst Stunden dauert, wird in Sekunden beantwortet. Das Team muss nicht mehr 38 Dokumente manuell durchsuchen.

**Qualitätssicherung** — Jede Antwort kombiniert automatisch den Gesetzestext mit der behördlichen Auslegung. Wichtige Quellen werden nicht übersehen.

**Nachvollziehbarkeit** — Alle Aussagen sind mit Artikel und Dokumentname belegt. Das Team kann jede Antwort direkt in der Originalquelle verifizieren.

**Konsistenz** — Einheitliche, strukturierte Analysen statt individuell unterschiedlicher Rechercheergebnisse.

**Aktualität** — Die Dokumentenbasis kann jederzeit um neue Dokumente erweitert werden (neue RTS, BaFin-Rundschreiben etc.).

---

## Technologie auf einen Blick

Chat DORA nutzt **Retrieval-Augmented Generation (RAG)** — eine etablierte KI-Methode, bei der das Sprachmodell ausschließlich auf Basis der hinterlegten Dokumente antwortet, nicht auf Basis von Trainingsdaten. Das minimiert das Risiko von Halluzinationen.

| Aspekt | Umsetzung |
|--------|-----------|
| Dokumentenspeicher | Supabase (gehostete Datenbank mit Vektorsuche) |
| KI-Modell | Google Gemini 2.0 Flash (via OpenRouter) |
| Oberfläche | Web-basiertes Chat-Interface (Streamlit) |
| Tracing | LangSmith — jede Antwort ist nachvollziehbar auditierbar |

**Hosting:** Läuft intern, keine Dokumente verlassen die eigene Infrastruktur.

---

## Status & Ausblick

### Aktueller Stand
- 38 Dokumente vollständig indexiert
- 5 spezialisierte Suchkategorien
- Chat-Interface einsatzbereit
- Gesprächskontext innerhalb einer Session (Follow-up-Fragen möglich)

### Mögliche Erweiterungen
- Anbindung weiterer Regulierungen (MaRisk, BAIT, EBA-Leitlinien)
- Export von Analysen als PDF
- Benutzerlogin und Gesprächshistorie über Sessions hinweg
- Integration in bestehende Compliance-Tools

---

*Chat DORA — damit das Compliance-Team Antworten findet, statt Dokumente zu suchen.*
