"""
TR Funds Intelligence Launchpad
===============================
High-level Turkish funds overview layer for the public FundPortal experience.

This module sits above the detailed TEFAS portfolio analysis and flow tools.
It keeps the existing content structure intact while giving the user a faster,
more premium entry point into Turkish fund intelligence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from app.data_collectors.tefas_portfolio_tracker import TEFASPortfolioTracker


POPULAR_FUNDS: Dict[str, str] = {
    "TCD": "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu",
    "YAT": "Yapi Kredi Portfoy Hisse Senedi Fonu",
    "GAH": "Garanti Portfoy Hisse Senedi Fonu",
    "FBA": "Finans Portfoy Birinci Hisse Senedi Fonu",
    "AKG": "Ak Portfoy Kisa Vadeli Borclanma Araclari Fonu",
    "ZPE": "Ziraat Portfoy Hisse Senedi Fonu",
}

ASSET_LABELS = {
    "stocks": "Hisse",
    "bonds": "Tahvil",
    "bills": "Bono",
    "repo": "Repo",
    "fx": "Doviz",
    "participation": "Katilim",
    "precious_metals": "Kiymetli Maden",
    "other": "Diger",
}


def _dominant_asset(asset_allocation: Dict[str, float]) -> tuple[str, float]:
    if not asset_allocation:
        return "Belirsiz", 0.0
    key = max(asset_allocation, key=lambda item: asset_allocation.get(item, 0.0))
    return ASSET_LABELS.get(key, key.title()), float(asset_allocation.get(key, 0.0))


def _fund_regime(summary: Dict) -> tuple[str, str]:
    value_delta = float(summary.get("portfolio_value_change", 0) or 0)
    investor_delta = float(summary.get("investor_change", 0) or 0)
    added = int(summary.get("total_new_holdings", 0) or 0)
    removed = int(summary.get("total_removed_holdings", 0) or 0)

    if value_delta > 0 and investor_delta > 0:
        return "Accumulation", "Net deger ve yatirimci sayisi birlikte artiyor."
    if value_delta < 0 and investor_delta < 0:
        return "Distribution", "Hem varlik tabani hem de yatirimci ilgisi geriliyor."
    if added > removed and investor_delta >= 0:
        return "Rotation", "Portfoy yeniden konumlaniyor; yeni eklemeler daha baskin."
    return "Mixed", "Sinyaller karisik; daha detayli akim analizi gerekli."


def _safe_growth_pct(latest_value: float, delta_value: float) -> float:
    latest = float(latest_value or 0)
    delta = float(delta_value or 0)
    base = latest - delta
    if abs(base) < 1e-9:
        return 0.0
    return (delta / abs(base)) * 100


def _latest_allocation_drift(summary: Dict[str, Any]) -> float:
    monthly_changes = summary.get("monthly_allocation_changes", []) or []
    if not monthly_changes:
        return 0.0

    latest_change = monthly_changes[-1]
    watched_columns = [
        "stocks_change",
        "bonds_change",
        "repo_change",
        "fx_change",
        "participation_change",
        "precious_metals_change",
    ]
    drift = sum(abs(float(latest_change.get(column, 0) or 0)) for column in watched_columns)
    return round(drift, 2)


def _signal_score(summary: Dict[str, Any]) -> float:
    latest_value = float(summary.get("latest_portfolio_value", 0) or 0)
    value_delta = float(summary.get("portfolio_value_change", 0) or 0)
    latest_investors = float(summary.get("latest_num_investors", 0) or 0)
    investor_delta = float(summary.get("investor_change", 0) or 0)
    added = int(summary.get("total_new_holdings", 0) or 0)
    removed = int(summary.get("total_removed_holdings", 0) or 0)

    value_growth_pct = _safe_growth_pct(latest_value, value_delta)
    investor_growth_pct = _safe_growth_pct(latest_investors, investor_delta)
    drift = _latest_allocation_drift(summary)
    regime, _ = _fund_regime(summary)

    regime_bonus = {
        "Accumulation": 22.0,
        "Rotation": 12.0,
        "Mixed": 0.0,
        "Distribution": -20.0,
    }.get(regime, 0.0)

    score = 50.0 + regime_bonus
    score += max(-15.0, min(15.0, value_growth_pct)) * 0.8
    score += max(-15.0, min(15.0, investor_growth_pct)) * 0.9

    if regime in ("Accumulation", "Rotation"):
        score += min(drift, 10.0)
    elif regime == "Distribution":
        score -= min(drift, 10.0) * 0.6
    else:
        score += min(drift, 10.0) * 0.3

    score += min(float(added), 10.0) * 0.7
    score -= min(float(removed), 10.0) * 0.5

    return round(max(0.0, min(100.0, score)), 1)


def _signal_band(score: float) -> str:
    if score >= 75:
        return "Leading"
    if score >= 60:
        return "Constructive"
    if score >= 45:
        return "Neutral"
    return "Under Pressure"


def _short_fund_name(fund_name: str) -> str:
    compact = fund_name.replace(" Portfoy ", " ").replace(" Endeks Hisse Senedi Fonu", "")
    compact = compact.replace(" Hisse Senedi Fonu", "").replace(" Kisa Vadeli Borclanma Araclari Fonu", "")
    return compact[:42]


def _load_tr_fund_summary_live(fund_code: str, months: int) -> Optional[Dict]:
    tracker = TEFASPortfolioTracker()
    return tracker.generate_portfolio_summary(fund_code, months)


# INTENTIONAL CACHE DIVERGENCE:
# This uses Streamlit's @st.cache_data for fast, local UI memoization.
# It is intentionally kept separate from the centralized get_cache() service.
# INTENTIONAL CACHE DIVERGENCE: This UI-bound memoization intentionally bypasses 
# the centralized get_cache() service to utilize Streamlit's native TTL handling.
@st.cache_data(ttl=600, show_spinner=False)
def _load_tr_fund_summary(fund_code: str, months: int) -> Optional[Dict]:
    return _load_tr_fund_summary_live(fund_code, months)


def _build_tr_peer_table(months: int) -> pd.DataFrame:
    rows = []
    for fund_code, fund_name in POPULAR_FUNDS.items():
        summary = _load_tr_fund_summary(fund_code, months) or _load_tr_fund_summary_live(fund_code, months)
        if not summary:
            continue

        dominant_name, dominant_weight = _dominant_asset(summary.get("asset_allocation_current", {}))
        regime, _ = _fund_regime(summary)
        signal_score = _signal_score(summary)
        latest_value = float(summary.get("latest_portfolio_value", 0) or 0)
        value_delta = float(summary.get("portfolio_value_change", 0) or 0)
        latest_investors = float(summary.get("latest_num_investors", 0) or 0)
        investor_delta = float(summary.get("investor_change", 0) or 0)
        allocation_drift = _latest_allocation_drift(summary)

        rows.append(
            {
                "fund_code": fund_code,
                "fund_name": fund_name,
                "fund_name_short": _short_fund_name(fund_name),
                "latest_portfolio_value": latest_value,
                "portfolio_value_change": value_delta,
                "value_growth_pct": _safe_growth_pct(latest_value, value_delta),
                "latest_num_investors": latest_investors,
                "investor_change": investor_delta,
                "investor_growth_pct": _safe_growth_pct(latest_investors, investor_delta),
                "dominant_asset": dominant_name,
                "dominant_weight": dominant_weight,
                "regime": regime,
                "allocation_drift": allocation_drift,
                "new_holdings": int(summary.get("total_new_holdings", 0) or 0),
                "removed_holdings": int(summary.get("total_removed_holdings", 0) or 0),
                "signal_score": signal_score,
                "signal_band": _signal_band(signal_score),
            }
        )

    peer_df = pd.DataFrame(rows)
    if peer_df.empty:
        return peer_df

    return peer_df.sort_values(
        ["signal_score", "investor_growth_pct", "value_growth_pct"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


# INTENTIONAL CACHE DIVERGENCE:
# This uses Streamlit's @st.cache_data for fast, local UI memoization.
@st.cache_data(ttl=600, show_spinner=False)
def _load_tr_peer_table(months: int) -> pd.DataFrame:
    return _build_tr_peer_table(months)


def get_tr_peer_signal_board(months: int = 12) -> pd.DataFrame:
    """Public helper for other UI surfaces that need the TR fund peer table."""
    peer_df = _load_tr_peer_table(months)
    if peer_df.empty:
        peer_df = _build_tr_peer_table(months)
    return peer_df.copy()


def get_tr_top_pick(months: int = 12) -> Optional[Dict[str, Any]]:
    """Return the top-ranked TR fund snapshot for lightweight landing surfaces."""
    peer_df = _load_tr_peer_table(months)
    if peer_df.empty:
        peer_df = _build_tr_peer_table(months)
        if peer_df.empty:
            return None
    return dict(peer_df.iloc[0])


def render_tr_funds_launchpad():
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 60%, #0ea5e9 100%);
                    padding: 1.4rem; border-radius: 16px; color: white; margin-bottom: 1rem;">
            <h2 style="margin: 0;">TR Funds Intelligence Launchpad</h2>
            <p style="margin: 0.45rem 0 0 0; font-size: 0.98rem;">
                TEFAS odakli hizli bakis: portfoy kaymasi, yatirimci momentumu ve bir sonraki
                derin analize gitmeden once fon rejimini gormek icin tasarlandi.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1.2, 1.2, 1])
    with col1:
        fund_code = st.selectbox(
            "Takip fonu",
            options=list(POPULAR_FUNDS.keys()),
            format_func=lambda code: f"{code} - {POPULAR_FUNDS[code]}",
            key="tr_launchpad_fund",
        )
    with col2:
        months = st.selectbox(
            "Pencere",
            options=[6, 9, 12, 18],
            index=2,
            format_func=lambda value: f"Son {value} ay",
            key="tr_launchpad_months",
        )
    with col3:
        st.metric("Veri evreni", "TEFAS", "Core")

    summary = _load_tr_fund_summary(fund_code, months) or _load_tr_fund_summary_live(fund_code, months)
    if not summary:
        st.warning("Secilen fon icin ozet veri alinamadi. Daha sonra tekrar dene.")
        return

    with st.spinner("TR fon peer evreni hazirlaniyor..."):
        peer_df = get_tr_peer_signal_board(months)

    dominant_name, dominant_weight = _dominant_asset(summary.get("asset_allocation_current", {}))
    regime, regime_note = _fund_regime(summary)
    signal_score = _signal_score(summary)
    signal_band = _signal_band(signal_score)

    metrics = st.columns(4)
    with metrics[0]:
        st.metric(
            "Portfoy Degeri",
            f"₺{float(summary.get('latest_portfolio_value', 0) or 0):,.0f}",
            f"₺{float(summary.get('portfolio_value_change', 0) or 0):,.0f}",
        )
    with metrics[1]:
        st.metric(
            "Yatirimci Sayisi",
            f"{int(summary.get('latest_num_investors', 0) or 0):,}",
            f"{int(summary.get('investor_change', 0) or 0):,}",
        )
    with metrics[2]:
        st.metric("Baskin Varlik", dominant_name, f"%{dominant_weight:.1f}")
    with metrics[3]:
        st.metric("Fon Rejimi", regime, summary.get("period", ""))

    st.info(f"{regime_note} Signal board gorunumu: {signal_band} ({signal_score}/100).")

    monthly_changes = summary.get("monthly_allocation_changes", [])
    if monthly_changes:
        df = pd.DataFrame(monthly_changes)
        if not df.empty:
            trend_df = pd.DataFrame(index=df["month"])
            if "stocks_curr" in df.columns:
                trend_df["Hisse %"] = df["stocks_curr"].values
            if "repo_curr" in df.columns:
                trend_df["Repo %"] = df["repo_curr"].values
            if "fx_curr" in df.columns:
                trend_df["Doviz %"] = df["fx_curr"].values
            if not trend_df.empty:
                st.markdown(f"**{fund_code} varlik kaymasi**")
                st.line_chart(trend_df, use_container_width=True)

    if not peer_df.empty:
        selected_peer = peer_df[peer_df["fund_code"] == fund_code]
        selected_row = selected_peer.iloc[0] if not selected_peer.empty else peer_df.iloc[0]
        peer_rank = int(peer_df.index[peer_df["fund_code"] == selected_row["fund_code"]][0]) + 1
        peer_median_score = float(peer_df["signal_score"].median())

        rank_cols = st.columns(4)
        with rank_cols[0]:
            st.metric("Peer Rank", f"#{peer_rank}/{len(peer_df)}", f"{selected_row['signal_score'] - peer_median_score:+.1f} vs median")
        with rank_cols[1]:
            st.metric("Signal Score", f"{selected_row['signal_score']:.1f}", selected_row["signal_band"])
        with rank_cols[2]:
            st.metric("Investor Growth", f"{selected_row['investor_growth_pct']:+.1f}%", f"{int(selected_row['investor_change']):,} net")
        with rank_cols[3]:
            st.metric("Allocation Drift", f"{selected_row['allocation_drift']:.1f}", selected_row["dominant_asset"])

    insight_cols = st.columns(3)
    with insight_cols[0]:
        st.markdown(
            f"""
            <div style="border: 1px solid #dbeafe; border-radius: 14px; padding: 1rem; background: #f8fbff;">
                <h4 style="margin-top: 0;">Allocation Drift</h4>
                <p style="margin-bottom: 0.35rem;"><strong>Yeni holdingler:</strong> {int(summary.get('total_new_holdings', 0) or 0)}</p>
                <p style="margin: 0;"><strong>Cikan holdingler:</strong> {int(summary.get('total_removed_holdings', 0) or 0)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with insight_cols[1]:
        st.markdown(
            f"""
            <div style="border: 1px solid #dcfce7; border-radius: 14px; padding: 1rem; background: #f7fff9;">
                <h4 style="margin-top: 0;">Investor Momentum</h4>
                <p style="margin-bottom: 0.35rem;"><strong>Son durum:</strong> {int(summary.get('latest_num_investors', 0) or 0):,}</p>
                <p style="margin: 0;"><strong>Degisim:</strong> {int(summary.get('investor_change', 0) or 0):,}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with insight_cols[2]:
        st.markdown(
            """
            <div style="border: 1px solid #ede9fe; border-radius: 14px; padding: 1rem; background: #faf7ff;">
                <h4 style="margin-top: 0;">Forecast Readiness</h4>
                <p style="margin-bottom: 0.35rem;"><strong>Durum:</strong> Hazir</p>
                <p style="margin: 0;">Bu fon, sonraki adimda akim ve tahmin katmanina genisletilebilir.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not peer_df.empty:
        st.markdown("---")
        st.subheader("🏁 FundPortal Signal Board")

        chart_df = peer_df.sort_values("signal_score", ascending=False)
        chart_cols = st.columns(2)
        with chart_cols[0]:
            st.markdown("**Signal Score**")
            st.bar_chart(
                chart_df.set_index("fund_code")[["signal_score"]],
                use_container_width=True,
            )
        with chart_cols[1]:
            st.markdown("**Investor Growth %**")
            st.bar_chart(
                chart_df.set_index("fund_code")[["investor_growth_pct"]],
                use_container_width=True,
            )

        board_cols = st.columns(3)
        top_pick = peer_df.iloc[0]
        under_pressure = peer_df.sort_values("signal_score", ascending=True).iloc[0]
        highest_drift = peer_df.sort_values("allocation_drift", ascending=False).iloc[0]

        with board_cols[0]:
            st.markdown(
                f"""
                <div style="border: 1px solid #bfdbfe; border-radius: 14px; padding: 1rem; background: #eff6ff;">
                    <h4 style="margin-top: 0;">Top Pick</h4>
                    <p style="margin-bottom: 0.35rem;"><strong>{top_pick['fund_code']}</strong> - {top_pick['signal_band']}</p>
                    <p style="margin-bottom: 0.35rem;">Score: {top_pick['signal_score']:.1f} | Investor Growth: {top_pick['investor_growth_pct']:+.1f}%</p>
                    <p style="margin: 0;">Dominant varlik: {top_pick['dominant_asset']} (%{top_pick['dominant_weight']:.1f})</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with board_cols[1]:
            st.markdown(
                f"""
                <div style="border: 1px solid #fecaca; border-radius: 14px; padding: 1rem; background: #fef2f2;">
                    <h4 style="margin-top: 0;">Under Pressure</h4>
                    <p style="margin-bottom: 0.35rem;"><strong>{under_pressure['fund_code']}</strong> - {under_pressure['signal_band']}</p>
                    <p style="margin-bottom: 0.35rem;">Score: {under_pressure['signal_score']:.1f} | Investor Growth: {under_pressure['investor_growth_pct']:+.1f}%</p>
                    <p style="margin: 0;">Removed holdings: {int(under_pressure['removed_holdings'])} | Regime: {under_pressure['regime']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with board_cols[2]:
            st.markdown(
                f"""
                <div style="border: 1px solid #fde68a; border-radius: 14px; padding: 1rem; background: #fffbeb;">
                    <h4 style="margin-top: 0;">Highest Drift</h4>
                    <p style="margin-bottom: 0.35rem;"><strong>{highest_drift['fund_code']}</strong> - {highest_drift['regime']}</p>
                    <p style="margin-bottom: 0.35rem;">Drift: {highest_drift['allocation_drift']:.1f} | New holdings: {int(highest_drift['new_holdings'])}</p>
                    <p style="margin: 0;">Bu fon daha derin flow veya forecast katmanina en hazir adaylardan biri.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        display_df = peer_df[
            [
                "fund_code",
                "fund_name_short",
                "signal_score",
                "signal_band",
                "regime",
                "value_growth_pct",
                "investor_growth_pct",
                "allocation_drift",
                "dominant_asset",
            ]
        ].copy()
        display_df.columns = [
            "Fon",
            "Fon Adi",
            "Signal Score",
            "Band",
            "Rejim",
            "Portfoy Buyume %",
            "Yatirimci Buyume %",
            "Allocation Drift",
            "Baskin Varlik",
        ]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.caption(
        f"Son guncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        "Bu launchpad mevcut TEFAS modullerini bozmadan hizli TR fon karar katmani ekler."
    )
