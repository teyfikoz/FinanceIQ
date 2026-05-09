"""
AI Narrative Engine — FinanceIQ
LLM-powered executive summaries and risk memos via HF Pro (Mixtral-8x7B).
Falls back to rule-based InsightEngine when HF is unavailable.
"""
import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# HF Inference model for narrative generation
_HF_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
_HF_CLIENT = None


def _get_hf_client():
    """Lazy-init HF InferenceClient. Returns None if token not configured."""
    global _HF_CLIENT
    if _HF_CLIENT is not None:
        return _HF_CLIENT
    token = os.environ.get("HF_API_TOKEN", "")
    if not token:
        return None
    try:
        from huggingface_hub import InferenceClient
        _HF_CLIENT = InferenceClient(token=token, timeout=20)
        logger.info("HF InferenceClient initialized for AI Narrative")
    except Exception as e:
        logger.warning(f"HF client init failed: {e}")
        return None
    return _HF_CLIENT


def _call_llm(prompt: str, max_tokens: int = 600) -> Optional[str]:
    """Call HF Inference API. Returns None on any failure."""
    client = _get_hf_client()
    if not client:
        return None
    try:
        resp = client.chat_completion(
            model=_HF_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.4,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM call failed, falling back: {e}")
        return None


# ── Narrative generators ───────────────────────────────────────────────────

def generate_executive_summary(
    market_data: Dict[str, Any],
    language: str = "en",
) -> str:
    """
    Generate a C-suite executive summary from market data dict.

    Args:
        market_data: dict with keys like 'indices', 'macro', 'sector_performance'
        language: 'en' or 'tr'

    Returns:
        Formatted executive summary string (markdown)
    """
    lang_instruction = "Respond in Turkish." if language == "tr" else "Respond in English."

    # Build context from market_data
    ctx_lines = []
    if "indices" in market_data:
        ctx_lines.append("Market Indices:")
        for name, val in market_data["indices"].items():
            ctx_lines.append(f"  - {name}: {val}")
    if "macro" in market_data:
        ctx_lines.append("Macro Indicators:")
        for k, v in market_data["macro"].items():
            ctx_lines.append(f"  - {k}: {v}")
    if "sector_performance" in market_data:
        ctx_lines.append("Sector Performance (%):")
        for sector, pct in market_data["sector_performance"].items():
            ctx_lines.append(f"  - {sector}: {pct:+.1f}%")

    context = "\n".join(ctx_lines) if ctx_lines else "Market data unavailable."

    prompt = f"""[INST] You are a senior macro strategist at a global investment bank.
Write a concise executive summary (3 paragraphs max, ~150 words) for a C-suite morning briefing.
Cover: (1) key market moves, (2) macro drivers, (3) one actionable takeaway.
Be specific with numbers. No bullet points — flowing prose only.
{lang_instruction}

Market Data:
{context}
[/INST]"""

    result = _call_llm(prompt, max_tokens=400)
    if result:
        return f"### 📊 Executive Summary\n\n{result}"

    # Fallback: rule-based summary
    return _fallback_executive_summary(market_data, language)


def generate_risk_memo(
    portfolio_summary: Dict[str, Any],
    risk_signals: List[str],
    language: str = "en",
) -> str:
    """
    Generate a risk memo for a portfolio or market position.

    Args:
        portfolio_summary: dict with allocation, exposure, drawdown info
        risk_signals: list of risk alert strings
        language: 'en' or 'tr'

    Returns:
        Formatted risk memo string (markdown)
    """
    lang_instruction = "Respond in Turkish." if language == "tr" else "Respond in English."

    signals_text = "\n".join(f"- {s}" for s in risk_signals) if risk_signals else "No signals provided."

    alloc = portfolio_summary.get("allocation", {})
    alloc_text = ", ".join(f"{k}: {v}" for k, v in alloc.items()) if alloc else "N/A"

    prompt = f"""[INST] You are a Chief Risk Officer writing a brief risk memo.
Write a structured risk assessment (under 200 words) covering:
1. Key risks identified
2. Severity assessment (Low/Medium/High)
3. Recommended actions (2-3 bullets)
Be direct and actionable. {lang_instruction}

Portfolio Allocation: {alloc_text}
Risk Signals Detected:
{signals_text}
[/INST]"""

    result = _call_llm(prompt, max_tokens=350)
    if result:
        return f"### ⚠️ Risk Memo\n\n{result}"

    return _fallback_risk_memo(risk_signals, language)


def generate_market_narrative(
    event: str,
    context: str = "",
    language: str = "en",
) -> str:
    """
    Generate a short market narrative explaining a specific event.

    Args:
        event: e.g. "S&P 500 dropped 2.3% today"
        context: additional background
        language: 'en' or 'tr'

    Returns:
        Narrative explanation string (markdown)
    """
    lang_instruction = "Respond in Turkish." if language == "tr" else "Respond in English."

    prompt = f"""[INST] You are a financial journalist explaining market events to professional investors.
Write a concise market narrative (100-150 words) explaining what happened and why it matters.
Connect it to macro trends, sector impacts, and investor implications.
{lang_instruction}

Event: {event}
{f'Context: {context}' if context else ''}
[/INST]"""

    result = _call_llm(prompt, max_tokens=300)
    if result:
        return f"### 📰 Market Narrative\n\n{result}"

    return f"### 📰 Market Narrative\n\n*{event}*\n\nAI narrative unavailable. Check HF_API_TOKEN configuration."


# ── Rule-based fallbacks ───────────────────────────────────────────────────

def _fallback_executive_summary(market_data: Dict, language: str) -> str:
    """Simple rule-based summary when LLM unavailable."""
    lines = ["### 📊 Executive Summary\n"]
    if language == "tr":
        lines.append("**Piyasa Özeti (Kural-Tabanlı)**\n")
    else:
        lines.append("**Market Summary (Rule-Based Fallback)**\n")

    if "indices" in market_data:
        for name, val in market_data["indices"].items():
            lines.append(f"- {name}: {val}")

    if not market_data:
        lines.append("No market data available for summary generation.")

    lines.append("\n*AI narrative requires HF_API_TOKEN. Configure it for LLM-powered summaries.*")
    return "\n".join(lines)


def _fallback_risk_memo(risk_signals: List[str], language: str) -> str:
    """Simple rule-based risk memo when LLM unavailable."""
    lines = ["### ⚠️ Risk Memo (Rule-Based)\n"]
    if risk_signals:
        for sig in risk_signals:
            lines.append(f"- {sig}")
    else:
        lines.append("No risk signals detected.")
    lines.append("\n*AI narrative requires HF_API_TOKEN.*")
    return "\n".join(lines)


# ── Streamlit UI component ─────────────────────────────────────────────────

def render_narrative_panel(
    market_data: Optional[Dict] = None,
    risk_signals: Optional[List[str]] = None,
    portfolio_summary: Optional[Dict] = None,
    language: str = "en",
) -> None:
    """
    Render the AI Narrative panel in a Streamlit app.
    Call this from main.py inside a st.tab() or st.expander().
    """
    try:
        import streamlit as st
    except ImportError:
        return

    hf_token = os.environ.get("HF_API_TOKEN", "")
    ai_available = bool(hf_token)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🤖 AI Narrative Engine")
    with col2:
        status = "🟢 AI Active" if ai_available else "🟡 Rule-Based"
        st.caption(status)

    if not ai_available:
        st.info(
            "**HF_API_TOKEN** not configured — showing rule-based summaries. "
            "Add token to `.env` for Mixtral-8x7B powered narratives."
        )

    narrative_view = st.radio(
        "Narrative View",
        ["📊 Executive Summary", "⚠️ Risk Memo", "📰 Event Narrative"],
        horizontal=True,
        key="ai_narrative_view_nav",
        label_visibility="collapsed"
    )

    if narrative_view == "📊 Executive Summary":
        if st.button("Generate Executive Summary", key="gen_exec"):
            with st.spinner("Generating narrative..."):
                md = market_data or {}
                summary = generate_executive_summary(md, language=language)
                st.markdown(summary)

    elif narrative_view == "⚠️ Risk Memo":
        if st.button("Generate Risk Memo", key="gen_risk"):
            with st.spinner("Analyzing risks..."):
                signals = risk_signals or []
                port = portfolio_summary or {}
                memo = generate_risk_memo(port, signals, language=language)
                st.markdown(memo)

    else:
        event_input = st.text_input(
            "Describe a market event",
            placeholder="e.g. BIST 100 rose 1.8% on central bank rate hold decision",
            key="event_input"
        )
        if st.button("Generate Narrative", key="gen_event") and event_input:
            with st.spinner("Writing narrative..."):
                narrative = generate_market_narrative(event_input, language=language)
                st.markdown(narrative)
