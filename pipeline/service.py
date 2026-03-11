"""
Pipeline Service
━━━━━━━━━━━━━━━━
Shared utilities to run the 6-agent pipeline outside of Streamlit.

This module encapsulates the step-by-step orchestration logic currently
used in app.py so that other entrypoints (e.g. FastAPI, tests) can launch
and inspect pipeline runs without depending on Streamlit.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Dict, Any, Optional

import config
from pipeline.orchestrator import (
    create_pipeline_state,
    PipelineState,
    AgentState,
    AGENT_REGISTRY,
    _summarize_output,
)


# In-memory store of pipeline runs. We keep the live PipelineState object
# so HTTP clients can poll and see agent-by-agent progress while the
# background thread is still running.
_RUNS: Dict[str, PipelineState] = {}


def _run_pipeline_background(run_id: str, pipeline_state: PipelineState) -> None:
    """
    Internal worker that executes the pipeline in a background thread.

    It mutates the shared PipelineState instance stored in _RUNS so that
    HTTP clients can poll for intermediate agent states.
    """
    import traceback as _tb

    for idx, agent_def in enumerate(AGENT_REGISTRY):
        agent = pipeline_state.agents[idx]
        pipeline_state.current_agent_index = idx
        if pipeline_state.pipeline_start_time:
            pipeline_state.total_elapsed = round(
                time.time() - pipeline_state.pipeline_start_time, 2
            )

        # WAITING
        agent.state = AgentState.WAITING
        agent.progress = 0.0

        # WORKING
        agent.state = AgentState.WORKING
        agent.start_time = time.time()
        agent.progress = 0.1
        if pipeline_state.pipeline_start_time:
            pipeline_state.total_elapsed = round(
                time.time() - pipeline_state.pipeline_start_time, 2
            )

        try:
            pipeline_state.context = agent_def["run"](pipeline_state.context)

            # COMPLETE
            agent.end_time = time.time()
            agent.elapsed_seconds = round(agent.end_time - agent.start_time, 2)
            agent.state = AgentState.COMPLETE
            agent.progress = 1.0
            output_key = f"{agent_def['id']}_output"
            output = pipeline_state.context.get(output_key, {})
            agent.output_summary = _summarize_output(agent_def["id"], output)

            if pipeline_state.pipeline_start_time:
                pipeline_state.total_elapsed = round(
                    time.time() - pipeline_state.pipeline_start_time, 2
                )
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
            break

    if not pipeline_state.has_error and pipeline_state.pipeline_start_time:
        pipeline_state.pipeline_end_time = time.time()
        pipeline_state.total_elapsed = round(
            pipeline_state.pipeline_end_time - pipeline_state.pipeline_start_time, 2
        )
        pipeline_state.is_running = False
        pipeline_state.is_complete = True

    # Ensure final state is visible even if something replaced the entry.
    _RUNS[run_id] = pipeline_state


def start_pipeline_run(
    query: str,
    llm_model: Optional[str] = None,
    openrouter_api_key: Optional[str] = None,
    tavily_api_key: Optional[str] = None,
    search_type: Optional[str] = "both",
) -> str:
    """
    Start the 6-agent pipeline in a background thread and return a run_id.

    The latest PipelineState for that run can be fetched via
    get_pipeline_state/get_pipeline_context while it is still running.
    If openrouter_api_key or tavily_api_key is provided, it is used for this run only (not stored in env).
    search_type: "both" (default), "rag_only", or "web_only" — controls retriever behavior.
    """
    run_id = str(uuid.uuid4())

    pipeline_state = create_pipeline_state()
    pipeline_state.is_running = True
    pipeline_state.is_complete = False
    pipeline_state.has_error = False
    pipeline_state.pipeline_start_time = time.time()

    raw = (search_type or "both").strip().lower()
    if raw not in ("both", "rag_only", "web_only"):
        raw = "both"
    pipeline_search_type = raw

    selected_model = llm_model or config.LLM_MODEL
    pipeline_state.context = {
        "query": query.strip(),
        "llm_model": selected_model,
        "llm_usage": {"prompt_tokens": 0, "completion_tokens": 0},
        "search_type": pipeline_search_type,
    }
    if openrouter_api_key and openrouter_api_key.strip():
        pipeline_state.context["openrouter_api_key"] = openrouter_api_key.strip()
    if tavily_api_key and tavily_api_key.strip():
        pipeline_state.context["tavily_api_key"] = tavily_api_key.strip()

    _RUNS[run_id] = pipeline_state

    worker = threading.Thread(
        target=_run_pipeline_background,
        args=(run_id, pipeline_state),
        name=f"astraeus-2-pipeline-{run_id}",
        daemon=True,
    )
    worker.start()

    return run_id


def get_pipeline_state(run_id: str) -> Optional[PipelineState]:
    """
    Return the stored PipelineState for a completed run, or None if unknown.
    """
    return _RUNS.get(run_id)


def get_pipeline_context(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Return the context dict for a completed run, or None if unknown.
    """
    state = _RUNS.get(run_id)
    if not state:
        return None
    return state.context

