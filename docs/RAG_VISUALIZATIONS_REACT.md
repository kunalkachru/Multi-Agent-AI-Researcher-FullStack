## RAG Visualizations — React Implementation

**Audience:** Frontend and full‑stack engineers working on the Sources tab or the pipeline context consumed by the React visualizations.  
**Prerequisites:** Familiarity with React, Recharts, and the high‑level pipeline/context from `ARCHITECTURE_OVERVIEW.md`.

**Terminology:** This document uses **“research run”** for a single pipeline execution, and **“context”** for the JSON returned by `GET /api/run/{run_id}/context`.

**See also:**
- [`docs/ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) — where the context comes from in the backend.
- [`docs/UI_COPY_AND_LAYOUT.md`](UI_COPY_AND_LAYOUT.md) — surrounding UI copy and layout for the Summary/Sources tabs.

This document describes how the **React** app visualizes retrieval and fact‑checking results. It is the source of truth for the current implementation and intentionally differs from the legacy Streamlit UI in a few places.

- API context source: `GET /api/run/{run_id}/context` (`RunContextDTO.data`).
- Components:
  - `frontend/src/components/EmbeddingSpaceViz.tsx`
  - `frontend/src/components/RetrievalWaterfallViz.tsx`
  - `frontend/src/components/ClaimsEvidenceViz.tsx`

The visualizations live under the **“Sources”** tab in `frontend/src/App.tsx`, which sits beside the “Summary” (report) tab.

---

### 1. Context overview

The RAG visualizations are driven entirely from the pipeline context returned by the backend. The relevant fields are:

- **Embedding Space**
  - `query_embedding: number[]`
  - `retrieved_chunks: RetrievedChunk[]`
    - `embedding: number[]`
    - `id: string`
    - `is_web: boolean`
    - `text: string`
    - `final_score: number`
    - `metadata.title?: string`
    - `metadata.url?: string` (for web results)
- **Retrieval Waterfall**
  - `retrieval_metadata.stage_counts`:
    - `queries: number`
    - `dense_candidates: number`
    - `after_rerank: number`
    - `final_chunks: number`
  - `source_distribution: Record<string, number>` — counts by source label (e.g. `arxiv`, `blog`, `web`, `government`).
- **Claims & Evidence**
  - `fact_check_results: FactCheckResult[]`
    - `claim: string`
    - `verdict: "verified" | "partially_verified" | "unverified" | "disputed" | ...`
    - `credibility_score: number`
    - `evidence_type?: string`
    - `supporting_sources?: number`
  - `credibility_summary.verdict_breakdown: Record<string, number>`
  - `evidence_chains: { claim: string; source_id: string; confidence: number; evidence_type?: string; strength?: string }[]`

Exact TypeScript definitions live in `frontend/src/api/client.ts`.

---

### 2. Embedding Space

**Component:** `EmbeddingSpaceViz`  
**Purpose:** Show where the user’s question sits relative to retrieved web results and local documents in a 2D PCA projection of embedding space.

**UI behavior**

- If there is no `query_embedding` or no chunks with embeddings:
  - Shows a placeholder: “No source map yet. Start a research run to see how your question relates to sources.”
- When data is available:
  - Runs PCA on `[query_embedding] + retrieved_chunks[].embedding` (via `ml-pca`), taking up to 2 components.
  - Projects each point to `(x, y)` and computes a `z` value used for symbol size:
    - Query: always highlighted with a large red star.
    - Web chunks: green diamonds, size increases with `final_score`.
    - Corpus chunks: blue circles; color and opacity derived from score.
  - Legend entries:
    - “Query”
    - “Web Results (Tavily)”
    - “Vector DB Docs”
  - Axes:
    - `PC1 (X% variance)` and `PC2 (Y% variance)`; also echoed in a caption under the chart.

**Interactivity**

- **Click a point**
  - Opens a snippet panel showing:
    - Type badge and label (`📌 Query`, `🌐 Web`, or `📦 Vector DB`).
    - Score (if present).
    - For web chunks: a clickable URL link (from `metadata.url`) truncated for readability.
    - A short text excerpt from the chunk.
  - Panel includes a **“Clear selection”** button to reset.
- **Jump‑to‑document dropdown**
  - Dropdown labeled “Jump to document…” with options:
    - `📌 Query`
    - `🌐 {web title}`
    - `📦 {doc label}`
  - Changing the selection focuses the same point and opens the snippet panel.
- **Document Snippets expander**
  - `<details>` block labeled “📋 Document Snippets (click to expand)” showing:
    - Top web chunks and top corpus chunks (derived from `retrieved_chunks` with embeddings).
    - For each: label, score, and a short text preview; web items include a link when `metadata.url` is present.

**Intentional differences vs Streamlit**

- React uses a PCA scatter with labeled axes and caption rather than copying Streamlit’s exact styling.
- Colors and point sizes are tuned for readability on light/dark themes but follow the same semantics (query vs web vs corpus).

---

### 3. Retrieval Waterfall

**Component:** `RetrievalWaterfallViz`  
**Purpose:** Explain how the system narrows down from all candidates to the final chunks that power the report.

**UI behavior**

- If `retrieval_metadata.stage_counts` is missing or empty:
  - Shows: “No retrieval data yet. Start a research run to see how we narrowed to top sources.”
- When data is present:
  - Builds a stage list from `stage_counts`:
    - “Queries Sent”
    - “Dense Candidates”
    - “After Re-ranking”
    - “Final Chunks”
  - Renders a vertical `BarChart` where each row is a stage and the bar length equals the count.
  - Stage bars use a small set of distinct colors for visual separation and display the numeric count as a label at the right end.

**Source distribution**

- Derived from `source_distribution` as `{ name, count }[]`.
- Rendered as a separate vertical `BarChart` titled “Source Distribution”.
- Each bar’s color is determined by a **source‑type color map** defined in the component, e.g.:
  - `arxiv` → blue
  - `blog` → orange
  - `documentation` → green
  - `web` / `web (Tavily)` → pink
  - `government` → teal
  - `unknown` → gray

**Interactivity**

- Tooltips:
  - Stage chart tooltip shows `Stage: value (X% of initial)` where “initial” is `queries` stage.
  - Source chart tooltip shows `{source_name}: {count}`.

**Intentional differences vs Streamlit**

- React uses **horizontal bar charts** instead of a funnel chart to keep dependencies small and improve responsiveness.
- Counts and percentages are shown via labels and tooltips rather than on‑bar text only.

---

### 4. Claims & Evidence

**Component:** `ClaimsEvidenceViz`  
**Purpose:** Summarize fact‑checking results and show how strong the evidence is for each claim.

**UI behavior**

- If `fact_check_results` is empty:
  - Shows: “No claims yet. Start a research run to see fact-check results.”
- When data is present:
  - Computes a donut breakdown from `credibility_summary.verdict_breakdown` and total claim count.
  - Shows a header: “Fact-check results” with a short description.

**Verdict donut**

- Uses a `PieChart` with an inner radius to create a donut:
  - Each slice corresponds to a verdict (e.g. `verified`, `partially_verified`, `unverified`, `disputed`).
  - Colors:
    - `verified` → green
    - `partially_verified` → amber
    - `unverified` → gray
    - `disputed` → red
  - Slice labels show `verdict_name percent%`.
- The center of the donut displays:
  - A large number: total count of claims.
  - A label: “Claims”.
- Legend and tooltip:
  - Legend lists verdicts with colors.
  - Tooltip shows the absolute claim count.

**Claim cards**

- Derived from `fact_check_results` (capped at a reasonable number for readability).
- Each card shows:
  - Verdict icon and name (e.g. ✅ verified, ⚠️ disputed).
  - `Score: {credibility_score} | {evidence_type} | {supporting_sources} supporting source(s)`.
  - The claim text truncated for display.
  - A horizontal bar whose width and color reflect the credibility score (green for high, amber for medium, red for low).

**Evidence Chains**

- If `evidence_chains` is non‑empty, shows a collapsible `<details>` section titled “🔗 Evidence Chains”.
- Each chain item includes:
  - The associated claim (truncated).
  - Metadata line: `Source: <source_id> | Confidence: <value> | Type: <evidence_type> | Strength: <strong/moderate/weak>`.
  - A colored left border derived from `strength` using a small color map:
    - strong → green
    - moderate → amber
    - weak → red

**Intentional differences vs Streamlit**

- Layout is optimized for the React app: verdict donut and claims list share vertical space with responsive behavior.
+- The app may show more than 10 claim cards for richer runs, while still keeping the layout scannable.

---

### 5. Adding new data to the visualizations

If you change what the pipeline returns in the run context, keep the following in mind:

- **Do not break existing fields.** The React components assume the fields listed in section 1 exist when the visualization is shown.
- **Additive changes** (e.g. new verdict types, new source types) are generally safe:
  - Verdicts not in the color map default to a neutral color.
  - Source types not in the color map default to gray.
- When introducing entirely new visualizations:
  - Add a new component under `frontend/src/components/`.
  - Wire it into the Sources tab in `App.tsx`.
  - Update this document to describe the new tab and the context fields it consumes.

