"""
Report Builder Agent
━━━━━━━━━━━━━━━━━━━
Sixth and final agent. Like the Final Approval desk at a bank — assembles
everything into a polished report with citations. Uses the LLM (OpenRouter)
to generate a proper Executive Summary and Key Insights that are actually
about the user's research topic, not about the training data.

Responsibilities:
  • Use LLM to synthesize findings into a real research summary
  • Assemble final report from all agent outputs
  • Include citations linking claims to source chunks
  • Output formatted markdown report
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import config
from llm import chat_completion_with_usage


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input context keys:
      - query, query_analysis, coordinator_output, retriever_output
      - claims, contradictions, evidence_chains
      - fact_check_results, credibility_summary
      - themes, gaps, hypotheses, key_insights
      - web_results: List[dict]   (from Tavily web search)
      - retrieved_chunks: List[dict]

    Output added to context:
      - report_markdown: str
      - report_metadata: dict
    """
    query = context.get("query", "")
    query_analysis = context.get("query_analysis", {})
    themes = context.get("themes", [])
    gaps = context.get("gaps", [])
    hypotheses = context.get("hypotheses", [])
    key_insights = context.get("key_insights", [])
    claims = context.get("claims", [])
    fact_results = context.get("fact_check_results", [])
    credibility = context.get("credibility_summary", {})
    contradictions = context.get("contradictions", [])
    evidence_chains = context.get("evidence_chains", [])
    retriever_output = context.get("retriever_output", {})
    web_results = context.get("web_results", [])
    all_chunks = context.get("retrieved_chunks", [])

    # ── Use LLM to generate content about the actual research topic ───
    llm_summary = _generate_llm_summary(query, all_chunks, web_results, context)
    llm_insights = _generate_llm_insights(query, all_chunks, web_results, claims, context)

    # ── Build report ──────────────────────────────────────────────────
    report = _build_report(
        query=query,
        query_analysis=query_analysis,
        themes=themes,
        gaps=gaps,
        hypotheses=hypotheses,
        key_insights=key_insights,
        llm_insights=llm_insights,
        claims=claims,
        fact_results=fact_results,
        credibility=credibility,
        contradictions=contradictions,
        evidence_chains=evidence_chains,
        retriever_output=retriever_output,
        web_results=web_results,
        llm_summary=llm_summary,
        context=context,
    )

    report_metadata = {
        "generated_at": datetime.now().isoformat(),
        "query": query,
        "total_claims": len(claims),
        "total_themes": len(themes),
        "total_gaps": len(gaps),
        "verified_claims": sum(1 for r in fact_results if r["verdict"] == "verified"),
        "web_sources": len(web_results),
        "word_count": len(report.split()),
    }

    context["report_markdown"] = report
    context["report_metadata"] = report_metadata
    context["report_builder_output"] = {
        "report_length": len(report),
        "word_count": report_metadata["word_count"],
        "sections": ["Executive Summary", "Key Insights", "Thematic Analysis",
                     "Evidence Assessment", "Knowledge Gaps", "Hypotheses",
                     "Detailed Findings", "Citations — Embedding Sources",
                     "Citations — Web Sources"],
    }

    return context


# ══════════════════════════════════════════════════════════════════════
# LLM-powered content generation
# ══════════════════════════════════════════════════════════════════════

def _gather_source_text(chunks: List[dict], web_results: List[dict], max_chars: int = 4000) -> str:
    """Collect the best source material for the LLM to work with."""
    parts = []
    char_count = 0

    # Web results first (more relevant for live topics)
    for w in web_results:
        title = w.get("title", "")
        snippet = w.get("snippet", "")
        url = w.get("url", "")
        block = f"[Web] {title}\nURL: {url}\n{snippet}\n"
        if char_count + len(block) > max_chars:
            break
        parts.append(block)
        char_count += len(block)

    # Then embedding chunks
    for c in chunks:
        text = c.get("text", "")
        src = c.get("metadata", {}).get("source", "")
        block = f"[{src}] {text}\n"
        if char_count + len(block) > max_chars:
            break
        parts.append(block)
        char_count += len(block)

    return "\n".join(parts)


def _generate_llm_summary(query: str, chunks: List[dict], web_results: List[dict], context: Dict[str, Any]) -> str:
    """Use LLM to generate an Executive Summary about the actual research topic."""
    # Prefer a per-run key from context, then fall back to env-based key.
    effective_key = (context.get("openrouter_api_key") or config.OPENROUTER_API_KEY or "").strip()
    if not effective_key:
        return ""

    source_text = _gather_source_text(chunks, web_results)
    if not source_text.strip():
        return ""

    prompt = f"""You are a senior research analyst. Based on the following source material, write a clear, structured Executive Summary answering this research query:

**Research Query:** {query}

**Source Material:**
{source_text}

Write the Executive Summary in **well-structured markdown**, following this shape:

1. 2–3 short paragraphs that:
   - Directly answer the research question
   - Synthesize the most important findings
   - Note any important caveats or limitations

2. A short bulleted list titled **"Key Points"** with 3–5 bullets. Each bullet should be:
   - One sentence
   - Decision-focused
   - Grounded in the sources (not speculation)

Style guidelines:
- Be concise but information-dense.
- Do NOT mention RAG, LLMs, embeddings, or vector databases unless the query is explicitly about those topics.
- Do NOT describe your own process; just present the conclusions.
- Keep everything focused on the research topic, not on AI or tooling."""

    model = context.get("llm_model", config.LLM_MODEL)
    reply, usage = chat_completion_with_usage(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.3,
        model=model,
        api_key=effective_key,
    )
    if usage:
        u = context.setdefault("llm_usage", {"prompt_tokens": 0, "completion_tokens": 0})
        u["prompt_tokens"] += usage.get("prompt_tokens", 0)
        u["completion_tokens"] += usage.get("completion_tokens", 0)
    return reply or ""


def _generate_llm_insights(
    query: str, chunks: List[dict], web_results: List[dict], claims: List[dict], context: Dict[str, Any]
) -> List[str]:
    """Use LLM to generate Key Insights about the actual research topic."""
    effective_key = (context.get("openrouter_api_key") or config.OPENROUTER_API_KEY or "").strip()
    if not effective_key:
        return []

    source_text = _gather_source_text(chunks, web_results, max_chars=3000)
    if not source_text.strip():
        return []

    # Include top claims for context
    claims_text = ""
    for c in claims[:8]:
        claims_text += f"- {c['claim'][:150]}\n"

    prompt = f"""You are writing board-level insights about this research topic: "{query}".

Use the following source material and extracted claims to derive the **5 most important, decision-ready insights**:

**Source Material:**
{source_text}

**Extracted Claims:**
{claims_text}

Output format (very strict):
- Exactly 5 lines
- Each line is ONE complete sentence insight
- No numbering, no bullets, no labels, no markdown headings
- Each insight should:
  - Stand alone (can be read out of context)
  - Be specific and actionable
  - Refer implicitly to the topic "{query}" (without generic phrases like "this topic")

Do not talk about RAG, LLMs, or embeddings; focus only on the subject matter."""

    model = context.get("llm_model", config.LLM_MODEL)
    reply, usage = chat_completion_with_usage(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.3,
        model=model,
        api_key=effective_key,
    )
    if usage:
        u = context.setdefault("llm_usage", {"prompt_tokens": 0, "completion_tokens": 0})
        u["prompt_tokens"] += usage.get("prompt_tokens", 0)
        u["completion_tokens"] += usage.get("completion_tokens", 0)
    if not reply:
        return []

    lines = [line.strip() for line in reply.strip().split("\n") if line.strip()]
    # Strip any numbering/bullets
    import re
    insights = []
    for line in lines:
        line = re.sub(r"^[\d]+[\.\)]\s*", "", line).strip()
        line = re.sub(r"^[-*•]\s*", "", line).strip()
        if line:
            insights.append(line)
    return insights[:5]


def _generate_llm_evidence_assessment(
    query: str, claims: List[dict], fact_results: List[dict], web_results: List[dict], context: Dict[str, Any]
) -> str:
    """Use LLM to summarize evidence quality for the research topic."""
    effective_key = (context.get("openrouter_api_key") or config.OPENROUTER_API_KEY or "").strip()
    if not effective_key or not claims:
        return ""

    verified = sum(1 for r in fact_results if r.get("verdict") in ("verified", "partially_verified"))
    unverified = sum(1 for r in fact_results if r.get("verdict") in ("unverified", "disputed"))
    web_count = len(web_results)

    claims_text = "\n".join(f"- {c['claim'][:120]}" for c in claims[:8])

    prompt = f"""You are assessing the strength of evidence for the research topic: "{query}".

Use these high-level stats and top claims to write a short, structured evaluation:

Stats: {len(claims)} claims extracted, {verified} verified or partially verified, {unverified} unverified or disputed, {web_count} web sources consulted.

Top claims:
{claims_text}

Write your answer in markdown with this shape:

1. One concise paragraph summarizing:
   - Overall strength of the evidence (e.g. strong / mixed / weak)
   - Whether the claims broadly support or challenge the topic

2. A bulleted list titled **"Evidence Notes"** with 2–4 bullets highlighting:
   - Any major limitations or biases in the evidence
   - Important nuances (e.g. results only apply to certain populations, doses, timeframes)

Guidelines:
- Be specific about "{query}".
- Do NOT mention RAG, embeddings, or AI models.
- Keep the whole section under ~150–200 words."""

    model = context.get("llm_model", config.LLM_MODEL)
    reply, usage = chat_completion_with_usage(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
        temperature=0.3,
        model=model,
        api_key=effective_key,
    )
    if usage:
        u = context.setdefault("llm_usage", {"prompt_tokens": 0, "completion_tokens": 0})
        u["prompt_tokens"] += usage.get("prompt_tokens", 0)
        u["completion_tokens"] += usage.get("completion_tokens", 0)
    return reply or ""


# ══════════════════════════════════════════════════════════════════════
# Report assembly
# ══════════════════════════════════════════════════════════════════════

def _build_report(
    query: str,
    query_analysis: dict,
    themes: List[dict],
    gaps: List[str],
    hypotheses: List[str],
    key_insights: List[str],
    llm_insights: List[str],
    claims: List[dict],
    fact_results: List[dict],
    credibility: dict,
    contradictions: List[dict],
    evidence_chains: List[dict],
    retriever_output: dict,
    web_results: Optional[List[dict]] = None,
    llm_summary: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Assemble the full markdown report."""
    sections = []

    # ── Header ────────────────────────────────────────────────────────
    sections.append(f"# Research Report\n")
    sections.append(f"**Query:** {query}\n")
    sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    sections.append(f"**Query Type:** {query_analysis.get('intent', 'N/A')} | "
                    f"**Complexity:** {query_analysis.get('complexity', 'N/A')}\n")
    sections.append("---\n")

    # ── Executive Summary (LLM-generated about actual topic) ──────────
    sections.append("## Executive Summary\n")
    total_claims = len(claims)
    verified = sum(1 for r in fact_results if r["verdict"] in ("verified", "partially_verified"))
    web_count = len(web_results) if web_results else 0

    if llm_summary:
        # If the LLM included its own "Executive Summary" heading(s), strip them so we don't repeat the section title.
        cleaned = llm_summary.lstrip()
        while True:
            first_newline = cleaned.find("\n")
            first_line = (cleaned if first_newline == -1 else cleaned[:first_newline]).strip()
            # Strip optional leading # and whitespace for markdown-style headings
            normalized = first_line.lstrip("#").strip().lower()
            if not normalized or not normalized.startswith("executive summary"):
                break
            cleaned = cleaned[first_newline + 1 :].lstrip() if first_newline != -1 else ""
            if not cleaned:
                break
        sections.append(cleaned)
        sections.append("")
        # Add a stats line
        sections.append(
            f"*Pipeline stats: {total_claims} claims analyzed from "
            f"{retriever_output.get('num_chunks', 0)} embedded docs"
            + (f" and {web_count} web sources" if web_count else "")
            + f", {verified} ({_pct(verified, total_claims)}%) verified.*\n"
        )
    else:
        # Fallback: template-based summary
        overall_cred = credibility.get("overall", "unknown")
        summary = (
            f"This research analysis examined **{total_claims} claims** extracted from "
            f"**{retriever_output.get('num_chunks', 0)} sources**"
        )
        if web_count:
            summary += f" (including **{web_count} web sources**)"
        summary += (
            f". Of these, **{verified}** ({_pct(verified, total_claims)}%) were at least partially verified. "
            f"The overall source credibility is rated **{overall_cred}** "
            f"(avg. score: {credibility.get('average_score', 0):.2f}).\n"
        )
        sections.append(summary)

    # ── Key Insights (LLM-generated about actual topic) ───────────────
    sections.append("## Key Insights\n")
    # Prefer LLM insights; fall back to pipeline-generated ones
    insights_to_show = llm_insights if llm_insights else key_insights
    if insights_to_show:
        for i, insight in enumerate(insights_to_show, 1):
            sections.append(f"{i}. {insight}")
        sections.append("")
    else:
        sections.append("*No key insights could be generated for this query.*\n")

    # ── Thematic Analysis ─────────────────────────────────────────────
    if themes:
        sections.append("## Thematic Analysis\n")
        for theme in themes:
            strength_icon = {"strong": "🟢", "moderate": "🟡", "emerging": "🔵"}.get(
                theme.get("strength", "moderate"), "⚪"
            )
            name = theme.get("name", "Unknown Theme")
            description = theme.get("description", "")
            theme_claims = theme.get("claims", [])

            sections.append(f"### {strength_icon} {name}\n")

            if description:
                # LLM-generated theme with a description
                sections.append(f"*{description}*\n")
                sections.append(f"- **Strength:** {theme.get('strength', 'N/A')}\n")
            else:
                # Fallback theme with claim details
                sections.append(
                    f"- **Claims:** {theme.get('claim_count', 0)} | "
                    f"**Avg. Confidence:** {theme.get('avg_confidence', 0)} | "
                    f"**Strength:** {theme.get('strength', 'N/A')}\n"
                )
                for claim in theme_claims[:3]:
                    sections.append(f'  - "{claim["claim"][:120]}..." `[{claim["source_id"]}]`')
            sections.append("")

    # ── Evidence Assessment ───────────────────────────────────────────
    sections.append("## Evidence Assessment\n")

    # Generate LLM-based evidence assessment if available
    llm_evidence = _generate_llm_evidence_assessment(query, claims, fact_results, web_results, context or {})
    if llm_evidence:
        sections.append(llm_evidence)
        sections.append("")

    sections.append("| Verdict | Count | Percentage |")
    sections.append("|---------|-------|------------|")
    verdict_counts = credibility.get("verdict_breakdown", {})
    for verdict, count in sorted(verdict_counts.items()):
        icon = {"verified": "✅", "partially_verified": "🟡", "unverified": "❓", "disputed": "⚠️"}.get(verdict, "")
        sections.append(f"| {icon} {verdict.replace('_', ' ').title()} | {count} | {_pct(count, total_claims)}% |")
    sections.append("")

    # Contradictions
    if contradictions:
        sections.append("### Contradictions Detected\n")
        for i, c in enumerate(contradictions[:5], 1):
            sections.append(
                f"**{i}.** Claim A: \"{c['claim_a']}...\"\n"
                f"   vs. Claim B: \"{c['claim_b']}...\"\n"
                f"   *(Opposing: {c['opposing_terms'][0]} vs {c['opposing_terms'][1]})*\n"
            )

    # ── Knowledge Gaps ────────────────────────────────────────────────
    if gaps:
        sections.append("## Knowledge Gaps\n")
        for gap in gaps:
            sections.append(f"- ⚠️ {gap}")
        sections.append("")

    # ── Hypotheses ────────────────────────────────────────────────────
    if hypotheses:
        sections.append("## Research Hypotheses\n")
        for i, h in enumerate(hypotheses, 1):
            sections.append(f"{i}. 💡 {h}")
        sections.append("")

    # ══════════════════════════════════════════════════════════════════
    # DETAILED FINDINGS — two parts: Web Sources + Embedding Sources
    # ══════════════════════════════════════════════════════════════════

    sections.append("## Detailed Findings\n")

    # ── Part A: Web-based findings (Tavily) — shown first ─────────────
    if web_results:
        sections.append("### 🌐 Part A — Web Sources (Live Search)\n")
        sections.append(
            "*These results come from live web search via Tavily, "
            "providing up-to-date information with clickable links.*\n"
        )
        for i, web in enumerate(web_results, 1):
            title = web.get("title", "Untitled")
            url = web.get("url", "")
            snippet = web.get("snippet", "")[:250]
            score = web.get("score", 0)
            score_icon = "🟢" if score >= 0.7 else "🟡" if score >= 0.4 else "🔴"
            sections.append(
                f"**{i}.** {score_icon} **[{title}]({url})**\n"
                f"   - Relevance: {score:.2f} | "
                f"🔗 [{_shorten_url(url)}]({url})\n"
                f"   - *\"{snippet}...\"*\n"
            )
        sections.append("")

    # ── Part B: Embedding-based findings (vector DB) ──────────────────
    # Filter to only show web-sourced evidence chains (from web chunks)
    web_chains = [c for c in evidence_chains if c.get("source_id", "").startswith("web_")]
    emb_chains = [c for c in evidence_chains if not c.get("source_id", "").startswith("web_")]

    if web_chains:
        sections.append("### 🔍 Analyzed Web Claims\n")
        sections.append(
            "*Claims extracted and fact-checked from web search results.*\n"
        )
        for i, chain in enumerate(web_chains[:8], 1):
            strength_icon = {"strong": "🟢", "moderate": "🟡", "weak": "🔴"}.get(chain["strength"], "⚪")
            source_info = chain.get("source_metadata", {})
            title = source_info.get("title", "")
            url = source_info.get("url", "")
            link_text = f"[{title}]({url})" if url else title or chain.get("source_id", "")
            sections.append(
                f"**{i}.** {strength_icon} {chain['claim'][:150]}\n"
                f"   - Source: {link_text} | "
                f"Confidence: {chain['confidence']} | "
                f"Type: {chain['evidence_type']} | "
                f"Strength: {chain['strength']}\n"
            )
        sections.append("")

    if emb_chains:
        sections.append("### 📦 Part B — Embedding Sources (Vector DB)\n")
        sections.append(
            "*These findings come from documents indexed in the local "
            "vector database.*\n"
        )
        for i, chain in enumerate(emb_chains[:6], 1):
            strength_icon = {"strong": "🟢", "moderate": "🟡", "weak": "🔴"}.get(chain["strength"], "⚪")
            source_info = chain.get("source_metadata", {})
            source_label = source_info.get("source", "unknown")
            doc_type = source_info.get("doc_type", "N/A")
            year = source_info.get("year", "N/A")
            sections.append(
                f"**{i}.** {strength_icon} {chain['claim'][:150]}\n"
                f"   - Source: `{chain['source_id']}` ({source_label}, {doc_type}, {year}) | "
                f"Confidence: {chain['confidence']} | "
                f"Type: {chain['evidence_type']} | "
                f"Strength: {chain['strength']}\n"
            )
        sections.append("")

    if not web_results and not evidence_chains:
        sections.append("*No findings available — try a different query.*\n")

    # ══════════════════════════════════════════════════════════════════
    # CITATIONS — two parts: Web links + Embedding refs
    # ══════════════════════════════════════════════════════════════════

    sections.append("## Citations\n")

    # ── Web citations (shown first — more relevant) ───────────────────
    sections.append("### 🌐 Web Sources\n")
    if web_results:
        for i, web in enumerate(web_results, 1):
            title = web.get("title", "Untitled")
            url = web.get("url", "")
            sections.append(f"{i}. [{title}]({url})")
    else:
        sections.append("- *No web sources available (Tavily API key may not be configured).*")
    sections.append("")

    # ── Embedding citations ───────────────────────────────────────────
    sections.append("### 📦 Embedding Sources\n")
    cited_sources = set()
    if emb_chains:
        for chain in emb_chains:
            src_id = chain.get("source_id", "")
            meta = chain.get("source_metadata", {})
            if src_id and src_id not in cited_sources:
                cited_sources.add(src_id)
                sections.append(
                    f"- `[{src_id}]` — {meta.get('source', 'Unknown')} "
                    f"({meta.get('doc_type', 'N/A')}, {meta.get('year', 'N/A')})"
                )
    else:
        sections.append("- *No embedding sources cited.*")
    sections.append("")

    sections.append("---\n*Report generated by Astraeus 2.0 — Multi-Agent AI Deep Researcher*")

    return "\n".join(sections)


def _pct(part: int, total: int) -> int:
    """Calculate percentage safely."""
    if total == 0:
        return 0
    return round(100 * part / total)


def _shorten_url(url: str, max_len: int = 50) -> str:
    """Shorten a URL for display, keeping the domain readable."""
    short = url.replace("https://", "").replace("http://", "")
    if len(short) > max_len:
        short = short[:max_len - 3] + "..."
    return short
