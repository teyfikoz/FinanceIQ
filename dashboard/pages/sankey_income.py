"""
Income Statement Sankey Page
Visualize income statement flow from revenue to net income.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.data_collectors.fundamentals_collector import get_income_statement, get_company_name
from app.analytics.sankey_transform import income_to_sankey
from app.analytics.sanity_checks import assert_balanced_income
from dashboard.components.charts_sankey import plot_income_sankey
from dashboard.components.kpis import kpi_row, metrics_table
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Income Statement Sankey",
    page_icon="💰",
    layout="wide"
)

# Title
st.title("💰 Income Statement Sankey")
st.markdown("Visualize financial flows from revenue to net income")

# Sidebar controls
st.sidebar.header("⚙️ Settings")

ticker = st.sidebar.text_input(
    "Ticker Symbol",
    value="AAPL",
    help="Enter stock ticker (e.g., AAPL, MSFT, GOOGL)"
).upper()

period = st.sidebar.selectbox(
    "Period",
    options=["annual", "quarterly"],
    index=0
)

limit = 4
show_yoy = st.sidebar.checkbox("Show YoY Changes", value=True)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()


@st.cache_data(ttl=3600)
def load_income_statement(ticker: str, period: str, limit: int):
    """Load income statement data with caching."""
    return get_income_statement(ticker, period, limit)


@st.cache_data(ttl=86400)
def load_company_name(ticker: str):
    """Load company name with caching."""
    return get_company_name(ticker)


# Main content
try:
    with st.spinner(f"Loading financial data for {ticker}..."):
        # Load data
        df = load_income_statement(ticker, period, limit)
        company_name = load_company_name(ticker)

        if df.empty:
            st.error(f"❌ No financial data found for {ticker}. Please check the ticker symbol and try again.")
            st.info("💡 Try common tickers like: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA")
            st.stop()

        # Select fiscal period
        if len(df) > 1:
            period_options = [f"{row['period_end']}" for _, row in df.iterrows()]
            selected_period_idx = st.sidebar.selectbox(
                "Select Period",
                options=range(len(period_options)),
                format_func=lambda x: period_options[x],
                index=0
            )
        else:
            selected_period_idx = 0

        # Transform to Sankey
        sankey_data = income_to_sankey(df, fiscal_index=selected_period_idx)

        if 'error' in sankey_data.get('meta', {}):
            st.error(f"❌ {sankey_data['meta']['error']}")
            st.stop()

        meta = sankey_data.get('meta', {})

        # Header KPIs
        st.subheader(f"{company_name} ({ticker})")

        kpis_data = [
            {
                'label': 'Revenue',
                'value': meta.get('revenue', 0),
                'delta': meta.get('yoy_revenue') if show_yoy else None,
                'format_type': 'currency',
                'help': 'Total revenue for the period'
            },
            {
                'label': 'Gross Margin',
                'value': meta.get('gross_margin', 0),
                'format_type': 'percent',
                'help': 'Gross Profit / Revenue'
            },
            {
                'label': 'Operating Margin',
                'value': meta.get('op_margin', 0),
                'format_type': 'percent',
                'help': 'Operating Income / Revenue'
            },
            {
                'label': 'Net Margin',
                'value': meta.get('net_margin', 0),
                'delta': meta.get('yoy_net_income') if show_yoy else None,
                'format_type': 'percent',
                'help': 'Net Income / Revenue'
            }
        ]

        kpi_row(kpis_data, columns=4)

        st.divider()

        # Main Sankey Chart
        st.subheader("📊 Income Statement Flow")

        fig = plot_income_sankey(
            sankey_data,
            title=f"{company_name} Income Statement ({meta.get('period_end', 'N/A')})"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Sanity check warnings
        row = df.iloc[selected_period_idx]
        revenue = abs(float(row.get('revenue', 0)))
        cost_of_revenue = abs(float(row.get('cost_of_revenue', 0)))
        gross_profit = abs(float(row.get('gross_profit', 0)))
        operating_income = abs(float(row.get('operating_income', 0)))
        rd_expense = abs(float(row.get('rd_expense', 0)))
        sga_expense = abs(float(row.get('sga_expense', 0)))
        other_operating_expense = abs(float(row.get('other_operating_expense', 0)))
        total_opex = rd_expense + sga_expense + other_operating_expense
        net_income = abs(float(row.get('net_income', 0)))
        tax_expense = abs(float(row.get('tax_expense', 0)))
        interest_expense = abs(float(row.get('interest_expense', 0)))

        is_valid, warnings = assert_balanced_income(
            revenue, cost_of_revenue, gross_profit, operating_income,
            total_opex, net_income, tax_expense, interest_expense
        )

        if warnings:
            with st.expander("⚠️ Data Quality Warnings"):
                for warning in warnings:
                    st.warning(warning)

        # Detailed metrics table
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Detailed Metrics")

            metrics_data = {
                'Revenue': f"${revenue:,.0f}",
                'Cost of Revenue': f"${cost_of_revenue:,.0f}",
                'Gross Profit': f"${gross_profit:,.0f}",
                'Operating Income': f"${operating_income:,.0f}",
                'Net Income': f"${net_income:,.0f}",
            }

            metrics_table(metrics_data)

        with col2:
            st.subheader("💼 Operating Expenses")

            opex_data = {
                'R&D Expense': f"${rd_expense:,.0f}" if rd_expense > 0 else "N/A",
                'SG&A Expense': f"${sga_expense:,.0f}" if sga_expense > 0 else "N/A",
                'Other OpEx': f"${other_operating_expense:,.0f}" if other_operating_expense > 0 else "N/A",
                'Tax Expense': f"${tax_expense:,.0f}" if tax_expense > 0 else "N/A",
                'Interest Expense': f"${interest_expense:,.0f}" if interest_expense > 0 else "N/A",
            }

            metrics_table(opex_data)

        # Historical data
        if len(df) > 1:
            st.divider()
            st.subheader("📅 Historical Summary")

            historical_df = df[['period_end', 'revenue', 'gross_profit', 'operating_income', 'net_income']].copy()
            historical_df.columns = ['Period', 'Revenue', 'Gross Profit', 'Operating Income', 'Net Income']

            # Format numbers
            for col in ['Revenue', 'Gross Profit', 'Operating Income', 'Net Income']:
                historical_df[col] = historical_df[col].apply(lambda x: f"${x:,.0f}")

            st.dataframe(historical_df, use_container_width=True, hide_index=True)

except Exception as e:
    logger.error(f"Error in Income Sankey page: {e}", exc_info=True)
    st.error(f"❌ An error occurred: {str(e)}")
    st.info("Please try again or contact support if the issue persists.")

# Footer
st.divider()
st.caption("💡 Data sources: FMP, Alpha Vantage, Yahoo Finance | Cached for performance")
