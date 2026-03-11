"""
Document Parser — Extract text from .txt, .pdf, .docx files.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Used by the file upload indexing pipeline.
"""

from __future__ import annotations
import io
from typing import Optional

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def parse_txt(file_bytes: bytes) -> str:
    """Extract text from a .txt file. Tries utf-8, falls back to latin-1."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")


def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def parse_docx(file_bytes: bytes) -> str:
    """Extract text from a .docx file using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    return "\n\n".join(parts)


def parse_file(file_bytes: bytes, filename: str) -> Optional[str]:
    """
    Parse a file and return its text content, or None on failure.

    Supports: .txt, .pdf, .docx
    """
    if not file_bytes or not filename:
        return None

    ext = _get_extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        return None

    try:
        if ext == ".txt":
            return parse_txt(file_bytes)
        elif ext == ".pdf":
            return parse_pdf(file_bytes)
        elif ext == ".docx":
            return parse_docx(file_bytes)
    except Exception:
        return None

    return None


def _get_extension(filename: str) -> str:
    """Return lowercase extension including the dot."""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    return ""
