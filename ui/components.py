"""
Reusable Streamlit components for the visual design system.
Agent cards, inter-agent arrows, pipeline progress bar, and metric cards.
"""

from __future__ import annotations
import streamlit as st
from pipeline.orchestrator import AgentState, AgentStatus, PipelineState
import config


def render_agent_card(agent_status: AgentStatus, agent_config: dict):
    """
    Render a single agent card with 4 zones: Header, Status, Activity, Output.
    The card reflects one of 4 states: not_started, waiting, working, complete.
    """
    state = agent_status.state.value
    icon = agent_config.get("icon", "🤖")
    name = agent_config.get("name", agent_status.name)
    subtitle = agent_config.get("subtitle", "")

    # Status text and badge
    status_text = {
        "not_started": "Idle",
        "waiting": "⏳ Waiting...",
        "working": "⚙️ Processing...",
        "complete": "✅ Complete",
        "error": "❌ Error",
    }.get(state, "Unknown")

    # Activity text — per-agent working descriptions
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

    # Output section
    output_html = ""
    if state == "complete" and agent_status.output_summary:
        output_html = f'<div class="agent-output">{agent_status.output_summary}</div>'
    elif state == "error":
        output_html = f'<div class="agent-output" style="color:#fca5a5;">{agent_status.error_message[:120]}</div>'

    # Elapsed time
    time_str = ""
    if agent_status.elapsed_seconds > 0:
        time_str = f'<div style="font-size:0.7rem;text-align:center;margin-top:4px;opacity:0.6;">{agent_status.elapsed_seconds:.1f}s</div>'

    card_html = f"""
    <div class="agent-card {state}">
        <div class="agent-header">
            <span class="agent-icon">{icon}</span>
            <div class="agent-name">{name}</div>
            <div class="agent-subtitle">{subtitle}</div>
        </div>
        <div class="agent-status status-{state}">
            {status_text}
        </div>
        <div class="agent-activity">
            {activity}
        </div>
        {output_html}
        {time_str}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_arrow(prev_state: str, current_state: str):
    """Render an inter-agent arrow between two cards."""
    if prev_state == "complete" and current_state == "working":
        arrow_class = "arrow-flowing"
        arrow_char = "→"
    elif prev_state == "complete" and current_state == "complete":
        arrow_class = "arrow-complete"
        arrow_char = "→"
    else:
        arrow_class = "arrow-inactive"
        arrow_char = "→"

    st.markdown(
        f'<div class="arrow-container"><span class="{arrow_class}">{arrow_char}</span></div>',
        unsafe_allow_html=True,
    )


def render_pipeline_progress(pipeline_state: PipelineState):
    """Render the segmented pipeline progress bar with status text."""
    segments_html = ""
    for agent in pipeline_state.agents:
        state = agent.state.value
        segments_html += f'<div class="progress-segment {state}"></div>'

    # Status text
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

    # Estimate remaining
    if completed > 0 and completed < total:
        avg_per_agent = elapsed / completed
        remaining = avg_per_agent * (total - completed)
        remaining_str = f"~{remaining:.0f}s remaining"
    elif pipeline_state.is_complete:
        remaining_str = "Complete!"
    else:
        remaining_str = "Estimating..."

    progress_html = f"""
    <div style="margin: 16px 0;">
        <div class="pipeline-progress">
            {segments_html}
        </div>
        <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#94a3b8;margin-top:8px;">
            <span>⏱️ {elapsed:.1f}s elapsed</span>
            <span>{'🔵 Active: ' + current_name if current_name and not pipeline_state.is_complete else '✅ All agents complete' if pipeline_state.is_complete else ''}</span>
            <span>{'➡️ Next: ' + next_name if next_name and not pipeline_state.is_complete else ''}</span>
            <span>{remaining_str}</span>
        </div>
        <div style="text-align:center;font-size:0.8rem;color:#60a5fa;margin-top:4px;">
            {completed}/{total} agents complete
        </div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, icon: str = ""):
    """Render a small metric display card."""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{icon} {value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_pipeline_cards(pipeline_state: PipelineState):
    """Render the full horizontal row of 6 agent cards with arrows between them."""
    agents_config = config.AGENTS

    # Use columns: card, arrow, card, arrow, ... card
    # 6 cards + 5 arrows = 11 columns, but we use unequal widths
    cols = st.columns([3, 0.5, 3, 0.5, 3, 0.5, 3, 0.5, 3, 0.5, 3])

    for i, (agent_status, agent_cfg) in enumerate(zip(pipeline_state.agents, agents_config)):
        col_idx = i * 2  # 0, 2, 4, 6, 8, 10

        with cols[col_idx]:
            render_agent_card(agent_status, agent_cfg)

        # Arrow between cards (not after the last card)
        if i < len(pipeline_state.agents) - 1:
            arrow_col_idx = col_idx + 1
            with cols[arrow_col_idx]:
                st.markdown("<div style='height:120px;'></div>", unsafe_allow_html=True)
                prev_state = agent_status.state.value
                next_state = pipeline_state.agents[i + 1].state.value
                render_arrow(prev_state, next_state)
