"""
Tavily Web Search Client
━━━━━━━━━━━━━━━━━━━━━━━
Fetches real web results with URLs, titles, and snippets.
Think of it like sending a research assistant to the internet library
while your other assistant searches the local filing cabinet (vector DB).
Two sources of evidence are always better than one — just like in banking
audits, you cross-reference internal records with external reports.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import config

_client = None


def is_available() -> bool:
    """Return True if Tavily API key is configured."""
    return bool(config.TAVILY_API_KEY and config.TAVILY_API_KEY.strip())


def test_tavily_key(api_key: Optional[str] = None) -> Tuple[bool, str]:
    """
    Test that a Tavily API key works with a minimal search.
    If api_key is provided use it; else use config.TAVILY_API_KEY.
    Returns (True, "") on success, (False, "error message") on failure.
    """
    key = (api_key or "").strip() or (config.TAVILY_API_KEY or "").strip()
    if not key:
        return (False, "No API key provided or set in environment.")
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=key)
        client.search(query="test", max_results=1, search_depth="basic", include_answer=False)
        return (True, "")
    except Exception as e:
        msg = str(e).strip() or "Unknown error"
        if "401" in msg or "unauthorized" in msg.lower() or "invalid" in msg.lower():
            return (False, "Invalid or unauthorized API key.")
        return (False, msg)


def _get_client(api_key: Optional[str] = None):
    """Lazy-init Tavily client (config key), or one-off client if api_key given."""
    if api_key and api_key.strip():
        from tavily import TavilyClient
        return TavilyClient(api_key=api_key.strip())
    global _client
    if _client is None:
        from tavily import TavilyClient
        _client = TavilyClient(api_key=config.TAVILY_API_KEY)
    return _client


def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search the web via Tavily and return structured results.

    Returns list of dicts, each with:
      - title: str
      - url: str
      - snippet: str  (content excerpt)
      - score: float  (relevance 0-1)
      - source: "web"
    """
    effective_key = (api_key or "").strip() or (config.TAVILY_API_KEY or "").strip()
    if not effective_key:
        return []

    try:
        client = _get_client(effective_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=False,
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:500],
                "score": item.get("score", 0.0),
                "source": "web",
            })

        return results

    except Exception:
        return []


def multi_query_web_search(
    queries: List[str],
    max_results_per_query: int = 3,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Run web search for multiple query variants, deduplicate by URL.
    Returns a merged, deduplicated list of web results.
    """
    effective_key = (api_key or "").strip() or (config.TAVILY_API_KEY or "").strip()
    if not effective_key:
        return []

    seen_urls = set()
    all_results = []

    for q in queries:
        results = web_search(q, max_results=max_results_per_query, api_key=effective_key)
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    # Sort by relevance score descending
    all_results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return all_results
