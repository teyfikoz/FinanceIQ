"""
Fintables-Style Fund Holdings Analysis Dashboard
Modern, temiz ve okunabilir fon analiz sayfası
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from pathlib import Path
import yfinance as yf
from datetime import datetime, timedelta
import time

# Path setup
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Fund Holdings Analysis",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern CSS styling - Fintables inspired
st.markdown("""
<style>
    /* Global styling */
    .main {
        padding-top: 2rem;
    }

    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }

    /* Card styling */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid #e1e5e9;
        margin: 0.5rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 5px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 8px;
        color: #495057;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: #667eea !important;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #e1e5e9;
    }

    /* DataFrame styling */
    .dataframe {
        border-radius: 8px;
        border: 1px solid #e1e5e9;
        overflow: hidden;
    }

    /* Search box styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #e1e5e9;
        padding: 0.5rem 1rem;
    }

    /* Section headers */
    .section-header {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }

    /* Fund item styling */
    .fund-item {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #e1e5e9;
        transition: all 0.2s ease;
    }

    .fund-item:hover {
        border-color: #667eea;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.1);
    }

    /* Stock item styling */
    .stock-item {
        background: linear-gradient(45deg, #f8f9fa, #ffffff);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #28a745;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive design */
    @media (max-width: 768px) {
        .metric-card {
            padding: 1rem;
        }
        .header-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Sample ETF holdings data (Real data would come from API)
SAMPLE_ETF_HOLDINGS = {
    "SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "total_assets": 430000000000,
        "expense_ratio": 0.0945,
        "holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "weight": 7.2, "shares": 185000000, "sector": "Technology"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "weight": 6.8, "shares": 95000000, "sector": "Technology"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "weight": 3.4, "shares": 12000000, "sector": "Consumer Discretionary"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "weight": 3.1, "shares": 8500000, "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "weight": 2.9, "shares": 9200000, "sector": "Communication"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "weight": 2.5, "shares": 4800000, "sector": "Consumer Discretionary"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "weight": 2.3, "shares": 6100000, "sector": "Communication"},
            {"symbol": "GOOG", "name": "Alphabet Inc. Class C", "weight": 2.2, "shares": 8900000, "sector": "Communication"},
            {"symbol": "BRK.B", "name": "Berkshire Hathaway Inc.", "weight": 1.8, "shares": 15200000, "sector": "Financial"},
            {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "weight": 1.5, "shares": 2100000, "sector": "Healthcare"}
        ]
    },
    "QQQ": {
        "name": "Invesco QQQ Trust",
        "total_assets": 220000000000,
        "expense_ratio": 0.20,
        "holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "weight": 12.1, "shares": 95000000, "sector": "Technology"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "weight": 11.2, "shares": 48000000, "sector": "Technology"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "weight": 5.8, "shares": 6200000, "sector": "Consumer Discretionary"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "weight": 5.2, "shares": 4300000, "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "weight": 4.9, "shares": 4800000, "sector": "Communication"},
            {"symbol": "GOOG", "name": "Alphabet Inc. Class C", "weight": 4.7, "shares": 4600000, "sector": "Communication"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "weight": 3.9, "shares": 3100000, "sector": "Communication"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "weight": 3.7, "shares": 2300000, "sector": "Consumer Discretionary"},
            {"symbol": "AVGO", "name": "Broadcom Inc.", "weight": 2.8, "shares": 900000, "sector": "Technology"},
            {"symbol": "COST", "name": "Costco Wholesale Corporation", "weight": 2.2, "shares": 800000, "sector": "Consumer Staples"}
        ]
    },
    "VTI": {
        "name": "Vanguard Total Stock Market ETF",
        "total_assets": 350000000000,
        "expense_ratio": 0.03,
        "holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "weight": 7.0, "shares": 180000000, "sector": "Technology"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "weight": 6.5, "shares": 92000000, "sector": "Technology"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "weight": 3.2, "shares": 11500000, "sector": "Consumer Discretionary"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "weight": 3.0, "shares": 8200000, "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "weight": 2.8, "shares": 8800000, "sector": "Communication"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "weight": 2.4, "shares": 4600000, "sector": "Consumer Discretionary"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "weight": 2.2, "shares": 5900000, "sector": "Communication"},
            {"symbol": "GOOG", "name": "Alphabet Inc. Class C", "weight": 2.1, "shares": 8500000, "sector": "Communication"},
            {"symbol": "BRK.B", "name": "Berkshire Hathaway Inc.", "weight": 1.7, "shares": 14800000, "sector": "Financial"},
            {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "weight": 1.4, "shares": 2000000, "sector": "Healthcare"}
        ]
    }
}

def get_stock_in_funds_data(stock_symbol):
    """Get data about which funds contain a specific stock"""
    stock_data = []

    for fund_symbol, fund_data in SAMPLE_ETF_HOLDINGS.items():
        for holding in fund_data["holdings"]:
            if holding["symbol"] == stock_symbol:
                stock_data.append({
                    "fund_symbol": fund_symbol,
                    "fund_name": fund_data["name"],
                    "weight": holding["weight"],
                    "shares": holding["shares"],
                    "fund_assets": fund_data["total_assets"],
                    "expense_ratio": fund_data["expense_ratio"]
                })

    return stock_data

def create_holdings_chart(fund_data, chart_type="pie"):
    """Create fund holdings visualization"""
    holdings = fund_data["holdings"]

    if chart_type == "pie":
        # Top 10 + Others
        top_holdings = holdings[:8]
        others_weight = sum([h["weight"] for h in holdings[8:]])

        if others_weight > 0:
            top_holdings.append({"symbol": "Others", "weight": others_weight})

        df = pd.DataFrame(top_holdings)

        fig = px.pie(
            df,
            values='weight',
            names='symbol',
            title=f"{fund_data['name']} Holdings Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Weight: %{value:.1f}%<extra></extra>'
        )
        fig.update_layout(
            font=dict(size=12),
            showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01),
            margin=dict(l=20, r=120, t=60, b=20)
        )

    else:  # bar chart
        df = pd.DataFrame(holdings[:10])
        fig = px.bar(
            df,
            x='weight',
            y='symbol',
            orientation='h',
            title=f"{fund_data['name']} Top 10 Holdings",
            color='weight',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="Weight (%)",
            yaxis_title="",
            margin=dict(l=80, r=20, t=60, b=20)
        )

    return fig

def create_stock_funds_chart(stock_symbol, stock_data):
    """Create chart showing stock weight across different funds"""
    if not stock_data:
        return None

    df = pd.DataFrame(stock_data)

    fig = go.Figure()

    colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']

    for i, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[row['weight']],
            y=[row['fund_symbol']],
            orientation='h',
            name=row['fund_symbol'],
            marker_color=colors[i % len(colors)],
            text=[f"{row['weight']:.2f}%"],
            textposition='auto',
            hovertemplate=f'<b>{row["fund_name"]}</b><br>Weight: {row["weight"]:.2f}%<br>Shares: {row["shares"]:,}<extra></extra>'
        ))

    fig.update_layout(
        title=f"{stock_symbol} Weight Across Funds",
        xaxis_title="Weight (%)",
        yaxis_title="Fund",
        showlegend=False,
        margin=dict(l=80, r=20, t=60, b=40),
        height=300 + len(df) * 30
    )

    return fig

def main():
    # Header
    st.markdown("""
    <div class="header-container">
        <h1>💼 Fund Holdings Analysis</h1>
        <p style="font-size: 1.2rem; opacity: 0.9;">Modern ETF & Fund Portfolio Analysis Platform</p>
        <p style="font-size: 1rem; opacity: 0.8;">Analyze fund compositions and discover which funds hold your favorite stocks</p>
    </div>
    """, unsafe_allow_html=True)

    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "🏢 Fund → Holdings Analysis",
        "📈 Stock → Funds Analysis",
        "📊 Portfolio Comparison"
    ])

    with tab1:
        st.markdown('<div class="section-header"><h3>🏢 Fund Holdings Analysis</h3><p>Analyze ETF and fund compositions in detail</p></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])

        with col1:
            # Fund selection
            st.markdown("### Select Fund")

            available_funds = list(SAMPLE_ETF_HOLDINGS.keys())
            fund_names = [SAMPLE_ETF_HOLDINGS[f]["name"] for f in available_funds]

            selected_fund_name = st.selectbox(
                "Choose a fund to analyze:",
                fund_names,
                key="fund_selector"
            )

            # Get selected fund symbol
            selected_fund = None
            for symbol, data in SAMPLE_ETF_HOLDINGS.items():
                if data["name"] == selected_fund_name:
                    selected_fund = symbol
                    break

            if selected_fund:
                fund_data = SAMPLE_ETF_HOLDINGS[selected_fund]

                # Fund overview cards
                st.markdown("### Fund Overview")

                # Metrics cards
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: #667eea; margin: 0;">Total Assets</h4>
                        <h2 style="margin: 5px 0;">${fund_data['total_assets']/1e9:.1f}B</h2>
                    </div>
                    """, unsafe_allow_html=True)

                with col_b:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: #764ba2; margin: 0;">Expense Ratio</h4>
                        <h2 style="margin: 5px 0;">{fund_data['expense_ratio']:.2f}%</h2>
                    </div>
                    """, unsafe_allow_html=True)

                # Holdings summary
                st.markdown("### Holdings Summary")
                top_10_weight = sum([h["weight"] for h in fund_data["holdings"][:10]])

                col_c, col_d = st.columns(2)

                with col_c:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: #28a745; margin: 0;">Total Holdings</h4>
                        <h2 style="margin: 5px 0;">{len(fund_data['holdings'])}+</h2>
                    </div>
                    """, unsafe_allow_html=True)

                with col_d:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: #ffc107; margin: 0;">Top 10 Weight</h4>
                        <h2 style="margin: 5px 0;">{top_10_weight:.1f}%</h2>
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            if selected_fund:
                # Chart type selection
                chart_type = st.radio("Chart Type:", ["Pie Chart", "Bar Chart"], horizontal=True)

                # Create and display chart
                chart = create_holdings_chart(
                    fund_data,
                    "pie" if chart_type == "Pie Chart" else "bar"
                )
                st.plotly_chart(chart, use_container_width=True)

                # Holdings table
                st.markdown("### Detailed Holdings")

                holdings_df = pd.DataFrame(fund_data["holdings"])
                holdings_df = holdings_df.rename(columns={
                    'symbol': 'Symbol',
                    'name': 'Company Name',
                    'weight': 'Weight (%)',
                    'shares': 'Shares',
                    'sector': 'Sector'
                })

                # Format the dataframe
                holdings_df['Weight (%)'] = holdings_df['Weight (%)'].apply(lambda x: f"{x:.2f}%")
                holdings_df['Shares'] = holdings_df['Shares'].apply(lambda x: f"{x:,}")

                st.dataframe(
                    holdings_df,
                    use_container_width=True,
                    hide_index=True
                )

    with tab2:
        st.markdown('<div class="section-header"><h3>📈 Stock in Funds Analysis</h3><p>Discover which funds hold your favorite stocks</p></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])

        with col1:
            # Stock selection
            st.markdown("### Select Stock")

            # Get all unique stocks from all funds
            all_stocks = set()
            for fund_data in SAMPLE_ETF_HOLDINGS.values():
                for holding in fund_data["holdings"]:
                    all_stocks.add(holding["symbol"])

            all_stocks = sorted(list(all_stocks))

            selected_stock = st.selectbox(
                "Choose a stock to analyze:",
                all_stocks,
                key="stock_selector"
            )

            # Search functionality
            stock_search = st.text_input("🔍 Search for a stock:", placeholder="e.g., AAPL, MSFT, AMZN")

            if stock_search and stock_search.upper() in all_stocks:
                selected_stock = stock_search.upper()

            if selected_stock:
                # Get stock data
                stock_data = get_stock_in_funds_data(selected_stock)

                if stock_data:
                    st.markdown("### Stock Overview")

                    # Calculate metrics
                    total_funds = len(stock_data)
                    max_weight = max([d["weight"] for d in stock_data])
                    avg_weight = sum([d["weight"] for d in stock_data]) / len(stock_data)

                    # Metrics cards
                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="color: #667eea; margin: 0;">Found in Funds</h4>
                            <h2 style="margin: 5px 0;">{total_funds}</h2>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_b:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="color: #764ba2; margin: 0;">Max Weight</h4>
                            <h2 style="margin: 5px 0;">{max_weight:.2f}%</h2>
                        </div>
                        """, unsafe_allow_html=True)

                    col_c, col_d = st.columns(2)

                    with col_c:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="color: #28a745; margin: 0;">Avg Weight</h4>
                            <h2 style="margin: 5px 0;">{avg_weight:.2f}%</h2>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_d:
                        total_value = sum([d["weight"] * d["fund_assets"] / 100 for d in stock_data])
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="color: #ffc107; margin: 0;">Est. Total Value</h4>
                            <h2 style="margin: 5px 0;">${total_value/1e9:.1f}B</h2>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning(f"Stock {selected_stock} not found in any of the analyzed funds.")

        with col2:
            if selected_stock and stock_data:
                # Create chart
                chart = create_stock_funds_chart(selected_stock, stock_data)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)

                # Stock in funds table
                st.markdown("### Fund Details")

                df = pd.DataFrame(stock_data)
                df = df.rename(columns={
                    'fund_symbol': 'Fund Symbol',
                    'fund_name': 'Fund Name',
                    'weight': 'Weight (%)',
                    'shares': 'Shares Held',
                    'fund_assets': 'Fund Assets',
                    'expense_ratio': 'Expense Ratio (%)'
                })

                # Format the dataframe
                df['Weight (%)'] = df['Weight (%)'].apply(lambda x: f"{x:.2f}%")
                df['Shares Held'] = df['Shares Held'].apply(lambda x: f"{x:,}")
                df['Fund Assets'] = df['Fund Assets'].apply(lambda x: f"${x/1e9:.1f}B")
                df['Expense Ratio (%)'] = df['Expense Ratio (%)'].apply(lambda x: f"{x:.2f}%")

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

    with tab3:
        st.markdown('<div class="section-header"><h3>📊 Portfolio Comparison</h3><p>Compare multiple funds side by side</p></div>', unsafe_allow_html=True)

        # Multi-fund selection
        selected_funds = st.multiselect(
            "Select funds to compare:",
            options=list(SAMPLE_ETF_HOLDINGS.keys()),
            default=["SPY", "QQQ"],
            format_func=lambda x: f"{x} - {SAMPLE_ETF_HOLDINGS[x]['name']}"
        )

        if len(selected_funds) >= 2:
            # Comparison metrics
            st.markdown("### Fund Comparison")

            cols = st.columns(len(selected_funds))

            for i, fund in enumerate(selected_funds):
                fund_data = SAMPLE_ETF_HOLDINGS[fund]

                with cols[i]:
                    st.markdown(f"""
                    <div class="fund-item">
                        <h4 style="color: #667eea; margin: 0 0 10px 0;">{fund}</h4>
                        <p style="font-size: 0.9rem; margin: 5px 0;"><strong>Assets:</strong> ${fund_data['total_assets']/1e9:.1f}B</p>
                        <p style="font-size: 0.9rem; margin: 5px 0;"><strong>Expense:</strong> {fund_data['expense_ratio']:.2f}%</p>
                        <p style="font-size: 0.9rem; margin: 5px 0;"><strong>Holdings:</strong> {len(fund_data['holdings'])}+</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Common holdings analysis
            st.markdown("### Common Holdings Analysis")

            # Find common stocks
            fund_holdings = {}
            for fund in selected_funds:
                fund_holdings[fund] = {h["symbol"]: h["weight"] for h in SAMPLE_ETF_HOLDINGS[fund]["holdings"]}

            all_stocks = set()
            for holdings in fund_holdings.values():
                all_stocks.update(holdings.keys())

            common_data = []
            for stock in all_stocks:
                row = {"Stock": stock}
                total_weight = 0
                funds_count = 0

                for fund in selected_funds:
                    weight = fund_holdings[fund].get(stock, 0)
                    row[f"{fund} Weight (%)"] = f"{weight:.2f}%" if weight > 0 else "-"
                    if weight > 0:
                        total_weight += weight
                        funds_count += 1

                row["Funds Count"] = funds_count
                row["Total Weight"] = f"{total_weight:.2f}%"

                if funds_count > 1:  # Only show stocks that appear in multiple funds
                    common_data.append(row)

            if common_data:
                common_df = pd.DataFrame(common_data)
                common_df = common_df.sort_values("Funds Count", ascending=False)

                st.dataframe(
                    common_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No common holdings found between selected funds.")

        else:
            st.info("Please select at least 2 funds to compare.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
        💼 Fund Holdings Analysis Platform | Modern Portfolio Analytics<br>
        <small>Data is for demonstration purposes. Use real-time data for actual investment decisions.</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()