"""
Contextual Retriever Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━
Second agent. Like the Document Verification desk at a bank — it pulls all
relevant documents from the vault (vector DB) AND searches the web via
Tavily, checks them, ranks them, and hands the best ones forward.

Responsibilities:
  • Take expanded queries from Coordinator
  • Search the vector store (multi-query + optional hybrid)
  • Search the web via Tavily for live sources with URLs
  • Return ranked chunks + web results with metadata for visualizations
"""

from __future__ import annotations
from typing import Dict, Any
from rag.retrieval import multi_query_retrieval
from rag.web_search import multi_query_web_search, is_available as tavily_available
from rag.embeddings import embed_query
import config


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input context keys:
      - expanded_queries: List[str]
      - query: str
      - search_type: "both" | "rag_only" | "web_only" (default "both")

    Output added to context:
      - retrieved_chunks: List[dict]       (from vector DB / embeddings and/or web)
      - web_results: List[dict]            (from Tavily web search)
      - retrieval_metadata: dict
      - query_embedding: list
    """
    expanded_queries = context.get("expanded_queries", [context.get("query", "")])
    original_query = context.get("query", "")
    search_type = (context.get("search_type") or "both").strip().lower()
    if search_type not in ("both", "rag_only", "web_only"):
        search_type = "both"

    # ── Part 1: Embedding retrieval (vector DB) ───────────────────────
    chunks = []
    stage_counts = {}
    per_query_counts = {}
    if search_type in ("both", "rag_only"):
        retrieval_result = multi_query_retrieval(
            queries=expanded_queries,
            top_k=config.TOP_K_RESULTS,
        )
        chunks = retrieval_result["chunks"]
        stage_counts = retrieval_result["stage_counts"]
        per_query_counts = retrieval_result["per_query_counts"]

    # ── Part 2: Web search via Tavily ─────────────────────────────────
    web_results = []
    if search_type in ("both", "web_only"):
        tavily_key = context.get("tavily_api_key") or (config.TAVILY_API_KEY if tavily_available() else None)
        if tavily_key:
            web_results = multi_query_web_search(
                queries=expanded_queries[:2],   # use top 2 queries to save API calls
                max_results_per_query=3,
                api_key=tavily_key,
            )

    # ── Get query embedding for visualization ─────────────────────────
    q_embedding = embed_query(original_query).tolist()

    # ── Convert web results into chunk-compatible format ─────────────
    web_chunks = []
    web_texts = [w.get("snippet", "") for w in web_results if w.get("snippet", "").strip()]
    web_embeddings = []
    if web_texts:
        from rag.embeddings import embed_texts
        web_embeddings = embed_texts(web_texts).tolist()

    for i, w in enumerate(web_results):
        snippet = w.get("snippet", "")
        web_chunks.append({
            "id": f"web_{i}",
            "text": snippet,
            "metadata": {
                "source": "web",
                "doc_type": "web_page",
                "title": w.get("title", ""),
                "url": w.get("url", ""),
                "year": "2025",
            },
            "final_score": w.get("score", 0.5),
            "embedding": web_embeddings[i] if i < len(web_embeddings) else None,
            "is_web": True,
        })

    # Merge: web chunks + embedding chunks = all chunks for analysis (both); or only one source
    all_chunks = (web_chunks + chunks) if search_type == "both" else (web_chunks if search_type == "web_only" else chunks)

    # ── Build retriever output ────────────────────────────────────────
    context["retrieved_chunks"] = all_chunks
    context["embedding_chunks"] = chunks
    context["web_results"] = web_results
    context["retrieval_metadata"] = {
        "stage_counts": stage_counts,
        "per_query_counts": per_query_counts,
        "total_chunks": len(chunks),
        "web_results_count": len(web_results),
        "top_score": chunks[0]["final_score"] if chunks else 0.0,
    }
    context["query_embedding"] = q_embedding

    # Source distribution for visualization
    source_dist = {}
    for chunk in chunks:
        src = chunk.get("metadata", {}).get("source", "unknown")
        source_dist[src] = source_dist.get(src, 0) + 1
    if web_results:
        source_dist["web (Tavily)"] = len(web_results)
    context["source_distribution"] = source_dist

    context["retriever_output"] = {
        "num_chunks": len(chunks),
        "web_results_count": len(web_results),
        "stage_counts": stage_counts,
        "per_query_counts": per_query_counts,
        "source_distribution": source_dist,
        "top_chunks_preview": [
            {"id": c["id"], "score": round(c["final_score"], 3),
             "text_preview": c["text"][:120] + "..."}
            for c in chunks[:5]
        ],
        "top_web_preview": [
            {"title": w["title"], "url": w["url"], "score": round(w.get("score", 0), 3)}
            for w in web_results[:3]
        ],
    }

    return context
