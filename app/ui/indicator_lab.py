#!/usr/bin/env python3
"""Indicator Lab UI for multi-timeframe technical analysis."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.market_data_fetcher import get_market_fetcher
from utils.data_quality import format_quality_badge, DataQuality
from app.analytics.custom_indicator_suite import PROFILES, compute_indicator_bundle


@st.cache_data(ttl=300)
def _load_indicator_bundle(symbol: str, profile_key: str, source_pref: str):
    profile = PROFILES[profile_key]
    fetcher = get_market_fetcher()
    hist, info, quality = fetcher.get_stock_data_with_meta(
        symbol,
        period=profile.period,
        interval=profile.interval,
        source_preference=source_pref,
    )
    analysis = compute_indicator_bundle(hist, profile) if hist is not None else {"error": "No data"}
    return hist, info, quality, analysis


def _render_profile_panel(symbol: str, profile_key: str, source_pref: str):
    profile = PROFILES[profile_key]
    hist, info, quality, analysis = _load_indicator_bundle(symbol, profile_key, source_pref)

    if hist is None or hist.empty:
        st.warning("Veri alınamadı. Lütfen sembolü kontrol edin veya veri kaynağını değiştirin.")
        return
    if analysis.get("error"):
        st.error(analysis["error"])
        return

    # Data quality badge
    if isinstance(quality, DataQuality):
        st.markdown(format_quality_badge(quality), unsafe_allow_html=True)

    latest = analysis["latest"]
    imse = analysis["imse"].iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fiyat", f"{latest['price']:.2f}")
    with col2:
        st.metric("IMSE Skor", f"{imse['final_score']:.3f}")
    with col3:
        st.metric("Güven", f"{imse['confidence']:.2f}")
    with col4:
        st.metric("Rejim", imse['regime'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("EMA Fast", f"{latest['ema_fast']:.2f}")
    with col2:
        st.metric("EMA Slow", f"{latest['ema_slow']:.2f}")
    with col3:
        st.metric("RSI", f"{latest['rsi']:.1f}")
    with col4:
        st.metric("Trend", latest['trend_state'])

    # Chart
    series = analysis["series"]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])

    fig.add_trace(
        go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name="Price",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(go.Scatter(x=hist.index, y=series['ema_fast'], name="EMA Fast", line=dict(color="#3b82f6")), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=series['ema_slow'], name="EMA Slow", line=dict(color="#a855f7")), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=series['sma_long'], name="SMA Long", line=dict(color="#f59e0b", dash="dot")), row=1, col=1)

    imse_df = analysis["imse"]
    fig.add_trace(go.Scatter(x=imse_df.index, y=imse_df['final_score'], name="IMSE Score", line=dict(color="#0ea5e9")), row=2, col=1)
    fig.add_trace(go.Scatter(x=imse_df.index, y=imse_df['threshold'], name="Threshold", line=dict(color="#94a3b8", dash="dash")), row=2, col=1)
    fig.add_trace(go.Scatter(x=imse_df.index, y=-imse_df['threshold'], name="-Threshold", line=dict(color="#94a3b8", dash="dash")), row=2, col=1)

    fig.update_layout(
        height=650,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="IMSE", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Detail table
    with st.expander("Detaylı Göstergeler"):
        detail = pd.DataFrame({
            "Metric": [
                "EMA Fast", "EMA Slow", "SMA Long", "RSI", "ATR", "MACD", "MACD Signal", "MACD Hist",
                "IMSE Score", "IMSE Threshold", "IMSE Confidence", "IMSE Slope", "ADX", "ATR%",
            ],
            "Value": [
                f"{latest['ema_fast']:.2f}",
                f"{latest['ema_slow']:.2f}",
                f"{latest['sma_long']:.2f}" if latest['sma_long'] else "N/A",
                f"{latest['rsi']:.2f}",
                f"{latest['atr']:.2f}",
                f"{latest['macd']:.4f}",
                f"{latest['macd_signal']:.4f}",
                f"{latest['macd_hist']:.4f}",
                f"{imse['final_score']:.4f}",
                f"{imse['threshold']:.4f}",
                f"{imse['confidence']:.4f}",
                f"{imse['trend_slope']:.4f}",
                f"{imse['adx']:.2f}",
                f"{imse['atrp']:.2f}%",
            ],
        })
        st.dataframe(detail, use_container_width=True, hide_index=True)


def render_indicator_lab():
    st.subheader("🧭 Indicator Lab – Günlük / Kısa / Orta / Uzun Vade")

    st.markdown(
        "Bu bölüm, IMSE (Institutional Market State Engine) + klasik göstergeleri "
        "çoklu vade profilleriyle birleştirir."
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        symbol = st.text_input("Sembol", value="AAPL", key="indicator_lab_symbol")
    with col2:
        source_pref = st.selectbox(
            "Veri Kaynağı",
            ["auto", "yfinance", "tradingview"],
            format_func=lambda x: "Auto" if x == "auto" else ("TradingView" if x == "tradingview" else "YFinance"),
            key="indicator_lab_source",
        )
    with col3:
        st.caption("TradingView modu için Node + @mathieuc/tradingview gerekir")

    if not symbol:
        st.info("👆 Lütfen sembol girin")
        return

    profile_tabs = st.tabs(list(PROFILES.keys()))
    for idx, profile_key in enumerate(PROFILES.keys()):
        with profile_tabs[idx]:
            _render_profile_panel(symbol, profile_key, source_pref)

    st.markdown("---")
    st.info(
        "IMSE serileri (Score / Threshold / Confidence / Slope) Python tarafında hesaplanır. "
        "TradingView strategy wrapper ile entegre etmek için Pine sürümündeki export plot isimlerini kullanın."
    )
