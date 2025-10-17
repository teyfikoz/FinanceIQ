"""
Fund Holdings Sankey Page
Visualize fund holdings (Fund → Stocks) and stock ownership (Stock → Funds).
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.data_collectors.holdings_collector_ext import get_fund_holdings, get_stock_in_funds
from app.analytics.sankey_transform import fund_to_sankey, stock_to_funds_sankey
from app.analytics.sanity_checks import check_fund_holdings_balance
from dashboard.components.charts_sankey import plot_fund_sankey
from dashboard.components.kpis import kpi_row
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Fund Holdings Sankey",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Fund Holdings & Ownership Sankey")
st.markdown("Visualize ETF/Fund holdings and stock ownership patterns")

# Tabs
tab1, tab2 = st.tabs(["🏢 Fund → Stocks", "📈 Stock → Funds"])

# ============================================================================
# TAB 1: Fund → Stocks
# ============================================================================
with tab1:
    st.header("Fund Holdings Breakdown")

    # Sidebar for Fund → Stocks
    col1, col2 = st.columns([2, 1])

    with col1:
        fund_symbol = st.text_input(
            "Fund/ETF Symbol",
            value="SPY",
            key="fund_input",
            help="Enter fund ticker (e.g., SPY, QQQ, VOO, ARKK)"
        ).upper()

    with col2:
        top_n = st.number_input(
            "Top N Holdings",
            min_value=5,
            max_value=50,
            value=10,
            step=5,
            key="top_n_input"
        )

    if st.button("🔄 Refresh Fund Data", key="refresh_fund"):
        st.cache_data.clear()
        st.rerun()


    @st.cache_data(ttl=43200)  # 12 hours
    def load_fund_holdings(fund: str, top: int):
        """Load fund holdings with caching."""
        return get_fund_holdings(fund, top)


    try:
        with st.spinner(f"Loading holdings for {fund_symbol}..."):
            holdings = load_fund_holdings(fund_symbol, top_n)

            if not holdings:
                st.error(f"❌ No holdings data found for {fund_symbol}")
                st.info("💡 Try popular ETFs: SPY, QQQ, VOO, ARKK, VT, IWM, VTI")
                st.stop()

            # Transform to Sankey
            sankey_data = fund_to_sankey(fund_symbol, holdings)
            meta = sankey_data.get('meta', {})

            # KPIs
            is_balanced, total_weight = check_fund_holdings_balance(holdings)

            top3_holdings = sorted(holdings, key=lambda x: x.get('weight', 0), reverse=True)[:3]
            top3_concentration = sum(h.get('weight', 0) for h in top3_holdings)

            kpis_data = [
                {
                    'label': 'Total Holdings Shown',
                    'value': len(holdings),
                    'format_type': 'number',
                    'help': f'Top {top_n} holdings displayed'
                },
                {
                    'label': 'Total Weight',
                    'value': total_weight,
                    'format_type': 'percent',
                    'help': 'Sum of displayed holdings weights'
                },
                {
                    'label': 'Top 3 Concentration',
                    'value': top3_concentration,
                    'format_type': 'percent',
                    'help': 'Weight of top 3 holdings'
                }
            ]

            kpi_row(kpis_data, columns=3)

            st.divider()

            # Sankey Chart
            st.subheader(f"📊 {fund_symbol} Holdings Flow")

            fig = plot_fund_sankey(
                sankey_data,
                title=f"{fund_symbol} → Top {len(holdings)} Holdings"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Holdings table
            st.divider()
            st.subheader("📋 Holdings Details")

            holdings_df = pd.DataFrame(holdings)
            if not holdings_df.empty:
                holdings_df['weight'] = holdings_df['weight'].apply(lambda x: f"{x:.2f}%")
                holdings_df.columns = ['Symbol', 'Weight', 'Name']
                st.dataframe(holdings_df, use_container_width=True, hide_index=True)

    except Exception as e:
        logger.error(f"Error in Fund → Stocks tab: {e}", exc_info=True)
        st.error(f"❌ An error occurred: {str(e)}")

# ============================================================================
# TAB 2: Stock → Funds
# ============================================================================
with tab2:
    st.header("Stock Ownership by Funds")

    # Inputs
    col1, col2 = st.columns([2, 1])

    with col1:
        stock_symbol = st.text_input(
            "Stock Symbol",
            value="AAPL",
            key="stock_input",
            help="Enter stock ticker to see which funds hold it"
        ).upper()

    preset_funds = ['SPY', 'QQQ', 'VOO', 'ARKK', 'VT', 'IWM', 'VTI', 'VUG', 'VTV', 'DIA']

    fund_list = st.multiselect(
        "Select Funds to Check",
        options=preset_funds,
        default=['SPY', 'QQQ', 'VOO', 'ARKK'],
        key="fund_list_input",
        help="Select which funds to check for ownership"
    )

    if st.button("🔄 Refresh Stock Data", key="refresh_stock"):
        st.cache_data.clear()
        st.rerun()


    @st.cache_data(ttl=43200)  # 12 hours
    def load_stock_ownership(stock: str, funds: list):
        """Load stock ownership with caching."""
        return get_stock_in_funds(stock, funds)


    try:
        if not fund_list:
            st.warning("⚠️ Please select at least one fund to check")
            st.stop()

        with st.spinner(f"Analyzing {stock_symbol} ownership..."):
            ownership = load_stock_ownership(stock_symbol, fund_list)

            if not ownership:
                st.warning(f"⚠️ {stock_symbol} is not held by any of the selected funds (or weight < 0.1%)")
                st.info(f"💡 {stock_symbol} might be held in small quantities or not tracked in our data")
                st.stop()

            # Transform to Sankey
            sankey_data = stock_to_funds_sankey(stock_symbol, ownership)
            meta = sankey_data.get('meta', {})

            # KPIs
            weights = [o['weight'] for o in ownership]
            avg_weight = sum(weights) / len(weights) if weights else 0
            max_weight = max(weights) if weights else 0

            kpis_data = [
                {
                    'label': 'Funds Holding',
                    'value': len(ownership),
                    'format_type': 'number',
                    'help': f'Number of funds holding {stock_symbol}'
                },
                {
                    'label': 'Max Weight',
                    'value': max_weight,
                    'format_type': 'percent',
                    'help': 'Highest weight in any fund'
                },
                {
                    'label': 'Avg Weight',
                    'value': avg_weight,
                    'format_type': 'percent',
                    'help': 'Average weight across funds'
                }
            ]

            kpi_row(kpis_data, columns=3)

            st.divider()

            # Sankey Chart
            st.subheader(f"📊 {stock_symbol} Ownership Distribution")

            fig = plot_fund_sankey(
                sankey_data,
                title=f"{stock_symbol} → Funds"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Ownership table
            st.divider()
            st.subheader("📋 Ownership Details")

            ownership_df = pd.DataFrame(ownership)
            if not ownership_df.empty:
                ownership_df['weight'] = ownership_df['weight'].apply(lambda x: f"{x:.2f}%")
                ownership_df.columns = ['Fund', 'Weight']
                st.dataframe(ownership_df, use_container_width=True, hide_index=True)

    except Exception as e:
        logger.error(f"Error in Stock → Funds tab: {e}", exc_info=True)
        st.error(f"❌ An error occurred: {str(e)}")

# Footer
st.divider()
st.caption("💡 Data sources: Yahoo Finance, ETF providers | Cached for performance | Some data is simulated for demonstration")
