## Sidebar: Keys, Models, and Usage — Current Behavior

**Audience:** Engineers working on the sidebar UX, key handling, or `/api/meta` and related endpoints.  
**Prerequisites:** Familiarity with React state/hooks and the backend meta/test endpoints described in `ARCHITECTURE_OVERVIEW.md`.

**Terminology:** This document uses **“research run”** for a single pipeline execution, and distinguishes **env keys** (from `.env`) from **user‑provided keys** (entered in the sidebar).

**See also:**
- [`docs/ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) — how `/api/meta`, `/api/llm/test`, `/api/tavily/test`, and `/api/run` fit into the backend.
- [`docs/UI_COPY_AND_LAYOUT.md`](UI_COPY_AND_LAYOUT.md) — copy and layout for the sidebar blocks.

This document explains how the left sidebar in the **React** app works today: what information it shows, how model selection and cost work, how API keys are handled, and how “Start research” is gated.

---

### 1. Data sources

The sidebar combines:

- `GET /api/meta` (`MetaDTO`)
  - `embedding_model`, `embedding_models[]`, `embedding_hf_configured`
  - `llm_models[]` with `id`, `name`, `input_per_1m`, `output_per_1m`, `hint`
  - `doc_count`
  - `tavily_available`, `tavily_configured`
  - `llm_available`, `llm_configured`
- Local runtime / secure storage
  - Keys optionally stored via `secureLocalKeys` (OpenRouter, Tavily, HF token) with a configurable TTL.
- Test endpoints
  - `POST /api/llm/test` → verifies LLM key.
  - `POST /api/tavily/test` → verifies Tavily key.
  - `POST /api/embedding/test` and `POST /api/embedding/configure` → test and set the embedding model.

---

### 2. Layout overview

From top to bottom, the sidebar in `frontend/src/App.tsx` contains:

1. **System status**
2. **Embedding model**
3. **Language model**
4. **Web search (Tavily)**
5. **LLM Usage**

Document upload is **not** in the sidebar — it lives in the main content under “Add Documents to Knowledge Base”.

---

### 3. System status

**Block:** `System status`  
**Purpose:** Quick read on what is indexed and which embedding model is active.

- Documents count:
  - `Documents in index: {meta.doc_count}`
- Current embedding model:
  - `Embedding: {name}` — derived from `embedding_models` and `embedding_model`.

This block is read‑only and updates when meta is re‑fetched (e.g. after uploads).

---

### 4. Embedding model

**Block:** `Embedding model`  
**Purpose:** Choose which embedding model to use for indexing and retrieval, and optionally configure a Hugging Face token.

Behavior:

- Lists available models from `meta.embedding_models`:
  - Label: `Model`
  - Options: `{name} ({dimension}d)` for each model.
- Optional HF token (when `embedding_hf_configured === false`):
  - Password field labeled `Hugging Face token (optional)` with placeholder `hf_…`.
  - Hint: `Add in .env as HF_TOKEN or paste here`.
  - Checkbox: `Remember this token on this device` (controls whether the token is persisted via secure storage).
  - If a token is stored, shows `✅ Token saved on this device.` plus a “Clear saved token” button.
- **Use this model** button:
  - Calls `POST /api/embedding/configure` with `model_id` and optional `token`.
  - Refreshes meta and shows a message like `Model in use. Re-upload documents if you changed the model.`
- **Advanced: test model load** details:
  - Button: `Test embedding` (calls `POST /api/embedding/test`).
  - Shows success (`✓ Model loaded successfully.`) or error message.

---

### 5. Language model & OpenRouter key

**Block:** `Language model`  
**Purpose:** Configure the research LLM and manage the OpenRouter API key used for runs.

Behavior:

- Status line:
  - If `llm_configured === true`:
    - `OpenRouter API key: from environment`
  - Else:
    - `API key required`

**When the key is not configured in env (`llm_configured === false`):**

- Shows a password input labeled `OpenRouter API key` with placeholder `sk-…`.
- Hint: `Required if not set in .env`.
- Checkbox: `Remember this key on this device`.
  - If checked on a successful test, the key is stored via `secureLocalKeys` under a TTL (see section 7).

**Test key flow**

- Button: `Test key`
- Calls `POST /api/llm/test` with:
  - Body `{ api_key: userApiKey }` if there is no env key.
  - No body if testing the env key.
- Status state:
  - `llmTestStatus: 'idle' | 'testing' | 'success' | 'error'`
  - `llmTestMessage: string`
- UI feedback:
  - While testing: button label `Testing…`.
  - On success: message `✓ Key is valid`.
  - On error: message from `llmTestMessage`.

**Post‑test key status (when no env key)**

- If “Remember this key” is checked:
  - `✅ Key saved on this device.` with a **Clear saved key** button that removes the stored key.
- If not remembered:
  - `✅ Key ready to use (not saved).`

**Research model selection and cost**

- Label: `Research model`
- Dropdown options from `meta.llm_models` (e.g. `gpt-4o-mini`, `gpt-4.1`):
  - Each option shows `name`.
- Under the dropdown, the app shows **Model cost & use** for the selected model:
  - `Input: $input_per_1m/1M tokens · Output: $output_per_1m/1M tokens`
  - Optional hint: one line from `model.hint`, such as “Good for long reports” or “Fast and cheap”.

**Key TTL preference**

- Control labeled `Keep saved keys for:`
- Options represent different TTLs in milliseconds:
  - `1 hour (shared devices)`
  - `8 hours`
  - `24 hours (default)`
  - `7 days (personal device only)`
- When changed, the TTL is persisted via a small preference helper so future saved keys use the new duration.

---

### 6. Web search (Tavily)

**Block:** `Web search (Tavily)`  
**Purpose:** Enable or disable web search via Tavily and test connectivity.

Behavior:

- Status text:
  - When `tavily_available` and not yet successful: `Status: Available`.
  - Main line:
    - If `tavily_configured === true`:
      - `Tavily API key: from environment`
    - Else:
      - `API key required`

**When the key is not configured in env (`tavily_configured === false`):**

- Shows a password input labeled `Tavily API key` with placeholder `tvly-…`.
- Hint: `Required for web search. Set TAVILY_API_KEY in .env or paste here.`
- Checkbox: `Remember this key on this device`.

**Test connection flow**

- Button: `Test connection`
- Calls `POST /api/tavily/test` with:
  - Body `{ api_key: userTavilyKey }` if there is no env key.
  - No body if testing the env key.
- Status state:
  - `tavilyTestStatus: 'idle' | 'testing' | 'success' | 'error'`
  - `tavilyTestMessage: string`
- UI feedback:
  - While testing: button label `Testing…`.
  - On success: message `✓ Connection working.`
  - On error: message from `tavilyTestMessage`.

**Post‑test key status (when no env key)**

- If remembered:
  - `✅ Key saved on this device.` with a **Clear saved key** button.
- If not remembered:
  - `✅ Key ready to use (not saved).`

---

### 7. Key storage & TTL

The app uses a small helper in `frontend/src/utils/secureLocalKeys.ts` to store keys in browser storage with an expiration time:

- Keys that can be stored:
  - OpenRouter LLM key.
  - Tavily API key.
  - HF embedding token.
- TTL:
  - Controlled by the “Keep saved keys for” dropdown; stored preferences apply to all keys.
- Behavior:
  - On startup, the app attempts to load any non‑expired stored keys and uses them as “runtime” keys.
  - Clearing a key via the sidebar buttons removes it from storage and resets the runtime value.

Keys are never returned from the backend; they are only sent **to** the backend:

- For tests (`/api/llm/test`, `/api/tavily/test`).
- When starting a run (`POST /api/run`) if env keys are not configured.

---

### 8. Gating “Start research”

The main launch button in the hero section is gated by sidebar state:

- The **Start research** button is disabled when:
  - A run is currently launching or polling (`runLoading || isPolling`).
  - `llmTestStatus !== 'success'` (LLM key not yet validated).
  - `searchType !== 'rag_only'` and `tavilyTestStatus !== 'success'` (web search selected but Tavily not validated).

This means:

- A research run cannot start until:
  - The LLM key (env or user‑provided) is successfully tested.
  - And, for `Both (RAG + Web)` or `Web search only`, the Tavily connection is successfully tested.

When a run is started:

- If `llm_configured === false`, the app sends `openrouter_api_key` in the `POST /api/run` body, using:
  - The stored runtime key if present; otherwise the current sidebar input.
- If `tavily_configured === false` and web search is used, the app sends `tavily_api_key` similarly.
- These run‑scoped keys are used only for that run on the backend; they are not persisted server‑side.

---

### 9. Relationship to legacy plan

The earlier document `SIDEBAR_LLM_KEY_AND_MODELS_PLAN.md` described a **plan** for:

- Sidebar spacing changes.
- Model cost/benefit display.
- LLM key input and “missing key” state.
- Testing keys before enabling “Start research”.

In the current React implementation:

- Model cost/benefit, key inputs, test flows, and gating logic are all implemented as described above.
- Document upload lives in the main content section **not** in the sidebar, so any references to “Add documents to index” inside the sidebar in older docs are outdated.

When evolving the sidebar:

- Keep this document aligned with the actual JSX in `App.tsx`.
- Update or archive `SIDEBAR_LLM_KEY_AND_MODELS_PLAN.md` as needed if you introduce new behavior.

