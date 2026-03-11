"""
Embedding Space Viewer
━━━━━━━━━━━━━━━━━━━━━
Reduces query + retrieved doc embeddings to 2D and plots them.
Think of it like a map: the query is a red star, web results are green
diamonds, and vector DB docs are blue circles. The closer a point is
to the query, the more semantically similar it is.
Click a point or use the dropdown to view the full document snippet.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from sklearn.decomposition import PCA


def _get_selected_chunk(
    trace_info: List[dict],
    curve_number: int,
    point_index: int,
    query_text: str,
) -> Optional[dict]:
    """Resolve (curveNumber, pointIndex) to chunk data or query."""
    if curve_number < 0 or curve_number >= len(trace_info):
        return None
    info = trace_info[curve_number]
    if info["type"] == "query":
        return {"type": "query", "text": query_text}
    chunks = info.get("chunks", [])
    if point_index < 0 or point_index >= len(chunks):
        return None
    chunk = chunks[point_index]
    return {"type": info["type"], "chunk": chunk}


def _render_snippet_panel(selected: dict) -> None:
    """Render the selected document snippet panel."""
    if selected["type"] == "query":
        st.markdown(
            '<div class="embedding-snippet-panel"><div class="embedding-snippet-title">📌 Query</div>'
            '<div class="embedding-snippet-text">{}</div></div>'.format(
                selected.get("text", "")[:500].replace("<", "&lt;").replace(">", "&gt;")
            ),
            unsafe_allow_html=True,
        )
        return
    chunk = selected["chunk"]
    source_type = "🌐 Web" if selected["type"] == "web" else "📦 Vector DB"
    title = chunk.get("metadata", {}).get("title", chunk.get("id", "Document"))
    score = chunk.get("final_score", 0)
    text = chunk.get("text", "")[:500]
    url = chunk.get("metadata", {}).get("url", "")
    escaped_text = text.replace("<", "&lt;").replace(">", "&gt;")
    url_html = f'<a href="{url}" target="_blank" rel="noopener">{url[:60]}...</a>' if url else ""
    st.markdown(
        f'<div class="embedding-snippet-panel">'
        f'<div class="embedding-snippet-title">{source_type} · {title[:50]}</div>'
        f'<div class="embedding-snippet-meta">Score: {score:.3f}' + (f' | {url_html}' if url else '') + '</div>'
        f'<div class="embedding-snippet-text">{escaped_text}...</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_embedding_viewer(context: Dict[str, Any]):
    """
    Render the 2D embedding space visualization.

    Uses ALL chunks that have embeddings — both web-sourced and
    vector-DB-sourced — plotted with different markers so the user
    can see where live web results sit relative to the corpus.
    """
    query_embedding = context.get("query_embedding")
    # Use ALL retrieved chunks (web + embedding) — filter to those with embeddings
    all_chunks = context.get("retrieved_chunks", [])

    if not query_embedding or not all_chunks:
        st.info("No embedding data available yet. Run the pipeline first.")
        return

    # Separate into web vs embedding chunks (both must have embeddings)
    web_chunks = []
    emb_chunks = []
    for chunk in all_chunks:
        if chunk.get("embedding") is not None:
            if chunk.get("is_web") or chunk.get("id", "").startswith("web_"):
                web_chunks.append(chunk)
            else:
                emb_chunks.append(chunk)

    if not web_chunks and not emb_chunks:
        st.warning("No chunks with embeddings available for visualization.")
        return

    # Collect all embeddings for PCA
    all_embeddings = [query_embedding]
    all_labels = ["Query"]
    all_types = ["query"]  # "query", "web", "corpus"

    for chunk in web_chunks:
        all_embeddings.append(chunk["embedding"])
        title = chunk.get("metadata", {}).get("title", chunk.get("id", "web"))
        all_labels.append(title[:40])
        all_types.append("web")

    for chunk in emb_chunks:
        all_embeddings.append(chunk["embedding"])
        all_labels.append(chunk.get("id", "doc"))
        all_types.append("corpus")

    if len(all_embeddings) < 2:
        st.warning("Not enough data points for visualization.")
        return

    # Reduce to 2D with PCA
    embeddings_array = np.array(all_embeddings)
    n_components = min(2, embeddings_array.shape[0], embeddings_array.shape[1])
    pca = PCA(n_components=n_components)
    coords_2d = pca.fit_transform(embeddings_array)

    fig = go.Figure()
    trace_info: List[dict] = []  # Maps curveNumber -> {type, chunks or query}

    # ── Web result points (green diamonds) ────────────────────────────
    web_indices = [i for i, t in enumerate(all_types) if t == "web"]
    if web_indices:
        wx = [coords_2d[i][0] for i in web_indices]
        wy = [coords_2d[i][1] for i in web_indices] if n_components > 1 else [0] * len(web_indices)
        w_scores = [web_chunks[idx].get("final_score", 0.5) for idx, _ in enumerate(web_indices)]
        w_texts = []
        for idx, i in enumerate(web_indices):
            chunk = web_chunks[idx]
            title = chunk.get("metadata", {}).get("title", "Web")
            url = chunk.get("metadata", {}).get("url", "")
            snippet = chunk.get("text", "")[:100]
            w_texts.append(
                f"<b>🌐 {title}</b><br>"
                f"Score: {chunk.get('final_score', 0):.3f}<br>"
                f"{snippet}...<br>"
                f"<i>{url[:60]}</i>"
            )
        w_sizes = [max(10, s * 28) for s in w_scores]

        fig.add_trace(go.Scatter(
            x=wx, y=wy,
            mode='markers',
            name='Web Results (Tavily)',
            marker=dict(
                size=w_sizes,
                color='#22c55e',
                symbol='diamond',
                line=dict(width=1.5, color='white'),
                opacity=0.9,
            ),
            text=w_texts,
            hoverinfo='text',
        ))
        trace_info.append({"type": "web", "chunks": web_chunks})

    # ── Corpus / Vector DB points (blue circles) ─────────────────────
    corpus_indices = [i for i, t in enumerate(all_types) if t == "corpus"]
    if corpus_indices:
        cx = [coords_2d[i][0] for i in corpus_indices]
        cy = [coords_2d[i][1] for i in corpus_indices] if n_components > 1 else [0] * len(corpus_indices)
        c_scores = [emb_chunks[idx].get("final_score", 0.5) for idx, _ in enumerate(corpus_indices)]
        c_texts = []
        for idx, i in enumerate(corpus_indices):
            chunk = emb_chunks[idx]
            c_texts.append(
                f"<b>{chunk.get('id', 'doc')}</b><br>"
                f"Score: {chunk.get('final_score', 0):.3f}<br>"
                f"{chunk.get('text', '')[:100]}..."
            )
        c_sizes = [max(8, s * 25) for s in c_scores]

        fig.add_trace(go.Scatter(
            x=cx, y=cy,
            mode='markers',
            name='Vector DB Docs',
            marker=dict(
                size=c_sizes,
                color=c_scores,
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="Relevance", thickness=15),
                line=dict(width=1, color='white'),
                opacity=0.7,
            ),
            text=c_texts,
            hoverinfo='text',
        ))
        trace_info.append({"type": "corpus", "chunks": emb_chunks})

    # ── Query point (red star) ────────────────────────────────────────
    query_x = [coords_2d[0][0]]
    query_y = [coords_2d[0][1]] if n_components > 1 else [0]

    fig.add_trace(go.Scatter(
        x=query_x, y=query_y,
        mode='markers+text',
        name='Query',
        marker=dict(size=20, color='#ef4444', symbol='star', line=dict(width=2, color='white')),
        text=['Query'],
        textposition='top center',
        textfont=dict(color='#dc2626', size=12),
        hovertext=f"<b>Query</b><br>{context.get('query', '')[:100]}",
        hoverinfo='text',
    ))
    trace_info.append({"type": "query"})

    # Layout (light theme)
    explained_var = pca.explained_variance_ratio_
    fig.update_layout(
        title=dict(
            text="Embedding Space — Query vs Web Results vs Corpus Documents",
            font=dict(size=14, color='#1e293b'),
        ),
        xaxis=dict(
            title=f"PC1 ({explained_var[0]:.1%} variance)" if len(explained_var) > 0 else "PC1",
            showgrid=True, gridcolor='rgba(0,0,0,0.08)',
            zeroline=False,
        ),
        yaxis=dict(
            title=f"PC2 ({explained_var[1]:.1%} variance)" if len(explained_var) > 1 else "PC2",
            showgrid=True, gridcolor='rgba(0,0,0,0.08)',
            zeroline=False,
        ),
        plot_bgcolor='#ffffff',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#475569'),
        height=480,
        margin=dict(l=50, r=50, t=60, b=50),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=11),
        ),
        clickmode='event+select',
    )

    query_text = context.get("query", "")

    # Chart with selection support (Streamlit 1.28+)
    try:
        event = st.plotly_chart(
            fig,
            key="embedding_chart",
            use_container_width=True,
            on_select="rerun",
        )
    except TypeError:
        event = None

    # Build selectbox options: [Query] + web docs + corpus docs
    select_options: List[str] = ["— Click a point or choose document —", "📌 Query"]
    query_ti = next((i for i, t in enumerate(trace_info) if t["type"] == "query"), -1)
    select_to_chunk: List[Tuple[int, int]] = [(-1, -1), (query_ti, 0) if query_ti >= 0 else (-1, -1)]
    for ti, info in enumerate(trace_info):
        if info["type"] == "web":
            for pi in range(len(info["chunks"])):
                title = info["chunks"][pi].get("metadata", {}).get("title", "Web")[:40]
                select_options.append(f"🌐 {title}")
                select_to_chunk.append((ti, pi))
        elif info["type"] == "corpus":
            for pi in range(len(info["chunks"])):
                doc_id = info["chunks"][pi].get("id", "doc")[:40]
                select_options.append(f"📦 {doc_id}")
                select_to_chunk.append((ti, pi))

    # Selection key for this pipeline run (reset when context changes)
    run_key = str(hash((tuple(c.get("id", "") for c in (web_chunks + emb_chunks)[:3]), query_text[:50])))
    state_key = f"embedding_selection_{run_key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = None

    selected_chunk_data = None

    # Parse chart selection event (Streamlit: event.selection.points)
    if event is not None:
        sel = event.get("selection") if isinstance(event, dict) else getattr(event, "selection", None)
        if sel is not None:
            pts = sel.get("points", []) if isinstance(sel, dict) else getattr(sel, "points", [])
            if pts:
                pt = pts[0]
                cn = pt.get("curve_number", pt.get("curveNumber", -1))
                pi = pt.get("point_index", pt.get("pointIndex", pt.get("point_number", 0)))
                if isinstance(pi, (list, tuple)):
                    pi = pi[0] if pi else 0
                selected_chunk_data = _get_selected_chunk(trace_info, cn, pi, query_text)
                if selected_chunk_data:
                    st.session_state[state_key] = selected_chunk_data

    # Selectbox fallback
    sel_idx = st.selectbox(
        "Jump to document...",
        options=list(range(len(select_options))),
        format_func=lambda i: select_options[i],
        key=f"embedding_select_{run_key}",
    )
    if sel_idx is not None and sel_idx >= 1 and selected_chunk_data is None:
        curve, point = select_to_chunk[sel_idx]
        if curve >= 0:
            selected_chunk_data = _get_selected_chunk(trace_info, curve, point, query_text)
            if selected_chunk_data:
                st.session_state[state_key] = selected_chunk_data

    # Use session state if we just reran from selectbox (no event)
    if selected_chunk_data is None and st.session_state.get(state_key):
        selected_chunk_data = st.session_state[state_key]

    # Clear selection button
    col_btn, _ = st.columns([1, 5])
    with col_btn:
        if st.button("Clear selection", key=f"embedding_clear_{run_key}"):
            st.session_state[state_key] = None
            sel_key = f"embedding_select_{run_key}"
            if sel_key in st.session_state:
                del st.session_state[sel_key]
            st.rerun()

    # Snippet panel
    if selected_chunk_data:
        _render_snippet_panel(selected_chunk_data)
    else:
        st.caption("Click a point on the chart or choose from the dropdown to view a document snippet.")

    # ── Document Snippets panel ───────────────────────────────────────
    with st.expander("📋 Document Snippets (click to expand)"):
        # Show web results first
        if web_chunks:
            st.markdown("**🌐 Web Sources**")
            for chunk in web_chunks[:5]:
                score = chunk.get("final_score", 0)
                title = chunk.get("metadata", {}).get("title", "Web")
                url = chunk.get("metadata", {}).get("url", "")
                col1, col2 = st.columns([1, 8])
                with col1:
                    st.markdown(f"**{score:.3f}**")
                with col2:
                    link = f"[{title}]({url})" if url else title
                    st.markdown(f"🌐 {link}: {chunk.get('text', '')[:180]}...")

        if emb_chunks:
            st.markdown("**📦 Vector DB Sources**")
            for chunk in emb_chunks[:5]:
                score = chunk.get("final_score", 0)
                col1, col2 = st.columns([1, 8])
                with col1:
                    st.markdown(f"**{score:.3f}**")
                with col2:
                    st.markdown(f"📦 *{chunk.get('id', 'doc')}*: {chunk.get('text', '')[:180]}...")
