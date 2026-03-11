"""
Embedding model wrapper.
Uses sentence-transformers for local embeddings.
Think of this like a translator that converts human text into numbers
that a computer can compare for similarity.
"""

from __future__ import annotations
import os
from typing import List, Optional
import numpy as np

_model = None
_model_id_loaded: Optional[str] = None
_override_model: Optional[str] = None
_override_token: Optional[str] = None


def get_effective_embedding_model() -> str:
    """Return the model id to use (override or config)."""
    import config
    return _override_model or config.EMBEDDING_MODEL


def get_effective_token() -> Optional[str]:
    """Return the token to use for Hugging Face (override or config)."""
    import config
    return _override_token if _override_token else (config.HF_TOKEN or None)


def set_embedding_override(model_id: Optional[str] = None, token: Optional[str] = None) -> None:
    """Set model/token override and clear cache so next use loads fresh."""
    global _override_model, _override_token, _model, _model_id_loaded
    _override_model = (model_id or "").strip() or None
    _override_token = (token or "").strip() or None
    _model = None
    _model_id_loaded = None


def _get_model():
    """Lazy-load the sentence-transformers model (heavy import)."""
    global _model, _model_id_loaded
    import config
    model_id = get_effective_embedding_model()
    token = get_effective_token()
    if _model is None or _model_id_loaded != model_id:
        if _model is not None:
            _model = None
        _model_id_loaded = model_id
        if token:
            os.environ["HF_TOKEN"] = token
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(
            model_id,
            token=token,
            model_kwargs={"low_cpu_mem_usage": False},
        )
    return _model


def reset_embedding_model():
    """Clear cached model so next use loads fresh (e.g. after model/token change)."""
    global _model, _model_id_loaded
    _model = None
    _model_id_loaded = None


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of texts and return an (N, dim) numpy array."""
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string and return a 1-D vector."""
    return embed_texts([query])[0]
