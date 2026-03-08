"""Document-type-aware chunking strategies for DORA documents."""

import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def chunk_documents(pages: list[Document], doc_type: str) -> list[Document]:
    """Chunk document pages using a strategy based on document type.

    Args:
        pages: List of Document objects from PDF loader (one per page).
        doc_type: Document type from filename metadata (REG, CORR, FAQ, GL, GUIDE, QA).

    Returns:
        List of chunked Document objects.
    """
    full_text = "\n".join(page.page_content for page in pages)
    base_metadata = pages[0].metadata if pages else {}

    if doc_type in ("REG", "CORR"):
        return _chunk_regulation(full_text, base_metadata)
    elif doc_type == "FAQ":
        return _chunk_faq(full_text, base_metadata)
    elif doc_type == "QA":
        return _chunk_qa(full_text, base_metadata)
    else:  # GL, GUIDE
        return _chunk_guide(full_text, base_metadata)


def _chunk_regulation(text: str, metadata: dict) -> list[Document]:
    """Split regulation text on article boundaries."""
    splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\nArtikel ",
            "\nArticle ",
            "\nAbschnitt ",
            "\nSection ",
            "\nKapitel ",
            "\nChapter ",
            "\n\n",
            "\n",
        ],
        chunk_size=1500,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = splitter.create_documents([text], metadatas=[metadata])

    # Extract article number from each chunk
    for chunk in chunks:
        article_match = re.search(r"(?:Artikel|Article)\s+(\d+)", chunk.page_content)
        if article_match:
            chunk.metadata["article"] = int(article_match.group(1))

    return chunks


def _chunk_faq(text: str, metadata: dict) -> list[Document]:
    """Split FAQ on question boundaries."""
    # BaFin FAQs use patterns like "Frage 1:", "Q1:", or numbered questions
    pattern = r"(?=(?:Frage\s+\d|Q\s*\d|\d+\.\s+Frage))"
    parts = re.split(pattern, text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 50]

    if not parts:
        # Fallback to standard chunking
        return _chunk_guide(text, metadata)

    chunks = []
    for i, part in enumerate(parts):
        chunk_meta = {**metadata, "chunk_index": i}
        question_match = re.search(r"(?:Frage|Q)\s*(\d+)", part)
        if question_match:
            chunk_meta["question_number"] = int(question_match.group(1))
        chunks.append(Document(page_content=part, metadata=chunk_meta))

    return chunks


def _chunk_qa(text: str, metadata: dict) -> list[Document]:
    """Split ESA Q&A compilation on DORA question numbers."""
    pattern = r"(?=DORA\d{3})"
    parts = re.split(pattern, text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 50]

    if not parts:
        return _chunk_guide(text, metadata)

    chunks = []
    for i, part in enumerate(parts):
        chunk_meta = {**metadata, "chunk_index": i}
        qa_match = re.search(r"(DORA\d{3})", part)
        if qa_match:
            chunk_meta["qa_number"] = qa_match.group(1)
        chunks.append(Document(page_content=part, metadata=chunk_meta))

    return chunks


def _chunk_guide(text: str, metadata: dict) -> list[Document]:
    """Standard chunking for guidelines and guidance documents."""
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
        chunk_size=1200,
        chunk_overlap=200,
        length_function=len,
    )
    return splitter.create_documents([text], metadatas=[metadata])
