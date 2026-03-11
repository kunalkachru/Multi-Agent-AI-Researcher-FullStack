# Plan: Sidebar UX, Model Cost/Benefit, LLM Key Input & Test

This document lays out a clear plan for four enhancements:

1. **Sidebar spacing** — Add documents section too close to dropdown above.
2. **Model cost/benefit section** — Show cost and benefit details for available models.
3. **LLM API key input** — Text box for user key when not in `.env`, with clear “missing key” state.
4. **Test LLM key before research** — Validate key (env or user-provided); enable “Start research” only after success.

---

## 1. Sidebar spacing (quick win)

**Goal:** Clear visual separation between “Research model” dropdown and “Add documents to index” so the layout doesn’t feel cramped.

**Approach:**
- In `frontend/src/styles.css`, increase spacing before the “Add documents” block.
- Options:
  - **A:** Increase `margin-top` for the `h3` that contains “Add documents to index” (e.g. use a class like `.sidebar-section--documents` and give it `margin-top: var(--space-xl)` or similar).
  - **B:** Use the existing `app-sidebar h3 + h3` rule and make the second section (Add documents) have more top margin (e.g. `.app-sidebar h3:nth-of-type(2)` or a dedicated class on the wrapper).

**Deliverable:** Add a class or selector so the “Add documents to index” section has noticeably more space above it (e.g. 24–32px) without changing other sidebar spacing.

---

## 2. Model cost/benefit section

**Goal:** Help users compare models by cost and brief benefit/use-case before choosing.

**Data:** `config.LLM_MODELS` already has `input_per_1m` and `output_per_1m` (e.g. $0.15 / $0.60 per 1M tokens). We can add short “benefit” or “best for” text per model in config or in the API response.

**Backend:**
- **GET /api/meta**  
  Extend `MetaDTO` so each model in `llm_models` includes:
  - `id`, `name` (existing)
  - `input_per_1m`, `output_per_1m` (from config; optional, for backward compatibility)
  - Optional: `hint` or `best_for` (string) — can be added to `config.LLM_MODELS` and returned here.
- Keep `llm_available` (or add `llm_configured` = key present in env) as needed for the key flow below.

**Frontend:**
- In the sidebar, under the “Research model” dropdown, add a **“Model cost & use”** (or “Cost / benefit”) section:
  - For the **currently selected** model (from dropdown), show:
    - Cost: e.g. “Input: $X.X / 1M tokens, Output: $X.X / 1M tokens”.
    - Optional one-line benefit/hint (e.g. “Good for long reports”, “Fast and cheap”).
  - Can be a small card or a few lines of text; avoid clutter.

**Deliverables:**
- API: meta returns cost (and optional hint) per model.
- Config: optional `hint` / `best_for` in `LLM_MODELS` if we want prose.
- UI: sidebar block “Model cost & use” with selected model’s cost (and optional benefit).

---

## 3. LLM API key input and “missing key” state

**Goal:** If the key is not in `.env`, show a clear place for the user to enter it and surface that the key is missing (e.g. “Not configured” or “API key required”) until they provide and validate it.

**Backend (semantics only; no key in meta response):**
- **GET /api/meta** should expose whether a key is **configured** (present in env), e.g.:
  - `llm_configured: boolean` — true if `OPENROUTER_API_KEY` is set and non-empty in env.
  - Keep or derive `llm_available` for “can we call LLM right now?” if desired (e.g. same as `llm_configured` until we have a “test” result).

**Frontend:**
- **When `llm_configured === true`:**
  - Optionally show “API key: from environment” (no input box).
  - Show “Test connection” (or “Test key”) that calls the new test endpoint (see below). No need to show a key input.
- **When `llm_configured === false`:**
  - Show a **text input** (password-type or masked) for “OpenRouter API key”.
  - Place it in the sidebar under “Language model” / “Research model”, with short hint: “Required if not set in .env”.
  - Store the key in React state only (never send to any endpoint except the test and run endpoints that need it; see security note below).
  - Show “Test key” button; on success, enable “Start research” (see section 4).

**Security:** Key is only in memory (and in request bodies to test/run). Do not log or store the key; do not include it in GET /api/meta or any other response.

**Deliverables:**
- API: meta includes `llm_configured`.
- UI: conditional key input in sidebar when not configured; clear “API key required” / “Not configured” state.

---

## 4. Test LLM key and gate “Start research”

**Goal:**  
- If key **is** in env: run a test (on load or on “Test key” click) and tell the user if the key works.  
- If key **is not** in env: require user to enter key and click “Test key”; only after a successful test enable “Start research”.  
- “Start research” is **disabled** until the key is validated (either via env test or user key test).

**Backend:**

- **POST /api/llm/test**  
  - Request body (optional): `{ "api_key": "sk-..." }`.  
  - Behavior:
    - If `api_key` is provided in body: use it for this request only (one-off test).
    - If `api_key` is not provided: use `config.OPENROUTER_API_KEY` (from env).
  - Action: call OpenRouter with a minimal request (e.g. one short completion, 1–5 tokens) to verify the key works.
  - Response:
    - Success: `{ "ok": true }` or `{ "ok": true, "message": "Key is valid" }`.
    - Failure: `{ "ok": false, "detail": "Invalid key" }` or similar (e.g. 401/403 with detail). Do not return the key.

- **LLM layer:** Add a small helper (e.g. in `llm/openrouter_client.py`) like `test_api_key(api_key: Optional[str] = None) -> Tuple[bool, str]` that:
  - Uses the given `api_key` if provided, else `config.OPENROUTER_API_KEY`.
  - Makes one minimal completion; returns `(True, "")` on success, `(False, "error message")` on failure.

**Run with user-provided key when not in env:**

- **POST /api/run**  
  - Extend request body to accept optional `openrouter_api_key: Optional[str]`.  
  - If provided, use this key for **this run only** (thread it through to the pipeline/LLM calls for that run). If not provided, use env key as today.

- **Pipeline / LLM:** The pipeline (or orchestrator) must accept an optional “run-scoped” API key and pass it to the LLM client for that run. Options:
  - **A:** Add an optional `api_key` argument to `chat_completion_with_usage` (and test helper) and use it for that call only (no global state).
  - **B:** Thread a “run context” or “options” dict through the pipeline that includes `openrouter_api_key` when set; LLM client reads from that for each call in that run.

**Frontend:**

- **State:**
  - `llmTestStatus: 'idle' | 'testing' | 'success' | 'error'`
  - `llmTestMessage: string` (e.g. error message or “Key is valid”)
  - `userApiKey: string` (user input when `llm_configured === false`)

- **Flow:**
  1. On load, fetch meta. If `llm_configured`, optionally auto-call POST /api/llm/test (no body); if success, set `llmTestStatus = 'success'` and enable “Start research”. If not configured, leave “Start research” disabled and show key input + “Test key”.
  2. “Test key” button:
     - If key from env: POST /api/llm/test with no body.
     - If key from user: POST /api/llm/test with `{ "api_key": userApiKey }`.
  3. On test success: set `llmTestStatus = 'success'`; enable “Start research”. Optionally show “Key is valid” or a checkmark.
  4. On test failure: set `llmTestStatus = 'error'`, show `llmTestMessage`; keep “Start research” disabled.
  5. “Start research” disabled when `llmTestStatus !== 'success'` (and optionally when `!query.trim()` or run in progress as today). When starting a run, if we have a user-provided key (no env key), send it in POST /api/run as `openrouter_api_key`.

**Deliverables:**
- Backend: POST /api/llm/test; optional `api_key` in body; use run-scoped key in POST /api/run and pipeline.
- Frontend: Test button, test status/message, enable “Start research” only after successful test; send `openrouter_api_key` in run request when key was user-provided.

---

## Implementation order

| Step | Task | Deps |
|------|------|------|
| 1 | Sidebar spacing (CSS) | None |
| 2 | Meta: `llm_configured` and model cost (and optional hint) | None |
| 3 | POST /api/llm/test + LLM test helper | None |
| 4 | Frontend: key input when not configured, Test key button, test status | 2, 3 |
| 5 | Frontend: enable “Start research” only when test success | 4 |
| 6 | POST /api/run accepts `openrouter_api_key`; pipeline uses run-scoped key | 3 |
| 7 | Frontend: send `openrouter_api_key` when user provided key | 5, 6 |
| 8 | Sidebar: “Model cost & use” section for selected model | 2 |

Steps 1–3 can be done in parallel; 4–5 and 6–7 can be done in parallel after 2–3; 8 after 2.

---

## Summary

- **Spacing:** One CSS change so “Add documents to index” is not cramped under the dropdown.
- **Cost/benefit:** Meta returns cost (and optional hint) per model; sidebar shows a small “Model cost & use” for the selected model.
- **Key input:** Sidebar shows key input when env key is missing; clear “not configured” state.
- **Test key:** New endpoint and flow so key (env or user) is tested before use; “Start research” enabled only after success; run request can send user key when not in env.

This keeps the UI clear, avoids sending the key except where needed, and gives a single gate (test success) before research runs.
