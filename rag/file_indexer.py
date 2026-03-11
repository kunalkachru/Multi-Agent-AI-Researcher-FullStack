"""
File Indexer — Parse, chunk, embed, and index uploaded files.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Orchestrates the pipeline: parse -> chunk -> index_documents.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any

from rag.document_parser import parse_file, SUPPORTED_EXTENSIONS


def _get_extension(filename: str) -> str:
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    return ""
from rag.chunking import chunk_text
from rag.vector_store import index_documents


def _sanitize_id_part(name: str) -> str:
    """Make a filename safe for use in chunk IDs."""
    base = re.sub(r"[^\w\-_.]", "_", name)
    return base[:80] if base else "file"


def index_uploaded_files(files: List[Any]) -> Dict[str, Any]:
    """
    Index one or more uploaded files into the vector store.

    Args:
        files: List of Streamlit UploadedFile or (bytes, filename) tuples.
               UploadedFile has .read() and .name attributes.

    Returns:
        {
            "success": int,      # number of files successfully indexed
            "failed": int,       # number of files that failed
            "total_chunks": int, # total chunks added
            "errors": List[str], # error messages for failed files
        }
    """
    result = {"success": 0, "failed": 0, "total_chunks": 0, "errors": []}
    all_texts = []
    all_metadatas = []
    all_ids = []

    for f in files:
        if hasattr(f, "read") and hasattr(f, "name"):
            file_bytes = f.read()
            filename = f.name or "unknown"
        elif isinstance(f, (tuple, list)) and len(f) >= 2:
            file_bytes, filename = f[0], f[1]
        else:
            result["failed"] += 1
            result["errors"].append("Invalid file object")
            continue

        ext = _get_extension(filename)
        if ext not in SUPPORTED_EXTENSIONS:
            result["failed"] += 1
            result["errors"].append(f"Unsupported format: {filename} (expected .txt, .pdf, .docx)")
            continue

        text = parse_file(file_bytes, filename)
        if not text or not text.strip():
            result["failed"] += 1
            result["errors"].append(f"Could not extract text from: {filename}")
            continue

        chunks = chunk_text(text)
        if not chunks:
            result["failed"] += 1
            result["errors"].append(f"No content to index in: {filename}")
            continue

        safe_name = _sanitize_id_part(filename)
        for i, chunk in enumerate(chunks):
            all_texts.append(chunk)
            all_metadatas.append({
                "source": safe_name,
                "doc_type": "user_upload",
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })
            all_ids.append(f"upload_{safe_name}_{i}")

        result["success"] += 1

    if all_texts:
        try:
            index_documents(all_texts, metadatas=all_metadatas, ids=all_ids)
            result["total_chunks"] = len(all_texts)
        except Exception as e:
            result["errors"].append(f"Indexing failed: {e}")
            result["success"] = 0
            result["total_chunks"] = 0

    return result
