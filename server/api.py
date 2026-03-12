from __future__ import annotations

"""
Astraeus 2.0 FastAPI API
━━━━━━━━━━━━━━━━━━━━
Thin HTTP layer exposing the 6-agent pipeline and context for use by
external frontends (e.g. React) while keeping the existing Python core.
"""

from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel

import config
from llm import is_available as llm_available
from pipeline.orchestrator import AgentState, PipelineState
from pipeline.service import (
    start_pipeline_run,
    get_pipeline_state,
    get_pipeline_context,
)
from rag.file_indexer import index_uploaded_files
from rag.vector_store import get_collection_count
from rag.web_search import is_available as tavily_available
from utils.pdf_export import markdown_to_pdf_bytes


app = FastAPI(
    title="Astraeus 2.0 API",
    version="0.1.0",
)

# CORS configuration — allow local React dev (Vite may use 5173, 5174, etc. if port in use).
_default_origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://127.0.0.1:5175",
]
_extra = __import__("os").getenv("ALLOWED_ORIGINS", "")
origins = _default_origins + [o.strip() for o in _extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# So Hugging Face hub uses auth from .env and avoids "unauthenticated requests" warning
if config.HF_TOKEN and config.HF_TOKEN.strip():
    import os
    os.environ["HF_TOKEN"] = config.HF_TOKEN.strip()


# ── Pydantic models ─────────────────────────────────────────────────────


class RunRequest(BaseModel):
    query: str
    llm_model: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    search_type: Optional[str] = "both"


class LLMTestRequest(BaseModel):
    api_key: Optional[str] = None


class LLMTestResponse(BaseModel):
    ok: bool
    detail: str = ""


class TavilyTestRequest(BaseModel):
    api_key: Optional[str] = None


class TavilyTestResponse(BaseModel):
    ok: bool
    detail: str = ""


class RunResponse(BaseModel):
    run_id: str


class AgentStatusDTO(BaseModel):
    agent_id: str
    name: str
    state: AgentState
    progress: float
    elapsed_seconds: float
    output_summary: str = ""
    error_message: str = ""


class PipelineStateSummary(BaseModel):
    run_id: str
    query: str
    llm_model: str
    is_running: bool
    is_complete: bool
    has_error: bool
    total_elapsed: float
    agents: List[AgentStatusDTO]


class RunContextDTO(BaseModel):
    # Use a loose schema for now; can be tightened later
    data: dict[str, Any]


class UploadResult(BaseModel):
    success: int
    failed: int
    total_chunks: int
    errors: List[str]
    doc_count: int


class LLMModelMeta(BaseModel):
    id: str
    name: str
    input_per_1m: float
    output_per_1m: float
    hint: str = ""


class EmbeddingModelMeta(BaseModel):
    id: str
    name: str
    dimension: int
    hint: str = ""


class MetaDTO(BaseModel):
    embedding_model: str
    embedding_models: List[EmbeddingModelMeta]
    embedding_hf_configured: bool
    llm_models: List[LLMModelMeta]
    doc_count: int
    tavily_available: bool
    tavily_configured: bool
    llm_available: bool
    llm_configured: bool


class EmbeddingTestRequest(BaseModel):
    model_id: Optional[str] = None
    token: Optional[str] = None


class EmbeddingConfigureRequest(BaseModel):
    model_id: str
    token: Optional[str] = None


class EmbeddingTestResponse(BaseModel):
    ok: bool
    detail: str = ""


# ── Helpers ─────────────────────────────────────────────────────────────


def _to_agent_status_dto(state: PipelineState) -> List[AgentStatusDTO]:
    items: List[AgentStatusDTO] = []
    for agent in state.agents:
        items.append(
            AgentStatusDTO(
                agent_id=agent.agent_id,
                name=agent.name,
                state=agent.state,
                progress=agent.progress,
                elapsed_seconds=agent.elapsed_seconds,
                output_summary=agent.output_summary or "",
                error_message=agent.error_message or "",
            )
        )
    return items


def _to_summary(run_id: str, state: PipelineState) -> PipelineStateSummary:
    context = state.context or {}
    query = context.get("query", "")
    llm_model = context.get("llm_model", "")
    return PipelineStateSummary(
        run_id=run_id,
        query=query,
        llm_model=llm_model,
        is_running=state.is_running,
        is_complete=state.is_complete,
        has_error=state.has_error,
        total_elapsed=state.total_elapsed,
        agents=_to_agent_status_dto(state),
    )


# ── Routes ──────────────────────────────────────────────────────────────


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/llm/test", response_model=LLMTestResponse)
def test_llm_key(req: LLMTestRequest) -> LLMTestResponse:
    from llm import test_api_key
    ok, detail = test_api_key(req.api_key)
    return LLMTestResponse(ok=ok, detail=detail)


@app.post("/api/tavily/test", response_model=TavilyTestResponse)
def test_tavily_key_route(req: TavilyTestRequest) -> TavilyTestResponse:
    from rag.web_search import test_tavily_key
    ok, detail = test_tavily_key(req.api_key)
    return TavilyTestResponse(ok=ok, detail=detail)


@app.post("/api/run", response_model=RunResponse, status_code=201)
def start_run(req: RunRequest) -> RunResponse:
    query = (req.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    search_type = (req.search_type or "both").strip().lower()
    if search_type not in ("both", "rag_only", "web_only"):
        search_type = "both"

    if search_type == "web_only":
        has_tavily = bool(
            (req.tavily_api_key and req.tavily_api_key.strip())
            or (config.TAVILY_API_KEY and config.TAVILY_API_KEY.strip())
        )
        if not has_tavily:
            raise HTTPException(
                status_code=400,
                detail="Web search only requires a Tavily API key. Set TAVILY_API_KEY in .env or provide it in the request.",
            )

    run_id = start_pipeline_run(
        query=query,
        llm_model=req.llm_model,
        openrouter_api_key=req.openrouter_api_key,
        tavily_api_key=req.tavily_api_key,
        search_type=search_type,
    )
    return RunResponse(run_id=run_id)


@app.get("/api/run/{run_id}", response_model=PipelineStateSummary)
def get_run(run_id: str) -> PipelineStateSummary:
    state = get_pipeline_state(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return _to_summary(run_id, state)


@app.get("/api/run/{run_id}/context", response_model=RunContextDTO)
def get_run_context(run_id: str) -> RunContextDTO:
    ctx = get_pipeline_context(run_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return RunContextDTO(data=ctx)


@app.get("/api/run/{run_id}/report/markdown", response_class=PlainTextResponse)
def get_run_report_markdown(run_id: str) -> PlainTextResponse:
    ctx = get_pipeline_context(run_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    report = ctx.get("report_markdown") or ""
    if not report:
        raise HTTPException(status_code=404, detail="Report not available for this run.")
    return PlainTextResponse(content=report, media_type="text/markdown")


@app.get("/api/run/{run_id}/report/pdf")
def get_run_report_pdf(run_id: str) -> Response:
    ctx = get_pipeline_context(run_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    report = ctx.get("report_markdown") or ""
    if not report:
        raise HTTPException(status_code=404, detail="Report not available for this run.")
    query = ctx.get("query", "")
    try:
        pdf_bytes = markdown_to_pdf_bytes(report, title=(query[:80] if query else "Research Report"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")
    return Response(content=pdf_bytes, media_type="application/pdf")


@app.post("/api/uploads", response_model=UploadResult)
async def upload_documents(files: List[UploadFile] = File(...)) -> UploadResult:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # Adapt FastAPI UploadFile objects into simple file-like objects expected by index_uploaded_files.
    class _SimpleFile:
        def __init__(self, data: bytes, name: str):
            self._data = data
            self.name = name

        def read(self) -> bytes:
            return self._data

    simple_files: List[_SimpleFile] = []
    for f in files:
        data = await f.read()
        simple_files.append(_SimpleFile(data=data, name=f.filename or "uploaded"))

    result = index_uploaded_files(simple_files)
    doc_count = get_collection_count()
    return UploadResult(
        success=result.get("success", 0),
        failed=result.get("failed", 0),
        total_chunks=result.get("total_chunks", 0),
        errors=result.get("errors", []),
        doc_count=doc_count,
    )


def _test_embedding_load(model_id: str, token: Optional[str]) -> tuple[bool, str]:
    """Try to load the embedding model with optional token. Returns (ok, detail). Does not change global state."""
    try:
        from sentence_transformers import SentenceTransformer
        SentenceTransformer(
            model_id,
            token=token or None,
            model_kwargs={"low_cpu_mem_usage": False},
        )
        return (True, "")
    except Exception as e:
        return (False, str(e).strip() or "Failed to load model")


@app.post("/api/embedding/test", response_model=EmbeddingTestResponse)
def test_embedding(req: EmbeddingTestRequest) -> EmbeddingTestResponse:
    from rag.embeddings import get_effective_embedding_model
    model_id = (req.model_id or "").strip() or get_effective_embedding_model()
    if not model_id:
        return EmbeddingTestResponse(ok=False, detail="No model selected.")
    ok, detail = _test_embedding_load(model_id, req.token)
    return EmbeddingTestResponse(ok=ok, detail=detail)


@app.post("/api/embedding/configure")
def configure_embedding(req: EmbeddingConfigureRequest) -> dict[str, str]:
    from rag.embeddings import set_embedding_override
    model_id = (req.model_id or "").strip()
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required.")
    set_embedding_override(model_id, req.token)
    return {"status": "ok", "embedding_model": model_id}


@app.get("/api/meta", response_model=MetaDTO)
def get_meta() -> MetaDTO:
    from llm import is_available as _llm_available  # ensure lazy import for environments without LLM
    from rag.embeddings import get_effective_embedding_model

    embedding_model = get_effective_embedding_model()
    # Normalize short name to full id so frontend dropdown can match
    if embedding_model == "all-MiniLM-L6-v2":
        embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_models = [
        EmbeddingModelMeta(
            id=m["id"],
            name=m["name"],
            dimension=int(m.get("dimension", 384)),
            hint=str(m.get("hint", "")),
        )
        for m in config.EMBEDDING_MODELS
    ]
    embedding_hf_configured = bool(config.HF_TOKEN and config.HF_TOKEN.strip())
    llm_models = [
        LLMModelMeta(
            id=m["id"],
            name=m["name"],
            input_per_1m=float(m.get("input_per_1m", 0)),
            output_per_1m=float(m.get("output_per_1m", 0)),
            hint=str(m.get("hint", "")),
        )
        for m in config.LLM_MODELS
    ]
    try:
        doc_count = get_collection_count()
    except Exception:
        doc_count = 0
    llm_configured = bool(config.OPENROUTER_API_KEY and config.OPENROUTER_API_KEY.strip())
    tavily_configured = bool(config.TAVILY_API_KEY and config.TAVILY_API_KEY.strip())
    return MetaDTO(
        embedding_model=embedding_model,
        embedding_models=embedding_models,
        embedding_hf_configured=embedding_hf_configured,
        llm_models=llm_models,
        doc_count=doc_count,
        tavily_available=tavily_available(),
        tavily_configured=tavily_configured,
        llm_available=_llm_available(),
        llm_configured=llm_configured,
    )


