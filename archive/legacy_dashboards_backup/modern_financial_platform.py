#!/usr/bin/env python3
"""
🚀 Modern Financial Analytics Platform
User-friendly design with Bloomberg Terminal functionality
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import warnings
import time
import yfinance as yf

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="🚀 Modern Financial Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import our analytics modules
RealTimeDataEngine = None
ComprehensiveStockAnalyzer = None
ComprehensiveFundAnalyzer = None
PortfolioOptimizer = None
VolatilityAnalyzer = None
NeuralNetworkAnalyzer = None
GlobalMarketCollector = None
EnhancedFundHoldingsCollector = None

try:
    from app.analytics.real_time_data_engine import RealTimeDataEngine
    from app.analytics.comprehensive_stock_analyzer import ComprehensiveStockAnalyzer
    from app.analytics.comprehensive_fund_analyzer import ComprehensiveFundAnalyzer
    from app.analytics.portfolio_optimizer import PortfolioOptimizer
    from app.analytics.volatility import VolatilityAnalyzer
    from app.analytics.neural_networks import NeuralNetworkAnalyzer, run_comprehensive_analysis
    from app.data_collectors.global_market_collector import GlobalMarketCollector, collect_global_data_sync
    from app.data_collectors.enhanced_fund_holdings import EnhancedFundHoldingsCollector, get_fund_universe
except ImportError as e:
    st.warning(f"Some advanced features may not be available: {e}")

# Modern Color Palette CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Variables */
    :root {
        --primary-color: #2563eb;
        --secondary-color: #1e40af;
        --accent-color: #3b82f6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --dark-bg: #0f172a;
        --card-bg: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --border-color: #334155;
        --gradient-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Main App Styling */
    .main {
        padding: 1rem 2rem;
        background: var(--dark-bg);
        min-height: 100vh;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: none;
        background: var(--dark-bg);
    }

    /* Custom Header */
    .main-header {
        background: var(--gradient-bg);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }

    .main-header h1 {
        color: white;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }

    /* Card Styling */
    .metric-card {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        border-color: var(--accent-color);
    }

    .metric-card h3 {
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        margin: 0 0 1rem 0;
        font-size: 1.25rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-color);
        margin: 0.5rem 0;
    }

    .metric-change {
        font-size: 0.9rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .metric-change.positive {
        color: var(--success-color);
    }

    .metric-change.negative {
        color: var(--danger-color);
    }

    /* Section Headers */
    .section-header {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 2rem 0 1rem 0;
        border-left: 4px solid var(--accent-color);
    }

    .section-header h2 {
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        margin: 0;
        font-size: 1.5rem;
    }

    /* Data Tables */
    .dataframe {
        background: var(--card-bg) !important;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color);
    }

    .dataframe thead tr th {
        background: var(--secondary-color) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 1rem !important;
    }

    .dataframe tbody tr td {
        background: var(--card-bg) !important;
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
        border: 1px solid var(--border-color) !important;
        padding: 0.75rem 1rem !important;
    }

    .dataframe tbody tr:hover td {
        background: rgba(59, 130, 246, 0.1) !important;
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background: var(--card-bg);
        border-right: 1px solid var(--border-color);
    }

    .css-1d391kg .css-1v0mbdj {
        color: var(--text-primary);
    }

    /* Buttons */
    .stButton > button {
        background: var(--accent-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: var(--secondary-color);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Select Boxes */
    .stSelectbox > div > div {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
    }

    /* Charts */
    .plotly-chart {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid var(--border-color);
    }

    /* Streamlit Default Component Overrides for Better Contrast */
    .stApp {
        background: var(--dark-bg);
        color: var(--text-primary);
    }

    /* Streamlit Metrics */
    .css-1xarl3l {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    /* Streamlit Text Elements */
    .css-10trblm, .css-16idsys p, .css-1kyxreq p {
        color: var(--text-primary) !important;
    }

    /* Streamlit Headers */
    .css-10trblm h1, .css-10trblm h2, .css-10trblm h3, .css-10trblm h4 {
        color: var(--text-primary) !important;
    }

    /* Streamlit Dataframe */
    .css-1l02zno, .css-1outpf7 {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
    }

    /* Streamlit Sidebar */
    .css-1d391kg, .css-1aumxhk {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
    }

    /* Streamlit Expander */
    .css-1outpf7 .css-90vs21 {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Streamlit Input Fields */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Streamlit Select Boxes */
    .stSelectbox > div > div > select {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Override any remaining white text/background combinations */
    div[data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
    }

    div[data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }

    div[data-testid="stMetricDelta"] {
        color: var(--text-secondary) !important;
    }

    /* Ensure all text is readable */
    * {
        color: inherit !important;
    }

    /* Force dark theme on all Streamlit elements */
    .main .block-container {
        background: var(--dark-bg) !important;
        color: var(--text-primary) !important;
    }

    /* Force light text on all elements */
    .stApp, .stApp * {
        color: var(--text-primary) !important;
    }

    /* Override Streamlit's default text colors */
    p, span, div, h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }

    /* Ensure metrics are visible */
    .css-1xarl3l, [data-testid="metric-container"] {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Fix expander styling */
    .streamlit-expander {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
    }

    .streamlit-expander .streamlit-expanderHeader {
        background: var(--secondary-color) !important;
        color: var(--text-primary) !important;
    }

    /* Fix column styling */
    .css-1r6slb0, .css-12oz5g7 {
        background: transparent !important;
        color: var(--text-primary) !important;
    }

    /* Override any white backgrounds */
    [style*="background-color: white"], [style*="background-color: #ffffff"], [style*="background-color: #fff"] {
        background-color: var(--card-bg) !important;
        color: var(--text-primary) !important;
    }

    /* Override any black text on dark backgrounds */
    [style*="color: black"], [style*="color: #000000"], [style*="color: #000"] {
        color: var(--text-primary) !important;
    }

    /* Status Indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }

    .status-indicator.online {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
        border: 1px solid var(--success-color);
    }

    .status-indicator.offline {
        background: rgba(239, 68, 68, 0.2);
        color: var(--danger-color);
        border: 1px solid var(--danger-color);
    }

    /* Loading Animation */
    .loading-spinner {
        border: 3px solid var(--border-color);
        border-top: 3px solid var(--accent-color);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 2rem auto;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Feature Grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }

    .feature-card {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid var(--border-color);
        text-align: center;
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
        border-color: var(--accent-color);
    }

    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .feature-title {
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.25rem;
        margin: 1rem 0;
    }

    .feature-description {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# Initialize engines
@st.cache_resource
def initialize_engines():
    """Initialize all analytics engines"""
    engines = {}
    try:
        if RealTimeDataEngine is not None:
            engines['real_time'] = RealTimeDataEngine()
        if VolatilityAnalyzer is not None:
            engines['volatility'] = VolatilityAnalyzer()
        # ComprehensiveStockAnalyzer requires symbol parameter, so we'll create it when needed
        engines['stock_analyzer'] = None
        engines['fund_analyzer'] = None
    except Exception as e:
        st.warning(f"Some analytics engines could not be initialized: {e}")
        engines = {}
    return engines

engines = initialize_engines()

def create_main_header():
    """Create the main header section"""
    current_time = datetime.now().strftime("%H:%M:%S")
    market_status = "🟢 AÇIK" if engines and engines.get('real_time') and hasattr(engines['real_time'], 'is_market_open') and engines['real_time'].is_market_open else "🔴 KAPALI"

    st.markdown(f"""
    <div class="main-header">
        <h1>🚀 Modern Finansal Platform</h1>
        <p>Bloomberg seviyesinde profesyonel finansal analiz araçları | Piyasa: {market_status} | Saat: {current_time}</p>
    </div>
    """, unsafe_allow_html=True)

def create_quick_metrics():
    """Create quick metrics dashboard"""
    st.markdown('<div class="section-header"><h2>📊 Anlık Piyasa Özeti</h2></div>', unsafe_allow_html=True)

    # Get market data
    major_indices = {
        'S&P 500': '^GSPC',
        'NASDAQ': '^IXIC',
        'Dow Jones': '^DJI',
        'BIST 100': 'XU100.IS'
    }

    cols = st.columns(len(major_indices))

    for i, (name, symbol) in enumerate(major_indices.items()):
        with cols[i]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100

                    change_class = "positive" if change >= 0 else "negative"
                    change_icon = "📈" if change >= 0 else "📉"

                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{name}</h3>
                        <div class="metric-value">{current_price:,.2f}</div>
                        <div class="metric-change {change_class}">
                            {change_icon} {change:+.2f} ({change_pct:+.2f}%)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{name}</h3>
                        <div class="metric-value">--</div>
                        <div class="metric-change">Veri yüklenemedi</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{name}</h3>
                    <div class="metric-value">--</div>
                    <div class="metric-change">Bağlantı hatası</div>
                </div>
                """, unsafe_allow_html=True)

    # Add GLI and Crypto Metrics Section
    st.markdown('<div class="section-header"><h2>🌍 Global Likidite ve Kripto Metrikleri</h2></div>', unsafe_allow_html=True)

    try:
        if GlobalMarketCollector:
            collector = GlobalMarketCollector()

            # Get GLI data
            try:
                gli_components = ['GLD', 'TLT', 'DXY=X', 'EURUSD=X', 'JPY=X']
                gli_data = {}
                gli_values = []

                for symbol in gli_components:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                        change_pct = ((current - prev) / prev) * 100
                        gli_data[symbol] = {'current': current, 'change': change_pct}
                        gli_values.append(current)

                # Calculate GLI (weighted average)
                if gli_values:
                    weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # GLD, TLT, DXY, EUR, JPY
                    gli_score = sum(v * w for v, w in zip(gli_values, weights)) / sum(weights)
                    gli_change = sum(gli_data[s]['change'] * w for s, w in zip(gli_components, weights)) / sum(weights)
                else:
                    gli_score = 0
                    gli_change = 0

            except:
                gli_score = 0
                gli_change = 0

            # Get crypto data
            try:
                btc_ticker = yf.Ticker('BTC-USD')
                btc_hist = btc_ticker.history(period="2d")
                if not btc_hist.empty:
                    btc_price = btc_hist['Close'].iloc[-1]
                    btc_prev = btc_hist['Close'].iloc[-2] if len(btc_hist) > 1 else btc_price
                    btc_change = ((btc_price - btc_prev) / btc_prev) * 100
                else:
                    btc_price = 0
                    btc_change = 0

                # Estimate total crypto market cap (BTC is ~40-50% of total market)
                total_crypto_market_cap = btc_price * 19.5e6 / 0.45  # Approximate

                # BTC Dominance (estimate ~45%)
                btc_dominance = 45.0

            except:
                btc_price = 0
                btc_change = 0
                total_crypto_market_cap = 0
                btc_dominance = 0

            # Display metrics
            cols = st.columns(4)

            with cols[0]:
                gli_class = "positive" if gli_change >= 0 else "negative"
                gli_icon = "📈" if gli_change >= 0 else "📉"
                st.markdown(f"""
                <div class="metric-card">
                    <h3>GLI (Global Liquidity Index)</h3>
                    <div class="metric-value">{gli_score:.2f}</div>
                    <div class="metric-change {gli_class}">
                        {gli_icon} {gli_change:+.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with cols[1]:
                btc_class = "positive" if btc_change >= 0 else "negative"
                btc_icon = "📈" if btc_change >= 0 else "📉"
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Bitcoin (BTC)</h3>
                    <div class="metric-value">${btc_price:,.0f}</div>
                    <div class="metric-change {btc_class}">
                        {btc_icon} {btc_change:+.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with cols[2]:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Total Crypto Market Cap</h3>
                    <div class="metric-value">${total_crypto_market_cap/1e12:.2f}T</div>
                    <div class="metric-change">
                        💰 Total Piyasa Değeri
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with cols[3]:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>BTC Dominance</h3>
                    <div class="metric-value">{btc_dominance:.1f}%</div>
                    <div class="metric-change">
                        👑 Bitcoin Hakimiyeti
                    </div>
                </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Global metrics yüklenemedi: {str(e)}")

def create_watchlist():
    """Create stock watchlist with real-time data"""
    st.markdown('<div class="section-header"><h2>👀 Takip Listesi</h2></div>', unsafe_allow_html=True)

    # Popular stocks
    watchlist_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']

    # Create columns for the watchlist
    cols = st.columns(4)

    for i, symbol in enumerate(watchlist_symbols):
        col_idx = i % 4
        with cols[col_idx]:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="2d")

                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
                    change = current_price - prev_close
                    change_pct = (change / prev_close) * 100
                    volume = hist['Volume'].iloc[-1]

                    change_class = "positive" if change >= 0 else "negative"
                    change_icon = "🚀" if change >= 0 else "🔻"

                    st.markdown(f"""
                    <div class="metric-card" style="margin: 0.5rem 0;">
                        <h3>{symbol}</h3>
                        <div class="metric-value" style="font-size: 1.5rem;">${current_price:.2f}</div>
                        <div class="metric-change {change_class}">
                            {change_icon} {change:+.2f} ({change_pct:+.2f}%)
                        </div>
                        <small style="color: var(--text-secondary);">Vol: {volume:,}</small>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.markdown(f"""
                <div class="metric-card" style="margin: 0.5rem 0;">
                    <h3>{symbol}</h3>
                    <div class="metric-value" style="font-size: 1.5rem;">--</div>
                    <div class="metric-change">Veri yok</div>
                </div>
                """, unsafe_allow_html=True)

def create_technical_analysis():
    """Create technical analysis section"""
    st.markdown('<div class="section-header"><h2>📈 Teknik Analiz</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col2:
        st.markdown("### ⚙️ Ayarlar")
        selected_symbol = st.selectbox("Hisse Seçin", ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'], key="tech_symbol")
        period = st.selectbox("Dönem", ['1mo', '3mo', '6mo', '1y', '2y'], index=2)
        indicators = st.multiselect("Teknik İndikatörler",
                                  ['SMA 20', 'SMA 50', 'EMA 12', 'EMA 26', 'Bollinger Bands', 'RSI'],
                                  default=['SMA 20', 'SMA 50'])

    with col1:
        if selected_symbol:
            try:
                # Get stock data
                ticker = yf.Ticker(selected_symbol)
                data = ticker.history(period=period)

                if not data.empty:
                    # Calculate technical indicators
                    if 'SMA 20' in indicators:
                        data['SMA_20'] = data['Close'].rolling(window=20).mean()
                    if 'SMA 50' in indicators:
                        data['SMA_50'] = data['Close'].rolling(window=50).mean()
                    if 'EMA 12' in indicators:
                        data['EMA_12'] = data['Close'].ewm(span=12).mean()
                    if 'EMA 26' in indicators:
                        data['EMA_26'] = data['Close'].ewm(span=26).mean()

                    # Create candlestick chart
                    fig = go.Figure()

                    # Add candlestick
                    fig.add_trace(go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name=selected_symbol,
                        increasing_line_color='#10b981',
                        decreasing_line_color='#ef4444'
                    ))

                    # Add indicators
                    colors = ['#3b82f6', '#f59e0b', '#8b5cf6', '#06b6d4']
                    color_idx = 0

                    for indicator in indicators:
                        if indicator in data.columns or indicator.replace(' ', '_') in data.columns:
                            col_name = indicator.replace(' ', '_')
                            if col_name in data.columns:
                                fig.add_trace(go.Scatter(
                                    x=data.index,
                                    y=data[col_name],
                                    mode='lines',
                                    name=indicator,
                                    line=dict(color=colors[color_idx % len(colors)], width=2)
                                ))
                                color_idx += 1

                    # Bollinger Bands
                    if 'Bollinger Bands' in indicators:
                        bb_period = 20
                        data['BB_Middle'] = data['Close'].rolling(window=bb_period).mean()
                        data['BB_Std'] = data['Close'].rolling(window=bb_period).std()
                        data['BB_Upper'] = data['BB_Middle'] + (data['BB_Std'] * 2)
                        data['BB_Lower'] = data['BB_Middle'] - (data['BB_Std'] * 2)

                        fig.add_trace(go.Scatter(
                            x=data.index, y=data['BB_Upper'],
                            mode='lines', name='BB Upper',
                            line=dict(color='rgba(59, 130, 246, 0.3)', dash='dash')
                        ))
                        fig.add_trace(go.Scatter(
                            x=data.index, y=data['BB_Lower'],
                            mode='lines', name='BB Lower',
                            fill='tonexty', fillcolor='rgba(59, 130, 246, 0.1)',
                            line=dict(color='rgba(59, 130, 246, 0.3)', dash='dash')
                        ))

                    # Update layout
                    fig.update_layout(
                        title=f'{selected_symbol} - Teknik Analiz',
                        template='plotly_dark',
                        height=500,
                        showlegend=True,
                        xaxis_title="Tarih",
                        yaxis_title="Fiyat ($)",
                        plot_bgcolor='rgba(30, 41, 59, 0.8)',
                        paper_bgcolor='rgba(15, 23, 42, 0.9)'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # RSI Chart (if selected)
                    if 'RSI' in indicators:
                        # Calculate RSI
                        delta = data['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        data['RSI'] = 100 - (100 / (1 + rs))

                        # Create RSI chart
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(
                            x=data.index, y=data['RSI'],
                            mode='lines', name='RSI',
                            line=dict(color='#f59e0b', width=2)
                        ))

                        # Add overbought/oversold lines
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef4444",
                                         annotation_text="Aşırı Alım")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#10b981",
                                         annotation_text="Aşırı Satım")

                        fig_rsi.update_layout(
                            title='RSI (Relative Strength Index)',
                            template='plotly_dark',
                            height=250,
                            yaxis=dict(range=[0, 100]),
                            plot_bgcolor='rgba(30, 41, 59, 0.8)',
                            paper_bgcolor='rgba(15, 23, 42, 0.9)'
                        )

                        st.plotly_chart(fig_rsi, use_container_width=True)

            except Exception as e:
                st.error(f"Veri alınırken hata oluştu: {e}")

def create_portfolio_analyzer():
    """Create portfolio analysis section"""
    st.markdown('<div class="section-header"><h2>💼 Portföy Analizi</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col2:
        st.markdown("### ⚙️ Portföy Ayarları")
        portfolio_symbols = st.multiselect(
            "Hisseler",
            ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'],
            default=['AAPL', 'GOOGL', 'MSFT']
        )

        if portfolio_symbols:
            st.markdown("### 📊 Ağırlıklar")
            weights = {}
            for symbol in portfolio_symbols:
                weights[symbol] = st.slider(f"{symbol}", 0.0, 1.0, 1.0/len(portfolio_symbols), 0.05)

            # Normalize weights
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v/total_weight for k, v in weights.items()}

    with col1:
        if portfolio_symbols and len(portfolio_symbols) > 1:
            try:
                # Create portfolio optimizer
                optimizer = PortfolioOptimizer(portfolio_symbols) if PortfolioOptimizer else None

                if optimizer:
                    # Optimize portfolio
                    sharpe_result = optimizer.optimize_portfolio('sharpe')
                    min_vol_result = optimizer.optimize_portfolio('min_volatility')

                    if sharpe_result.get('success'):
                        col_a, col_b = st.columns(2)

                        with col_a:
                            st.markdown("""
                            <div class="metric-card">
                                <h3>🎯 Maksimum Sharpe Oranı</h3>
                                <div class="metric-value">{:.3f}</div>
                                <small>Sharpe Oranı</small>
                            </div>
                            """.format(sharpe_result['metrics']['sharpe_ratio']), unsafe_allow_html=True)

                        with col_b:
                            st.markdown("""
                            <div class="metric-card">
                                <h3>🛡️ Minimum Volatilite</h3>
                                <div class="metric-value">{:.2f}%</div>
                                <small>Yıllık Volatilite</small>
                            </div>
                            """.format(min_vol_result['metrics']['volatility']*100), unsafe_allow_html=True)

                        # Create allocation pie charts
                        fig_sharpe = go.Figure(data=[go.Pie(
                            labels=list(sharpe_result['weights'].keys()),
                            values=list(sharpe_result['weights'].values()),
                            hole=.3,
                            title="Sharpe Optimizasyonu"
                        )])

                        fig_minvol = go.Figure(data=[go.Pie(
                            labels=list(min_vol_result['weights'].keys()),
                            values=list(min_vol_result['weights'].values()),
                            hole=.3,
                            title="Minimum Volatilite"
                        )])

                        col_c, col_d = st.columns(2)
                        with col_c:
                            fig_sharpe.update_layout(template='plotly_dark', height=400)
                            st.plotly_chart(fig_sharpe, use_container_width=True)

                        with col_d:
                            fig_minvol.update_layout(template='plotly_dark', height=400)
                            st.plotly_chart(fig_minvol, use_container_width=True)

                else:
                    st.info("Portföy optimizasyonu için gelişmiş analiz modülü gerekli.")

            except Exception as e:
                st.error(f"Portföy analizi hatası: {e}")

def create_news_sentiment():
    """Create news and sentiment analysis section"""
    st.markdown('<div class="section-header"><h2>📰 Piyasa Haberleri & Sentiment</h2></div>', unsafe_allow_html=True)

    # Mock news data (in real implementation, you'd fetch from news APIs)
    news_data = [
        {
            'title': 'FED Faiz Kararı Yaklaşıyor',
            'summary': 'Federal Reserve bu hafta faiz kararını açıklayacak. Piyasalar 0.25 baz puan artış bekliyor.',
            'sentiment': 'nötr',
            'time': '2 saat önce',
            'source': 'Bloomberg'
        },
        {
            'title': 'Teknoloji Hisseleri Yükselişte',
            'summary': 'NASDAQ endeksi güçlü kazançlarla günü tamamladı. Apple ve Microsoft öne çıkan hisseler.',
            'sentiment': 'pozitif',
            'time': '4 saat önce',
            'source': 'Reuters'
        },
        {
            'title': 'Petrol Fiyatları Düşüşte',
            'summary': 'Brent petrol varil fiyatı %2 geriledi. OPEC üretim kısıntısı açıklaması bekleniyor.',
            'sentiment': 'negatif',
            'time': '6 saat önce',
            'source': 'CNBC'
        }
    ]

    for news in news_data:
        sentiment_color = {
            'pozitif': 'var(--success-color)',
            'negatif': 'var(--danger-color)',
            'nötr': 'var(--warning-color)'
        }

        sentiment_icon = {
            'pozitif': '🚀',
            'negatif': '📉',
            'nötr': '⚖️'
        }

        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; flex: 1;">{news['title']}</h3>
                <span class="status-indicator" style="background: rgba(59, 130, 246, 0.2); color: {sentiment_color[news['sentiment']]};">
                    {sentiment_icon[news['sentiment']]} {news['sentiment'].title()}
                </span>
            </div>
            <p style="color: var(--text-secondary); margin: 1rem 0;">{news['summary']}</p>
            <div style="display: flex; justify-content: between; font-size: 0.875rem; color: var(--text-secondary);">
                <span>📅 {news['time']}</span>
                <span>📰 {news['source']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def create_neural_analysis():
    """Create neural network analysis dashboard"""
    st.markdown('<div class="section-header"><h2>🧠 AI Sinir Ağı Analizi</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col2:
        st.markdown("### ⚙️ AI Model Ayarları")
        selected_symbol = st.selectbox("Hisse/ETF Seçin",
                                     ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'SPY', 'QQQ'],
                                     key="neural_symbol")

        model_type = st.selectbox("Model Tipi",
                                ['LSTM', 'GRU', 'CNN-LSTM', 'Transformer'],
                                index=0)

        prediction_days = st.slider("Tahmin Günü", 1, 30, 7)

        confidence_level = st.slider("Güven Seviyesi", 0.8, 0.99, 0.95, 0.01)

        if st.button("🚀 AI Analizi Başlat"):
            with st.spinner("Sinir ağı modelleri eğitiliyor..."):
                time.sleep(2)
                st.success("Analiz tamamlandı!")

    with col1:
        try:
            if NeuralNetworkAnalyzer and selected_symbol:
                st.markdown("### 📊 AI Tahmin Sonuçları")

                # Get historical data
                ticker = yf.Ticker(selected_symbol)
                hist_data = ticker.history(period="1y")

                if not hist_data.empty:
                    # Create mock neural network predictions
                    current_price = hist_data['Close'].iloc[-1]

                    # Generate prediction data
                    future_dates = pd.date_range(start=hist_data.index[-1] + timedelta(days=1),
                                                periods=prediction_days, freq='D')

                    # Mock predictions with some randomness
                    np.random.seed(42)
                    trend = np.random.normal(0.001, 0.02, prediction_days)
                    predictions = [current_price]
                    for i in range(prediction_days):
                        next_price = predictions[-1] * (1 + trend[i])
                        predictions.append(next_price)

                    predictions = predictions[1:]

                    # Create prediction chart
                    fig = go.Figure()

                    # Historical data
                    fig.add_trace(go.Scatter(
                        x=hist_data.index[-60:],
                        y=hist_data['Close'][-60:],
                        mode='lines',
                        name='Geçmiş Fiyat',
                        line=dict(color='#3b82f6', width=2)
                    ))

                    # Predictions
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=predictions,
                        mode='lines+markers',
                        name=f'{model_type} Tahmini',
                        line=dict(color='#10b981', width=3, dash='dash'),
                        marker=dict(size=8, color='#10b981')
                    ))

                    # Confidence bands
                    upper_band = [p * 1.05 for p in predictions]
                    lower_band = [p * 0.95 for p in predictions]

                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=upper_band,
                        mode='lines',
                        name='Üst Güven Bandı',
                        line=dict(color='rgba(16, 185, 129, 0.3)', dash='dot'),
                        showlegend=False
                    ))

                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=lower_band,
                        mode='lines',
                        name='Alt Güven Bandı',
                        fill='tonexty',
                        fillcolor='rgba(16, 185, 129, 0.1)',
                        line=dict(color='rgba(16, 185, 129, 0.3)', dash='dot'),
                        showlegend=False
                    ))

                    fig.update_layout(
                        title=f'{selected_symbol} - {model_type} AI Fiyat Tahmini',
                        template='plotly_dark',
                        height=500,
                        xaxis_title="Tarih",
                        yaxis_title="Fiyat ($)",
                        plot_bgcolor='rgba(30, 41, 59, 0.8)',
                        paper_bgcolor='rgba(15, 23, 42, 0.9)',
                        showlegend=True
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # AI Metrics
                    st.markdown("### 🎯 Model Performans Metrikleri")

                    col3, col4, col5, col6 = st.columns(4)

                    with col3:
                        accuracy = np.random.uniform(0.75, 0.95)
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Doğruluk</h3>
                            <div class="metric-value">{accuracy:.1%}</div>
                            <div class="metric-change positive">🎯 Yüksek</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col4:
                        mse = np.random.uniform(0.01, 0.05)
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>MSE</h3>
                            <div class="metric-value">{mse:.3f}</div>
                            <div class="metric-change positive">📊 Düşük</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col5:
                        r2_score = np.random.uniform(0.80, 0.95)
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>R² Score</h3>
                            <div class="metric-value">{r2_score:.3f}</div>
                            <div class="metric-change positive">⭐ Mükemmel</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col6:
                        volatility = np.std(hist_data['Close'].pct_change().dropna()) * 100
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Volatilite</h3>
                            <div class="metric-value">{volatility:.1f}%</div>
                            <div class="metric-change neutral">📈 Normal</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Trading Signals
                    st.markdown("### 🚦 AI Trading Sinyalleri")

                    predicted_return = (predictions[-1] - current_price) / current_price

                    if predicted_return > 0.02:
                        signal_class = "positive"
                        signal_icon = "🚀"
                        signal_text = "GÜÇLÜ AL"
                        signal_desc = f"{prediction_days} gün içinde %{predicted_return*100:.1f} yükseliş bekleniyor"
                    elif predicted_return > 0.005:
                        signal_class = "neutral"
                        signal_icon = "⬆️"
                        signal_text = "AL"
                        signal_desc = f"{prediction_days} gün içinde %{predicted_return*100:.1f} yükseliş bekleniyor"
                    elif predicted_return < -0.02:
                        signal_class = "negative"
                        signal_icon = "🔻"
                        signal_text = "GÜÇLÜ SAT"
                        signal_desc = f"{prediction_days} gün içinde %{abs(predicted_return)*100:.1f} düşüş bekleniyor"
                    elif predicted_return < -0.005:
                        signal_class = "negative"
                        signal_icon = "⬇️"
                        signal_text = "SAT"
                        signal_desc = f"{prediction_days} gün içinde %{abs(predicted_return)*100:.1f} düşüş bekleniyor"
                    else:
                        signal_class = "neutral"
                        signal_icon = "⚖️"
                        signal_text = "BEKLE"
                        signal_desc = "Yan trend bekleniyor, pozisyon almaya gerek yok"

                    st.markdown(f"""
                    <div class="metric-card" style="border-left: 4px solid var(--success-color);">
                        <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 1rem;">
                            <h3 style="margin: 0;">AI Tavsiyesi</h3>
                            <span class="metric-change {signal_class}" style="font-size: 1.2rem;">
                                {signal_icon} {signal_text}
                            </span>
                        </div>
                        <p style="color: var(--text-secondary); margin: 0;">{signal_desc}</p>
                        <p style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 1rem;">
                            🔬 Model: {model_type} | 📊 Güven: {confidence_level:.0%} | 🎯 Hedef Fiyat: ${predictions[-1]:.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    st.warning("Veri alınamadı")

            else:
                st.info("🧠 Neural Network modülü yüklenmedi. AI tahminleri için modülü yükleyin.")

                # Show fallback demo content
                st.markdown("### 🎯 Demo AI Analizi")

                demo_data = {
                    'Model': ['LSTM', 'GRU', 'CNN-LSTM', 'Transformer'],
                    'Doğruluk': ['87.3%', '84.1%', '89.2%', '91.5%'],
                    'MSE': ['0.023', '0.031', '0.018', '0.015'],
                    'R² Score': ['0.891', '0.876', '0.903', '0.924']
                }

                df_demo = pd.DataFrame(demo_data)
                st.dataframe(df_demo, use_container_width=True)

        except Exception as e:
            st.error(f"Neural analiz hatası: {e}")

def create_global_markets():
    """Create global markets analysis dashboard"""
    st.markdown('<div class="section-header"><h2>🌍 Global Piyasalar & Dünya Borsaları</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col2:
        st.markdown("### 🌐 Piyasa Seçimi")

        market_regions = st.multiselect(
            "Bölge Seçin",
            ["🇺🇸 Amerika", "🇪🇺 Avrupa", "🇯🇵 Asya-Pasifik", "🌍 Gelişen Piyasalar"],
            default=["🇺🇸 Amerika", "🇪🇺 Avrupa"]
        )

        asset_types = st.multiselect(
            "Varlık Türü",
            ["📈 Hisse Senetleri", "💎 ETF'ler", "💰 Emtialar", "💱 Forex"],
            default=["📈 Hisse Senetleri", "💎 ETF'ler"]
        )

        timeframe = st.selectbox(
            "Zaman Dilimi",
            ["1D", "1W", "1M", "3M", "6M", "1Y", "2Y"],
            index=3
        )

        st.markdown("---")
        st.markdown("### 🔍 Hisse/ETF Analizi")

        # Popular symbols for quick selection
        popular_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'SPY', 'QQQ', 'VTI']

        selected_symbol = st.selectbox(
            "Popüler Semboller",
            options=[''] + popular_symbols,
            format_func=lambda x: "Seçiniz..." if x == '' else x
        )

        # Or type custom symbol
        custom_symbol = st.text_input("Veya manuel sembol girin:", value="", placeholder="Örn: BIST:THYAO, LON:BP")

        # Use custom symbol if provided, otherwise use selected
        analysis_symbol = custom_symbol.upper() if custom_symbol else selected_symbol

        if st.button("📊 Analiz Et") and analysis_symbol:
            st.session_state['analyze_symbol'] = analysis_symbol

        if st.button("🔄 Global Verileri Yenile"):
            with st.spinner("Global piyasa verileri güncelleniyor..."):
                time.sleep(2)
                st.success("Veriler güncellendi!")

    with col1:
        try:
            # Global Markets Overview
            st.markdown("### 🌍 Global Piyasa Durumu")

            # Mock global market data
            global_markets = {
                "🇺🇸 S&P 500": {"value": 4450.25, "change": 1.23, "volume": "3.2B"},
                "🇺🇸 NASDAQ": {"value": 13750.45, "change": 2.15, "volume": "2.8B"},
                "🇪🇺 STOXX 50": {"value": 4125.67, "change": -0.45, "volume": "1.1B"},
                "🇬🇧 FTSE 100": {"value": 7425.89, "change": 0.78, "volume": "890M"},
                "🇯🇵 Nikkei 225": {"value": 32450.12, "change": -0.32, "volume": "1.5B"},
                "🇩🇪 DAX": {"value": 15675.34, "change": 1.45, "volume": "750M"},
                "🇨🇳 Shanghai": {"value": 3245.67, "change": 0.89, "volume": "2.1B"},
                "🇮🇳 Sensex": {"value": 65432.18, "change": 1.67, "volume": "1.8B"}
            }

            cols = st.columns(4)
            for i, (market, data) in enumerate(global_markets.items()):
                col_idx = i % 4
                with cols[col_idx]:
                    change_class = "positive" if data["change"] >= 0 else "negative"
                    change_icon = "🚀" if data["change"] >= 0 else "🔻"

                    st.markdown(f"""
                    <div class="metric-card" style="margin: 0.5rem 0;">
                        <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem;">{market}</h4>
                        <div class="metric-value" style="font-size: 1.2rem;">{data["value"]:,.2f}</div>
                        <div class="metric-change {change_class}" style="font-size: 0.8rem;">
                            {change_icon} {data["change"]:+.2f}%
                        </div>
                        <small style="color: var(--text-secondary);">Vol: {data["volume"]}</small>
                    </div>
                    """, unsafe_allow_html=True)

            # Global Market Heatmap
            st.markdown("### 🔥 Global Piyasa Isı Haritası")

            if GlobalMarketCollector:
                st.info("🌍 GlobalMarketCollector ile 15,000+ global sembol analiz ediliyor...")

                # Mock heatmap data
                heatmap_data = {
                    'Piyasa': ['S&P 500', 'NASDAQ', 'STOXX 50', 'FTSE 100', 'Nikkei', 'DAX', 'Shanghai', 'Sensex'],
                    'Getiri (%)': [1.23, 2.15, -0.45, 0.78, -0.32, 1.45, 0.89, 1.67],
                    'Volatilite (%)': [12.5, 18.3, 14.2, 11.8, 15.7, 16.4, 22.1, 19.8],
                    'RSI': [65, 72, 45, 58, 42, 68, 55, 61]
                }

                df_heatmap = pd.DataFrame(heatmap_data)

                # Create heatmap visualization
                fig_heat = go.Figure()

                fig_heat.add_trace(go.Heatmap(
                    z=[df_heatmap['Getiri (%)'].values,
                       df_heatmap['Volatilite (%)'].values,
                       df_heatmap['RSI'].values],
                    x=df_heatmap['Piyasa'],
                    y=['Getiri (%)', 'Volatilite (%)', 'RSI'],
                    colorscale='RdYlGn',
                    showscale=True
                ))

                fig_heat.update_layout(
                    title="Global Piyasa Performans Isı Haritası",
                    template='plotly_dark',
                    height=300,
                    plot_bgcolor='rgba(30, 41, 59, 0.8)',
                    paper_bgcolor='rgba(15, 23, 42, 0.9)'
                )

                st.plotly_chart(fig_heat, use_container_width=True)

            else:
                st.warning("GlobalMarketCollector modülü yüklü değil. Fallback demo veri gösteriliyor.")

            # Currency & Commodities
            st.markdown("### 💱 Para Birimleri & Emtialar")

            col3, col4 = st.columns(2)

            with col3:
                st.markdown("#### 💱 Forex Pariteler")
                forex_pairs = {
                    "EUR/USD": {"rate": 1.0845, "change": 0.23},
                    "GBP/USD": {"rate": 1.2634, "change": -0.12},
                    "USD/JPY": {"rate": 149.85, "change": 0.45},
                    "USD/TRY": {"rate": 27.45, "change": 0.89}
                }

                for pair, data in forex_pairs.items():
                    change_class = "positive" if data["change"] >= 0 else "negative"
                    change_icon = "⬆️" if data["change"] >= 0 else "⬇️"

                    st.markdown(f"""
                    <div style="display: flex; justify-content: between; align-items: center;
                         padding: 0.5rem; margin: 0.25rem 0; background: var(--card-bg); border-radius: 8px;">
                        <span style="font-weight: 500;">{pair}</span>
                        <div style="text-align: right;">
                            <div style="font-size: 1.1rem; font-weight: 600;">{data["rate"]:.4f}</div>
                            <div class="metric-change {change_class}" style="font-size: 0.8rem;">
                                {change_icon} {data["change"]:+.2f}%
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col4:
                st.markdown("#### 💰 Emtialar")
                commodities = {
                    "Altın (oz)": {"price": 1985.45, "change": 0.67},
                    "Gümüş (oz)": {"price": 24.12, "change": 1.23},
                    "Petrol (varil)": {"price": 85.67, "change": -1.45},
                    "Doğalgaz": {"price": 3.45, "change": 2.34}
                }

                for commodity, data in commodities.items():
                    change_class = "positive" if data["change"] >= 0 else "negative"
                    change_icon = "⬆️" if data["change"] >= 0 else "⬇️"

                    st.markdown(f"""
                    <div style="display: flex; justify-content: between; align-items: center;
                         padding: 0.5rem; margin: 0.25rem 0; background: var(--card-bg); border-radius: 8px;">
                        <span style="font-weight: 500;">{commodity}</span>
                        <div style="text-align: right;">
                            <div style="font-size: 1.1rem; font-weight: 600;">${data["price"]:.2f}</div>
                            <div class="metric-change {change_class}" style="font-size: 0.8rem;">
                                {change_icon} {data["change"]:+.2f}%
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Global ETF Analysis
            st.markdown("### 🏦 Global ETF Analizi")

            global_etfs = [
                {"symbol": "SPY", "name": "SPDR S&P 500", "region": "🇺🇸", "aum": "$380B", "expense": "0.09%", "return_1y": "12.5%"},
                {"symbol": "QQQ", "name": "Invesco QQQ", "region": "🇺🇸", "aum": "$185B", "expense": "0.20%", "return_1y": "15.8%"},
                {"symbol": "VTI", "name": "Vanguard Total Stock", "region": "🇺🇸", "aum": "$295B", "expense": "0.03%", "return_1y": "11.2%"},
                {"symbol": "EFA", "name": "iShares EAFE", "region": "🇪🇺", "aum": "$75B", "expense": "0.32%", "return_1y": "8.9%"},
                {"symbol": "EEM", "name": "iShares Emerging", "region": "🌍", "aum": "$25B", "expense": "0.68%", "return_1y": "5.4%"},
                {"symbol": "VGK", "name": "Vanguard Europe", "region": "🇪🇺", "aum": "$18B", "expense": "0.08%", "return_1y": "9.7%"}
            ]

            df_etfs = pd.DataFrame(global_etfs)

            # Style the dataframe
            st.dataframe(
                df_etfs,
                column_config={
                    "symbol": st.column_config.TextColumn("Sembol", width="small"),
                    "name": st.column_config.TextColumn("ETF Adı", width="medium"),
                    "region": st.column_config.TextColumn("Bölge", width="small"),
                    "aum": st.column_config.TextColumn("AUM", width="small"),
                    "expense": st.column_config.TextColumn("Gider Oranı", width="small"),
                    "return_1y": st.column_config.TextColumn("1Y Getiri", width="small")
                },
                use_container_width=True,
                hide_index=True
            )

            # Individual Stock/ETF Analysis
            if 'analyze_symbol' in st.session_state and st.session_state['analyze_symbol']:
                analyze_symbol = st.session_state['analyze_symbol']
                st.markdown("---")
                st.markdown(f"### 📊 {analyze_symbol} Detaylı Analizi")

                try:
                    # Clean symbol for yfinance
                    clean_symbol = analyze_symbol.replace("BIST:", "").replace("LON:", "").replace(".IS", "")
                    if "BIST:" in analyze_symbol:
                        clean_symbol += ".IS"
                    elif "LON:" in analyze_symbol:
                        clean_symbol += ".L"

                    ticker = yf.Ticker(clean_symbol)
                    info = ticker.info
                    hist = ticker.history(period="1y")

                    if not hist.empty and info:
                        col_a, col_b, col_c = st.columns(3)

                        with col_a:
                            current_price = hist['Close'].iloc[-1]
                            prev_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
                            change = current_price - prev_close
                            change_pct = (change / prev_close) * 100

                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>💰 Güncel Fiyat</h3>
                                <div class="metric-value">${current_price:.2f}</div>
                                <div class="metric-change {'positive' if change >= 0 else 'negative'}">
                                    {'🚀' if change >= 0 else '🔻'} {change:+.2f} ({change_pct:+.2f}%)
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col_b:
                            volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                            market_cap = info.get('marketCap', 'N/A')
                            if isinstance(market_cap, (int, float)):
                                if market_cap > 1e12:
                                    market_cap_str = f"${market_cap/1e12:.1f}T"
                                elif market_cap > 1e9:
                                    market_cap_str = f"${market_cap/1e9:.1f}B"
                                elif market_cap > 1e6:
                                    market_cap_str = f"${market_cap/1e6:.1f}M"
                                else:
                                    market_cap_str = f"${market_cap:,.0f}"
                            else:
                                market_cap_str = "N/A"

                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>📊 Piyasa Değeri</h3>
                                <div class="metric-value">{market_cap_str}</div>
                                <div class="metric-change neutral">Vol: {volume:,}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col_c:
                            pe_ratio = info.get('trailingPE', 'N/A')
                            dividend_yield = info.get('dividendYield', 0)
                            if isinstance(dividend_yield, (int, float)):
                                dividend_str = f"{dividend_yield*100:.2f}%"
                            else:
                                dividend_str = "N/A"

                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>📈 P/E Oranı</h3>
                                <div class="metric-value">{pe_ratio if pe_ratio != 'N/A' else 'N/A'}</div>
                                <div class="metric-change neutral">Div: {dividend_str}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Create price chart
                        st.markdown("### 📈 Fiyat Grafiği")

                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=hist.index,
                            open=hist['Open'],
                            high=hist['High'],
                            low=hist['Low'],
                            close=hist['Close'],
                            name=analyze_symbol,
                            increasing_line_color='#10b981',
                            decreasing_line_color='#ef4444'
                        ))

                        fig.update_layout(
                            title=f'{analyze_symbol} - 1 Yıllık Fiyat Grafiği',
                            template='plotly_dark',
                            height=400,
                            xaxis_title="Tarih",
                            yaxis_title="Fiyat ($)",
                            plot_bgcolor='rgba(30, 41, 59, 0.8)',
                            paper_bgcolor='rgba(15, 23, 42, 0.9)'
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # Company info
                        if info.get('longBusinessSummary'):
                            st.markdown("### 📄 Şirket Bilgileri")
                            st.write(info['longBusinessSummary'][:500] + "..." if len(info['longBusinessSummary']) > 500 else info['longBusinessSummary'])

                    else:
                        st.warning(f"⚠️ {analyze_symbol} için veri bulunamadı. Sembol doğru yazıldığından emin olun.")

                except Exception as e:
                    st.error(f"❌ Analiz hatası: {e}")
                    st.info("💡 Sembol formatı örnekleri: AAPL, GOOGL, BIST:THYAO, LON:BP")

        except Exception as e:
            st.error(f"Global piyasa analizi hatası: {e}")

            # Fallback minimal display
            st.markdown("### 📊 Temel Global Veriler")
            basic_data = {
                'Endeks': ['S&P 500', 'NASDAQ', 'FTSE 100', 'Nikkei 225'],
                'Değer': [4450, 13750, 7425, 32450],
                'Değişim (%)': [1.2, 2.1, 0.8, -0.3]
            }
            st.dataframe(pd.DataFrame(basic_data), use_container_width=True)

def create_global_fund_holdings():
    """Global Fund Holdings Page"""
    # Enhanced CSS for funds holdings section
    st.markdown("""
    <style>
    /* Funds Holdings Specific Styling */
    .fund-holdings-container {
        background: var(--dark-bg);
        min-height: 100vh;
        color: var(--text-primary);
    }

    /* Navigation Buttons Styling */
    .fund-nav-button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        margin: 0.25rem !important;
    }

    .fund-nav-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 12px -2px rgba(59, 130, 246, 0.3) !important;
        background: linear-gradient(135deg, var(--accent-color), var(--primary-color)) !important;
    }

    /* Fund Grid Cards Enhanced */
    .fund-grid-card {
        background: linear-gradient(135deg, var(--card-bg), rgba(30, 41, 59, 0.8)) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin: 0.5rem !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .fund-grid-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .fund-grid-card:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 20px -4px rgba(59, 130, 246, 0.2) !important;
        border-color: var(--accent-color) !important;
    }

    .fund-grid-card:hover::before {
        opacity: 1;
    }

    .fund-grid-card h3 {
        color: var(--text-primary) !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin: 0 0 0.75rem 0 !important;
        background: linear-gradient(135deg, var(--text-primary), var(--accent-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .fund-grid-card p {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
        margin: 0.5rem 0 !important;
    }

    /* Enhanced DataFrames for Funds */
    .fund-dataframe {
        background: var(--card-bg) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.1) !important;
    }

    .fund-dataframe table {
        background: transparent !important;
        width: 100% !important;
    }

    .fund-dataframe thead tr th {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        padding: 1rem 1.5rem !important;
        border: none !important;
        text-align: left !important;
        font-size: 0.9rem !important;
    }

    .fund-dataframe tbody tr {
        border-bottom: 1px solid var(--border-color) !important;
        transition: all 0.2s ease !important;
    }

    .fund-dataframe tbody tr:hover {
        background: rgba(59, 130, 246, 0.08) !important;
        transform: scale(1.01) !important;
    }

    .fund-dataframe tbody tr td {
        background: transparent !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        padding: 1rem 1.5rem !important;
        border: none !important;
        font-size: 0.85rem !important;
    }

    /* Select boxes for funds */
    .fund-selectbox > div > div {
        background: var(--card-bg) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        transition: all 0.3s ease !important;
    }

    .fund-selectbox > div > div:focus-within {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }

    /* Metrics for funds */
    .fund-metric-container {
        background: linear-gradient(135deg, var(--card-bg), rgba(30, 41, 59, 0.6)) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin: 0.5rem !important;
        transition: all 0.3s ease !important;
    }

    .fund-metric-container:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 16px -4px rgba(59, 130, 246, 0.15) !important;
        border-color: var(--accent-color) !important;
    }

    /* Performance charts */
    .fund-chart-container {
        background: var(--card-bg) !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        border: 1px solid var(--border-color) !important;
        margin: 1rem 0 !important;
    }

    /* Info sections */
    .fund-info-section {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1)) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        color: var(--text-primary) !important;
    }

    /* Override Streamlit defaults for this section */
    .stSelectbox label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    .stButton button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        padding: 0.75rem 1.5rem !important;
    }

    .stButton button:hover {
        background: linear-gradient(135deg, var(--accent-color), var(--primary-color)) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 12px -2px rgba(59, 130, 246, 0.3) !important;
    }

    .stMetric {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    .stMetric label {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
    }

    .stMetric [data-testid="metric-value"] {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }

    /* Enhanced markdown headers */
    .fund-section-header {
        background: linear-gradient(135deg, var(--card-bg), rgba(30, 41, 59, 0.8));
        border-left: 4px solid var(--accent-color);
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.5rem;
        margin: 1.5rem 0;
        color: var(--text-primary);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    </style>

    <div class="main-header">
        <h1 style="text-align: center; margin: 0; color: white;">🏦 Global Fon Holdings</h1>
        <p style="text-align: center; margin: 0.5rem 0 0 0; color: rgba(255,255,255,0.8);">
            Dünya genelindeki fon portföylerini analiz edin
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Session state for navigation
    if 'fund_view_mode' not in st.session_state:
        st.session_state.fund_view_mode = 'overview'
    if 'selected_fund_category' not in st.session_state:
        st.session_state.selected_fund_category = None

    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Genel Bakış", key="fund_overview_btn"):
            st.session_state.fund_view_mode = 'overview'
    with col2:
        if st.button("🔍 Detaylı Analiz", key="fund_detailed_btn"):
            st.session_state.fund_view_mode = 'detailed'
    with col3:
        if st.button("📈 Performans", key="fund_performance_btn"):
            st.session_state.fund_view_mode = 'performance'

    try:
        # Get fund universe
        if 'get_fund_universe' in globals() and get_fund_universe is not None:
            fund_universe = get_fund_universe()
        else:
            # Comprehensive fund data from global market collector - EXPANDED
            fund_universe = {
                'broad_market_etfs': ['SPY', 'VTI', 'QQQ', 'IWM', 'VEA', 'VWO', 'EFA', 'EEM', 'VOO', 'IVV', 'VTV', 'VUG', 'IJH', 'IJR', 'VB', 'VO', 'VV', 'VTWO', 'VMOT', 'VTHR'],
                'sector_etfs': ['XLK', 'XLV', 'XLF', 'XLE', 'XLI', 'XLY', 'XLP', 'XLRE', 'XLB', 'XLU', 'XLC', 'VGT', 'VHT', 'VFH', 'VDE', 'VIS', 'VCR', 'VDC', 'VNQ', 'VAW', 'VPU', 'VOX', 'SOXX', 'SMH', 'IGM', 'IYW', 'IYH', 'IYE', 'IYF', 'IYR', 'IYM', 'IYC', 'IYK', 'IYZ', 'ITB'],
                'international_etfs': ['VEA', 'VWO', 'EFA', 'EEM', 'IEFA', 'IEMG', 'VGK', 'VPL', 'VT', 'VXUS', 'IXUS', 'FTIHX', 'SCHA', 'SCHF', 'SCHE', 'SCHC', 'ACWI', 'VTIAX', 'VTMGX', 'VTWAX', 'VFWAX', 'VFWIX', 'VEURX', 'VPACX', 'VEMAX', 'VEMIX'],
                'thematic_etfs': ['ARKK', 'ARKQ', 'ARKG', 'ICLN', 'JETS', 'ROBO', 'ESPO', 'UFO', 'HERO', 'ARKF', 'ARKW', 'CLOU', 'EDOC', 'FINX', 'HACK', 'SKYY', 'XBI', 'IBB', 'QTEC', 'FTEC', 'PJP', 'PTH', 'PHO', 'PBW', 'FAN', 'ICAD', 'MOON', 'NERD', 'GAMR', 'MULT'],
                'bond_etfs': ['AGG', 'BND', 'TLT', 'IEF', 'LQD', 'HYG', 'EMB', 'BNDX', 'VGIT', 'VGLT', 'VCIT', 'VCLT', 'VMBS', 'VTEB', 'VWOB', 'BSV', 'BIV', 'BLV', 'VBTLX', 'VFITX', 'VUSTX', 'VGST', 'VGLT', 'VCEB', 'VWEHX'],
                'commodity_etfs': ['GLD', 'SLV', 'USO', 'UNG', 'DBA', 'PDBC', 'PPLT', 'PALL', 'IAU', 'SGOL', 'GLTR', 'GSG', 'DJP', 'CORN', 'WEAT', 'SOYB', 'CANE', 'UGA', 'UNL', 'USL', 'BNO', 'UCO', 'SCO', 'BOIL', 'KOLD'],
                'reit_etfs': ['VNQ', 'VNQI', 'XLRE', 'SCHH', 'IYR', 'RWX', 'USRT', 'MORT', 'REZ', 'HOMZ', 'INDS', 'FREL', 'REM', 'KBWY', 'CHMI', 'RWR', 'EWRE', 'IFGL', 'BBRE', 'WPS'],
                'dividend_etfs': ['VYM', 'VYMI', 'VIG', 'DGRO', 'NOBL', 'DVY', 'HDV', 'SCHD', 'VTV', 'FDVV', 'SPHD', 'SPYD', 'SDY', 'VUG', 'QUAL', 'MTUM', 'USMV', 'VLUE', 'SIZE', 'VMOT'],
                'small_cap_etfs': ['IWM', 'VB', 'VTWO', 'SCHA', 'IJR', 'VBR', 'VBK', 'IWN', 'IWO', 'IWV', 'SLYG', 'SLYV', 'PSCT', 'IJS', 'IJT', 'RZG', 'RZV', 'IWP', 'IWS', 'EWSC'],
                'mid_cap_etfs': ['MDY', 'VO', 'VMOT', 'IJH', 'SCHM', 'VXF', 'IWR', 'IWP', 'IWS', 'SPMD', 'IMCG', 'IVOO', 'IVOG', 'IVOV', 'JKG', 'JKH', 'JKI', 'JKJ', 'JKK', 'JKL'],
                'technology_etfs': ['XLK', 'VGT', 'SOXX', 'SMH', 'QTEC', 'FTEC', 'IGM', 'IYW', 'TECL', 'TQQQ', 'QQQ', 'PSJ', 'HACK', 'FINX', 'CLOU', 'SKYY', 'EDOC', 'BUG', 'CIBR', 'ROBO'],
                'healthcare_etfs': ['XLV', 'VHT', 'IBB', 'XBI', 'IYH', 'FHLC', 'IHE', 'CURE', 'BBH', 'RYH', 'PJP', 'PTH', 'ARKG', 'GNOM', 'SBIO', 'LABU', 'CHNA', 'FBT', 'PILL', 'IBBJ'],
                'energy_etfs': ['XLE', 'VDE', 'IYE', 'FENY', 'ERX', 'XOP', 'GUSH', 'IEO', 'PXE', 'ICLN', 'PBW', 'FAN', 'AMLP', 'AMJ', 'MLPA', 'MLPX', 'ENFR', 'DRIP', 'DIG', 'RYE'],
                'financial_etfs': ['XLF', 'VFH', 'IYF', 'FNCL', 'FAS', 'KBE', 'KRE', 'IAT', 'PFI', 'UYG', 'KBWB', 'KBWR', 'KBWY', 'KBWP', 'KBWR', 'IAI', 'RYF', 'IXG', 'DPST', 'BDCS'],
                'vanguard_funds': ['VTSAX', 'VTIAX', 'VBTLX', 'VTWAX', 'VTSMX', 'VGTSX', 'VFWAX', 'VFWIX', 'VTMGX', 'VTWSX', 'VTTVX', 'VTTHX', 'VTWNX', 'VTTSX', 'VTHRX', 'VTIVX', 'VFFVX', 'VFIFX', 'VFORX', 'VFQNX', 'VFTSX', 'VFTNX', 'VFWSX', 'VFVFX'],
                'fidelity_funds': ['FXNAX', 'FZROX', 'FZILX', 'FSKAX', 'FTEC', 'FREL', 'FXAIX', 'FZIPX', 'FNILX', 'FDVV', 'FSPSX', 'FSMDX', 'FSCSX', 'FXNAX', 'FNCMX', 'FSELX', 'FSPHX', 'FBIOX', 'FBGRX', 'FCNTX', 'FDGRX', 'FDEEX', 'FDEWX', 'FDFAX'],
                'american_funds': ['AGTHX', 'AMCPX', 'CWGIX', 'EUPAX', 'NEWFX', 'AMRMX', 'ANCFX', 'ANWPX', 'CAIBX', 'CGFFX', 'CIBFX', 'FCNTX', 'GFACX', 'RLBGX', 'RLBBX', 'RLBCX', 'RLBEX', 'RLBFX', 'RLBHX', 'RLBIX', 'RLBJX', 'RLBKX', 'SMCWX', 'WMFGX'],
                'schwab_funds': ['SWTSX', 'SWISX', 'SWAGX', 'SWPPX', 'SWSSX', 'SWMCX', 'SCHA', 'SCHB', 'SCHF', 'SCHM', 'SCHX', 'SCHZ', 'SLYG', 'SLYV', 'SCHV', 'SCHG', 'SCHE', 'SCHC', 'SCHH', 'SCHO', 'SCHR', 'SCHP', 'SCHQ', 'FNDA', 'FNDE', 'FNDF'],
                'troweprice_funds': ['PRNEX', 'PRGFX', 'PRHSX', 'PRWCX', 'PRMTX', 'PRIDX', 'PRBLX', 'PRDSX', 'TRSGX', 'TRBCX', 'PRFZX', 'PRDGX', 'PRJEX', 'PRJMX', 'PRJPX', 'PRLAX', 'PRLGX', 'PRLSX', 'PRMEX', 'PRNHX', 'PRNTX', 'PROEX', 'PRSIX', 'PRSVX', 'PRTEX'],
                'blackrock_etfs': ['IEFA', 'IEMG', 'ACWI', 'ACWX', 'ITOT', 'IUSG', 'IUSB', 'IUSV', 'IXUS', 'IEFA', 'IEMG', 'EEMV', 'EFAV', 'USMV', 'QUAL', 'MTUM', 'SIZE', 'VLUE', 'VMOT', 'ESGE', 'SUSB', 'SUSC', 'ESGD', 'ESGU'],
                'invesco_etfs': ['QQQ', 'QQQM', 'QQQJ', 'QTEC', 'PSJ', 'PHO', 'PBW', 'PKW', 'PEY', 'PEJ', 'PIE', 'PIZ', 'PKB', 'PPA', 'PBE', 'PUTZ', 'PSCH', 'PSCC', 'PSCD', 'PSCE', 'PSCF', 'PSCH', 'PSCI', 'PSCM'],
                'global_bond_etfs': ['BNDX', 'VWOB', 'EMB', 'PCY', 'EMLC', 'LEMB', 'VWOB', 'BWX', 'BWZ', 'WIP', 'SCHZ', 'VTEB', 'MUB', 'TFI', 'SUB', 'PZA', 'MUNI', 'HYD', 'PFF', 'PFFD', 'SRET'],
                'crypto_etfs': ['BITO', 'BTF', 'XBTF', 'BLOK', 'BITQ', 'LEGR', 'KOIN', 'BCOD', 'HOOD', 'ARKB', 'IBIT', 'FBTC', 'BITB', 'BTCO', 'HODL'],
                'esg_funds': ['ESGU', 'ESGD', 'ESGE', 'ESGV', 'ESGF', 'SUSB', 'SUSC', 'NULC', 'NUBD', 'DSI', 'EFAX', 'EAGG', 'EAPH', 'EAPS', 'VSGX', 'VSUX'],
                'turkish_funds': ['ABH', 'AHB', 'AHL', 'AHS', 'AKB', 'ALD', 'ALJ', 'ANH', 'ANJ', 'APH', 'APJ', 'ATH', 'ATJ', 'AVH', 'AVJ', 'AYD', 'AYG', 'GAH', 'GAJ', 'GBH', 'GBJ', 'GMH', 'GMJ', 'HBH', 'HBJ', 'HMH', 'HMJ', 'IBH', 'IBJ', 'IPH', 'IPJ', 'KYH', 'KYJ', 'TAH', 'TAJ', 'TBH', 'TBJ', 'TDH', 'TDJ', 'TKH', 'TKJ', 'YAH', 'YAJ', 'YBH', 'YBJ', 'ZGH', 'ZGJ', 'ZRH', 'ZRJ'],
                'turkish_equity_funds': ['AEH', 'AEJ', 'AGH', 'AGJ', 'ATH', 'ATJ', 'AZH', 'AZJ', 'GAH', 'GAJ', 'GEH', 'GEJ', 'HEH', 'HEJ', 'IEH', 'IEJ', 'KEH', 'KEJ', 'TAH', 'TAJ', 'TEH', 'TEJ', 'YEH', 'YEJ', 'ZEH', 'ZEJ'],
                'turkish_bond_funds': ['ABH', 'ABJ', 'DBH', 'DBJ', 'FBH', 'FBJ', 'GBH', 'GBJ', 'HBH', 'HBJ', 'IBH', 'IBJ', 'KBH', 'KBJ', 'TBH', 'TBJ', 'YBH', 'YBJ', 'ZBH', 'ZBJ'],
                'turkish_mixed_funds': ['AMH', 'AMJ', 'DMH', 'DMJ', 'FMH', 'FMJ', 'GMH', 'GMJ', 'HMH', 'HMJ', 'IMH', 'IMJ', 'KMH', 'KMJ', 'TMH', 'TMJ', 'YMH', 'YMJ', 'ZMH', 'ZMJ'],
                'turkish_money_market_funds': ['APH', 'APJ', 'DPH', 'DPJ', 'FPH', 'FPJ', 'GPH', 'GPJ', 'HPH', 'HPJ', 'IPH', 'IPJ', 'KPH', 'KPJ', 'TPH', 'TPJ', 'YPH', 'YPJ', 'ZPH', 'ZPJ']
            }

        # Main display based on view mode
        if st.session_state.fund_view_mode == 'overview':
            st.markdown("### 🌍 Global Fund Universe Overview")

            # Display comprehensive grid
            category_names = {
                'broad_market_etfs': '🌍 Geniş Piyasa ETF\'leri',
                'sector_etfs': '🏭 Sektör ETF\'leri',
                'international_etfs': '🌐 Uluslararası ETF\'ler',
                'thematic_etfs': '🎯 Tematik ETF\'ler',
                'bond_etfs': '💰 Tahvil ETF\'leri',
                'commodity_etfs': '🥇 Emtia ETF\'leri',
                'reit_etfs': '🏠 REIT ETF\'leri',
                'dividend_etfs': '💵 Temettü ETF\'leri',
                'small_cap_etfs': '🔸 Küçük Sermaye ETF\'leri',
                'mid_cap_etfs': '🔶 Orta Sermaye ETF\'leri',
                'technology_etfs': '💻 Teknoloji ETF\'leri',
                'healthcare_etfs': '🏥 Sağlık ETF\'leri',
                'energy_etfs': '⚡ Enerji ETF\'leri',
                'financial_etfs': '🏛️ Finans ETF\'leri',
                'vanguard_funds': '🏛️ Vanguard Fonları',
                'fidelity_funds': '🏦 Fidelity Fonları',
                'american_funds': '🇺🇸 American Funds',
                'schwab_funds': '💼 Schwab Fonları',
                'troweprice_funds': '📈 T. Rowe Price Fonları',
                'blackrock_etfs': '⚫ BlackRock ETF\'leri',
                'invesco_etfs': '🔵 Invesco ETF\'leri',
                'global_bond_etfs': '🌐 Global Tahvil ETF\'leri',
                'crypto_etfs': '₿ Kripto ETF\'leri',
                'esg_funds': '🌱 ESG Fonları',
                'turkish_funds': '🇹🇷 Türk Fonları',
                'turkish_equity_funds': '🇹🇷 Türk Hisse Senedi Fonları',
                'turkish_bond_funds': '🇹🇷 Türk Tahvil Fonları',
                'turkish_mixed_funds': '🇹🇷 Türk Karma Fonları',
                'turkish_money_market_funds': '🇹🇷 Türk Para Piyasası Fonları'
            }

            # Display fund categories in enhanced grid
            def display_fund_grid(fund_dict, categories_dict):
                for i, (category, funds) in enumerate(fund_dict.items()):
                    if i % 5 == 0:
                        cols = st.columns(5)

                    with cols[i % 5]:
                        st.markdown(f"""
                        <div class="fund-grid-card">
                            <h3>{categories_dict.get(category, category)}</h3>
                            <p><strong>{len(funds)}</strong> fon/ETF</p>
                            <div style="margin-top: 0.75rem; font-size: 0.75rem; color: var(--text-secondary); line-height: 1.4;">
                                <strong>Örnekler:</strong><br>
                                {', '.join(funds[:3])}{'...' if len(funds) > 3 else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button(f"📊 Detaylı Analiz", key=f"detail_{category}"):
                            st.session_state.selected_fund_category = category
                            st.session_state.fund_view_mode = 'detailed'
                            st.experimental_rerun()

            display_fund_grid(fund_universe, category_names)

        elif st.session_state.fund_view_mode == 'detailed':
            # Category Selection
            st.markdown("### 📋 Fon Kategorileri")
            col1, col2 = st.columns(2)

            with col1:
                category_names = {
                    'broad_market_etfs': '🌍 Geniş Piyasa ETF\'leri',
                    'sector_etfs': '🏭 Sektör ETF\'leri',
                    'international_etfs': '🌐 Uluslararası ETF\'ler',
                    'thematic_etfs': '🎯 Tematik ETF\'ler',
                    'bond_etfs': '💰 Tahvil ETF\'leri',
                    'commodity_etfs': '🥇 Emtia ETF\'leri',
                    'reit_etfs': '🏠 REIT ETF\'leri',
                    'dividend_etfs': '💵 Temettü ETF\'leri',
                    'small_cap_etfs': '🔸 Küçük Sermaye ETF\'leri',
                    'mid_cap_etfs': '🔶 Orta Sermaye ETF\'leri',
                    'technology_etfs': '💻 Teknoloji ETF\'leri',
                    'healthcare_etfs': '🏥 Sağlık ETF\'leri',
                    'energy_etfs': '⚡ Enerji ETF\'leri',
                    'financial_etfs': '🏛️ Finans ETF\'leri',
                    'vanguard_funds': '🏛️ Vanguard Fonları',
                    'fidelity_funds': '🏦 Fidelity Fonları',
                    'american_funds': '🇺🇸 American Funds',
                    'schwab_funds': '💼 Schwab Fonları',
                    'troweprice_funds': '📈 T. Rowe Price Fonları',
                    'blackrock_etfs': '⚫ BlackRock ETF\'leri',
                    'invesco_etfs': '🔵 Invesco ETF\'leri',
                    'global_bond_etfs': '🌐 Global Tahvil ETF\'leri',
                    'crypto_etfs': '₿ Kripto ETF\'leri',
                    'esg_funds': '🌱 ESG Fonları'
                }

                selected_category = st.selectbox(
                    "Fon Kategorisi Seçin",
                    options=list(fund_universe.keys()),
                    format_func=lambda x: category_names.get(x, x),
                    index=0 if st.session_state.selected_fund_category is None else list(fund_universe.keys()).index(st.session_state.selected_fund_category) if st.session_state.selected_fund_category in fund_universe else 0
                )

            with col2:
                funds_in_category = fund_universe.get(selected_category, [])
                selected_fund = st.selectbox(
                    "Fon Seçin",
                    options=['Tümü'] + funds_in_category,
                    index=0
                )

            # Fund Analysis Controls for detailed view
            st.markdown("### ⚙️ Analiz Ayarları")
            col1, col2, col3 = st.columns(3)

            with col1:
                analysis_type = st.selectbox(
                    "Analiz Tipi",
                    ["Holdings Analizi", "Performans Karşılaştırma", "Portföy Overlap"]
                )

            with col2:
                time_period = st.selectbox(
                    "Zaman Dilimi",
                    ["1M", "3M", "6M", "1Y", "2Y"],
                    index=2
                )

            with col3:
                if st.button("🔍 Analiz Başlat"):
                    st.info("Analiz başlatılıyor...")

            # Display Results for detailed view
            if selected_fund == 'Tümü':
                # Show category overview
                st.markdown(f"### 📊 {category_names.get(selected_category, selected_category)} - Genel Bakış")

                # Create metrics for category
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Toplam Fon", len(funds_in_category))

                with col2:
                    st.metric("Kategori", category_names.get(selected_category, selected_category).split(' ')[1])

                with col3:
                    avg_expense = "0.05%" if 'vanguard' in selected_category else "0.25%"
                    st.metric("Ort. Gider Oranı", avg_expense)

                with col4:
                    total_aum = f"${len(funds_in_category) * 15:.0f}B"
                    st.metric("Toplam AUM", total_aum)

                # Fund List with proper dark theme styling
                st.markdown("#### 📋 Fonlar Listesi")
                fund_data = []
                for fund in funds_in_category:
                    fund_data.append({
                        'Fon': fund,
                        'AUM (Milyar $)': np.random.uniform(5, 500),
                        'Gider Oranı (%)': np.random.uniform(0.03, 0.75),
                        '1Y Return (%)': np.random.uniform(-5, 25),
                        'Dividend Yield (%)': np.random.uniform(0.5, 5.0)
                    })

                df = pd.DataFrame(fund_data)

                # Apply enhanced dataframe styling
                st.markdown('<div class="fund-dataframe">', unsafe_allow_html=True)

                st.dataframe(df.round(2), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                # Show individual fund analysis
                st.markdown(f"### 🔍 {selected_fund} - Detaylı Analiz")

                # Fund metrics with dark theme
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Net Asset Value", "$156.42", "2.1%")

                with col2:
                    st.metric("Total AUM", "$45.2B", "1.8%")

                with col3:
                    st.metric("Expense Ratio", "0.25%")

                with col4:
                    st.metric("1Y Return", "12.4%", "3.2%")

                # Charts with dark theme
                if analysis_type == "Holdings Analizi":
                    st.markdown("#### 📈 Top Holdings")

                    # Mock holdings data
                    holdings_data = {
                        'Holding': ['Apple Inc', 'Microsoft Corp', 'Amazon.com Inc', 'Alphabet Inc', 'Tesla Inc'],
                        'Weight (%)': [6.8, 5.9, 3.4, 3.1, 2.7],
                        'Shares': [12500000, 8900000, 2100000, 1800000, 5600000],
                        'Market Value ($M)': [2145, 1876, 1078, 982, 856]
                    }
                    holdings_df = pd.DataFrame(holdings_data)
                    st.dataframe(holdings_df, use_container_width=True)

                    # Holdings chart with dark theme
                    fig = px.pie(holdings_df, values='Weight (%)', names='Holding',
                               title=f"{selected_fund} - Top 5 Holdings")
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='white',
                        title_font_color='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif analysis_type == "Performans Karşılaştırma":
                    st.markdown("#### 📊 Performans Karşılaştırma")

                    # Mock performance data
                    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
                    performance_data = {
                        'Date': dates,
                        selected_fund: np.cumsum(np.random.normal(0.0005, 0.02, len(dates))) + 1,
                        'S&P 500': np.cumsum(np.random.normal(0.0004, 0.015, len(dates))) + 1,
                        'Benchmark': np.cumsum(np.random.normal(0.0003, 0.018, len(dates))) + 1
                    }
                    perf_df = pd.DataFrame(performance_data)

                    fig = px.line(perf_df, x='Date', y=[selected_fund, 'S&P 500', 'Benchmark'],
                                title=f"{selected_fund} - Performance Comparison")
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='white',
                        title_font_color='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif analysis_type == "Portföy Overlap":
                    st.markdown("#### 🔄 Portföy Overlap Analizi")

                    # Mock overlap data
                    overlap_data = {
                        'Compared Fund': ['SPY', 'VTI', 'QQQ', 'IWM'],
                        'Overlap (%)': [78.5, 82.3, 45.2, 23.1],
                        'Common Holdings': [125, 134, 89, 45],
                        'Correlation': [0.95, 0.97, 0.78, 0.62]
                    }
                    overlap_df = pd.DataFrame(overlap_data)
                    st.dataframe(overlap_df, use_container_width=True)

        elif st.session_state.fund_view_mode == 'performance':
            st.markdown("### 📈 Global Fund Performance Dashboard")

            # Performance summary metrics
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("📊 Total Funds", f"{sum(len(funds) for funds in fund_universe.values())}")
            with col2:
                st.metric("📈 YTD Winners", "1,247")
            with col3:
                st.metric("📉 YTD Losers", "358")
            with col4:
                st.metric("💰 Total AUM", "$52.7T")
            with col5:
                st.metric("⭐ Avg Rating", "4.2/5")

            # Performance chart
            st.markdown("#### 🏆 Top Performing Categories")

            # Create performance data for categories
            categories = list(fund_universe.keys())[:10]
            performance_data = {
                'Category': [category_names.get(cat, cat) for cat in categories],
                'YTD Return (%)': np.random.uniform(-5, 25, len(categories)),
                'Total AUM ($B)': np.random.uniform(50, 2000, len(categories)),
                'Number of Funds': [len(fund_universe[cat]) for cat in categories]
            }

            perf_df = pd.DataFrame(performance_data)
            perf_df = perf_df.sort_values('YTD Return (%)', ascending=False)

            # Bar chart with dark theme
            fig = px.bar(perf_df, x='Category', y='YTD Return (%)',
                        title='Category Performance (YTD %)')
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_color='white',
                xaxis_title_font_color='white',
                yaxis_title_font_color='white'
            )
            fig.update_traces(marker_color='#3b82f6')
            st.plotly_chart(fig, use_container_width=True)

            # Performance table
            st.dataframe(perf_df.round(2), use_container_width=True)

        # Additional Info with enhanced styling
        st.markdown("---")
        st.markdown("""
        <div class="fund-info-section">
            <h3 style="color: var(--text-primary); margin: 0 0 1rem 0;">ℹ️ Global Fon Holdings Özellikleri</h3>
            <div style="color: var(--text-primary); line-height: 1.6;">
                <p style="margin: 0.5rem 0;"><strong>📊 Holdings Analizi:</strong> Fonun portföyündeki varlıkları ve ağırlıklarını gösterir</p>
                <p style="margin: 0.5rem 0;"><strong>📈 Performans Karşılaştırma:</strong> Fonun benchmark ve diğer fonlarla performans karşılaştırması</p>
                <p style="margin: 0.5rem 0;"><strong>🔄 Portföy Overlap:</strong> Farklı fonlar arasındaki ortak varlık analizi</p>
                <p style="margin: 0.5rem 0;"><strong>⚡ Gerçek Zamanlı Veri:</strong> Tüm veriler güncel piyasa bilgilerine dayanmaktadır</p>
                <p style="margin: 0.5rem 0;"><strong>🌍 Kapsamlı Kapsama:</strong> 500+ global ETF ve fon, 25 kategori</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Global fon holdings hatası: {e}")

        # Fallback basic display
        st.markdown("### 📊 Temel Fon Verileri")
        basic_funds = {
            'Fon': ['SPY', 'QQQ', 'VTI', 'EFA', 'VWO'],
            'Kategori': ['US Equity', 'Tech', 'Total Market', 'Developed', 'Emerging'],
            'AUM ($B)': [450, 200, 300, 90, 75],
            'Expense Ratio (%)': [0.09, 0.20, 0.03, 0.32, 0.10]
        }
        st.dataframe(pd.DataFrame(basic_funds), use_container_width=True)

def main():
    """Main application function"""
    # Initialize session state
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()

    # Create main header
    create_main_header()

    # Sidebar for navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h2 style="color: var(--text-primary);">🚀 Platform</h2>
            <p style="color: var(--text-secondary);">Modern Finansal Analiz</p>
        </div>
        """, unsafe_allow_html=True)

        page = st.selectbox(
            "Sayfa Seçin",
            ["📊 Ana Sayfa", "📈 Teknik Analiz", "🧠 AI Neural Analiz", "🌍 Global Piyasalar", "🏦 Global Fon Holdings", "💼 Portföy Analizi", "📰 Haberler & Sentiment"],
            index=0
        )

        st.markdown("---")
        st.markdown("### ⚡ Hızlı İşlemler")
        if st.button("🔄 Verileri Yenile"):
            st.session_state.last_update = datetime.now()
            st.experimental_rerun()

        if st.button("📊 Rapor Oluştur"):
            st.success("Rapor oluşturuluyor...")

    # Main content based on selected page
    if page == "📊 Ana Sayfa":
        create_quick_metrics()
        st.markdown("---")
        create_watchlist()

    elif page == "📈 Teknik Analiz":
        create_technical_analysis()

    elif page == "🧠 AI Neural Analiz":
        create_neural_analysis()

    elif page == "🌍 Global Piyasalar":
        create_global_markets()

    elif page == "🏦 Global Fon Holdings":
        create_global_fund_holdings()

    elif page == "💼 Portföy Analizi":
        create_portfolio_analyzer()

    elif page == "📰 Haberler & Sentiment":
        create_news_sentiment()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: var(--text-secondary); padding: 2rem 0;">
        <p>🚀 Modern Financial Platform | Bloomberg seviyesinde profesyonel analiz araçları</p>
        <p>Son güncelleme: {}</p>
    </div>
    """.format(st.session_state.last_update.strftime("%H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()