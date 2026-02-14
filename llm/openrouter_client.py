"""
OpenRouter LLM Client
━━━━━━━━━━━━━━━━━━━
Uses OpenRouter's OpenAI-compatible API so you can use any model
(GPT-4, Claude, Llama, etc.) with one key. Like having one bank card
that works at every ATM.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import config

_client = None


def _get_client():
    """Lazy-init OpenAI client pointed at OpenRouter."""
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
        )
    return _client


def is_available() -> bool:
    """Return True if OpenRouter is configured (API key set)."""
    return bool(config.OPENROUTER_API_KEY and config.OPENROUTER_API_KEY.strip())


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> Optional[str]:
    """
    Send a chat completion request to OpenRouter.
    messages: [{"role": "user"|"system"|"assistant", "content": "..."}]
    Returns the assistant's reply text, or None on error or if not configured.
    """
    if not is_available():
        return None

    model = model or config.LLM_MODEL

    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choice = resp.choices[0] if resp.choices else None
        if choice and choice.message and choice.message.content:
            return choice.message.content.strip()
        return None
    except Exception:
        return None
