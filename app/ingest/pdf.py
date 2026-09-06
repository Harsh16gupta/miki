"""PDF and plain-text extraction for Phase 3 ingestion.

Accepts raw uploaded bytes, sniffs PDF vs text, and returns clean text.
All LLM extraction downstream consumes this text — never raw bytes.
"""

from __future__ import annotations

from io import BytesIO


def extract_text_from_pdf_bytes(data: bytes) -> str:
    """Extract text from PDF bytes via pypdf.

    Raises:
        ValueError: If the bytes are not a valid PDF or contain no text.
    """
    from pypdf import PdfReader

    try:
        reader = PdfReader(BytesIO(data))
    except Exception as e:
        raise ValueError(f"Invalid PDF file: {e}") from e

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            pages_text.append("")

    text = "\n".join(t for t in pages_text if t.strip()).strip()
    if not text:
        raise ValueError("PDF contained no extractable text (scanned image?)")
    return text


def extract_text_from_bytes(data: bytes, filename: str | None = None) -> str:
    """Sniff PDF magic bytes (or .pdf filename) and return decoded text.

    Raises:
        ValueError: If decoding fails or the result is empty.
    """
    if data[:4] == b"%PDF" or (filename or "").lower().endswith(".pdf"):
        return extract_text_from_pdf_bytes(data)

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = data.decode(encoding).strip()
            if text:
                return text
        except (UnicodeDecodeError, ValueError):
            continue
    raise ValueError("Could not decode uploaded file as text")
