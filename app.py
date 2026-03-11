"""
Astraeus 2.0 — Multi-Agent AI Deep Researcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Streamlit Application · 6 Agents · RAG-Powered

Run with:
    streamlit run app.py
"""

import streamlit as st
import time
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from pipeline.orchestrator import (
    create_pipeline_state, run_pipeline, PipelineState, AgentState,
    AGENT_REGISTRY, _summarize_output,
)
from ui.styles import get_custom_css
from ui.components import render_pipeline_cards, render_pipeline_progress, render_metric_card
from ui.embedding_viewer import render_embedding_viewer
from ui.retrieval_waterfall import render_retrieval_waterfall
from ui.source_or_claims import render_claims_evidence

# ══════════════════════════════════════════════════════════════════════
# Page config
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# Session state initialization
# ══════════════════════════════════════════════════════════════════════
if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = create_pipeline_state()
if "pipeline_ran" not in st.session_state:
    st.session_state.pipeline_ran = False
if "corpus_loaded" not in st.session_state:
    st.session_state.corpus_loaded = False
if "selected_llm_model" not in st.session_state:
    st.session_state.selected_llm_model = config.LLM_MODEL

# ══════════════════════════════════════════════════════════════════════
# Load demo corpus on first run
# ══════════════════════════════════════════════════════════════════════
if not st.session_state.corpus_loaded:
    with st.spinner("Loading demo corpus into vector store..."):
        try:
            from data.demo_corpus import load_demo_corpus
            doc_count = load_demo_corpus()
            st.session_state.corpus_loaded = True
            st.session_state.doc_count = doc_count
        except Exception as e:
            st.error(f"Failed to load demo corpus: {e}")
            st.session_state.corpus_loaded = True  # don't retry
            st.session_state.doc_count = 0


# ══════════════════════════════════════════════════════════════════════
# TOP NAVIGATION
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="top-bar">
    <div class="app-title">🔬 {config.APP_TITLE}</div>
    <div class="app-tagline">{config.APP_TAGLINE}</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# HERO & QUERY CHIPS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-section">
    <p class="hero-text">Enter a research question and our 6-agent pipeline will retrieve, analyze, fact-check, and produce a cited report in under 2 minutes.</p>
</div>
""", unsafe_allow_html=True)

# One-click query chips — pre-fill only (no auto-launch; user can edit or Launch)
DEMO_QUERIES = [
    ("How does RAG reduce LLM hallucinations?", "RAG & hallucinations"),
    ("Compare vector databases for semantic search", "Vector DBs comparison"),
    ("What are multi-agent AI systems?", "Multi-agent AI"),
    ("Best practices for chunking in RAG", "RAG chunking"),
    ("Query expansion techniques for retrieval", "Query expansion"),
]
chip_cols = st.columns(5)
for i, (full_query, label) in enumerate(DEMO_QUERIES):
    with chip_cols[i]:
        if st.button(f"✨ {label}", key=f"chip_{i}", use_container_width=True):
            st.session_state["research_query"] = full_query
            st.rerun()

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── Query input row ───────────────────────────────────────────────────
col_input, col_btn, col_reset = st.columns([6, 1.2, 1])

with col_input:
    query = st.text_input(
        "Research Query",
        placeholder="e.g., How does RAG reduce LLM hallucinations?",
        label_visibility="collapsed",
        key="research_query",
    )

with col_btn:
    launch = st.button("🚀 Launch Research", use_container_width=True, type="primary")

with col_reset:
    reset = st.button("🔄 Reset", use_container_width=True)

if reset:
    st.session_state.pipeline_state = create_pipeline_state()
    st.session_state.pipeline_ran = False
    st.rerun()

# ── Settings & Metrics bar ────────────────────────────────────────────
with st.expander("⚙️ Settings & Metrics", expanded=False):
    from llm import is_available as llm_available
    # Model selection dropdown
    model_options = [f"{m['name']} · ${m['input_per_1m']}/{m['output_per_1m']} per 1M" for m in config.LLM_MODELS]
    model_ids = [m["id"] for m in config.LLM_MODELS]
    current_id = st.session_state.get("selected_llm_model", config.LLM_MODEL)
    try:
        default_idx = model_ids.index(current_id) if current_id in model_ids else 0
    except (ValueError, IndexError):
        default_idx = 0
    sel_idx = st.selectbox(
        "LLM Model",
        range(len(model_options)),
        format_func=lambda i: model_options[i],
        index=default_idx,
    )
    if sel_idx is not None:
        st.session_state.selected_llm_model = model_ids[sel_idx]

    s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)
    with s_col1:
        render_metric_card("Documents Indexed", str(st.session_state.get("doc_count", 0)), "📚")
    with s_col2:
        render_metric_card("Embedding Model", config.EMBEDDING_MODEL, "🧠")
    with s_col3:
        sel_name = next((m["name"] for m in config.LLM_MODELS if m["id"] == st.session_state.selected_llm_model), st.session_state.selected_llm_model)
        llm_label = f"OpenRouter · {sel_name}" if llm_available() else "Not configured"
        render_metric_card("LLM", llm_label[:22] + "…" if len(llm_label) > 22 else llm_label, "🤖")
    with s_col4:
        render_metric_card("Top-K Results", str(config.TOP_K_RESULTS), "🎯")
    with s_col5:
        render_metric_card("Query Expansions", str(config.MAX_QUERY_EXPANSIONS), "🔀")

# ── Add Documents (upload single or multiple files) ─────────────────────
with st.expander("📤 Add Documents to Knowledge Base", expanded=False):
    st.caption("Upload .txt, .pdf, or .docx files. They will be parsed, chunked, embedded, and indexed for retrieval.")
    uploaded_files = st.file_uploader(
        "Select 1 or more files",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
        key="doc_uploader",
        label_visibility="collapsed",
    )
    # Placeholder for completion message — shows above the Index Documents button
    msg_placeholder = st.empty()
    if st.session_state.get("index_completed_message"):
        with msg_placeholder.container():
            st.success(st.session_state.pop("index_completed_message"))
        if hasattr(st, "toast"):
            st.toast("Document indexing completed.", icon="✅")
    col_upload_btn, col_upload_status = st.columns([1, 3])
    with col_upload_btn:
        index_btn = st.button("Index Documents", type="secondary", disabled=not uploaded_files)
    if index_btn and uploaded_files:
        from rag.file_indexer import index_uploaded_files
        from rag.vector_store import get_collection_count

        with st.spinner("Parsing, chunking, and indexing..."):
            result = index_uploaded_files(list(uploaded_files))
        if result["total_chunks"] > 0:
            st.session_state.doc_count = get_collection_count()
            st.session_state.index_completed_message = (
                "**Document indexing completed.** "
                f"Indexed {result['success']} file(s), {result['total_chunks']} chunks added. "
                f"Total in store: {st.session_state.doc_count}"
            )
            st.rerun()  # refresh UI, clear uploader, show message above button
        if result["failed"] > 0:
            st.warning(f"{result['failed']} file(s) failed.")
            for err in result["errors"]:
                st.caption(f"• {err}")
        if result["total_chunks"] == 0 and result["success"] == 0 and result["failed"] > 0:
            st.error("No files could be indexed. Check format (.txt, .pdf, .docx) and that files contain extractable text.")
    elif index_btn and not uploaded_files:
        st.info("Select 1 or more files first.")

# ══════════════════════════════════════════════════════════════════════
# RESEARCH PIPELINE SECTION
# ══════════════════════════════════════════════════════════════════════
st.markdown("### 🔬 Research Pipeline")

pipeline_state = st.session_state.pipeline_state

# ── Live-update placeholders (replaced in-place during pipeline run) ──
progress_placeholder = st.empty()
cards_placeholder = st.empty()

# Render current state (static when idle, will be replaced during run)
with progress_placeholder.container():
    render_pipeline_progress(pipeline_state)
with cards_placeholder.container():
    render_pipeline_cards(pipeline_state)

# ══════════════════════════════════════════════════════════════════════
# LAUNCH PIPELINE — step-by-step with live UI updates
# ══════════════════════════════════════════════════════════════════════
if launch and query.strip():
    # Fresh pipeline state
    pipeline_state = create_pipeline_state()
    st.session_state.pipeline_state = pipeline_state
    st.session_state.pipeline_ran = False

    # Helper to repaint both placeholders
    def _repaint():
        with progress_placeholder.container():
            render_pipeline_progress(pipeline_state)
        with cards_placeholder.container():
            render_pipeline_cards(pipeline_state)

    # ── Initialise ────────────────────────────────────────────────────
    pipeline_state.is_running = True
    pipeline_state.pipeline_start_time = time.time()
    selected_model = st.session_state.get("selected_llm_model") or config.LLM_MODEL
    pipeline_state.context = {
        "query": query.strip(),
        "llm_model": selected_model,
        "llm_usage": {"prompt_tokens": 0, "completion_tokens": 0},
    }
    _repaint()                       # all cards grey / not-started

    # ── Walk through each agent sequentially ──────────────────────────
    import traceback as _tb

    for idx, agent_def in enumerate(AGENT_REGISTRY):
        agent = pipeline_state.agents[idx]
        pipeline_state.current_agent_index = idx
        pipeline_state.total_elapsed = round(
            time.time() - pipeline_state.pipeline_start_time, 2
        )

        # 1️⃣  WAITING  (amber / dashed border)
        agent.state = AgentState.WAITING
        agent.progress = 0.0
        _repaint()
        time.sleep(0.6)              # visible pause so user sees amber

        # 2️⃣  WORKING  (blue glow + shimmer)
        agent.state = AgentState.WORKING
        agent.start_time = time.time()
        agent.progress = 0.1
        pipeline_state.total_elapsed = round(
            time.time() - pipeline_state.pipeline_start_time, 2
        )
        _repaint()
        # Ensure blue "Working" state is visible for at least 1.2s
        # (fast agents like Critical Analysis finish in <1ms otherwise)
        min_working_visible = 1.2
        working_paint_time = time.time()

        # ── Actually run the agent ────────────────────────────────────
        try:
            pipeline_state.context = agent_def["run"](pipeline_state.context)

            # If the agent was too fast, hold the blue state so user sees it
            actual_run_time = time.time() - working_paint_time
            if actual_run_time < min_working_visible:
                # Update progress mid-way to show activity
                agent.progress = 0.5
                pipeline_state.total_elapsed = round(
                    time.time() - pipeline_state.pipeline_start_time, 2
                )
                _repaint()
                time.sleep(min_working_visible - actual_run_time)

            # 3️⃣  COMPLETE  (green flash)
            agent.end_time = time.time()
            agent.elapsed_seconds = round(agent.end_time - agent.start_time, 2)
            agent.state = AgentState.COMPLETE
            agent.progress = 1.0
            output_key = f"{agent_def['id']}_output"
            output = pipeline_state.context.get(output_key, {})
            agent.output_summary = _summarize_output(agent_def["id"], output)

            pipeline_state.total_elapsed = round(
                time.time() - pipeline_state.pipeline_start_time, 2
            )
            _repaint()
            time.sleep(0.4)          # brief green flash pause

        except Exception as e:
            agent.state = AgentState.ERROR
            agent.error_message = str(e)
            agent.end_time = time.time()
            agent.elapsed_seconds = round(agent.end_time - agent.start_time, 2)
            pipeline_state.has_error = True
            pipeline_state.is_running = False
            pipeline_state.context["pipeline_error"] = {
                "agent": agent_def["id"],
                "error": str(e),
                "traceback": _tb.format_exc(),
            }
            _repaint()
            break   # stop on error

    # ── Finalise ──────────────────────────────────────────────────────
    if not pipeline_state.has_error:
        pipeline_state.pipeline_end_time = time.time()
        pipeline_state.total_elapsed = round(
            pipeline_state.pipeline_end_time - pipeline_state.pipeline_start_time, 2
        )
        pipeline_state.is_running = False
        pipeline_state.is_complete = True
        _repaint()

    st.session_state.pipeline_state = pipeline_state
    st.session_state.pipeline_ran = True

    # Final rerun so downstream sections (report, viz) render
    st.rerun()

elif launch and not query.strip():
    st.warning("Please enter a research query before launching the pipeline.")

# ══════════════════════════════════════════════════════════════════════
# POST-PIPELINE: Results & Visualizations
# ══════════════════════════════════════════════════════════════════════
if st.session_state.pipeline_ran and pipeline_state.is_complete:
    context = pipeline_state.context

    # ── Completion celebration banner ─────────────────────────────────
    st.markdown(
        '<div class="pipeline-complete-banner">'
        '<span class="banner-icon">✅</span><span class="banner-text">Research complete — Your report is ready below</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Summary metrics ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 Pipeline Results")

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_metric_card(
            "Total Time",
            f"{pipeline_state.total_elapsed:.1f}s",
            "⏱️",
        )
    with m2:
        render_metric_card(
            "Chunks Retrieved",
            str(context.get("retrieval_metadata", {}).get("total_chunks", 0)),
            "📄",
        )
    with m3:
        render_metric_card(
            "Claims Extracted",
            str(len(context.get("claims", []))),
            "📝",
        )
    with m4:
        verified = sum(1 for r in context.get("fact_check_results", []) if r["verdict"] == "verified")
        render_metric_card("Verified Claims", str(verified), "✅")
    with m5:
        render_metric_card(
            "Themes Found",
            str(len(context.get("themes", []))),
            "💡",
        )

    # ── RAG Visualizations ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎨 RAG Visualizations")

    viz_tab1, viz_tab2, viz_tab3 = st.tabs([
        "🗺️ Embedding Space",
        "🏗️ Retrieval Waterfall",
        "✅ Claims & Evidence",
    ])

    with viz_tab1:
        render_embedding_viewer(context)

    with viz_tab2:
        render_retrieval_waterfall(context)

    with viz_tab3:
        render_claims_evidence(context)

    # ── Final Report ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📄 Research Report")

    report = context.get("report_markdown", "")
    if report:
        st.markdown(
            '<div class="report-container">',
            unsafe_allow_html=True,
        )
        st.markdown(report)
        st.markdown('</div>', unsafe_allow_html=True)

        # Download buttons (Markdown + PDF)
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="📥 Download Report (Markdown)",
                data=report,
                file_name="research_report.md",
                mime="text/markdown",
                key="download_report_md",
            )
        with dl_col2:
            try:
                from utils.pdf_export import (
                    get_pdf_export_status,
                    markdown_to_pdf_bytes,
                    sanitize_filename_for_pdf,
                )
                pdf_available, pdf_error = get_pdf_export_status()
                if pdf_available:
                    query_text = context.get("query", "")
                    pdf_bytes = markdown_to_pdf_bytes(report, title=(query_text[:80] if query_text else "Research Report"))
                    pdf_name = sanitize_filename_for_pdf(query_text) + "_report.pdf" if query_text.strip() else "research_report.pdf"
                    st.download_button(
                        label="📥 Download Report (PDF)",
                        data=pdf_bytes,
                        file_name=pdf_name,
                        mime="application/pdf",
                        key="download_report_pdf",
                    )
                else:
                    err_msg = pdf_error or "PDF libraries not available"
                    st.caption(f"PDF export unavailable. Run: pip install xhtml2pdf")
                    with st.expander("Details", expanded=False):
                        st.code(err_msg)
            except Exception as e:
                st.caption(f"PDF export error. Try restarting the app.")
                with st.expander("Details", expanded=False):
                    st.code(str(e))

        # ── LLM Usage ─────────────────────────────────────────────────
        llm_usage = context.get("llm_usage", {})
        prompt_tok = llm_usage.get("prompt_tokens", 0)
        compl_tok = llm_usage.get("completion_tokens", 0)
        total_tok = prompt_tok + compl_tok
        model_id = context.get("llm_model", config.LLM_MODEL)
        model_cfg = next((m for m in config.LLM_MODELS if m["id"] == model_id), None)
        est_cost = None
        if model_cfg and total_tok > 0:
            est_cost = (prompt_tok / 1_000_000 * model_cfg["input_per_1m"]) + (compl_tok / 1_000_000 * model_cfg["output_per_1m"])

        with st.expander("💰 LLM Usage", expanded=True):
            u1, u2, u3, u4 = st.columns(4)
            with u1:
                render_metric_card("Prompt Tokens", f"{prompt_tok:,}", "📥")
            with u2:
                render_metric_card("Completion Tokens", f"{compl_tok:,}", "📤")
            with u3:
                render_metric_card("Total Tokens", f"{total_tok:,}", "📊")
            with u4:
                cost_str = f"~${est_cost:.6f}" if est_cost is not None else "—"
                render_metric_card("Est. Cost (USD)", cost_str, "💵")
            st.caption("Pricing approximate; see [openrouter.ai/pricing](https://openrouter.ai/pricing)")
    else:
        st.info("No report generated. Try running the pipeline again.")

# ── Pipeline error display ────────────────────────────────────────────
if pipeline_state.has_error:
    st.markdown("---")
    st.error("⚠️ Pipeline encountered an error")
    error_info = pipeline_state.context.get("pipeline_error", {})
    if error_info:
        st.markdown(f"**Agent:** {error_info.get('agent', 'Unknown')}")
        st.markdown(f"**Error:** {error_info.get('error', 'Unknown error')}")
        with st.expander("Traceback"):
            st.code(error_info.get("traceback", ""), language="python")

    if st.button("🔄 Retry Pipeline"):
        st.session_state.pipeline_state = create_pipeline_state()
        st.session_state.pipeline_ran = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    f'<div style="text-align:center;color:#64748b;font-size:0.8rem;padding:16px;">'
    f'🔬 {config.APP_TITLE} | {config.APP_TAGLINE}'
    '</div>',
    unsafe_allow_html=True,
)
