"""
Chunking — Split text into overlapping chunks for embedding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sentence-boundary aware where possible; character-based fallback.
"""

from __future__ import annotations
import re
from typing import List

import config


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[str]:
    """
    Split text into chunks with overlap.
    Prefers splitting on sentence boundaries (. ! ?) when possible.
    """
    if not text or not text.strip():
        return []

    chunk_size = chunk_size if chunk_size is not None else config.CHUNK_SIZE
    chunk_overlap = chunk_overlap if chunk_overlap is not None else config.CHUNK_OVERLAP
    chunk_overlap = min(chunk_overlap, chunk_size - 1)

    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    # Split into sentences (roughly)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = []

    def flush():
        nonlocal current
        if current:
            chunk = " ".join(current).strip()
            if chunk:
                chunks.append(chunk)
            current = []

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        # Single sentence longer than chunk_size: split by chars
        if len(sent) > chunk_size:
            flush()
            for i in range(0, len(sent), chunk_size - chunk_overlap):
                chunk = sent[i : i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
            continue

        current.append(sent)
        joined = " ".join(current)

        if len(joined) >= chunk_size:
            # Overlap: keep the last part for context before flushing
            overlap_sents = []
            overlap_len = 0
            for s in reversed(current):
                overlap_sents.insert(0, s)
                overlap_len += len(s) + 1
                if overlap_len >= chunk_overlap:
                    break
            flush()
            current = overlap_sents

    flush()
    return chunks
