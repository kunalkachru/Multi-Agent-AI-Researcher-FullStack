## UI Copy & Layout — Current React App

**Audience:** Product, design, and engineering teams editing or reviewing UI copy and layout in the React app.  
**Prerequisites:** Ability to read basic React/TSX and familiarity with the high‑level flows in `ARCHITECTURE_OVERVIEW.md`.

**Terminology:** This document uses **“research run”** consistently for a single execution of the pipeline, and **“Sources tab”** / **“Summary tab”** for the two main result views.

**See also:**
- [`docs/ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) — where the UI fits in the overall system.
- [`docs/RAG_VISUALIZATIONS_REACT.md`](RAG_VISUALIZATIONS_REACT.md) — detailed behavior of the Sources tab visualizations.
- [`docs/SIDEBAR_KEYS_AND_MODELS.md`](SIDEBAR_KEYS_AND_MODELS.md) — precise sidebar behavior for keys and models.

This document captures the **actual labels, titles, and messages** used in the React UI. Use it as the source of truth when updating copy or designing new UI that should feel consistent.

---

### 1. Header & global

- **Logo / title**
  - `🔬 Astraeus 2.0`
- **Subtitle**
  - `Multi-Agent AI Deep Researcher – 6 Agents – RAG-Powered`
- **Theme toggle**
  - Tooltip / aria: “Switch to light mode” / “Switch to dark mode”.
- **Connection status**
  - Dot + text from `/api/health`: typically `Backend connected` / error text.
  - When there is an API error, the header right area includes a title hint:
    - `Backend disconnected. Start the API server (e.g. uvicorn server.api:app --reload --port 8765) to connect.`

---

### 2. Sidebar — System status & models

#### 2.1 System status block

- Title: **System status**
- Items:
  - `Documents in index: {doc_count}`
  - `Embedding: {current_embedding_model_name}`

#### 2.2 Embedding model block

- Title: **Embedding model**
- Notice text:
  - `All models work without a token. Without one you may see rate limit or unauthenticated-request messages in server logs; adding a token avoids this.`
- Label: **Model**
- Select options: `{model.name} ({dimension}d)` for each embedding model.
- Optional HF token fields (when not configured via env):
  - Label: **Hugging Face token (optional)**
  - Placeholder: `hf_…`
  - Hint: `Add in .env as HF_TOKEN or paste here`
  - Checkbox: `Remember this token on this device`
  - Saved status: `✅ Token saved on this device.` with **Clear saved token** button.
- Primary action button:
  - `Use this model`
- Advanced test section:
  - Summary: `Advanced: test model load`
  - Button: `Test embedding`
  - Result messages:
    - Success: `✓ Model loaded successfully.`
    - Error: `Test failed.` or specific error.

#### 2.3 Language model block

- Title: **Language model**
- Status line:
  - If configured via env: `OpenRouter API key: from environment`
  - Otherwise: `API key required`
- When not configured:
  - Label: **OpenRouter API key**
  - Placeholder: `sk-…`
  - Hint: `Required if not set in .env`
  - Checkbox: `Remember this key on this device`
- Test button:
  - `Test key`
- Test messages:
  - Success: `✓ Key is valid`
  - Error: `{llmTestMessage}` (e.g. network or auth issues).
- Post‑test key status (when no env key):
  - If remembered: `✅ Key saved on this device.` with **Clear saved key** button.
  - If not remembered: `✅ Key ready to use (not saved).`
- Research model selector:
  - Label: **Research model**
  - Options: `meta.llm_models[].name`
- Model cost summary:
  - Title: **Model cost & use**
  - Line: `Input: $X/1M tokens · Output: $Y/1M tokens`
  - Optional hint: `selected.hint` from `MetaDTO`.
- Key TTL preference:
  - Label: `Keep saved keys for:`
  - Options:
    - `1 hour (shared devices)`
    - `8 hours`
    - `24 hours (default)`
    - `7 days (personal device only)`

#### 2.4 Web search (Tavily) block

- Title: **Web search (Tavily)**
- Status:
  - If available and not yet tested: `Status: Available`
  - Configured via env: `Tavily API key: from environment`
  - Otherwise: `API key required`
- When not configured:
  - Label: **Tavily API key**
  - Placeholder: `tvly-…`
  - Hint: `Required for web search. Set TAVILY_API_KEY in .env or paste here.`
  - Checkbox: `Remember this key on this device`
- Test button:
  - `Test connection`
- Test messages:
  - Success: `✓ Connection working.`
  - Error: `{tavilyTestMessage}`
- Post‑test key status (when no env key):
  - If remembered: `✅ Key saved on this device.` with **Clear saved key** button.
  - If not remembered: `✅ Key ready to use (not saved).`

#### 2.5 LLM Usage block

- Title: **LLM Usage**
- When a completed run has usage data:
  - Metrics:
    - **Prompt Tokens**
    - **Completion Tokens**
    - **Total Tokens**
    - **Est. Cost (USD)** (when cost can be calculated from model pricing).
  - Disclaimer:
    - `Pricing approximate; see openrouter.ai/pricing`
- Empty state:
  - `Run a search to see LLM usage.`

---

### 3. Main — Documents, hero, and launch

#### 3.1 Add documents section

- Section title: **Add Documents to Knowledge Base**
- File input:
  - Accepts: `.pdf, .txt, .md`
- Upload progress states:
  - Steps:
    - **Uploading files**
    - **Processing & indexing**
    - **Updating search index**
- Result message on success:
  - `X document(s) added, Y sections indexed.` with optional `Failed: Z.` suffix.
- Error message pattern:
  - `Upload failed. {message} Try again or check file format (PDF, TXT, MD).`

#### 3.2 Hero section

- Title (H1): **Start a research run**
- Subtitle:
  - `Enter your research question. We&apos;ll search your documents and the web, analyze claims, and generate a report.`

#### 3.3 Launch card

- Label for query textarea: **Research question**
- Placeholder:
  - `Enter a research question and our 6-agent pipeline will retrieve, analyze, fact-check, and produce a cited report in under 2 minutes.`
- Suggestion buttons:
  - Labels like:
    - `RAG & hallucinations`
    - `Vector DBs comparison`
    - `Multi-agent AI`
    - `RAG chunking`
    - `Query expansion`
  - Each injects a full example question into the textarea.

**Search type controls**

- Label: **Search type**
- Radio options:
  - `Both (RAG + Web)`
  - `RAG only`
  - `Web search only`

**Launch / reset actions**

- Primary button:
  - Label: `Start research`
  - Loading label: `Research in progress…`
- Secondary button:
  - Label: `Reset`
  - Icon: `↻`
  - Aria: `Reset search and run`

**Guidance messages**

- When LLM key not yet tested:
  - `Test your LLM key in the sidebar first to enable Start research.`
- When LLM tested but Tavily not tested (for web searches):
  - `Test your Tavily connection in the sidebar to use web search.`
- Launch validation error:
  - `Please enter a research question.`

---

### 4. Pipeline section & results

#### 4.1 Pipeline section

- Section title (H2): **Research pipeline**
- Meta line:
  - `Run abc12345 · 12.3s total` (run id truncated to 8 chars).
- Live badge:
  - `Updating` when polling is active.

#### 4.2 Pipeline results strip

- Title:
  - **Run summary** (implicit via `PipelineResultsStrip` layout and classes).
- Metric cards (labels may vary slightly depending on implementation):
  - **Time elapsed**
  - **Sources used**
  - **Claims found**
  - **Claims verified**
  - **Themes identified**

---

### 5. Tabs: Summary & Sources

After a run starts, the main content area shows two tabs:

- **Summary** tab
  - Contains the markdown research report.
  - Section title: **Research report**
  - Download buttons:
    - `Download as Markdown`
    - `Download as PDF`
  - Error text (when report cannot be fetched):
    - `Could not load report.` (plus any backend error details).

- **Sources** tab
  - Contains the RAG visualizations section.
  - Section title text in the layout emphasizes **How we used your sources** (see `RAG_VISUALIZATIONS_REACT.md` for per‑viz copy).

---

### 6. Errors & empty states (selected)

- **Backend disconnected**
  - Header status text reflects the health response (e.g. `Backend disconnected`), and the tooltip explains how to start the API.
- **No run yet**
  - The Summary tab shows instructions to start a research run before a report or sources are available.
- **RAG visualizations**
  - Embedding: `No source map yet. Start a research run to see how your question relates to sources.`
  - Retrieval: `No retrieval data yet. Start a research run to see how we narrowed to top sources.`
  - Claims: `No claims yet. Start a research run to see fact-check results.`

---

### 7. How to use this doc

- When changing **labels or headings**, update this file in parallel so future engineers know what is “current truth”.
- When adding a new section or card:
  - Decide on title, short description (optional), and any empty/error messages.
  - Add a short entry in the appropriate section above (Header, Sidebar, Main, Pipeline, Tabs).
- When deprecating a feature:
  - Remove its entry here once the UI code is removed or hidden behind a feature flag.

