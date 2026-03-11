"""
Configuration for Astraeus 2.0 — Multi-Agent AI Deep Researcher.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Vector DB ──────────────────────────────────────────────────────────────
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma")          # "chroma" only for v1
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "research_docs")

# ── Embedding Model ───────────────────────────────────────────────────────
# HF token: set HF_TOKEN or HUGGING_FACE_HUB_TOKEN for higher rate limits and gated models
HF_TOKEN = (
    os.getenv("HF_TOKEN")
    or os.getenv("HUGGING_FACE_HUB_TOKEN")
    or os.getenv("HUGGINGFACE_TOKEN")
    or ""
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

# Popular open-source embedding models (id = HuggingFace model id, dimension = output size)
EMBEDDING_MODELS = [
    {"id": "sentence-transformers/all-MiniLM-L6-v2", "name": "MiniLM-L6-v2", "dimension": 384, "hint": "Fast, good for most use cases"},
    {"id": "sentence-transformers/all-MiniLM-L12-v2", "name": "MiniLM-L12-v2", "dimension": 384, "hint": "Slightly better quality, same size"},
    {"id": "sentence-transformers/all-mpnet-base-v2", "name": "MPNet Base v2", "dimension": 768, "hint": "Higher quality, larger"},
    {"id": "BAAI/bge-small-en-v1.5", "name": "BGE Small EN", "dimension": 384, "hint": "Strong retrieval, small footprint"},
    {"id": "BAAI/bge-base-en-v1.5", "name": "BGE Base EN", "dimension": 768, "hint": "Strong retrieval, medium size"},
    {"id": "BAAI/bge-large-en-v1.5", "name": "BGE Large EN", "dimension": 1024, "hint": "Best quality, largest"},
    {"id": "intfloat/e5-small-v2", "name": "E5 Small v2", "dimension": 384, "hint": "E5 family, efficient"},
    {"id": "intfloat/e5-base-v2", "name": "E5 Base v2", "dimension": 768, "hint": "E5 family, balanced"},
    {"id": "thenlper/gte-small", "name": "GTE Small", "dimension": 384, "hint": "General Text Embeddings"},
    {"id": "thenlper/gte-base", "name": "GTE Base", "dimension": 768, "hint": "General Text Embeddings"},
]

# ── LLM (OpenRouter) ───────────────────────────────────────────────────
# OpenRouter: one API for many models (GPT-4, Claude, etc.)
OPENROUTER_API_KEY = (
    os.getenv("OPENROUTER_API_KEY")
    or os.getenv("OPEN_ROUTER_API_KEY")
    or os.getenv("OPEN_ROUTER_API")
    or ""
)
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")  # OpenRouter model id
LLM_PROVIDER = "openrouter"  # only openrouter for v1

# Economical OpenRouter models for dropdown (id, name, $/1M input, $/1M output, optional hint)
LLM_MODELS = [
    {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "input_per_1m": 0.15, "output_per_1m": 0.60, "hint": "Good balance of speed and quality for reports"},
    {"id": "meta-llama/llama-3.2-3b-instruct", "name": "Llama 3.2 3B", "input_per_1m": 0.06, "output_per_1m": 0.06, "hint": "Very low cost, best for drafts"},
    {"id": "google/gemma-2-9b-it", "name": "Gemma 2 9B", "input_per_1m": 0.07, "output_per_1m": 0.07, "hint": "Low cost, solid for summaries"},
    {"id": "mistralai/mistral-7b-instruct", "name": "Mistral 7B", "input_per_1m": 0.07, "output_per_1m": 0.07, "hint": "Fast and cheap"},
    {"id": "qwen/qwen-2-7b-instruct", "name": "Qwen 2 7B", "input_per_1m": 0.04, "output_per_1m": 0.04, "hint": "Lowest cost option"},
    {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku", "input_per_1m": 0.25, "output_per_1m": 1.25, "hint": "Higher quality, best for final reports"},
]

# ── Tavily (optional web search for research) ────────────────────────────
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ── Pipeline ──────────────────────────────────────────────────────────────
MAX_QUERY_EXPANSIONS = int(os.getenv("MAX_QUERY_EXPANSIONS", "3"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "10"))
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() == "true"

# ── Document Chunking (for file uploads) ───────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# ── App ───────────────────────────────────────────────────────────────────
APP_TITLE = "Astraeus 2.0"
APP_TAGLINE = "Multi-Agent AI Deep Researcher · 6 Agents · RAG-Powered"
DEMO_TIMEOUT_SECONDS = int(os.getenv("DEMO_TIMEOUT_SECONDS", "180"))

# ── Agent definitions (order matters) ─────────────────────────────────────
AGENT_COLORS = {
    "coordinator": "#ec4899",       # pink
    "retriever": "#38bdf8",         # light blue
    "critical_analysis": "#a78bfa", # purple
    "fact_checker": "#4ade80",      # light green
    "insight_generator": "#fbbf24", # amber
    "report_builder": "#22d3ee",    # cyan
}

AGENTS = [
    {"id": "coordinator",       "name": "Research Coordinator",  "icon": "🤖", "corner_icon": "🎯", "subtitle": "Query Analysis & Expansion"},
    {"id": "retriever",         "name": "Contextual Retriever",  "icon": "🤖", "corner_icon": "📋", "subtitle": "Vector Search & Ranking"},
    {"id": "critical_analysis", "name": "Critical Analysis",     "icon": "🤖", "corner_icon": "🔍", "subtitle": "Claims & Contradictions"},
    {"id": "fact_checker",      "name": "Fact-Checker",          "icon": "🤖", "corner_icon": "✓", "subtitle": "Source Credibility"},
    {"id": "insight_generator", "name": "Insight Generator",     "icon": "🤖", "corner_icon": "💡", "subtitle": "Themes & Gaps"},
    {"id": "report_builder",    "name": "Report Builder",        "icon": "🤖", "corner_icon": "📄", "subtitle": "Final Report & Citations"},
]
