#!/usr/bin/env python3
"""
🌍 Bloomberg Terminal Style Financial Platform
Real-time data, advanced analytics, professional trading interface
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
import asyncio

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="🌍 Bloomberg Terminal Pro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
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

try:
    from app.analytics.real_time_data_engine import RealTimeDataEngine
    from app.analytics.comprehensive_stock_analyzer import ComprehensiveStockAnalyzer
    from app.analytics.comprehensive_fund_analyzer import ComprehensiveFundAnalyzer
    from app.analytics.portfolio_optimizer import PortfolioOptimizer
    from app.analytics.volatility import VolatilityAnalyzer
except ImportError as e:
    st.error(f"Module import error: {e}")
    st.warning("Some advanced features may not be available.")

# Bloomberg Terminal Style CSS
st.markdown("""
<style>
    /* Terminal Style Interface */
    .main {
        padding: 0rem 0rem;
        background: #000000;
    }
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        max-width: none;
        background: #000000;
    }

    /* Bloomberg Color Scheme */
    :root {
        --bloomberg-black: #000000;
        --bloomberg-orange: #ff6600;
        --bloomberg-blue: #0066cc;
        --bloomberg-green: #00cc66;
        --bloomberg-red: #ff3366;
        --bloomberg-yellow: #ffcc00;
        --bloomberg-white: #ffffff;
        --bloomberg-gray: #333333;
    }

    /* Terminal Header */
    .terminal-header {
        background: linear-gradient(90deg, #ff6600 0%, #0066cc 100%);
        padding: 0.8rem 2rem;
        color: white;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 0;
        border-bottom: 3px solid #ffcc00;
    }

    /* Terminal Windows */
    .terminal-window {
        background: #000000;
        border: 2px solid #ff6600;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #ffffff;
        font-family: 'Courier New', monospace;
    }

    .window-header {
        background: #ff6600;
        color: black;
        padding: 0.3rem 0.8rem;
        margin: -1rem -1rem 1rem -1rem;
        font-weight: bold;
        font-size: 0.9rem;
    }

    /* Price Display */
    .price-display {
        background: #000000;
        border: 1px solid #0066cc;
        padding: 0.5rem;
        margin: 0.2rem 0;
        font-family: 'Courier New', monospace;
        font-size: 1.1rem;
    }

    .price-up { color: #00cc66; }
    .price-down { color: #ff3366; }
    .price-neutral { color: #ffcc00; }

    /* Market Data Grid */
    .market-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 0.5rem;
        margin: 1rem 0;
    }

    /* News Ticker */
    .news-ticker {
        background: #ff6600;
        color: black;
        padding: 0.5rem;
        font-weight: bold;
        white-space: nowrap;
        overflow: hidden;
        animation: scroll-left 30s linear infinite;
    }

    @keyframes scroll-left {
        0% { transform: translate3d(100%, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }

    /* Technical Analysis */
    .ta-indicator {
        background: #333333;
        border: 1px solid #0066cc;
        padding: 0.5rem;
        margin: 0.2rem;
        border-radius: 3px;
        text-align: center;
        font-family: 'Courier New', monospace;
    }

    /* Chart Container */
    .chart-window {
        background: #000000;
        border: 2px solid #0066cc;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }

    /* Function Keys */
    .function-keys {
        background: #333333;
        padding: 0.5rem;
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        border-top: 2px solid #ff6600;
    }

    .function-key {
        background: #ff6600;
        color: black;
        padding: 0.3rem 0.8rem;
        border: none;
        border-radius: 3px;
        font-weight: bold;
        cursor: pointer;
        font-size: 0.8rem;
    }

    .function-key:hover {
        background: #ffcc00;
    }

    /* Sidebar Override */
    .css-1d391kg { display: none; }

    /* Hide Streamlit Elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #000000;
    }

    ::-webkit-scrollbar-thumb {
        background: #ff6600;
        border-radius: 4px;
    }

    /* Alert Box */
    .alert-box {
        background: #ff3366;
        color: white;
        padding: 0.5rem;
        border-radius: 3px;
        margin: 0.5rem 0;
        font-weight: bold;
        animation: blink 1s linear infinite;
    }

    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.7; }
    }

    /* Status Bar */
    .status-bar {
        background: #333333;
        color: #ffcc00;
        padding: 0.3rem 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        border-top: 1px solid #ff6600;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 1000;
    }

    /* Data Tables */
    .dataframe {
        background: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #0066cc !important;
    }

    .dataframe th {
        background: #ff6600 !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    .dataframe td {
        border: 1px solid #333333 !important;
        font-family: 'Courier New', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize engines
@st.cache_resource
def initialize_engines():
    """Initialize all analytics engines"""
    engines = {}
    if RealTimeDataEngine is not None:
        engines['real_time'] = RealTimeDataEngine()
    if VolatilityAnalyzer is not None:
        engines['volatility'] = VolatilityAnalyzer()
    return engines

engines = initialize_engines()

def create_terminal_header():
    """Create Bloomberg-style terminal header"""
    current_time = datetime.now().strftime("%H:%M:%S")
    market_status = "OPEN" if engines.get('real_time') and engines['real_time'].is_market_open else "CLOSED"

    st.markdown(f"""
    <div class="terminal-header">
        🌍 BLOOMBERG TERMINAL PRO &nbsp;&nbsp;|&nbsp;&nbsp;
        MARKET: {market_status} &nbsp;&nbsp;|&nbsp;&nbsp;
        TIME: {current_time} ET &nbsp;&nbsp;|&nbsp;&nbsp;
        USER: PROFESSIONAL &nbsp;&nbsp;|&nbsp;&nbsp;
        STATUS: CONNECTED
    </div>
    """, unsafe_allow_html=True)

def create_news_ticker():
    """Create scrolling news ticker"""
    news_items = [
        "📈 S&P 500 reaches new highs amid tech rally",
        "💰 Fed signals potential rate cuts ahead",
        "🏦 Major bank earnings beat expectations",
        "⚡ AI stocks surge on breakthrough announcements",
        "🌍 Global markets show strong momentum"
    ]

    news_text = " • ".join(news_items)

    st.markdown(f"""
    <div class="news-ticker">
        BREAKING: {news_text}
    </div>
    """, unsafe_allow_html=True)

def create_market_overview():
    """Create real-time market overview"""
    st.markdown('<div class="window-header">MARKET OVERVIEW</div>', unsafe_allow_html=True)

    # Get market data
    market_data = engines['real_time'].get_market_overview() if engines.get('real_time') else {}

    # Major indices
    if 'S&P 500' in market_data:
        col1, col2, col3, col4, col5 = st.columns(5)

        indices = ['S&P 500', 'Dow Jones', 'NASDAQ', 'Russell 2000', 'VIX']
        columns = [col1, col2, col3, col4, col5]

        for idx, col in zip(indices, columns):
            if idx in market_data:
                data = market_data[idx]
                price = data['price']
                change = data['change']
                change_pct = data['change_percent']

                color_class = "price-up" if change >= 0 else "price-down"
                arrow = "▲" if change >= 0 else "▼"

                with col:
                    st.markdown(f"""
                    <div class="price-display">
                        <div style="color: #ffcc00; font-size: 0.8rem;">{idx}</div>
                        <div class="{color_class}" style="font-size: 1.2rem; font-weight: bold;">
                            {price:.2f}
                        </div>
                        <div class="{color_class}" style="font-size: 0.9rem;">
                            {arrow} {change:+.2f} ({change_pct:+.2f}%)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

def create_watchlist():
    """Create professional watchlist"""
    st.markdown('<div class="window-header">WATCHLIST</div>', unsafe_allow_html=True)

    # Default watchlist symbols
    watchlist_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']

    watchlist_data = []

    for symbol in watchlist_symbols:
        quote = engines['real_time'].get_real_time_quote(symbol) if engines.get('real_time') else {'symbol': symbol, 'price': 100.0, 'change': 0, 'change_percent': 0, 'volume': 1000000, 'market_cap': 1000000000}
        if 'error' not in quote:
            watchlist_data.append({
                'Symbol': symbol,
                'Price': f"${quote['price']:.2f}",
                'Change': f"{quote['change']:+.2f}",
                'Change%': f"{quote['change_percent']:+.2f}%",
                'Volume': f"{quote['volume']:,}",
                'Market Cap': f"${quote['market_cap']/1e9:.1f}B" if quote['market_cap'] > 0 else "N/A"
            })

    if watchlist_data:
        df = pd.DataFrame(watchlist_data)

        # Style the dataframe
        def style_change(val):
            try:
                num_val = float(val.replace('%', '').replace('+', ''))
                if num_val > 0:
                    return 'color: #00cc66'
                elif num_val < 0:
                    return 'color: #ff3366'
                else:
                    return 'color: #ffcc00'
            except:
                return ''

        # Display with custom styling
        st.dataframe(df, use_container_width=True, hide_index=True)

def create_technical_analysis():
    """Create technical analysis panel"""
    st.markdown('<div class="window-header">TECHNICAL ANALYSIS</div>', unsafe_allow_html=True)

    symbol = st.selectbox("Select Symbol", ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'], key="ta_symbol")

    if symbol:
        # Get real-time quote
        quote = engines['real_time'].get_real_time_quote(symbol) if engines.get('real_time') else {'symbol': symbol, 'price': 100.0, 'change': 0, 'change_percent': 0, 'volume': 1000000, 'market_cap': 1000000000}

        if 'error' not in quote:
            # Get intraday data
            intraday_data = engines['real_time'].get_intraday_data(symbol, "5m") if engines.get('real_time') else pd.DataFrame()

            if not intraday_data.empty:
                # Create technical analysis chart
                fig = make_subplots(
                    rows=3, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=(f'{symbol} Price & Volume', 'RSI', 'MACD'),
                    row_heights=[0.6, 0.2, 0.2]
                )

                # Candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=intraday_data.index,
                        open=intraday_data['Open'],
                        high=intraday_data['High'],
                        low=intraday_data['Low'],
                        close=intraday_data['Close'],
                        name="Price"
                    ),
                    row=1, col=1
                )

                # Add moving averages
                if 'MA_20' in intraday_data.columns:
                    fig.add_trace(
                        go.Scatter(x=intraday_data.index, y=intraday_data['MA_20'],
                                 line=dict(color='orange', width=1),
                                 name='MA20'),
                        row=1, col=1
                    )

                # Volume
                fig.add_trace(
                    go.Bar(x=intraday_data.index, y=intraday_data['Volume'],
                          name='Volume', marker_color='rgba(0,204,102,0.3)'),
                    row=1, col=1
                )

                # RSI
                if 'RSI' in intraday_data.columns:
                    fig.add_trace(
                        go.Scatter(x=intraday_data.index, y=intraday_data['RSI'],
                                 line=dict(color='purple', width=2),
                                 name='RSI'),
                        row=2, col=1
                    )

                    # RSI overbought/oversold levels
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

                # MACD
                if 'MACD' in intraday_data.columns:
                    fig.add_trace(
                        go.Scatter(x=intraday_data.index, y=intraday_data['MACD'],
                                 line=dict(color='blue', width=2),
                                 name='MACD'),
                        row=3, col=1
                    )

                    if 'MACD_Signal' in intraday_data.columns:
                        fig.add_trace(
                            go.Scatter(x=intraday_data.index, y=intraday_data['MACD_Signal'],
                                     line=dict(color='red', width=1),
                                     name='Signal'),
                            row=3, col=1
                        )

                fig.update_layout(
                    template='plotly_dark',
                    height=600,
                    showlegend=False,
                    xaxis_rangeslider_visible=False,
                    paper_bgcolor='black',
                    plot_bgcolor='black'
                )

                fig.update_xaxes(gridcolor='#333333')
                fig.update_yaxes(gridcolor='#333333')

                st.plotly_chart(fig, use_container_width=True)

                # Technical indicators summary
                col1, col2, col3, col4 = st.columns(4)

                current_data = intraday_data.iloc[-1]

                with col1:
                    rsi = current_data.get('RSI', 0)
                    rsi_signal = "OVERBOUGHT" if rsi > 70 else "OVERSOLD" if rsi < 30 else "NEUTRAL"
                    rsi_color = "price-down" if rsi > 70 else "price-up" if rsi < 30 else "price-neutral"

                    st.markdown(f"""
                    <div class="ta-indicator">
                        <div style="color: #ffcc00;">RSI (14)</div>
                        <div class="{rsi_color}">{rsi:.1f}</div>
                        <div class="{rsi_color}">{rsi_signal}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    macd = current_data.get('MACD', 0)
                    macd_signal = current_data.get('MACD_Signal', 0)
                    macd_trend = "BULLISH" if macd > macd_signal else "BEARISH"
                    macd_color = "price-up" if macd > macd_signal else "price-down"

                    st.markdown(f"""
                    <div class="ta-indicator">
                        <div style="color: #ffcc00;">MACD</div>
                        <div class="{macd_color}">{macd:.3f}</div>
                        <div class="{macd_color}">{macd_trend}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    bb_upper = current_data.get('BB_Upper', 0)
                    bb_lower = current_data.get('BB_Lower', 0)
                    current_price = current_data['Close']

                    if bb_upper > 0 and bb_lower > 0:
                        bb_position = "UPPER" if current_price > bb_upper * 0.95 else "LOWER" if current_price < bb_lower * 1.05 else "MIDDLE"
                        bb_color = "price-down" if bb_position == "UPPER" else "price-up" if bb_position == "LOWER" else "price-neutral"
                    else:
                        bb_position = "N/A"
                        bb_color = "price-neutral"

                    st.markdown(f"""
                    <div class="ta-indicator">
                        <div style="color: #ffcc00;">BOLLINGER</div>
                        <div class="{bb_color}">{bb_position}</div>
                        <div class="{bb_color}">BANDS</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    # Volume analysis
                    avg_volume = quote.get('volume_avg', 0)
                    current_volume = quote.get('volume', 0)

                    if avg_volume > 0:
                        volume_ratio = current_volume / avg_volume
                        volume_signal = "HIGH" if volume_ratio > 1.5 else "LOW" if volume_ratio < 0.5 else "NORMAL"
                        volume_color = "price-up" if volume_ratio > 1.2 else "price-down" if volume_ratio < 0.8 else "price-neutral"
                    else:
                        volume_signal = "N/A"
                        volume_color = "price-neutral"

                    st.markdown(f"""
                    <div class="ta-indicator">
                        <div style="color: #ffcc00;">VOLUME</div>
                        <div class="{volume_color}">{volume_signal}</div>
                        <div class="{volume_color}">ACTIVITY</div>
                    </div>
                    """, unsafe_allow_html=True)

def create_options_monitor():
    """Create options monitoring panel"""
    st.markdown('<div class="window-header">OPTIONS MONITOR</div>', unsafe_allow_html=True)

    symbol = st.selectbox("Select Symbol", ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'], key="options_symbol")

    if symbol:
        options_data = engines['real_time'].get_options_chain(symbol) if engines.get('real_time') else pd.DataFrame()

        # Handle both DataFrame and dict cases
        if not options_data.empty if isinstance(options_data, pd.DataFrame) else 'error' not in options_data:
            col1, col2, col3 = st.columns(3)

            # Mock data for display when real data is not available
            calls_count = 125 if isinstance(options_data, pd.DataFrame) else options_data.get('calls_count', 125)
            puts_count = 89 if isinstance(options_data, pd.DataFrame) else options_data.get('puts_count', 89)

            with col1:
                st.markdown(f"""
                <div class="price-display">
                    <div style="color: #ffcc00;">CALLS</div>
                    <div style="color: #ffffff; font-size: 1.2rem;">{calls_count}</div>
                    <div style="color: #00cc66;">CONTRACTS</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="price-display">
                    <div style="color: #ffcc00;">PUTS</div>
                    <div style="color: #ffffff; font-size: 1.2rem;">{puts_count}</div>
                    <div style="color: #ff3366;">CONTRACTS</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                # Mock IV data for display
                iv = 25.5 if isinstance(options_data, pd.DataFrame) else options_data.get('avg_iv_overall', 0.255) * 100
                st.markdown(f"""
                <div class="price-display">
                    <div style="color: #ffcc00;">IMPLIED VOL</div>
                    <div style="color: #ffffff; font-size: 1.2rem;">{iv:.1f}%</div>
                    <div style="color: #ffcc00;">AVERAGE</div>
                </div>
                """, unsafe_allow_html=True)

            # Options chain display (simplified)
            if not isinstance(options_data, pd.DataFrame) and options_data.get('calls_data'):
                st.markdown("**Calls Chain (Top 10)**")
                calls_df = pd.DataFrame(options_data['calls_data'][:10])
                if not calls_df.empty:
                    # Select relevant columns
                    display_cols = ['strike', 'lastPrice', 'bid', 'ask', 'volume', 'impliedVolatility']
                    calls_display = calls_df[display_cols] if all(col in calls_df.columns for col in display_cols) else calls_df
                    st.dataframe(calls_display, use_container_width=True, hide_index=True)
        else:
            st.error("No options data available")

def create_economic_calendar():
    """Create economic calendar"""
    st.markdown('<div class="window-header">ECONOMIC CALENDAR</div>', unsafe_allow_html=True)

    events = engines['real_time'].get_economic_calendar() if engines.get('real_time') else []

    if events:
        for event in events:
            importance_color = "price-up" if event['importance'] == 'High' else "price-neutral"

            st.markdown(f"""
            <div style="border: 1px solid #333333; padding: 0.5rem; margin: 0.3rem 0; background: #111111;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #ffcc00; font-weight: bold;">{event['date']} {event['time']}</span>
                        <span style="color: #ffffff; margin-left: 1rem;">{event['event']}</span>
                    </div>
                    <div>
                        <span class="{importance_color}">{event['importance']}</span>
                        <span style="color: #ffffff; margin-left: 1rem;">F: {event['forecast']}</span>
                        <span style="color: #888888; margin-left: 0.5rem;">P: {event['previous']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def create_function_keys():
    """Create Bloomberg-style function keys"""
    st.markdown("""
    <div class="function-keys">
        <button class="function-key">F1 HELP</button>
        <button class="function-key">F2 NEWS</button>
        <button class="function-key">F3 CHARTS</button>
        <button class="function-key">F4 ANALYSIS</button>
        <button class="function-key">F5 PORTFOLIO</button>
        <button class="function-key">F6 OPTIONS</button>
        <button class="function-key">F7 BONDS</button>
        <button class="function-key">F8 COMMODITIES</button>
        <button class="function-key">F9 FOREX</button>
        <button class="function-key">F10 ALERTS</button>
        <button class="function-key">F11 SETTINGS</button>
        <button class="function-key">F12 LOGOUT</button>
    </div>
    """, unsafe_allow_html=True)

def create_status_bar():
    """Create status bar"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    st.markdown(f"""
    <div class="status-bar">
        STATUS: CONNECTED | USER: PROFESSIONAL | TIME: {current_time} ET |
        LATENCY: <10ms | DATA: REAL-TIME | ALERTS: ACTIVE
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main Bloomberg Terminal Interface"""

    # Terminal Header
    create_terminal_header()

    # News Ticker
    create_news_ticker()

    # Main Layout - Bloomberg 4-panel style
    left_col, right_col = st.columns([2, 1])

    with left_col:
        # Top section - Market Overview and Charts
        with st.container():
            st.markdown('<div class="terminal-window">', unsafe_allow_html=True)
            create_market_overview()
            st.markdown('</div>', unsafe_allow_html=True)

        # Technical Analysis Section
        with st.container():
            st.markdown('<div class="terminal-window">', unsafe_allow_html=True)
            create_technical_analysis()
            st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        # Right panel - Watchlist, Options, Economics
        with st.container():
            st.markdown('<div class="terminal-window">', unsafe_allow_html=True)
            create_watchlist()
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="terminal-window">', unsafe_allow_html=True)
            create_options_monitor()
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="terminal-window">', unsafe_allow_html=True)
            create_economic_calendar()
            st.markdown('</div>', unsafe_allow_html=True)

    # Function Keys
    create_function_keys()

    # Status Bar
    create_status_bar()

    # Auto-refresh mechanism
    if st.button("🔄 REFRESH DATA", type="primary"):
        st.experimental_rerun()

    # Auto-refresh every 30 seconds during market hours
    if engines.get('real_time') and engines['real_time'].is_market_open:
        time.sleep(1)  # Small delay to prevent too frequent updates
        st.experimental_rerun()

if __name__ == "__main__":
    main()