#!/usr/bin/env python3
"""HF Inference powered insight UI."""

from __future__ import annotations

import os
import streamlit as st
import yfinance as yf

from utils.hf_inference import HFInferenceClient


def _extract_text_from_news(news_items, max_items=6):
    lines = []
    for item in (news_items or [])[:max_items]:
        title = item.get("title", "")
        summary = item.get("summary", "")
        if title:
            lines.append(title)
        if summary:
            lines.append(summary)
    return "\n".join(lines)


def _render_hf_output(resp):
    if not resp.ok:
        st.error(resp.error or "HF request failed")
        return

    data = resp.data
    if isinstance(data, list) and data:
        # Summarization or classification
        if "summary_text" in data[0]:
            st.success(data[0]["summary_text"])
            return
        if "generated_text" in data[0]:
            st.success(data[0]["generated_text"])
            return
        if "label" in data[0]:
            st.json(data)
            return

    st.json(data)


def render_hf_insights():
    st.subheader("🧠 HF Insights – Market Explainer / KAP & Earnings")

    client = HFInferenceClient()
    if not client.token:
        st.warning("HF_API_TOKEN bulunamadı. Streamlit secrets veya env ile ekleyin.")

    col1, col2 = st.columns([2, 1])
    with col1:
        symbol = st.text_input("Haber çekmek için sembol (opsiyonel)", value="", key="hf_symbol")
    with col2:
        max_items = st.number_input("Haber sayısı", min_value=1, max_value=10, value=5, step=1)

    if st.button("Haberleri getir", type="secondary") and symbol:
        try:
            news = yf.Ticker(symbol).news
            st.session_state["hf_news_text"] = _extract_text_from_news(news, max_items=max_items)
            st.success("Haber metni hazırlandı")
        except Exception as e:
            st.error(f"Haber çekilemedi: {e}")

    default_summary_model = os.getenv("HF_SUMMARY_MODEL", "facebook/bart-large-cnn")
    default_sentiment_model = os.getenv("HF_SENTIMENT_MODEL", "ProsusAI/finbert")
    default_risk_model = os.getenv("HF_RISK_MODEL", "google/flan-t5-base")

    text = st.text_area(
        "İçerik / Haber metni",
        value=st.session_state.get("hf_news_text", ""),
        height=220,
        key="hf_text",
        placeholder="Örn: KAP metni, earnings açıklaması, haber özetleri...",
    )

    if not text.strip():
        st.info("Analiz için içerik girin.")
        return

    st.markdown("### Modeller")
    col1, col2, col3 = st.columns(3)
    with col1:
        summary_model = st.text_input("Summary Model", value=default_summary_model)
    with col2:
        sentiment_model = st.text_input("Sentiment Model", value=default_sentiment_model)
    with col3:
        risk_model = st.text_input("Risk Model", value=default_risk_model)

    run = st.button("🚀 Insight üret", type="primary")

    if run:
        with st.spinner("HF Inference çalışıyor..."):
            st.markdown("#### Özet")
            _render_hf_output(client.summarize(text, summary_model))

            st.markdown("#### Duygu / Sentiment")
            _render_hf_output(client.sentiment(text, sentiment_model))

            st.markdown("#### Risk & Red Flags")
            _render_hf_output(client.extract_risks(text, risk_model))

        st.caption("Not: HF Inference Serverless gecikmeli olabilir. İlk çağrı model yüklemesi yapabilir.")
