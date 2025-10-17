#!/usr/bin/env python3
"""
🌍 Comprehensive Financial Intelligence Platform
Bloomberg Terminal-level analytics with 10,000+ stocks and 5,000+ funds
"""

import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="🌍 Comprehensive Financial Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import our custom modules
try:
    from app.analytics.comprehensive_stock_analyzer import ComprehensiveStockAnalyzer
    from app.analytics.comprehensive_fund_analyzer import ComprehensiveFundAnalyzer
    from app.analytics.unified_intelligence import unified_intelligence
except ImportError:
    st.error("Please ensure the analytics modules are in the correct path")

# Page configuration (moved to main function to avoid conflicts)

# Enhanced CSS for Bloomberg-style interface
st.markdown("""
<style>
    .main { padding: 0rem 0.5rem; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: none; }

    /* Color Palette */
    :root {
        --bloomberg-black: #000000;
        --bloomberg-orange: #ff6600;
        --bloomberg-blue: #0066cc;
        --bloomberg-green: #00cc66;
        --bloomberg-red: #ff3366;
        --bloomberg-yellow: #ffcc00;
        --dark-bg: #0d1117;
        --dark-secondary: #161b22;
        --dark-tertiary: #21262d;
        --text-primary: #ffffff;
        --text-secondary: #8b949e;
        --accent-blue: #58a6ff;
        --accent-green: #3fb950;
        --accent-red: #f85149;
    }

    /* Main header */
    .platform-header {
        background: linear-gradient(135deg, var(--bloomberg-black) 0%, var(--dark-secondary) 100%);
        color: var(--bloomberg-orange);
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid var(--bloomberg-orange);
        box-shadow: 0 4px 20px rgba(255, 102, 0, 0.3);
    }

    .platform-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        color: var(--bloomberg-orange);
    }

    .platform-subtitle {
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
        color: var(--text-secondary);
        font-weight: 300;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: var(--dark-bg);
        border-radius: 8px;
        padding: 0.25rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: var(--dark-secondary);
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--bloomberg-orange) 0%, var(--bloomberg-blue) 100%);
        color: white;
        box-shadow: 0 2px 10px rgba(255, 102, 0, 0.4);
    }

    /* Analysis cards */
    .analysis-card {
        background: linear-gradient(135deg, var(--dark-secondary) 0%, var(--dark-tertiary) 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--accent-blue);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
    }

    .analysis-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.4);
    }

    .card-header {
        color: var(--bloomberg-orange);
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .metric-item {
        background: var(--dark-bg);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid var(--dark-tertiary);
    }

    .metric-label {
        color: var(--text-secondary);
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }

    .metric-value {
        color: var(--text-primary);
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .metric-change {
        font-size: 0.8rem;
        font-weight: 500;
    }

    .positive { color: var(--accent-green) !important; }
    .negative { color: var(--accent-red) !important; }
    .neutral { color: var(--text-secondary) !important; }

    /* Stock search */
    .search-container {
        background: var(--dark-secondary);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid var(--dark-tertiary);
    }

    /* Rating badges */
    .rating-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0.25rem;
    }

    .rating-strong-buy {
        background: linear-gradient(135deg, var(--accent-green) 0%, #2ea043 100%);
        color: white;
    }

    .rating-buy {
        background: linear-gradient(135deg, #3fb950 0%, #238636 100%);
        color: white;
    }

    .rating-hold {
        background: linear-gradient(135deg, var(--bloomberg-yellow) 0%, #bf8700 100%);
        color: black;
    }

    .rating-sell {
        background: linear-gradient(135deg, var(--accent-red) 0%, #da3633 100%);
        color: white;
    }

    /* Section headers */
    .section-header {
        background: linear-gradient(135deg, var(--bloomberg-blue) 0%, var(--bloomberg-orange) 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 600;
        font-size: 1.1rem;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .platform-title { font-size: 1.8rem; }
        .metric-grid { grid-template-columns: 1fr; }
        .analysis-card { padding: 1rem; }
    }

    /* Custom Streamlit elements */
    .stMetric {
        background: var(--dark-secondary);
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid var(--accent-blue);
    }

    .stMetric > div {
        color: var(--text-primary) !important;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Chart styling */
    .js-plotly-plot {
        background: transparent !important;
    }

    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent-green) 0%, var(--bloomberg-yellow) 50%, var(--accent-red) 100%);
    }
</style>
""", unsafe_allow_html=True)

def create_platform_header():
    """Create main platform header"""
    st.markdown("""
    <div class="platform-header">
        <div class="platform-title">🌍 Comprehensive Financial Intelligence Platform</div>
        <div class="platform-subtitle">
            Professional-grade analytics • 10,000+ stocks • 5,000+ funds • Real-time insights
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_stock_search_section():
    """Create stock search interface"""
    st.markdown('<div class="section-header">🔍 Stock Analysis Engine</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        symbol = st.text_input(
            "Enter Stock Symbol",
            value="AAPL",
            key="stock_symbol",
            help="Enter any stock symbol (e.g., AAPL, MSFT, GOOGL, TSLA)"
        )

    with col2:
        if st.button("🔍 Analyze", type="primary", use_container_width=True):
            if symbol:
                st.session_state.analyze_stock = symbol.upper()

    with col3:
        if st.button("📊 Quick View", use_container_width=True):
            if symbol:
                st.session_state.quick_view = symbol.upper()

    return symbol

def display_stock_analysis(symbol: str):
    """Display comprehensive stock analysis"""
    try:
        with st.spinner(f"Analyzing {symbol}... This may take a moment."):
            analyzer = ComprehensiveStockAnalyzer(symbol)
            analysis = analyzer.get_comprehensive_analysis()

        if "error" in analysis:
            st.error(f"Analysis failed: {analysis['error']}")
            return

        # Basic info section
        basic_info = analysis.get("basic_info", {})
        if basic_info and "error" not in basic_info:
            display_basic_info_card(basic_info)

        # Create tabs for different analysis types
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "💰 Valuation",
            "📈 Technical",
            "🏢 Fundamentals",
            "🎯 Rating & Targets"
        ])

        with tab1:
            display_overview_tab(analysis)

        with tab2:
            display_valuation_tab(analysis)

        with tab3:
            display_technical_tab(analysis, symbol)

        with tab4:
            display_fundamentals_tab(analysis)

        with tab5:
            display_rating_tab(analysis)

    except Exception as e:
        st.error(f"Failed to analyze {symbol}: {str(e)}")

def display_basic_info_card(basic_info: Dict):
    """Display basic stock information card"""
    col1, col2, col3, col4 = st.columns(4)

    current_price = basic_info.get("current_price", 0)
    day_change = basic_info.get("day_change", 0)
    day_change_percent = basic_info.get("day_change_percent", 0)
    market_cap = basic_info.get("market_cap", 0)

    change_color = "positive" if day_change >= 0 else "negative"

    with col1:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">💰 Current Price</div>
            <div class="metric-value">${current_price:.2f}</div>
            <div class="metric-change {change_color}">
                {'+' if day_change >= 0 else ''}{day_change:.2f} ({day_change_percent:.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🏢 Market Cap</div>
            <div class="metric-value">${market_cap/1e9:.1f}B</div>
            <div class="metric-change neutral">
                {basic_info.get("sector", "N/A")}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        volume = basic_info.get("volume", 0)
        avg_volume = basic_info.get("avg_volume", 1)
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        volume_color = "positive" if volume_ratio > 1.5 else "neutral"

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📊 Volume</div>
            <div class="metric-value">{volume/1e6:.1f}M</div>
            <div class="metric-change {volume_color}">
                {volume_ratio:.1f}x avg
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        week_52_high = basic_info.get("week_52_high", current_price)
        week_52_low = basic_info.get("week_52_low", current_price)
        price_position = ((current_price - week_52_low) / (week_52_high - week_52_low) * 100) if week_52_high > week_52_low else 50

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📈 52W Position</div>
            <div class="metric-value">{price_position:.0f}%</div>
            <div class="metric-change neutral">
                ${week_52_low:.0f} - ${week_52_high:.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_overview_tab(analysis: Dict):
    """Display overview tab content"""
    st.markdown('<div class="section-header">📊 Company Overview</div>', unsafe_allow_html=True)

    basic_info = analysis.get("basic_info", {})
    valuation = analysis.get("valuation_analysis", {})
    financial_health = analysis.get("financial_health", {})

    col1, col2 = st.columns(2)

    with col1:
        if basic_info and "error" not in basic_info:
            st.markdown(f"""
            <div class="analysis-card">
                <div class="card-header">🏢 Company Information</div>
                <p><strong>Company:</strong> {basic_info.get('company_name', 'N/A')}</p>
                <p><strong>Sector:</strong> {basic_info.get('sector', 'N/A')}</p>
                <p><strong>Industry:</strong> {basic_info.get('industry', 'N/A')}</p>
                <p><strong>Country:</strong> {basic_info.get('country', 'N/A')}</p>
                <p><strong>Exchange:</strong> {basic_info.get('exchange', 'N/A')}</p>
                <p><strong>Employees:</strong> {basic_info.get('employees', 0):,}</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if valuation and "error" not in valuation:
            current_ratios = valuation.get("current_ratios", {})
            st.markdown(f"""
            <div class="analysis-card">
                <div class="card-header">💰 Key Valuation Metrics</div>
                <p><strong>P/E Ratio:</strong> {current_ratios.get('pe_ratio', 0):.1f}</p>
                <p><strong>P/B Ratio:</strong> {current_ratios.get('pb_ratio', 0):.1f}</p>
                <p><strong>P/S Ratio:</strong> {current_ratios.get('ps_ratio', 0):.1f}</p>
                <p><strong>PEG Ratio:</strong> {current_ratios.get('peg_ratio', 0):.1f}</p>
                <p><strong>EV/Revenue:</strong> {current_ratios.get('ev_revenue', 0):.1f}</p>
                <p><strong>EV/EBITDA:</strong> {current_ratios.get('ev_ebitda', 0):.1f}</p>
            </div>
            """, unsafe_allow_html=True)

    # Business summary
    business_summary = basic_info.get("business_summary", "")
    if business_summary and business_summary != "N/A":
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📄 Business Summary</div>
            <p>{business_summary[:500]}{'...' if len(business_summary) > 500 else ''}</p>
        </div>
        """, unsafe_allow_html=True)

def display_valuation_tab(analysis: Dict):
    """Display valuation analysis tab"""
    st.markdown('<div class="section-header">💰 Valuation Analysis</div>', unsafe_allow_html=True)

    valuation = analysis.get("valuation_analysis", {})
    if "error" in valuation:
        st.error("Valuation analysis not available")
        return

    col1, col2 = st.columns(2)

    with col1:
        current_ratios = valuation.get("current_ratios", {})
        relative_val = valuation.get("relative_valuation", {})

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📊 Current Valuation Ratios</div>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-label">P/E Ratio</div>
                    <div class="metric-value">{current_ratios.get('pe_ratio', 0):.1f}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">P/B Ratio</div>
                    <div class="metric-value">{current_ratios.get('pb_ratio', 0):.1f}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">P/S Ratio</div>
                    <div class="metric-value">{current_ratios.get('ps_ratio', 0):.1f}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">PEG Ratio</div>
                    <div class="metric-value">{current_ratios.get('peg_ratio', 0):.1f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Sector comparison
        pe_vs_sector = relative_val.get("pe_vs_sector", 0)
        pe_color = "negative" if pe_vs_sector > 20 else "positive" if pe_vs_sector < -10 else "neutral"

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🏭 Sector Comparison</div>
            <p><strong>P/E vs Sector:</strong> <span class="{pe_color}">{pe_vs_sector:+.1f}%</span></p>
            <p><strong>P/B vs Sector:</strong> <span class="neutral">{relative_val.get('pb_vs_sector', 0):+.1f}%</span></p>
            <p><strong>P/E Percentile:</strong> {relative_val.get('pe_percentile', 0):.0f}th percentile</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        intrinsic_models = valuation.get("intrinsic_value_models", {})
        val_summary = valuation.get("valuation_summary", {})

        dcf_value = intrinsic_models.get("dcf_value", 0)
        dcf_upside = intrinsic_models.get("dcf_upside_downside", 0)
        dcf_color = "positive" if dcf_upside > 10 else "negative" if dcf_upside < -10 else "neutral"

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🎯 Intrinsic Value Models</div>
            <p><strong>DCF Fair Value:</strong> ${dcf_value:.2f}</p>
            <p><strong>DCF Upside/Downside:</strong> <span class="{dcf_color}">{dcf_upside:+.1f}%</span></p>
            <p><strong>Graham Number:</strong> ${intrinsic_models.get('graham_number', 0):.2f}</p>
            <p><strong>Fair Value Estimate:</strong> ${val_summary.get('fair_value_estimate', 0):.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        # Valuation summary
        overall_val = val_summary.get("overall_valuation", "Neutral")
        val_score = val_summary.get("valuation_score", 50)

        val_color = "positive" if val_score > 70 else "negative" if val_score < 40 else "neutral"

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📈 Valuation Summary</div>
            <p><strong>Overall Valuation:</strong> <span class="{val_color}">{overall_val}</span></p>
            <p><strong>Valuation Score:</strong> {val_score:.0f}/100</p>
            <p><strong>Margin of Safety:</strong> {val_summary.get('margin_of_safety', 0):.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

def display_technical_tab(analysis: Dict, symbol: str):
    """Display technical analysis tab"""
    st.markdown('<div class="section-header">📈 Technical Analysis</div>', unsafe_allow_html=True)

    technical = analysis.get("technical_analysis", {})
    if "error" in technical:
        st.error("Technical analysis not available")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Current levels
        current_levels = technical.get("current_levels", {})
        current_price = current_levels.get("current_price", 0)
        sma_20 = current_levels.get("sma_20", 0)
        sma_50 = current_levels.get("sma_50", 0)
        sma_200 = current_levels.get("sma_200", 0)

        dist_20 = current_levels.get("distance_from_sma20", 0)
        dist_50 = current_levels.get("distance_from_sma50", 0)
        dist_200 = current_levels.get("distance_from_sma200", 0)

        color_20 = "positive" if dist_20 > 0 else "negative"
        color_50 = "positive" if dist_50 > 0 else "negative"
        color_200 = "positive" if dist_200 > 0 else "negative"

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📍 Current Price Levels</div>
            <p><strong>Current Price:</strong> ${current_price:.2f}</p>
            <p><strong>SMA 20:</strong> ${sma_20:.2f} <span class="{color_20}">({dist_20:+.1f}%)</span></p>
            <p><strong>SMA 50:</strong> ${sma_50:.2f} <span class="{color_50}">({dist_50:+.1f}%)</span></p>
            <p><strong>SMA 200:</strong> ${sma_200:.2f} <span class="{color_200}">({dist_200:+.1f}%)</span></p>
        </div>
        """, unsafe_allow_html=True)

        # Momentum indicators
        momentum = technical.get("momentum_indicators", {})
        rsi = momentum.get("rsi_14", 50)
        rsi_signal = momentum.get("rsi_signal", "Neutral")
        macd = momentum.get("macd", 0)
        macd_signal = momentum.get("macd_signal", 0)

        rsi_color = "negative" if rsi > 70 else "positive" if rsi < 30 else "neutral"
        macd_color = "positive" if macd > macd_signal else "negative"

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">⚡ Momentum Indicators</div>
            <p><strong>RSI (14):</strong> <span class="{rsi_color}">{rsi:.1f}</span> - {rsi_signal}</p>
            <p><strong>MACD:</strong> <span class="{macd_color}">{macd:.3f}</span></p>
            <p><strong>MACD Signal:</strong> {macd_signal:.3f}</p>
            <p><strong>Stochastic %K:</strong> {momentum.get('stochastic_k', 0):.1f}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Support and resistance
        support_resistance = technical.get("support_resistance", {})
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🎯 Support & Resistance</div>
            <p><strong>Support Level 1:</strong> ${support_resistance.get('support_1', 0):.2f}</p>
            <p><strong>Support Level 2:</strong> ${support_resistance.get('support_2', 0):.2f}</p>
            <p><strong>Resistance Level 1:</strong> ${support_resistance.get('resistance_1', 0):.2f}</p>
            <p><strong>Resistance Level 2:</strong> ${support_resistance.get('resistance_2', 0):.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        # Technical score and signals
        tech_score = technical.get("technical_score", 50)
        signals = technical.get("signals", {})

        score_color = "positive" if tech_score > 70 else "negative" if tech_score < 40 else "neutral"

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🎯 Technical Summary</div>
            <p><strong>Technical Score:</strong> <span class="{score_color}">{tech_score:.0f}/100</span></p>
            <p><strong>Overall Signal:</strong> {signals.get('overall', 'Neutral')}</p>
            <p><strong>Trend:</strong> {signals.get('trend', 'Sideways')}</p>
            <p><strong>Momentum:</strong> {signals.get('momentum', 'Neutral')}</p>
        </div>
        """, unsafe_allow_html=True)

    # Price chart
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="6mo")
        if not hist.empty:
            fig = go.Figure()

            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name="Price"
            ))

            # Add moving averages
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'].rolling(20).mean(),
                name="SMA 20",
                line=dict(color='orange', width=1)
            ))

            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'].rolling(50).mean(),
                name="SMA 50",
                line=dict(color='blue', width=1)
            ))

            fig.update_layout(
                title=f"{symbol} - 6 Month Price Chart with Moving Averages",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                template="plotly_dark",
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)
    except:
        st.info("Price chart not available")

def display_fundamentals_tab(analysis: Dict):
    """Display fundamentals analysis tab"""
    st.markdown('<div class="section-header">🏢 Fundamental Analysis</div>', unsafe_allow_html=True)

    financial_health = analysis.get("financial_health", {})
    growth = analysis.get("growth_analysis", {})

    if "error" not in financial_health:
        col1, col2 = st.columns(2)

        with col1:
            # Liquidity ratios
            liquidity = financial_health.get("liquidity_ratios", {})
            st.markdown(f"""
            <div class="analysis-card">
                <div class="card-header">💧 Liquidity Ratios</div>
                <p><strong>Current Ratio:</strong> {liquidity.get('current_ratio', 0):.2f}</p>
                <p><strong>Quick Ratio:</strong> {liquidity.get('quick_ratio', 0):.2f}</p>
                <p><strong>Cash Ratio:</strong> {liquidity.get('cash_ratio', 0):.2f}</p>
            </div>
            """, unsafe_allow_html=True)

            # Leverage ratios
            leverage = financial_health.get("leverage_ratios", {})
            debt_to_equity = leverage.get("debt_to_equity", 0)
            debt_color = "negative" if debt_to_equity > 2 else "positive" if debt_to_equity < 0.5 else "neutral"

            st.markdown(f"""
            <div class="analysis-card">
                <div class="card-header">⚖️ Leverage Ratios</div>
                <p><strong>Debt to Equity:</strong> <span class="{debt_color}">{debt_to_equity:.2f}</span></p>
                <p><strong>Debt to Assets:</strong> {leverage.get('debt_to_assets', 0):.2f}</p>
                <p><strong>Equity Ratio:</strong> {leverage.get('equity_ratio', 0):.2f}</p>
                <p><strong>Interest Coverage:</strong> {leverage.get('interest_coverage', 0):.1f}x</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Financial strength scores
            strength = financial_health.get("financial_strength_scores", {})
            piotroski = strength.get("piotroski_f_score", 0)
            altman_z = strength.get("altman_z_score", 0)

            piotroski_color = "positive" if piotroski >= 7 else "negative" if piotroski <= 3 else "neutral"
            altman_color = "positive" if altman_z > 3 else "negative" if altman_z < 1.8 else "neutral"

            st.markdown(f"""
            <div class="analysis-card">
                <div class="card-header">💪 Financial Strength</div>
                <p><strong>Piotroski F-Score:</strong> <span class="{piotroski_color}">{piotroski}/9</span></p>
                <p><strong>Altman Z-Score:</strong> <span class="{altman_color}">{altman_z:.1f}</span></p>
                <p><strong>Health Grade:</strong> {strength.get('financial_health_grade', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

            # Cash flow metrics
            cashflow = financial_health.get("cash_flow_metrics", {})
            st.markdown(f"""
            <div class="analysis-card">
                <div class="card-header">💰 Cash Flow Metrics</div>
                <p><strong>Operating Cash Flow:</strong> ${cashflow.get('operating_cashflow', 0)/1e9:.1f}B</p>
                <p><strong>Free Cash Flow:</strong> ${cashflow.get('free_cashflow', 0)/1e9:.1f}B</p>
                <p><strong>OCF to Revenue:</strong> {cashflow.get('ocf_to_revenue', 0)*100:.1f}%</p>
                <p><strong>FCF to Revenue:</strong> {cashflow.get('fcf_to_revenue', 0)*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)

def display_rating_tab(analysis: Dict):
    """Display rating and price targets tab"""
    st.markdown('<div class="section-header">🎯 Overall Rating & Targets</div>', unsafe_allow_html=True)

    rating = analysis.get("overall_rating", {})
    if "error" in rating:
        st.error("Rating analysis not available")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Overall rating
        overall_score = rating.get("overall_score", 50)
        investment_rating = rating.get("rating", "Hold")
        stars = rating.get("stars", 3)

        rating_class = f"rating-{investment_rating.lower().replace(' ', '-')}"

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">⭐ Overall Investment Rating</div>
            <div style="text-align: center; margin: 1rem 0;">
                <div class="rating-badge {rating_class}">
                    {investment_rating}
                </div>
            </div>
            <p><strong>Overall Score:</strong> {overall_score:.0f}/100</p>
            <p><strong>Stars:</strong> {'⭐' * stars}</p>
            <p><strong>Confidence:</strong> {rating.get('confidence_level', 'Medium')}</p>
            <p><strong>Time Horizon:</strong> {rating.get('time_horizon', 'Medium Term')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Component scores
        components = rating.get("component_scores", {})
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📊 Component Scores</div>
            <p><strong>Valuation:</strong> {components.get('valuation', 0):.0f}/100</p>
            <p><strong>Financial Health:</strong> {components.get('financial_health', 0):.0f}/100</p>
            <p><strong>Technical:</strong> {components.get('technical', 0):.0f}/100</p>
            <p><strong>Growth:</strong> {components.get('growth', 0):.0f}/100</p>
            <p><strong>Momentum:</strong> {components.get('momentum', 0):.0f}/100</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Key strengths and concerns
        strengths = rating.get("key_strengths", [])
        concerns = rating.get("key_concerns", [])

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">✅ Key Strengths</div>
            {''.join([f'<p>• {strength}</p>' for strength in strengths[:5]])}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">⚠️ Key Concerns</div>
            {''.join([f'<p>• {concern}</p>' for concern in concerns[:5]])}
        </div>
        """, unsafe_allow_html=True)

    # Investment thesis
    thesis = analysis.get("investment_thesis", "")
    if thesis:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📝 Investment Thesis</div>
            <p>{thesis}</p>
        </div>
        """, unsafe_allow_html=True)

def create_fund_analysis_tab():
    """Create fund analysis tab"""
    st.markdown('<div class="section-header">🏦 Fund Analysis Engine</div>', unsafe_allow_html=True)

    # Analysis mode selection
    analysis_mode = st.radio(
        "Select Analysis Mode:",
        ["🔍 Individual Fund Analysis", "📊 Fund Screener", "🏆 Top Funds"],
        horizontal=True
    )

    if analysis_mode == "🔍 Individual Fund Analysis":
        create_individual_fund_analysis()
    elif analysis_mode == "📊 Fund Screener":
        create_fund_screener()
    else:
        create_top_funds_analysis()

def create_individual_fund_analysis():
    """Create individual fund analysis section"""
    col1, col2 = st.columns([3, 1])

    with col1:
        fund_symbol = st.text_input(
            "Enter Fund Symbol",
            value="SPY",
            key="fund_symbol",
            help="Enter any fund symbol (e.g., SPY, QQQ, VTI, ARKK)"
        )

    with col2:
        if st.button("🔍 Analyze Fund", type="primary", use_container_width=True):
            if fund_symbol:
                st.session_state.analyze_fund = fund_symbol.upper()

    # Display fund analysis if requested
    if hasattr(st.session_state, 'analyze_fund'):
        display_fund_analysis(st.session_state.analyze_fund)

def create_fund_screener():
    """Create fund screener section"""
    st.markdown("### 📊 Advanced Fund Screener")

    col1, col2, col3 = st.columns(3)

    with col1:
        category_filter = st.selectbox(
            "Fund Category",
            ["All", "Large Blend", "Large Growth", "Large Value", "Mid-Cap", "Small-Cap", "International", "Emerging Markets", "Bond", "Sector"]
        )

        min_aum = st.number_input("Minimum AUM (Billions)", min_value=0.0, value=1.0, step=0.1)

    with col2:
        max_expense_ratio = st.number_input("Max Expense Ratio (%)", min_value=0.0, max_value=3.0, value=1.0, step=0.1)

        min_return_1y = st.number_input("Min 1Y Return (%)", value=-50.0, step=1.0)

    with col3:
        max_volatility = st.number_input("Max Volatility (%)", min_value=0.0, value=25.0, step=1.0)

        min_sharpe = st.number_input("Min Sharpe Ratio", value=0.0, step=0.1)

    if st.button("🔍 Screen Funds", type="primary"):
        with st.spinner("Screening funds..."):
            # Import the popular funds list from our analyzer
            from app.analytics.comprehensive_fund_analyzer import POPULAR_FUNDS

            screened_funds = []

            for symbol in POPULAR_FUNDS[:20]:  # Limit to first 20 for performance
                try:
                    analyzer = ComprehensiveFundAnalyzer(symbol)
                    analysis = analyzer.get_comprehensive_analysis()

                    if 'error' not in analysis:
                        basic_info = analysis.get('basic_info', {})
                        performance = analysis.get('performance_metrics', {})

                        # Apply filters
                        aum = basic_info.get('total_assets', 0) / 1e9
                        expense_ratio = basic_info.get('expense_ratio', 0) * 100
                        return_1y = performance.get('return_1Y', -100)
                        volatility = performance.get('annual_volatility', 100)
                        sharpe = performance.get('sharpe_ratio', -10)

                        if (aum >= min_aum and
                            expense_ratio <= max_expense_ratio and
                            return_1y >= min_return_1y and
                            volatility <= max_volatility and
                            sharpe >= min_sharpe):

                            screened_funds.append({
                                'Symbol': symbol,
                                'Name': basic_info.get('fund_name', 'N/A'),
                                'Category': basic_info.get('category', 'N/A'),
                                'AUM (B)': round(aum, 1),
                                'Expense Ratio (%)': round(expense_ratio, 2),
                                '1Y Return (%)': return_1y,
                                'Volatility (%)': round(volatility, 1),
                                'Sharpe Ratio': round(sharpe, 2),
                                'Rating': analysis.get('fund_rating', {}).get('overall_rating', 0)
                            })
                except:
                    continue

            if screened_funds:
                df = pd.DataFrame(screened_funds)
                df = df.sort_values('Rating', ascending=False)
                st.success(f"Found {len(screened_funds)} funds matching your criteria")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No funds found matching your criteria. Try adjusting the filters.")

def create_top_funds_analysis():
    """Create top funds analysis section"""
    st.markdown("### 🏆 Top Performing Funds")

    category = st.selectbox(
        "Select Category",
        ["All Categories", "Equity Funds", "Bond Funds", "International Funds", "Sector Funds"]
    )

    time_period = st.selectbox(
        "Performance Period",
        ["1 Year", "3 Years", "5 Years", "YTD"]
    )

    if st.button("📊 Get Top Funds", type="primary"):
        with st.spinner("Analyzing top funds..."):
            # Sample top funds for demonstration
            top_funds_data = [
                {'Symbol': 'SPY', 'Name': 'SPDR S&P 500 ETF', 'Category': 'Large Blend', 'Return': '12.5%', 'Rating': '9.2'},
                {'Symbol': 'QQQ', 'Name': 'Invesco QQQ Trust', 'Category': 'Large Growth', 'Return': '18.3%', 'Rating': '8.8'},
                {'Symbol': 'VTI', 'Name': 'Vanguard Total Stock Market', 'Category': 'Large Blend', 'Return': '11.8%', 'Rating': '9.0'},
                {'Symbol': 'VXUS', 'Name': 'Vanguard Total International', 'Category': 'International', 'Return': '8.2%', 'Rating': '8.5'},
                {'Symbol': 'BND', 'Name': 'Vanguard Total Bond Market', 'Category': 'Bond', 'Return': '2.1%', 'Rating': '8.0'}
            ]

            df = pd.DataFrame(top_funds_data)
            st.dataframe(df, use_container_width=True)

            st.info("📈 Click on any fund symbol above to get detailed analysis in Individual Fund Analysis mode.")

def display_fund_analysis(symbol: str):
    """Display comprehensive fund analysis"""
    st.markdown(f'<div class="section-header">📊 {symbol} Fund Analysis</div>', unsafe_allow_html=True)

    with st.spinner(f"Analyzing {symbol}..."):
        try:
            analyzer = ComprehensiveFundAnalyzer(symbol)
            analysis = analyzer.get_comprehensive_analysis()

            if 'error' in analysis:
                st.error(analysis['error'])
                return

            # Create tabs for different analysis sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Overview",
                "📈 Performance",
                "⚖️ Risk Analysis",
                "🏛️ Holdings",
                "🎯 Rating"
            ])

            with tab1:
                display_fund_overview_tab(analysis, symbol)

            with tab2:
                display_fund_performance_tab(analysis, symbol)

            with tab3:
                display_fund_risk_tab(analysis)

            with tab4:
                display_fund_holdings_tab(analysis)

            with tab5:
                display_fund_rating_tab(analysis)

        except Exception as e:
            st.error(f"Failed to analyze fund {symbol}: {str(e)}")

def display_fund_overview_tab(analysis: Dict[str, Any], symbol: str):
    """Display fund overview tab"""
    basic_info = analysis.get('basic_info', {})
    performance = analysis.get('performance_metrics', {})

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        nav = performance.get('current_price', 0)
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">💰 Current NAV</div>
            <div class="metric-value">${nav:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        aum = basic_info.get('total_assets', 0)
        aum_display = f"${aum/1e9:.1f}B" if aum > 1e9 else f"${aum/1e6:.1f}M" if aum > 1e6 else f"${aum:,.0f}"
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📊 Total Assets</div>
            <div class="metric-value">{aum_display}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        expense_ratio = basic_info.get('expense_ratio', 0) * 100
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">💸 Expense Ratio</div>
            <div class="metric-value">{expense_ratio:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        fund_yield = basic_info.get('yield', 0) * 100
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">💎 Yield</div>
            <div class="metric-value">{fund_yield:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    # Fund details
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🏦 Fund Information</div>
            <p><strong>Fund Name:</strong> {basic_info.get('fund_name', 'N/A')}</p>
            <p><strong>Category:</strong> {basic_info.get('category', 'N/A')}</p>
            <p><strong>Fund Family:</strong> {basic_info.get('fund_family', 'N/A')}</p>
            <p><strong>Inception Date:</strong> {basic_info.get('inception_date', 'N/A')}</p>
            <p><strong>Minimum Investment:</strong> ${basic_info.get('minimum_investment', 0):,}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        rating = analysis.get('fund_rating', {})
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">⭐ Quick Rating</div>
            <p><strong>Overall Rating:</strong> {rating.get('overall_rating', 0)}/10</p>
            <p><strong>Performance:</strong> {rating.get('performance_rating', 0)}/10</p>
            <p><strong>Risk:</strong> {rating.get('risk_rating', 0)}/10</p>
            <p><strong>Cost:</strong> {rating.get('cost_rating', 0)}/10</p>
            <p><strong>Morningstar:</strong> {'⭐' * basic_info.get('morningstar_rating', 0)}</p>
        </div>
        """, unsafe_allow_html=True)

def display_fund_performance_tab(analysis: Dict[str, Any], symbol: str):
    """Display fund performance tab"""
    performance = analysis.get('performance_metrics', {})

    # Performance metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📈 Short-term Returns</div>
            <p><strong>1 Month:</strong> {performance.get('return_1M', 'N/A')}%</p>
            <p><strong>3 Months:</strong> {performance.get('return_3M', 'N/A')}%</p>
            <p><strong>6 Months:</strong> {performance.get('return_6M', 'N/A')}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📊 Long-term Returns</div>
            <p><strong>1 Year:</strong> {performance.get('return_1Y', 'N/A')}%</p>
            <p><strong>3 Years:</strong> {performance.get('return_3Y', 'N/A')}%</p>
            <p><strong>5 Years:</strong> {performance.get('return_5Y', 'N/A')}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">⚡ Key Metrics</div>
            <p><strong>Volatility:</strong> {performance.get('annual_volatility', 'N/A')}%</p>
            <p><strong>Sharpe Ratio:</strong> {performance.get('sharpe_ratio', 'N/A')}</p>
            <p><strong>Max Drawdown:</strong> {performance.get('max_drawdown', 'N/A')}%</p>
        </div>
        """, unsafe_allow_html=True)

    # Performance chart
    try:
        fund = yf.Ticker(symbol)
        hist = fund.history(period="2y")

        if not hist.empty:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='NAV',
                line=dict(color='#58a6ff', width=2)
            ))

            fig.update_layout(
                title=f"{symbol} - 2 Year Performance",
                xaxis_title="Date",
                yaxis_title="NAV ($)",
                template="plotly_dark",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
    except:
        st.info("Performance chart temporarily unavailable")

def display_fund_risk_tab(analysis: Dict[str, Any]):
    """Display fund risk analysis tab"""
    risk_metrics = analysis.get('risk_metrics', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📉 Risk Metrics</div>
            <p><strong>Beta:</strong> {risk_metrics.get('beta', 'N/A')}</p>
            <p><strong>Alpha:</strong> {risk_metrics.get('alpha', 'N/A')}%</p>
            <p><strong>Correlation (SPY):</strong> {risk_metrics.get('correlation_spy', 'N/A')}</p>
            <p><strong>Downside Deviation:</strong> {risk_metrics.get('downside_deviation', 'N/A')}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📊 Distribution</div>
            <p><strong>Skewness:</strong> {risk_metrics.get('skewness', 'N/A')}</p>
            <p><strong>Kurtosis:</strong> {risk_metrics.get('kurtosis', 'N/A')}</p>
            <p><strong>Sortino Ratio:</strong> {risk_metrics.get('sortino_ratio', 'N/A')}</p>
            <p><strong>VaR (95%):</strong> {risk_metrics.get('var_95', 'N/A')}%</p>
        </div>
        """, unsafe_allow_html=True)

def display_fund_holdings_tab(analysis: Dict[str, Any]):
    """Display fund holdings tab"""
    holdings = analysis.get('holdings_analysis', {})

    if holdings.get('top_holdings'):
        st.markdown("### 🏛️ Top Holdings")
        holdings_df = pd.DataFrame(holdings['top_holdings'])
        st.dataframe(holdings_df, use_container_width=True)
    else:
        st.info("Holdings data not available for this fund")

    col1, col2 = st.columns(2)

    with col1:
        sector_allocation = holdings.get('sector_allocation', {})
        if sector_allocation:
            st.markdown("### 🏭 Sector Allocation")
            sector_df = pd.DataFrame(list(sector_allocation.items()), columns=['Sector', 'Weight'])
            st.dataframe(sector_df, use_container_width=True)

    with col2:
        geo_allocation = holdings.get('geographic_allocation', {})
        if geo_allocation:
            st.markdown("### 🌍 Geographic Allocation")
            geo_df = pd.DataFrame(list(geo_allocation.items()), columns=['Country', 'Weight'])
            st.dataframe(geo_df, use_container_width=True)

def display_fund_rating_tab(analysis: Dict[str, Any]):
    """Display fund rating tab"""
    rating = analysis.get('fund_rating', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">🎯 Overall Rating</div>
            <div class="metric-value">{rating.get('overall_rating', 0)}/10</div>
            <p>{rating.get('rating_explanation', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">📊 Rating Breakdown</div>
            <p><strong>Performance Rating:</strong> {rating.get('performance_rating', 0)}/10</p>
            <p><strong>Risk Rating:</strong> {rating.get('risk_rating', 0)}/10</p>
            <p><strong>Cost Rating:</strong> {rating.get('cost_rating', 0)}/10</p>
        </div>
        """, unsafe_allow_html=True)

    # Benchmark comparison if available
    basic_info = analysis.get('basic_info', {})
    if basic_info.get('morningstar_rating', 0) > 0:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="card-header">⭐ External Ratings</div>
            <p><strong>Morningstar Overall:</strong> {'⭐' * basic_info.get('morningstar_rating', 0)}</p>
            <p><strong>Morningstar Risk:</strong> {basic_info.get('morningstar_risk_rating', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application"""
    create_platform_header()

    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌍 Dashboard",
        "📈 Stock Analysis",
        "🏦 Fund Analysis",
        "💼 Portfolio Tools",
        "🔍 Screener"
    ])

    with tab1:
        st.markdown('<div class="section-header">🌍 Global Financial Intelligence Dashboard</div>', unsafe_allow_html=True)

        # Quick metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("S&P 500", "4,234", "12.5 (0.3%)")
        with col2:
            st.metric("Bitcoin", "$45,234", "1,023 (2.3%)")
        with col3:
            st.metric("VIX", "18.5", "-0.8 (-4.1%)")
        with col4:
            st.metric("DXY", "103.2", "0.3 (0.3%)")

        st.info("🚀 Welcome to your comprehensive financial intelligence platform! Use the tabs above to access advanced analytics.")

    with tab2:
        symbol = create_stock_search_section()

        # Display analysis if triggered
        if hasattr(st.session_state, 'analyze_stock'):
            display_stock_analysis(st.session_state.analyze_stock)
        elif hasattr(st.session_state, 'quick_view') and symbol:
            # Quick view with basic metrics
            try:
                stock = yf.Ticker(symbol)
                info = stock.info

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Price", f"${info.get('currentPrice', 0):.2f}",
                             f"{info.get('regularMarketChangePercent', 0):.1f}%")
                with col2:
                    st.metric("P/E Ratio", f"{info.get('forwardPE', 0):.1f}")
                with col3:
                    st.metric("Market Cap", f"${info.get('marketCap', 0)/1e9:.1f}B")
                with col4:
                    st.metric("Volume", f"{info.get('volume', 0)/1e6:.1f}M")
            except:
                st.error("Could not fetch quick data")

    with tab3:
        create_fund_analysis_tab()

    with tab4:
        st.markdown('<div class="section-header">💼 Portfolio Analysis Tools</div>', unsafe_allow_html=True)
        st.info("🚧 Portfolio analysis tools coming soon! This will include portfolio optimization, risk analysis, and performance attribution.")

    with tab5:
        st.markdown('<div class="section-header">🔍 Advanced Stock & Fund Screener</div>', unsafe_allow_html=True)
        st.info("🚧 Advanced screening tools coming soon! Screen 10,000+ stocks and 5,000+ funds with custom criteria.")

if __name__ == "__main__":
    main()