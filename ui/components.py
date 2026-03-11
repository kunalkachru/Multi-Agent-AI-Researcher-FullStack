"""
Reusable Streamlit components for the visual design system.
Agent cards, inter-agent arrows, pipeline progress bar, and metric cards.
Neon pipeline UI with per-agent colors.
"""

from __future__ import annotations
import html as html_module
import streamlit as st
from pipeline.orchestrator import AgentState, AgentStatus, PipelineState
import config


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert #RRGGBB to (r, g, b)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _agent_card_style(agent_id: str, state: str) -> str:
    """Build inline style for card border and glow based on agent and state."""
    color = config.AGENT_COLORS.get(agent_id, "#6b7280")
    r, g, b = _hex_to_rgb(color)

    if state == "error":
        border = "2px solid #ef4444"
        shadow = "0 0 20px rgba(239, 68, 68, 0.4)"
    elif state == "not_started":
        border = f"2px solid rgba({r},{g},{b},0.3)"
        shadow = "none"
    elif state == "waiting":
        border = f"2px dashed rgba({r},{g},{b},0.6)"
        shadow = f"0 0 12px rgba({r},{g},{b},0.2)"
    elif state == "working":
        border = f"2px solid {color}"
        shadow = f"0 0 25px rgba({r},{g},{b},0.5), 0 0 50px rgba({r},{g},{b},0.2)"
    else:  # complete
        border = f"2px solid {color}"
        shadow = f"0 0 20px rgba({r},{g},{b},0.4), 0 0 40px rgba({r},{g},{b},0.2)"

    return f"border: {border}; box-shadow: {shadow};"


def render_agent_card(agent_status: AgentStatus, agent_config: dict):
    """
    Render a single agent card with neon styling.
    Layout: corner icon, center robot, name, status with dot, activity, execution time, progress bar.
    """
    state = agent_status.state.value
    agent_id = agent_config.get("id", agent_status.agent_id)
    icon = agent_config.get("icon", "🤖")
    corner_icon = agent_config.get("corner_icon", "•")
    name = agent_config.get("name", agent_status.name)
    subtitle = agent_config.get("subtitle", "")
    color = config.AGENT_COLORS.get(agent_id, "#6b7280")
    r, g, b = _hex_to_rgb(color)

    status_text = {
        "not_started": "Idle",
        "waiting": "Waiting...",
        "working": "Processing...",
        "complete": "Complete",
        "error": "Error",
    }.get(state, "Unknown")

    working_messages = {
        "coordinator": "Analyzing query & expanding search terms...",
        "retriever": "Searching vector DB & web sources...",
        "critical_analysis": "Extracting claims & detecting contradictions...",
        "fact_checker": "Cross-checking sources & verifying claims...",
        "insight_generator": "Clustering themes & identifying gaps...",
        "report_builder": "Assembling final report with citations...",
    }

    if state == "not_started":
        activity = "Waiting for pipeline to start"
    elif state == "waiting":
        activity = "Ready — waiting for previous agent"
    elif state == "working":
        activity = working_messages.get(agent_status.agent_id, "Processing...")
    elif state == "complete":
        activity = agent_status.output_summary or f"Done in {agent_status.elapsed_seconds:.1f}s"
    elif state == "error":
        activity = agent_status.error_message[:100]
    else:
        activity = ""

    output_html = ""
    if state == "complete" and agent_status.output_summary:
        safe_summary = html_module.escape(str(agent_status.output_summary)[:200])
        output_html = f'<div class="agent-output">{safe_summary}</div>'
    elif state == "error":
        safe_err = html_module.escape(str(agent_status.error_message)[:120])
        output_html = f'<div class="agent-output" style="color:#dc2626;">{safe_err}</div>'

    execution_html = ""
    if agent_status.elapsed_seconds > 0:
        execution_html = f'<div class="agent-execution">Execution: {agent_status.elapsed_seconds:.1f}s</div>'

    if state == "not_started" or state == "waiting":
        progress_pct = 0
    elif state == "working":
        progress_pct = 50
    else:
        progress_pct = 100

    card_style = _agent_card_style(agent_id, state)
    corner_style = f"background: rgba({r},{g},{b},0.2); box-shadow: 0 0 15px rgba({r},{g},{b},0.5); color: {color};"
    dot_style = f"background: {color};"
    fill_style = f"width: {progress_pct}%; background: {color};" if state != "error" else "width: 100%; background: #ef4444;"

    safe_activity = html_module.escape(activity)
    safe_name = html_module.escape(name)
    safe_subtitle = html_module.escape(subtitle)

    card_html = (
        f'<div class="agent-card {state}" data-agent-id="{agent_id}" style="{card_style}">'
        f'<div class="agent-corner-icon" style="{corner_style}">{corner_icon}</div>'
        f'<div class="agent-icon-wrap"><span class="agent-icon" style="color: {color};">{icon}</span></div>'
        f'<div class="agent-name">{safe_name}</div>'
        f'<div class="agent-subtitle">{safe_subtitle}</div>'
        f'<div class="agent-status-row"><span class="agent-status-dot" style="{dot_style}"></span><span>{status_text}</span></div>'
        f'<div class="agent-activity">{safe_activity}</div>'
        f'{output_html}'
        f'{execution_html}'
        f'<div class="agent-card-progress"><div class="agent-card-progress-fill" style="{fill_style}"></div></div>'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def render_arrow(prev_state: str, current_state: str):
    """Render an inter-agent arrow between two cards with glow."""
    if prev_state == "complete" and current_state == "working":
        arrow_class = "arrow-flowing"
    elif prev_state == "complete" and current_state == "complete":
        arrow_class = "arrow-complete"
    else:
        arrow_class = "arrow-inactive"

    st.markdown(
        f'<div class="arrow-container"><span class="{arrow_class}">→</span></div>',
        unsafe_allow_html=True,
    )


def render_pipeline_progress(pipeline_state: PipelineState):
    """Render the segmented pipeline progress bar with agent-themed colors."""
    agents_config = config.AGENTS
    segments_html = ""
    for i, agent in enumerate(pipeline_state.agents):
        state = agent.state.value
        agent_id = agents_config[i].get("id", "unknown")
        color = config.AGENT_COLORS.get(agent_id, "#6b7280")

        if state == "not_started":
            seg_class = "dim"
            seg_style = f"background: {color}; opacity: 0.3;"
        elif state == "waiting":
            seg_class = "pulse"
            seg_style = f"background: {color};"
        elif state == "working":
            seg_class = "pulse"
            seg_style = f"background: {color}; box-shadow: 0 0 8px {color};"
        elif state == "complete":
            seg_class = ""
            seg_style = f"background: {color}; box-shadow: 0 0 6px {color};"
        else:
            seg_class = ""
            seg_style = "background: #ef4444;"

        segments_html += f'<div class="pipeline-progress-segment {seg_class}" style="{seg_style}"></div>'

    current_name = ""
    next_name = ""
    idx = pipeline_state.current_agent_index
    if 0 <= idx < len(pipeline_state.agents):
        current_name = pipeline_state.agents[idx].name
    if idx + 1 < len(pipeline_state.agents):
        next_name = pipeline_state.agents[idx + 1].name

    elapsed = pipeline_state.total_elapsed
    completed = sum(1 for a in pipeline_state.agents if a.state == AgentState.COMPLETE)
    total = len(pipeline_state.agents)

    if completed > 0 and completed < total:
        avg_per_agent = elapsed / completed
        remaining = avg_per_agent * (total - completed)
        remaining_str = f"~{remaining:.0f}s remaining"
    elif pipeline_state.is_complete:
        remaining_str = "Complete!"
    else:
        remaining_str = "Estimating..."

    status_span = (
        "🔵 Active: " + current_name if current_name and not pipeline_state.is_complete
        else "✅ All agents complete" if pipeline_state.is_complete else ""
    )
    next_span = "➡️ Next: " + next_name if next_name and not pipeline_state.is_complete else ""
    progress_html = (
        f'<div style="margin: 16px 0;">'
        f'<div class="pipeline-progress">{segments_html}</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#64748b;margin-top:8px;">'
        f'<span>⏱️ {elapsed:.1f}s elapsed</span>'
        f'<span>{status_span}</span>'
        f'<span>{next_span}</span>'
        f'<span>{remaining_str}</span>'
        f'</div>'
        f'<div style="text-align:center;font-size:0.85rem;font-weight:600;color:#334155;margin-top:6px;">'
        f'{completed}/{total} agents complete'
        f'</div>'
        f'</div>'
    )
    st.markdown(progress_html, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, icon: str = ""):
    """Render a small metric display card."""
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">{icon} {value}</div><div class="metric-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def render_pipeline_cards(pipeline_state: PipelineState):
    """Render the full horizontal row of 6 agent cards with arrows between them."""
    agents_config = config.AGENTS

    cols = st.columns([3, 0.5, 3, 0.5, 3, 0.5, 3, 0.5, 3, 0.5, 3])

    for i, (agent_status, agent_cfg) in enumerate(zip(pipeline_state.agents, agents_config)):
        col_idx = i * 2

        with cols[col_idx]:
            render_agent_card(agent_status, agent_cfg)

        if i < len(pipeline_state.agents) - 1:
            arrow_col_idx = col_idx + 1
            with cols[arrow_col_idx]:
                st.markdown("<div style='height:140px;'></div>", unsafe_allow_html=True)
                prev_state = agent_status.state.value
                next_state = pipeline_state.agents[i + 1].state.value
                render_arrow(prev_state, next_state)
