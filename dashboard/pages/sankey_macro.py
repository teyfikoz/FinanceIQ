"""
Macro Liquidity Sankey Page
Visualize macro liquidity flows from sources to risk assets.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.analytics.sankey_transform import macro_to_sankey
from dashboard.components.charts_sankey import plot_macro_sankey
from dashboard.components.kpis import kpi_row
import logging

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Macro Liquidity Sankey",
    page_icon="🌍",
    layout="wide"
)

# Title
st.title("🌍 Macro Liquidity Flow Sankey")
st.markdown("Visualize global liquidity flows from sources to risk assets")

# Sidebar controls
st.sidebar.header("⚙️ Liquidity Sources")

use_m2 = st.sidebar.checkbox("Include M2", value=True)
m2_weight = st.sidebar.slider("M2 Weight", 0, 100, 40, 5) if use_m2 else 0

use_cb = st.sidebar.checkbox("Include Central Bank Balance Sheets", value=True)
cb_weight = st.sidebar.slider("CB Balance Weight", 0, 100, 35, 5) if use_cb else 0

use_gli = st.sidebar.checkbox("Include Global Liquidity Index", value=True)
gli_weight = st.sidebar.slider("GLI Weight", 0, 100, 25, 5) if use_gli else 0

st.sidebar.divider()
st.sidebar.header("🎯 Asset Allocations")

equities_alloc = st.sidebar.slider("Equities Allocation", 0, 100, 50, 5)
btc_alloc = st.sidebar.slider("Bitcoin Allocation", 0, 100, 30, 5)
gold_alloc = st.sidebar.slider("Gold Allocation", 0, 100, 20, 5)

# Main content
try:
    # Build liquidity sources
    liquidity_sources = {}

    if use_m2 and m2_weight > 0:
        liquidity_sources['M2 Money Supply'] = m2_weight

    if use_cb and cb_weight > 0:
        liquidity_sources['Central Bank Balance'] = cb_weight

    if use_gli and gli_weight > 0:
        liquidity_sources['Global Liquidity Index'] = gli_weight

    # Build asset allocations
    asset_allocations = {}

    if equities_alloc > 0:
        asset_allocations['Equities'] = equities_alloc

    if btc_alloc > 0:
        asset_allocations['Bitcoin'] = btc_alloc

    if gold_alloc > 0:
        asset_allocations['Gold'] = gold_alloc

    # Validate
    if not liquidity_sources:
        st.warning("⚠️ Please select at least one liquidity source")
        st.stop()

    if not asset_allocations:
        st.warning("⚠️ Please set at least one asset allocation > 0")
        st.stop()

    # Calculate totals
    total_liquidity = sum(liquidity_sources.values())
    total_allocation = sum(asset_allocations.values())

    # KPIs
    st.subheader("📊 Liquidity Overview")

    kpis_data = [
        {
            'label': 'Total Liquidity Score',
            'value': total_liquidity,
            'format_type': 'number',
            'help': 'Weighted sum of liquidity sources'
        },
        {
            'label': 'Total Asset Allocation',
            'value': total_allocation,
            'format_type': 'number',
            'help': 'Sum of all asset allocations'
        },
        {
            'label': 'Sources Active',
            'value': len(liquidity_sources),
            'format_type': 'number',
            'help': 'Number of liquidity sources enabled'
        },
        {
            'label': 'Asset Classes',
            'value': len(asset_allocations),
            'format_type': 'number',
            'help': 'Number of asset classes tracked'
        }
    ]

    kpi_row(kpis_data, columns=4)

    st.divider()

    # Transform to Sankey
    sankey_data = macro_to_sankey(liquidity_sources, asset_allocations)

    if 'error' in sankey_data.get('meta', {}):
        st.error(f"❌ {sankey_data['meta']['error']}")
        st.stop()

    # Sankey Chart
    st.subheader("🌊 Liquidity Flow Visualization")

    fig = plot_macro_sankey(
        sankey_data,
        title="Global Liquidity → Risk Assets"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Breakdown tables
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Liquidity Sources")

        sources_list = []
        for source, weight in liquidity_sources.items():
            pct = (weight / total_liquidity * 100) if total_liquidity > 0 else 0
            sources_list.append({
                'Source': source,
                'Weight': weight,
                'Percentage': f"{pct:.1f}%"
            })

        import pandas as pd
        sources_df = pd.DataFrame(sources_list)
        st.dataframe(sources_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("🎯 Asset Allocations")

        assets_list = []
        for asset, alloc in asset_allocations.items():
            pct = (alloc / total_allocation * 100) if total_allocation > 0 else 0
            assets_list.append({
                'Asset': asset,
                'Allocation': alloc,
                'Percentage': f"{pct:.1f}%"
            })

        assets_df = pd.DataFrame(assets_list)
        st.dataframe(assets_df, use_container_width=True, hide_index=True)

    # Insights
    st.divider()
    st.subheader("💡 Insights")

    insights = []

    # Dominant liquidity source
    if liquidity_sources:
        dominant_source = max(liquidity_sources.items(), key=lambda x: x[1])
        insights.append(f"📌 **Dominant Liquidity Source**: {dominant_source[0]} ({dominant_source[1]} weight)")

    # Dominant asset
    if asset_allocations:
        dominant_asset = max(asset_allocations.items(), key=lambda x: x[1])
        insights.append(f"📌 **Highest Asset Allocation**: {dominant_asset[0]} ({dominant_asset[1]}% allocation)")

    # Balance check
    if abs(total_liquidity - total_allocation) > 10:
        insights.append(f"⚠️ **Imbalance Detected**: Liquidity sources ({total_liquidity}) and asset allocations ({total_allocation}) differ significantly")

    for insight in insights:
        st.markdown(insight)

    # Educational info
    with st.expander("ℹ️ About Macro Liquidity"):
        st.markdown("""
        ### What is Macro Liquidity?

        Macro liquidity refers to the total amount of money available in the financial system. Key sources include:

        - **M2 Money Supply**: Broad measure of money supply (cash, deposits, money market funds)
        - **Central Bank Balance Sheets**: Assets held by central banks (Fed, ECB, BoJ, PBoC)
        - **Global Liquidity Index**: Composite measure of worldwide liquidity conditions

        ### How it Affects Markets

        When macro liquidity increases:
        - ✅ Risk assets (stocks, crypto, commodities) tend to rise
        - ✅ More capital available for investment
        - ⚠️ Potential inflation concerns

        When macro liquidity decreases:
        - ❌ Risk assets may decline
        - ❌ Tighter financial conditions
        - ✅ Currency strength may improve

        ### Correlation with Assets

        - **Equities**: High positive correlation (0.6-0.8)
        - **Bitcoin**: Very high correlation (0.7-0.9)
        - **Gold**: Moderate correlation (0.4-0.6)
        """)

except Exception as e:
    logger.error(f"Error in Macro Liquidity Sankey page: {e}", exc_info=True)
    st.error(f"❌ An error occurred: {str(e)}")
    st.info("Please adjust your settings and try again.")

# Footer
st.divider()
st.caption("💡 This is a visualization tool showing normalized liquidity flows | Adjust weights to see different scenarios")
