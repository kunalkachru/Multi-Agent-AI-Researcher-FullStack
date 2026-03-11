"""
End-to-end tests for file upload and indexing.
Run with: pytest tests/test_file_upload.py -v
"""

import io
import sys
import os

# Project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_parse_txt():
    from rag.document_parser import parse_file

    content = b"Hello world. This is a test document for RAG indexing."
    text = parse_file(content, "test.txt")
    assert text is not None
    assert "RAG indexing" in text


def test_parse_pdf():
    from rag.document_parser import parse_file
    from pypdf import PdfWriter

    # Create a minimal PDF
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    # pypdf creates blank pages - add actual text via a different approach
    # Use PyPDF2/Pypdf page with text - for simplicity we test that parse doesn't crash
    content = buf.getvalue()
    text = parse_file(content, "test.pdf")
    assert text is not None  # May be empty for blank PDF


def test_parse_docx():
    from rag.document_parser import parse_file
    from docx import Document

    doc = Document()
    doc.add_paragraph("Sample content for RAG testing.")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    text = parse_file(buf.getvalue(), "test.docx")
    assert text is not None
    assert "RAG testing" in text


def test_chunk_text():
    from rag.chunking import chunk_text

    short = "Short text."
    assert chunk_text(short) == ["Short text."]

    long_text = " ".join(["Sentence number " + str(i) + "." for i in range(100)])
    chunks = chunk_text(long_text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= 2
    assert all(len(c) <= 120 for c in chunks)


def test_index_single_file():
    from rag.file_indexer import index_uploaded_files
    from rag.vector_store import get_collection_count, reset_collection

    reset_collection()
    count_before = get_collection_count()

    files = [(b"Content about machine learning and neural networks.", "doc.txt")]
    result = index_uploaded_files(files)

    assert result["success"] == 1
    assert result["total_chunks"] >= 1
    assert result["failed"] == 0
    assert get_collection_count() == count_before + result["total_chunks"]


def test_index_multiple_files():
    from rag.file_indexer import index_uploaded_files
    from rag.vector_store import get_collection_count, reset_collection

    reset_collection()

    files = [
        (b"First document about Python programming.", "a.txt"),
        (b"Second document about data science.", "b.txt"),
    ]
    result = index_uploaded_files(files)

    assert result["success"] == 2
    assert result["total_chunks"] >= 2
    assert result["failed"] == 0


def test_index_unsupported_format():
    from rag.file_indexer import index_uploaded_files

    files = [(b"content", "file.exe")]
    result = index_uploaded_files(files)
    assert result["success"] == 0
    assert result["failed"] == 1
    assert "Unsupported" in result["errors"][0]


def test_index_empty_file():
    from rag.file_indexer import index_uploaded_files

    files = [(b"", "empty.txt")]
    result = index_uploaded_files(files)
    assert result["failed"] >= 1 or result["total_chunks"] == 0
