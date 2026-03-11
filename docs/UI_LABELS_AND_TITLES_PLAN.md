# UI Labels & Titles — Product Design Copy Plan

**Goal:** Make every label and title intuitive at a glance: user intent first, consistent verbs, minimal jargon, clear hierarchy.

---

## Principles

1. **Outcome over mechanism** — Say what the user gets or does, not the technical step (“Sources found” vs “Chunks retrieved”).
2. **Consistent verbs** — Use one verb for “start research” everywhere (e.g. “Start research” not “Launch”).
3. **Scannable sections** — Section titles answer “What is this?” in 1–3 words, then subtitle/description clarifies.
4. **Reduce jargon** — Replace or explain terms like “RAG”, “embedding”, “chunks”, “vector index” where a non-expert sees them.
5. **Errors and empty states** — One short sentence: what’s wrong and what to do next.

---

## 1. Header & global

| Location        | Current              | Suggested                 | Rationale |
|----------------|----------------------|---------------------------|-----------|
| Header right   | `API: ok` / `Offline` | `Backend connected` / `Backend disconnected` | Clearer than “API”; “connected” matches mental model. |

---

## 2. Left sidebar

| Location     | Current           | Suggested                    | Rationale |
|-------------|-------------------|------------------------------|-----------|
| Section     | **Metrics**        | **System status** or **Index & services** | “Metrics” is vague; new title reflects “what’s in the system”. |
| List item   | Docs in index      | **Documents in index**       | Slightly more readable. |
| List item   | Embedding          | **Embedding model**          | “Embedding” alone is unclear; “model” clarifies. |
| List item   | Web search         | **Web search** (keep)        | Already clear. |
| Section     | **LLM**            | **Language model**           | Spell out for non-experts; optional subtitle “(LLM)”. |
| Status line | Available / Unavailable | **Ready** / **Not configured** | “Ready” is action-oriented; “Not configured” suggests fix. |
| Label       | Model              | **Research model**           | Ties dropdown to “research” and avoids generic “Model”. |
| Section     | **Upload files**   | **Add documents to index**   | Describes outcome: documents get indexed for search. |
| Progress    | Chunking & embedding | **Processing & indexing**    | Less technical, same meaning. |
| Progress    | Updating vector index | **Updating search index**   | “Search index” is familiar; “vector” is implementation detail. |
| Result msg  | “Uploaded X file(s), Y chunks” | **X document(s) added, Y sections indexed** | “Sections indexed” is clearer than “chunks” for non-technical users. |

---

## 3. Main — Hero & launch

| Location     | Current | Suggested | Rationale |
|-------------|---------|-----------|-----------|
| H1          | Launch research | **Start a research run** or **Run research** | “Launch” is jargony; “Start”/“Run” are standard. |
| Subtitle    | Enter a question. The pipeline will retrieve… | **Enter your research question. We’ll search your documents and the web, analyze claims, and generate a report.** | User outcome in one sentence; “we’ll” is friendly and clear. |
| Label       | Query   | **Research question**       | Matches mental model of “asking a question”. |
| Placeholder | e.g. What are the main risks of… | **e.g. What are the main risks of large-scale LLM deployment?** (keep) or shorten to **e.g. What are the key risks of AI in healthcare?** | Keep or shorten; both are good examples. |
| Button      | Launch / Running… | **Start research** / **Research in progress…** | Matches H1 and section; “in progress” is clearer than “Running”. |
| Error       | Enter a research query. | **Please enter a research question.** | Softer, still clear. |

---

## 4. Pipeline section

| Location   | Current    | Suggested              | Rationale |
|------------|------------|------------------------|-----------|
| H2         | Pipeline   | **Research pipeline** or **How this run is progressing** | Clarifies it’s “this run”; optional more conversational subtitle. |
| Meta line  | Run `abc12345` · 12.3s total | **Run** `abc12345` **· 12.3 s** (keep) | Fine as-is; “Run” is clear. |
| Badge      | Live       | **Updating** or **Live** (keep) | “Updating” is more descriptive; “Live” is short and common. |

---

## 5. Pipeline results strip (metrics row)

| Location | Current           | Suggested              | Rationale |
|----------|-------------------|------------------------|-----------|
| H2       | Pipeline Results  | **This run at a glance** or **Run summary** | User-centric; “summary” is familiar. |
| Card     | Total Time        | **Time elapsed**       | Clear and standard. |
| Card     | Chunks Retrieved  | **Sources used** or **Documents used** | Outcome-focused; “chunks” is internal. |
| Card     | Claims Extracted  | **Claims found**       | Simpler. |
| Card     | Verified Claims    | **Claims verified**    | Parallel structure with “Claims found”. |
| Card     | Themes Found      | **Themes identified**  | Slightly more formal; optional to keep “Themes found”. |

---

## 6. RAG visualizations section

| Location | Current                    | Suggested                          | Rationale |
|----------|----------------------------|------------------------------------|-----------|
| H2       | RAG Visualizations         | **How we used your sources** or **Source analysis** | Removes “RAG”; focuses on “your sources” and analysis. |
| Tab      | Embedding Space            | **Query vs sources** or **Where your question meets sources** | Explains the view without “embedding”. |
| Tab      | Retrieval Waterfall        | **From query to sources** or **How we narrowed to top sources** | Describes the funnel in plain language. |
| Tab      | Claims & Evidence          | **Claims & evidence** (keep)       | Already clear. |
| Embedding chart title | Embedding Space — Query vs Web Results vs Corpus Documents | **Your question vs web results vs your documents** | “Your” reinforces ownership; “corpus” → “your documents”. |
| Waterfall title | Retrieval Waterfall — From Queries to Final Chunks | **From your queries to final sources** | “Chunks” → “sources”. |
| Claims H3 | Fact-Check Results        | **Fact-check results** (keep)      | Already good. |
| Placeholder (embedding) | No embedding data… Run the pipeline with retrieval… | **No source map yet. Start a research run to see how your question relates to sources.** | Softer; “source map” is a simple metaphor. |
| Placeholder (waterfall) | No retrieval data… Run the pipeline… | **No retrieval data yet. Start a research run to see how we narrowed to top sources.** | Same pattern. |
| Placeholder (claims)    | No fact-check data… Run the pipeline… | **No claims yet. Start a research run to see fact-check results.** | Short and actionable. |

---

## 7. Report section

| Location | Current           | Suggested                | Rationale |
|----------|-------------------|--------------------------|-----------|
| H2       | Report            | **Research report**      | Clarifies it’s the research output. |
| Button   | Download Markdown | **Download as Markdown** | “As” clarifies format. |
| Button   | Download PDF      | **Download as PDF**      | Consistent. |

---

## 8. Backend / empty state (no run)

| Location | Current | Suggested | Rationale |
|----------|---------|-----------|-----------|
| H2       | Backend | **Connection** or **Backend status** | Section is about connection, not “backend” in general. |
| Hint     | Run `uvicorn server.api:app --reload`… | **Start the API server** (e.g. `uvicorn server.api:app --reload`) **to connect.** | Action-first; command as example. |

---

## 9. Agent card states (internal but visible)

| Current   | Suggested     | Rationale |
|-----------|---------------|-----------|
| Pending   | **Queued** or **Pending** (keep) | “Queued” implies order; “Pending” is fine. |
| Waiting   | **Waiting** (keep) | Clear. |
| Working…  | **Running…** or **Working…** (keep) | Both ok. |
| Done      | **Done** (keep) | Clear. |
| Error     | **Error** (keep) | Clear. |

---

## 10. Upload error

| Current | Suggested | Rationale |
|---------|-----------|-----------|
| Upload failed: {message} | **Upload failed.** {message} **Try again or check file format (PDF, TXT, MD).** | Clear cause + next step + format hint. |

---

## Summary table (quick reference)

| Area        | Key changes |
|------------|--------------|
| **Sidebar** | “Metrics” → “System status”; “LLM” → “Language model”; “Upload files” → “Add documents to index”; “Model” → “Research model”; progress steps less technical. |
| **Hero**    | “Launch research” → “Start a research run”; “Query” → “Research question”; button “Launch” → “Start research”. |
| **Pipeline** | “Pipeline” → “Research pipeline”; results strip “Pipeline Results” → “Run summary”; metric labels outcome-focused (“Sources used”, “Claims verified”). |
| **RAG viz** | “RAG Visualizations” → “How we used your sources”; tab names explain view; placeholders “Start a research run” + what they’ll see. |
| **Report**  | “Report” → “Research report”; download buttons “Download as Markdown/PDF”. |
| **Errors & empty** | One sentence: what’s wrong + what to do; backend hint action-first. |

---

## Suggested rollout

1. **Phase 1 (high impact, low risk)**  
   Hero (H1, subtitle, label, button), Report (H2, buttons), Pipeline H2, Run summary strip titles, sidebar “Upload files” and progress steps, placeholder/error messages.

2. **Phase 2**  
   Sidebar “Metrics”/“LLM”/“Model”, RAG section and tab titles, chart titles.

3. **Phase 3**  
   Header “Backend connected”, agent state labels, any remaining microcopy.

You can approve all, subset by phase, or adjust wording per row; then we can apply the chosen changes in the codebase.
