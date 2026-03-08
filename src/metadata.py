"""Extract structured metadata from standardized DORA document filenames.

Filename schema: {CODE}_{LANG}_{TYP}_{Thema}.pdf
Example: 0100_DE_REG_DORA-Verordnung.pdf
"""

import re
from pathlib import Path

CATEGORY_MAP = {
    "01": "DORA-Verordnung",
    "02": "IKT-Risikomanagement",
    "03": "IKT-Vorfallmeldung",
    "04": "IKT-Drittparteienrisiko",
    "05": "TLPT-Penetrationstests",
    "09": "BaFin-BBK-Aufsicht",
    "99": "ESA-QA",
}

AUTHORITY_MAP = {
    "REG": "EU",
    "CORR": "EU",
    "GL": "EU",
    "FAQ": "BaFin",
    "QA": "ESA",
}


def parse_filename(filepath: str | Path) -> dict:
    """Parse metadata from a DORA document filename.

    Returns dict with: source_code, language, document_type, topic,
    category, authority, source_file.
    """
    filename = Path(filepath).stem  # without .pdf
    match = re.match(r"(\d{4})_(DE|EN)_(REG|CORR|FAQ|GL|GUIDE|QA)_(.+)", filename)
    if not match:
        raise ValueError(f"Filename does not match schema: {filename}")

    code, lang, doc_type, topic = match.groups()

    # Determine authority from doc_type or topic
    authority = AUTHORITY_MAP.get(doc_type, "EU")
    topic_lower = topic.lower()
    if "bafin" in topic_lower:
        authority = "BaFin"
    elif "ezb" in topic_lower or "ecb" in topic_lower or "tiber-eu" in topic_lower:
        authority = "ECB"
    elif "bbk" in topic_lower or "tiber-de" in topic_lower:
        authority = "BBK"
    elif "esa" in topic_lower:
        authority = "ESA"

    return {
        "source_code": code,
        "language": lang,
        "document_type": doc_type,
        "topic": topic.replace("-", " "),
        "category": CATEGORY_MAP.get(code[:2], "Sonstige"),
        "authority": authority,
        "source_file": Path(filepath).name,
    }
