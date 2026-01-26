#!/usr/bin/env python3
"""TradingView tools UI and Pine export helpers."""

from __future__ import annotations

from pathlib import Path
import streamlit as st

from utils.tradingview_bridge import TradingViewBridge


def render_tradingview_tools():
    st.subheader("🧩 TradingView Tools")

    bridge = TradingViewBridge()
    if bridge.available():
        st.success("TradingView bridge aktif (Node + script bulundu).")
    else:
        st.warning(
            "TradingView bridge pasif. Node.js ve @mathieuc/tradingview kurulumu gerekiyor. "
            "Env: TRADINGVIEW_SESSION / TRADINGVIEW_SIGNATURE (opsiyonel)."
        )

    st.markdown("### IMSE Indicator (Export-Ready)")
    pine_path = Path(__file__).resolve().parents[2] / "docs" / "imse_indicator.pine"
    if pine_path.exists():
        pine_code = pine_path.read_text(encoding="utf-8")
        st.code(pine_code, language="pine")
        st.download_button(
            label="⬇️ IMSE Pine Script indir",
            data=pine_code,
            file_name="imse_indicator.pine",
            mime="text/plain",
        )
    else:
        st.info("IMSE Pine script dosyası bulunamadı.")

    st.markdown(
        """
**Strategy wrapper eşleştirme notu**

Strategy tarafındaki `input.source()` dropdown'unda aşağıdaki isimleri seçin:
- IMSE Score
- IMSE Threshold
- IMSE Confidence
- IMSE Slope

Bu plot isimleri yoksa wrapper seri seçemez.
"""
    )
