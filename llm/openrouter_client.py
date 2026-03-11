"""
OpenRouter LLM Client
━━━━━━━━━━━━━━━━━━━
Uses OpenRouter's OpenAI-compatible API so you can use any model
(GPT-4, Claude, Llama, etc.) with one key. Like having one bank card
that works at every ATM.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import config

_client = None


def _get_client(api_key: Optional[str] = None):
    """Lazy-init OpenAI client pointed at OpenRouter. If api_key is given, return a one-off client with it."""
    if api_key and api_key.strip():
        from openai import OpenAI
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key.strip(),
        )
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


def test_api_key(api_key: Optional[str] = None) -> Tuple[bool, str]:
    """
    Test that an OpenRouter API key works with a minimal request.
    If api_key is provided, use it; otherwise use config.OPENROUTER_API_KEY.
    Returns (True, "") on success, (False, "error message") on failure.
    """
    key = (api_key or "").strip() or config.OPENROUTER_API_KEY or ""
    if not key:
        return (False, "No API key provided or set in environment.")
    try:
        client = _get_client(key)
        resp = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
            temperature=0,
        )
        if resp.choices and resp.choices[0].message and resp.choices[0].message.content:
            return (True, "")
        return (False, "Empty response from API.")
    except Exception as e:
        msg = str(e).strip() or "Unknown error"
        if "401" in msg or "unauthorized" in msg.lower() or "invalid" in msg.lower():
            return (False, "Invalid or unauthorized API key.")
        return (False, msg)


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    api_key: Optional[str] = None,
) -> Optional[str]:
    """
    Send a chat completion request to OpenRouter.
    messages: [{"role": "user"|"system"|"assistant", "content": "..."}]
    api_key: optional run-scoped key; if not set, uses config.OPENROUTER_API_KEY.
    Returns the assistant's reply text, or None on error or if not configured.
    """
    effective_key = (api_key or "").strip() or config.OPENROUTER_API_KEY
    if not effective_key:
        return None

    model = model or config.LLM_MODEL

    try:
        client = _get_client(effective_key)
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


def chat_completion_with_usage(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    api_key: Optional[str] = None,
) -> Tuple[Optional[str], Optional[Dict[str, int]]]:
    """
    Send a chat completion request to OpenRouter; return text and token usage.
    api_key: optional run-scoped key; if not set, uses config.OPENROUTER_API_KEY.
    Returns (reply_text, usage_dict) where usage_dict = {"prompt_tokens": int, "completion_tokens": int}.
    On error or if not configured: (None, None). Usage is None when text is None.
    """
    effective_key = (api_key or "").strip() or config.OPENROUTER_API_KEY
    if not effective_key:
        return (None, None)

    model = model or config.LLM_MODEL

    try:
        client = _get_client(effective_key)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choice = resp.choices[0] if resp.choices else None
        text = None
        if choice and choice.message and choice.message.content:
            text = choice.message.content.strip()

        usage = None
        if hasattr(resp, "usage") and resp.usage is not None:
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or getattr(resp.usage, "input_tokens", 0),
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or getattr(resp.usage, "output_tokens", 0),
            }

        return (text, usage)
    except Exception:
        return (None, None)
