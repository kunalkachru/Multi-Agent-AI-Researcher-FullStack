## Astraeus 2.0 — Architecture Overview

**Audience:** Full‑stack engineers working on the backend pipeline, RAG stack, and React frontend.  
**Prerequisites:** Comfortable with Python (FastAPI), basic React, and high‑level RAG concepts.

**Terminology:** This document uses **“research run”** to mean a single end‑to‑end execution of the 6‑agent pipeline.

**See also:**
- [`docs/DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) — how to run Astraeus locally and on a server.
- [`docs/RAG_VISUALIZATIONS_REACT.md`](RAG_VISUALIZATIONS_REACT.md) — how the Sources tab visualizations consume pipeline context.
- [`docs/SIDEBAR_KEYS_AND_MODELS.md`](SIDEBAR_KEYS_AND_MODELS.md) — how `/api/meta` and key testing interact with the UI.

### 1. High‑level system

- **Backend API** (`server/`, `pipeline/`, `agents/`, `rag/`, `llm/`): FastAPI app that orchestrates a 6‑agent research pipeline, performs RAG over local documents and web results, and exposes run status plus final report/context.
- **Frontend** (`frontend/`): React SPA (Vite) that lets users upload documents, configure models/keys, launch research runs, and explore results (summary report + RAG visualizations).
- **Vector store & files** (`data/chroma_db/`): ChromaDB collection for indexed documents and metadata.
- **Legacy UI** (`ui/`, `app.py`): Streamlit UI kept for reference; the React app is the primary interface.

### 2. Backend structure

- **`server/api.py`**
  - Creates the FastAPI app and configures CORS for local dev and Docker.
  - Exposes all external endpoints (health, meta, run, context, uploads, report download, key tests, embedding configure/test).
  - Translates internal pipeline state into DTOs the frontend can consume.

- **`pipeline/`**
  - `pipeline/orchestrator.py`:
    - Defines `PipelineState` (per‑run state: agents, status flags, context dict).
    - Holds the ordered list of agents and executes them sequentially in a background thread.
  - `pipeline/service.py`:
    - `start_pipeline_run(...)`: creates a run ID, spins up a background worker, and seeds the initial context (query, search_type, keys, etc.).
    - `get_pipeline_state(run_id)`: returns `PipelineState` for summaries.
    - `get_pipeline_context(run_id)`: returns the raw `context` dict used by the React app (RAG viz + report).

- **`agents/`**
  - Each agent is a Python module implementing one stage of the research workflow, reading and writing to the shared `context`:
    - `coordinator`: sets up the research intent and orchestrates high‑level steps.
    - `retriever`: runs document + web retrieval (RAG) using `rag/` and Tavily.
    - `critical_analysis`: analyzes retrieved content and structures claims.
    - `fact_checker`: verifies claims, producing `fact_check_results` and `credibility_summary`.
    - `insight_generator`: synthesizes insights/themes from the evidence.
    - `report_builder`: turns the context into markdown and metadata used for report export.

- **`rag/`**
  - `rag/document_parser.py`: normalizes and parses PDFs / text / markdown into raw text.
  - `rag/chunking.py`: splits text into overlapping chunks suitable for embedding.
  - `rag/embeddings.py`: computes vector embeddings for chunks.
  - `rag/vector_store.py`: wraps ChromaDB operations (index documents, query by vector, get collection count).
  - `rag/file_indexer.py`: end‑to‑end “upload → parse → chunk → embed → index” pipeline.
  - `rag/retrieval.py`: retrieves top‑k chunks for a query (local docs + web as needed).
  - `rag/web_search.py`: uses Tavily to fetch and cache web results; provides `is_available` and `test_tavily_key`.

- **`llm/`**
  - `llm/openrouter_client.py`: shared OpenRouter client for chat completion.
  - Supports:
    - Global key from `.env` (`OPENROUTER_API_KEY`).
    - Per‑run override key passed from the frontend.
    - `test_api_key(...)` used by `/api/llm/test` to validate a key before running.

- **`config.py`**
  - Central configuration for:
    - Available embedding models and default embedding model.
    - Available LLM models (`LLM_MODELS`) with `input_per_1m`, `output_per_1m`, and `hint` (used for sidebar “Model cost & use”).
    - Tavily API key, HF token, and other operational settings.

### 3. Core API endpoints

All routes live in [`server/api.py`](server/api.py).

- **Health**
  - `GET /api/health` → `{ "status": "ok" }`

- **Meta / configuration**
  - `GET /api/meta` → `MetaDTO`
    - `embedding_model`: ID of the current embedding model.
    - `embedding_models[]`: available models with `id`, `name`, `dimension`, `hint`.
    - `embedding_hf_configured`: whether a Hugging Face token is configured.
    - `llm_models[]`: available LLMs with `id`, `name`, `input_per_1m`, `output_per_1m`, `hint`.
    - `doc_count`: number of indexed documents (`get_collection_count()`).
    - `tavily_available` / `tavily_configured`.
    - `llm_available` / `llm_configured`.

- **Run lifecycle**
  - `POST /api/run` → `{ "run_id": string }`
    - Body: `RunRequest { query, llm_model?, openrouter_api_key?, tavily_api_key?, search_type? }`.
    - Validates non‑empty query and acceptable `search_type` (`both`, `rag_only`, `web_only`).
    - For `web_only`, enforces that a Tavily key is present (env or request).
    - Calls `start_pipeline_run(...)` and returns the new `run_id`.
  - `GET /api/run/{run_id}` → `PipelineStateSummary`
    - High‑level run status: `is_running`, `is_complete`, `has_error`, `total_elapsed`.
    - Per‑agent status via `AgentStatusDTO` (progress percentage, elapsed, brief output summary).
  - `GET /api/run/{run_id}/context` → `RunContextDTO`
    - `data: dict[str, Any]` – the full context dict used by React for:
      - RAG visualizations (embedding space, retrieval waterfall, claims & evidence).
      - The final report, fact‑check results, evidence chains, usage metrics, etc.
  - `GET /api/run/{run_id}/report/markdown` → `text/markdown`
  - `GET /api/run/{run_id}/report/pdf` → `application/pdf`

- **Uploads / indexing**
  - `POST /api/uploads` → `UploadResult`
    - Accepts multiple `UploadFile` items.
    - Uses `rag.file_indexer.index_uploaded_files()` to:
      - Parse files.
      - Chunk, embed, and add to vector store.
    - Returns counts of `success`, `failed`, `total_chunks`, `errors[]`, and new `doc_count`.

- **Key tests & embedding configuration**
  - `POST /api/llm/test` → `LLMTestResponse { ok, detail }`
    - Optional body: `{ api_key?: string }`; if omitted and `llm_configured` is true, tests the env key.
  - `POST /api/tavily/test` → `TavilyTestResponse { ok, detail }`
    - Optional body: `{ api_key?: string }`; similar semantics for Tavily.
  - `POST /api/embedding/test` → `EmbeddingTestResponse { ok, detail }`
  - `POST /api/embedding/configure` → `204 No Content`
    - Selects an embedding model (and optional HF token), persists config, and may require re‑uploading docs.

### 4. Frontend structure

The main React app lives under [`frontend/src`](frontend/src).

- **`frontend/src/App.tsx`**
  - Overall layout:
    - Header with branding, dark/light toggle, and backend connection status.
    - Resizable left sidebar for system status, model selection, and key management.
    - Main content area with:
      - “Start a research run” hero and query form.
      - Run pipeline section and agent progress cards.
      - “Summary” tab (markdown report + download buttons).
      - “Sources” tab (RAG visualizations).
      - “Add Documents to Knowledge Base” upload section.
  - State and effects:
    - Loads `meta` on startup (`getMeta()`).
    - Manages theme, sidebar open/width, current run (`runId`, `runState`), and run context.
    - Uses `usePipelineRun(runId)` to poll `/api/run/{run_id}` until complete, then fetches context and report markdown.
    - Handles file uploads and refreshes `doc_count` after upload completes.

- **RAG visualization components** (`frontend/src/components/`) — documented in more detail in `RAG_VISUALIZATIONS_REACT.md`:
  - `EmbeddingSpaceViz.tsx`: PCA scatter showing query, web results, and corpus documents; jump‑to‑document dropdown; snippet panel; document snippets list.
  - `RetrievalWaterfallViz.tsx`: Vertical bar charts showing retrieval stages and per‑source distribution.
  - `ClaimsEvidenceViz.tsx`: Donut chart of fact‑check verdicts, list of claim cards, and evidence chains.

- **API client & hooks**
  - `frontend/src/api/client.ts`: Typed client for the backend endpoints (`RunContextDTO`, `MetaDTO`, `UploadResult`, etc.).
  - `frontend/src/api/usePipelineRun.ts`: React hook that polls `/api/run/{run_id}` and exposes live run state to `App.tsx`.

- **Sidebar keys & models**
  - Implemented within `App.tsx`:
    - Embedding model selection and test/configure actions.
    - LLM key input when env key is missing, “Test key” button, and “Model cost & use” block.
    - Tavily key input and “Test connection” button.
    - Gating logic so “Start research” is only enabled when the LLM key is tested successfully (and Tavily when needed).
  - Uses `frontend/src/utils/secureLocalKeys.ts` to optionally persist keys locally with a TTL (OpenRouter, Tavily, HF embedding).

### 5. Key flows

#### 5.1 Start a research run

1. User enters a **research question** in the main form and chooses `search_type` (e.g. both / RAG only / web only) and research model.
2. Sidebar ensures the required keys are configured and tested (LLM and Tavily if needed).
3. Frontend calls `POST /api/run` with:
   - `query`, optional `llm_model`, and any per‑run API keys (OpenRouter, Tavily) if not configured in env.
4. Backend:
   - Creates a run via `start_pipeline_run(...)` and returns `run_id`.
   - Executes agents in sequence, updating `PipelineState` and the shared `context`.
5. Frontend:
   - Uses `usePipelineRun(runId)` to poll `GET /api/run/{run_id}` for `PipelineStateSummary`.
   - Once `is_complete` is true (and `has_error` is false), calls `GET /api/run/{run_id}/context` and populates:
     - Summary tab (report markdown via context or `GET /report/markdown`).
     - Sources tab (RAG visualizations fed from the same context).

#### 5.2 Upload and index documents

1. User uses the **“Add Documents to Knowledge Base”** section in the main content to select files (PDF, TXT, MD).
2. Frontend calls `POST /api/uploads` with the selected files.
3. Backend:
   - Parses files, chunks content, computes embeddings, and indexes them into Chroma via `rag.file_indexer`.
   - Returns `UploadResult` with counts and new `doc_count`.
4. Frontend:
   - Shows a 3‑step progress indicator (“Uploading files”, “Processing & indexing”, “Updating search index”).
   - Displays a final message like `X document(s) added, Y sections indexed. Failed: Z.` if any failures.
   - Refreshes `meta` to show the updated `Documents in index` count in the sidebar.

### 6. Related documentation

- **RAG visualizations:** See `RAG_VISUALIZATIONS_REACT.md` for detailed descriptions of each visualization and the context fields they consume.
- **UI copy & layout:** See `UI_COPY_AND_LAYOUT.md` for canonical labels, headings, and empty/error state copy.
- **Sidebar keys & models:** See `SIDEBAR_KEYS_AND_MODELS.md` for sidebar behavior, model metadata, and key validation flows.
- **Deployment:** See `DEPLOYMENT_GUIDE.md` for local Docker/dev and cloud deployment instructions.

