"""Security helpers for the FastAPI layer."""

from __future__ import annotations

import os
from typing import Any

_SENSITIVE_CONTEXT_KEYS = frozenset(
    {"openrouter_api_key", "tavily_api_key", "open_router_api_key"}
)

MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", "10000"))
UPLOAD_MAX_REQUEST_BODY_BYTES = int(
    os.getenv("UPLOAD_MAX_REQUEST_BODY_BYTES", str(25 * 1024 * 1024))
)


def redact_context(ctx: dict[str, Any]) -> dict[str, Any]:
    """Remove API keys from pipeline context before returning to clients."""
    return {k: v for k, v in ctx.items() if k not in _SENSITIVE_CONTEXT_KEYS}
