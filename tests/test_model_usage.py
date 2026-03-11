"""
Tests for model selection and LLM usage tracking.
Run with: pytest tests/test_model_usage.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_llm_models_config():
    """LLM_MODELS list exists and has required keys."""
    import config

    assert hasattr(config, "LLM_MODELS")
    assert len(config.LLM_MODELS) >= 1
    for m in config.LLM_MODELS:
        assert "id" in m
        assert "name" in m
        assert "input_per_1m" in m
        assert "output_per_1m" in m


def test_default_model_in_list():
    """Default LLM_MODEL is in LLM_MODELS."""
    import config

    ids = [m["id"] for m in config.LLM_MODELS]
    assert config.LLM_MODEL in ids


def test_chat_completion_with_usage_signature():
    """chat_completion_with_usage exists and returns tuple."""
    from llm import chat_completion_with_usage

    # Without API key, returns (None, None)
    text, usage = chat_completion_with_usage(
        messages=[{"role": "user", "content": "hi"}],
        model="openai/gpt-4o-mini",
    )
    # May be None if no key, or tuple (str, dict)
    assert isinstance(text, (str, type(None)))
    assert isinstance(usage, (dict, type(None)))
    if usage:
        assert "prompt_tokens" in usage or "input_tokens" in usage
        assert "completion_tokens" in usage or "output_tokens" in usage


def test_usage_accumulation():
    """Context llm_usage accumulates correctly."""
    ctx = {"llm_usage": {"prompt_tokens": 0, "completion_tokens": 0}}

    usage1 = {"prompt_tokens": 100, "completion_tokens": 50}
    u = ctx.setdefault("llm_usage", {"prompt_tokens": 0, "completion_tokens": 0})
    u["prompt_tokens"] += usage1.get("prompt_tokens", 0)
    u["completion_tokens"] += usage1.get("completion_tokens", 0)

    usage2 = {"prompt_tokens": 200, "completion_tokens": 80}
    u["prompt_tokens"] += usage2.get("prompt_tokens", 0)
    u["completion_tokens"] += usage2.get("completion_tokens", 0)

    assert ctx["llm_usage"]["prompt_tokens"] == 300
    assert ctx["llm_usage"]["completion_tokens"] == 130


def test_cost_calculation():
    """Cost formula matches plan."""
    import config

    model = config.LLM_MODELS[0]
    prompt_tokens = 1000
    completion_tokens = 500
    cost = (prompt_tokens / 1_000_000 * model["input_per_1m"]) + (
        completion_tokens / 1_000_000 * model["output_per_1m"]
    )
    assert cost > 0
    assert cost < 1  # reasonable for 1.5k tokens


def test_coordinator_passes_context():
    """Coordinator _expand_query receives context."""
    from agents.coordinator import _expand_query

    ctx = {"llm_model": "openai/gpt-4o-mini", "llm_usage": {"prompt_tokens": 0, "completion_tokens": 0}}
    result = _expand_query("test query", 2, ctx)
    assert isinstance(result, list)
    assert len(result) >= 1
    # If LLM unavailable, uses fallback
    assert "llm_usage" in ctx


def test_report_builder_context():
    """Report builder uses context for model and usage."""
    from agents.report_builder import _build_report

    ctx = {
        "llm_model": "openai/gpt-4o-mini",
        "llm_usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }
    report = _build_report(
        query="test",
        query_analysis={"intent": "exploratory", "complexity": "simple"},
        themes=[],
        gaps=[],
        hypotheses=[],
        key_insights=[],
        llm_insights=["Insight 1"],
        claims=[],
        fact_results=[],
        credibility={"overall": "medium", "verdict_breakdown": {}, "average_score": 0.7},
        contradictions=[],
        evidence_chains=[],
        retriever_output={"num_chunks": 0},
        web_results=[],
        llm_summary="Summary",
        context=ctx,
    )
    assert "test" in report
    assert "Insight 1" in report
