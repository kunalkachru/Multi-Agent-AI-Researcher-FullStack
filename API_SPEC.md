# Astraeus 2.0 API Specification (Draft)

> Status: DRAFT  
> Purpose: Define a thin HTTP API so both Streamlit and a future React frontend can drive the existing 6‑agent pipeline and RAG stack.

---

## 1. Overview

- **Backend runtime**: Python (FastAPI preferred)
- **Existing core**: `pipeline/orchestrator.py`, `agents/*`, `rag/*`, `llm/*`, `utils/pdf_export.py`
- **API consumers**:
  - Current: future React/TypeScript SPA
  - Optional: internal tools, CLI, tests

All endpoints are prefixed with `/api`.

---

## 2. Data Models (high level)

These are conceptual models; exact types will be expressed as Pydantic models.

### 2.1 AgentStatus

- `id: string` – agent id (`coordinator`, `retriever`, etc.)
- `name: string` – human-readable name
- `state: "not_started" | "waiting" | "working" | "complete" | "error"`
- `progress: number` – 0.0–1.0
- `elapsed_seconds: number`
- `output_summary: string | null`
- `error_message: string | null`

### 2.2 PipelineStateSummary

- `run_id: string`
- `query: string`
- `llm_model: string`
- `is_running: boolean`
- `is_complete: boolean`
- `has_error: boolean`
- `total_elapsed: number`
- `agents: AgentStatus[]`

### 2.3 RunContext

Subset of the internal `context` dict, shaped for UI use:

- `query: string`
- `retrieval_metadata: object`
- `retrieved_chunks: object[]`
- `web_results: object[]`
- `claims: object[]`
- `fact_check_results: object[]`
- `themes: object[]`
- `gaps: object[]`
- `hypotheses: object[]`
- `key_insights: string[]`
- `report_markdown: string`
- `report_metadata: object`
- `llm_usage: { prompt_tokens?: number; completion_tokens?: number; [k: string]: any }`

### 2.4 UploadResult

- `success: number`
- `failed: number`
- `total_chunks: number`
- `errors: string[]`
- `doc_count: number` – updated total in vector store

### 2.5 Meta

- `embedding_model: string`
- `llm_models: { id: string; name: string }[]`
- `doc_count: number`
- `tavily_available: boolean`
- `llm_available: boolean`

---

## 3. Endpoints

### 3.1 Health

**GET `/api/health`**

- **200 OK** → `{ "status": "ok" }`

Used for basic liveness checks.

---

### 3.2 Pipeline Runs

#### 3.2.1 Start a run

**POST `/api/run`**

Request body:

```json
{
  "query": "How does RAG reduce hallucinations?",
  "llm_model": "openai/gpt-4o-mini"  // optional; defaults from config
}
```

Response `201 Created`:

```json
{
  "run_id": "uuid-string"
}
```

Errors:

- `400` – missing or empty `query`
- `500` – unexpected server error

Implementation notes:

- May initially run the pipeline synchronously in this request.
- Later can offload to background task and mark `is_running = true`.

#### 3.2.2 Get run summary (state)

**GET `/api/run/{run_id}`**

Response `200 OK`:

```json
{
  "run_id": "uuid-string",
  "query": "How does RAG reduce hallucinations?",
  "llm_model": "openai/gpt-4o-mini",
  "is_running": false,
  "is_complete": true,
  "has_error": false,
  "total_elapsed": 31.2,
  "agents": [ /* AgentStatus[] */ ]
}
```

Errors:

- `404` – unknown `run_id`

#### 3.2.3 Get run context (full results)

**GET `/api/run/{run_id}/context`**

Response `200 OK`:

```json
{
  "query": "How does RAG reduce hallucinations?",
  "retrieval_metadata": { /* as produced by retriever */ },
  "retrieved_chunks": [ /* ranked corpus chunks */ ],
  "web_results": [ /* Tavily results, if any */ ],
  "claims": [ /* claims extracted */ ],
  "fact_check_results": [ /* verdicts + evidence */ ],
  "themes": [ /* themes */ ],
  "gaps": [ /* knowledge gaps */ ],
  "hypotheses": [ /* hypotheses */ ],
  "key_insights": [ /* final bullet insights */ ],
  "report_markdown": "## Executive Summary...",
  "report_metadata": { /* word counts, timestamps, etc. */ },
  "llm_usage": {
    "prompt_tokens": 12345,
    "completion_tokens": 6789
  }
}
```

Errors:

- `404` – unknown `run_id`
- `409` – run not complete yet (optional; otherwise return partial context)

---

### 3.3 Reports

#### 3.3.1 Markdown

**GET `/api/run/{run_id}/report/markdown`**

- **200 OK** → `text/markdown` body with `report_markdown`.
- `404` – unknown `run_id` or no report available.

#### 3.3.2 PDF

**GET `/api/run/{run_id}/report/pdf`**

- **200 OK** → `application/pdf` binary.
- `404` – unknown `run_id` or no report available.
- `500` – PDF generation failed (WeasyPrint / xhtml2pdf errors).

Implementation:

- Use `markdown_to_pdf_bytes(report_markdown, title=query)` from `utils/pdf_export.py`.

---

### 3.4 Document Uploads

**POST `/api/uploads`**

- Content-Type: `multipart/form-data`
- Fields: one or more `files` entries.

Response `200 OK`:

```json
{
  "success": 2,
  "failed": 0,
  "total_chunks": 145,
  "errors": [],
  "doc_count": 42
}
```

Errors:

- `400` – no files provided
- `500` – indexing failure

Implementation:

- Wrap `rag/file_indexer.index_uploaded_files`.
- Use `rag/vector_store.get_collection_count()` for `doc_count`.

---

### 3.5 Meta / Configuration

**GET `/api/meta`**

Response `200 OK`:

```json
{
  "embedding_model": "all-MiniLM-L6-v2",
  "llm_models": [
    { "id": "openai/gpt-4o-mini", "name": "GPT-4o Mini" },
    { "id": "meta-llama/llama-3.2-3b-instruct", "name": "Llama 3.2 3B" }
  ],
  "doc_count": 42,
  "tavily_available": true,
  "llm_available": true
}
```

Implementation:

- Read from `config.py` and `rag/vector_store.get_collection_count()`.
- `tavily_available` from `rag.web_search.is_available()`.
- `llm_available` from `llm.is_available()`.

---

## 4. Non-Goals (for this draft)

- No authentication/authorization.
- No pagination or filtering on large arrays (e.g. `retrieved_chunks`) – can be added later.
- No long-polling/WebSocket endpoints – polling `GET /api/run/{run_id}` is sufficient initially.

---

## 5. Next Steps

- Implement a reusable pipeline service module (`pipeline/service.py`) that the API and Streamlit can share.
- Scaffold FastAPI app (`server/api.py`) and wire the endpoints to the service functions.

