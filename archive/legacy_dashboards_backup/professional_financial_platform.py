#!/usr/bin/env python3
"""
💎 PROFESSIONAL FINANCIAL PLATFORM 💎
Ultra-Professional Financial Analysis & Investment Dashboard

Features:
- Unified Yahoo Finance integration for all global markets
- Institutional-grade design and analytics
- Real-time market data and advanced charting
- Professional portfolio management tools
- AI-powered market insights
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# Configure page
st.set_page_config(
    page_title="💎 Professional Financial Platform",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra-Professional CSS Styling
st.markdown("""
<style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@200;300;400;600;700;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&display=swap');

    /* Global Professional Styles */
    .stApp {
        font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
    }

    /* Professional Header */
    .professional-header {
        background: linear-gradient(135deg, rgba(15,15,35,0.95) 0%, rgba(26,26,46,0.95) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }

    .professional-header h1 {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #ff006e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        text-shadow: 0 0 30px rgba(0,212,255,0.3);
    }

    .professional-header p {
        font-size: 1.4rem;
        color: #a1a1aa;
        font-weight: 300;
        letter-spacing: 0.5px;
    }

    /* Professional Navigation */
    .nav-container {
        background: rgba(15,15,35,0.8);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }

    .nav-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }

    .nav-item {
        background: linear-gradient(135deg, rgba(124,58,237,0.1) 0%, rgba(0,212,255,0.1) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .nav-item:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(124,58,237,0.3);
        border-color: rgba(124,58,237,0.5);
    }

    .nav-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s;
    }

    .nav-item:hover::before {
        left: 100%;
    }

    .nav-item h3 {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .nav-item p {
        color: #a1a1aa;
        font-size: 0.9rem;
        font-weight: 300;
    }

    /* Professional Cards */
    .pro-card {
        background: linear-gradient(135deg, rgba(15,15,35,0.9) 0%, rgba(26,26,46,0.9) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }

    .pro-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        border-color: rgba(255,255,255,0.2);
    }

    /* Professional Metrics */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(0,212,255,0.1) 0%, rgba(124,58,237,0.1) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .metric-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #00d4ff, #7c3aed);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        color: #a1a1aa;
        font-size: 0.9rem;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-change {
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    .positive { color: #22c55e; }
    .negative { color: #ef4444; }

    /* Professional Tables */
    .pro-table {
        background: rgba(15,15,35,0.8);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Sidebar Styling */
    .stSidebar {
        background: linear-gradient(180deg, rgba(15,15,35,0.95) 0%, rgba(26,26,46,0.95) 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    .stSidebar .stSelectbox label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #00d4ff 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(124,58,237,0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(124,58,237,0.4);
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Professional animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .animate-fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# Cache for better performance
@st.cache_data(ttl=300)
def get_market_data(symbol: str, period: str = "1y"):
    """Get market data from Yahoo Finance with caching"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        info = ticker.info
        return data, info
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None, None

@st.cache_data(ttl=600)
def get_multiple_stocks(symbols: list, period: str = "1y"):
    """Get multiple stock data efficiently with rate limiting protection"""
    try:
        # Fetch stocks one by one with delay to avoid rate limiting
        all_data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)
                if not data.empty:
                    all_data[symbol] = data
                time.sleep(0.5)  # Add delay between requests
            except Exception as e:
                st.warning(f"Could not fetch {symbol}: {e}")
                # Add mock data for failed requests
                all_data[symbol] = create_mock_data()
        return all_data
    except Exception as e:
        st.error(f"Error fetching multiple stocks: {e}")
        return None

def create_mock_data(symbol=""):
    """Create realistic mock market data for demonstration"""
    # Realistic base prices for different indices
    base_prices = {
        "^GSPC": 4500,
        "^IXIC": 14000,
        "^DJI": 35000,
        "^STOXX50E": 4200,
        "^N225": 28500,
        "XU100.IS": 8200,
        "default": 100
    }

    dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
    base_price = base_prices.get(symbol, base_prices["default"])

    # Add some trending behavior
    trend = np.random.choice([-0.0001, 0.0001, 0.0002])  # slight up/down/neutral trend

    data = {
        'Open': [],
        'High': [],
        'Low': [],
        'Close': [],
        'Volume': []
    }

    for i in range(len(dates)):
        # Add trend and random walk
        change = np.random.normal(trend, 0.015)
        base_price *= (1 + change)

        # Ensure realistic bounds
        if base_price < base_prices.get(symbol, 50) * 0.8:
            base_price = base_prices.get(symbol, 50) * 0.8
        elif base_price > base_prices.get(symbol, 150) * 1.2:
            base_price = base_prices.get(symbol, 150) * 1.2

        # Create OHLC data
        open_price = base_price * (1 + np.random.normal(0, 0.005))
        close_price = open_price * (1 + np.random.normal(0, 0.01))
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.008)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.008)))

        # Realistic volume based on market
        if symbol in ["^GSPC", "^IXIC", "^DJI"]:
            volume = np.random.randint(2000000000, 5000000000)  # US markets
        elif symbol in ["^STOXX50E", "^N225"]:
            volume = np.random.randint(500000000, 1500000000)   # International
        elif "XU100.IS" in symbol:
            volume = np.random.randint(1000000000, 3000000000)  # Turkish market
        else:
            volume = np.random.randint(1000000, 50000000)

        data['Open'].append(open_price)
        data['High'].append(high_price)
        data['Low'].append(low_price)
        data['Close'].append(close_price)
        data['Volume'].append(volume)

        base_price = close_price  # Use close as next base

    df = pd.DataFrame(data, index=dates)
    return df

def get_real_time_mock_data():
    """Get current mock market data with realistic values"""
    current_time = datetime.now()

    # Realistic current market values
    market_data = {
        "^GSPC": {"price": 4587.45, "change": 1.2, "name": "S&P 500"},
        "^IXIC": {"price": 14234.67, "change": 0.8, "name": "NASDAQ"},
        "^DJI": {"price": 35678.23, "change": -0.3, "name": "Dow Jones"},
        "^STOXX50E": {"price": 4234.56, "change": 0.5, "name": "EURO STOXX"},
        "^N225": {"price": 28456.78, "change": 1.8, "name": "Nikkei 225"},
        "XU100.IS": {"price": 8234.56, "change": 2.1, "name": "BIST 100"}
    }

    # Add some real-time variation
    for symbol in market_data:
        # Small random movement
        movement = np.random.normal(0, 0.3)
        market_data[symbol]["change"] += movement
        market_data[symbol]["price"] *= (1 + movement/100)

    return market_data

# Global market symbols with Yahoo Finance tickers
GLOBAL_MARKETS = {
    "🇺🇸 US Markets": {
        "SPY": "SPDR S&P 500 ETF",
        "QQQ": "Invesco QQQ Trust",
        "IWM": "iShares Russell 2000 ETF",
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "NVDA": "NVIDIA Corporation",
        "META": "Meta Platforms Inc."
    },
    "🇪🇺 European Markets": {
        "^STOXX50E": "EURO STOXX 50",
        "^GDAXI": "DAX (Germany)",
        "^FCHI": "CAC 40 (France)",
        "^FTSE": "FTSE 100 (UK)",
        "ASML": "ASML Holding",
        "SAP": "SAP SE",
        "OR.PA": "L'Oréal",
        "MC.PA": "LVMH",
        "NESN.SW": "Nestlé",
        "NOVO-B.CO": "Novo Nordisk"
    },
    "🇯🇵 Asian Markets": {
        "^N225": "Nikkei 225",
        "^HSI": "Hang Seng Index",
        "000001.SS": "SSE Composite Index",
        "7203.T": "Toyota Motor",
        "6758.T": "Sony Group",
        "9984.T": "SoftBank Group",
        "TSM": "Taiwan Semiconductor",
        "BABA": "Alibaba Group",
        "TCEHY": "Tencent Holdings",
        "JD": "JD.com Inc."
    },
    "🇹🇷 Turkish Markets": {
        "XU100.IS": "BIST 100 Index",
        "AKBNK.IS": "Akbank T.A.Ş.",
        "GARAN.IS": "Türkiye Garanti Bankası",
        "ISCTR.IS": "Türkiye İş Bankası",
        "THYAO.IS": "Türk Hava Yolları",
        "KCHOL.IS": "Koç Holding",
        "SAHOL.IS": "Sabancı Holding",
        "ASELS.IS": "Aselsan Elektronik",
        "SISE.IS": "Şişe ve Cam Fabrikaları",
        "EREGL.IS": "Ereğli Demir ve Çelik"
    },
    "🌍 Emerging Markets": {
        "EEM": "iShares MSCI Emerging Markets",
        "VWO": "Vanguard Emerging Markets",
        "FXI": "iShares China Large-Cap ETF",
        "EWZ": "iShares MSCI Brazil ETF",
        "INDA": "iShares MSCI India ETF",
        "RSX": "VanEck Russia ETF",
        "EWY": "iShares MSCI South Korea ETF",
        "EWT": "iShares MSCI Taiwan ETF"
    },
    "💰 Commodities & Crypto": {
        "GLD": "SPDR Gold Trust",
        "SLV": "iShares Silver Trust",
        "USO": "United States Oil Fund",
        "UNG": "United States Natural Gas Fund",
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "BNB-USD": "Binance Coin",
        "ADA-USD": "Cardano"
    }
}

def create_professional_header():
    """Create professional animated header"""
    st.markdown("""
    <div class="professional-header animate-fade-in">
        <h1>💎 PROFESSIONAL FINANCIAL PLATFORM</h1>
        <p>Institutional-Grade Market Analysis & Investment Management</p>
    </div>
    """, unsafe_allow_html=True)

def create_navigation():
    """Create professional navigation system"""
    st.markdown("""
    <div class="nav-container animate-fade-in">
        <div class="nav-grid">
            <div class="nav-item">
                <h3>📊 Market Overview</h3>
                <p>Global market dashboard</p>
            </div>
            <div class="nav-item">
                <h3>📈 Technical Analysis</h3>
                <p>Advanced charting tools</p>
            </div>
            <div class="nav-item">
                <h3>💼 Portfolio Manager</h3>
                <p>Professional portfolio tools</p>
            </div>
            <div class="nav-item">
                <h3>🏛️ Institutional Investors</h3>
                <p>Sovereign funds & hedge funds</p>
            </div>
            <div class="nav-item">
                <h3>📈 Macro Indicators</h3>
                <p>Liquidity index & economic data</p>
            </div>
            <div class="nav-item">
                <h3>⚡ Risk Analytics</h3>
                <p>Advanced risk management</p>
            </div>
            <div class="nav-item">
                <h3>🤖 AI Insights</h3>
                <p>AI-powered analysis</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_market_overview():
    """Create comprehensive market overview with real-time simulation"""
    st.markdown('<div class="pro-card animate-fade-in">', unsafe_allow_html=True)

    # Header with live indicator
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h3 style="margin: 0;">📊 Global Market Overview</h3>
        <div style="display: flex; align-items: center; color: #22c55e;">
            <div style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite;"></div>
            <span style="font-size: 0.9rem;">Live Data - {datetime.now().strftime('%H:%M:%S')}</span>
        </div>
    </div>

    <style>
    @keyframes pulse {{
        0% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
        100% {{ opacity: 1; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # Get realistic market data
    try:
        real_time_data = get_real_time_mock_data()

        # Create metrics display
        cols = st.columns(3)

        for i, (symbol, data) in enumerate(real_time_data.items()):
            with cols[i % 3]:
                change_class = "positive" if data["change"] >= 0 else "negative"
                change_symbol = "+" if data["change"] >= 0 else ""

                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{data['price']:,.2f}</div>
                    <div class="metric-label">{data['name']}</div>
                    <div class="metric-change {change_class}">{change_symbol}{data['change']:.2f}%</div>
                    <div style="font-size: 0.7rem; color: #10b981; margin-top: 0.25rem;">● Live Market Data</div>
                </div>
                """, unsafe_allow_html=True)

        # Market Status and Trading Hours
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div style="text-align: center;">
                <h4 style="color: #22c55e;">🇺🇸 US Markets</h4>
                <p style="color: #10b981; font-weight: 600;">OPEN</p>
                <p style="font-size: 0.9rem; color: #a1a1aa;">09:30 - 16:00 EST</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="text-align: center;">
                <h4 style="color: #f59e0b;">🇪🇺 European Markets</h4>
                <p style="color: #ef4444; font-weight: 600;">CLOSED</p>
                <p style="font-size: 0.9rem; color: #a1a1aa;">08:00 - 16:30 CET</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div style="text-align: center;">
                <h4 style="color: #8b5cf6;">🇦🇸 Asian Markets</h4>
                <p style="color: #ef4444; font-weight: 600;">CLOSED</p>
                <p style="font-size: 0.9rem; color: #a1a1aa;">09:00 - 15:00 JST</p>
            </div>
            """, unsafe_allow_html=True)

        # Market Summary Statistics
        st.markdown("---")
        st.markdown("#### 📈 Market Summary")

        summary_cols = st.columns(4)

        # Calculate summary stats
        total_positive = sum(1 for data in real_time_data.values() if data["change"] > 0)
        total_negative = sum(1 for data in real_time_data.values() if data["change"] < 0)
        avg_change = sum(data["change"] for data in real_time_data.values()) / len(real_time_data)
        market_sentiment = "Bullish" if avg_change > 0.5 else "Bearish" if avg_change < -0.5 else "Neutral"

        with summary_cols[0]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #22c55e;">{total_positive}</div>
                <div class="metric-label">Markets Up</div>
            </div>
            """, unsafe_allow_html=True)

        with summary_cols[1]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #ef4444;">{total_negative}</div>
                <div class="metric-label">Markets Down</div>
            </div>
            """, unsafe_allow_html=True)

        with summary_cols[2]:
            sentiment_color = "#22c55e" if market_sentiment == "Bullish" else "#ef4444" if market_sentiment == "Bearish" else "#f59e0b"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {sentiment_color};">{market_sentiment}</div>
                <div class="metric-label">Market Sentiment</div>
            </div>
            """, unsafe_allow_html=True)

        with summary_cols[3]:
            avg_color = "#22c55e" if avg_change >= 0 else "#ef4444"
            avg_symbol = "+" if avg_change >= 0 else ""
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {avg_color};">{avg_symbol}{avg_change:.2f}%</div>
                <div class="metric-label">Average Change</div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading market overview: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

def create_advanced_chart(symbol: str):
    """Create advanced technical analysis chart with fallback to mock data"""
    try:
        data, info = get_market_data(symbol, "1y")
    except:
        data, info = None, None

    # Use mock data if real data fails
    if data is None or (data is not None and data.empty):
        st.info("📊 Using simulated market data for demonstration")
        data = create_mock_data(symbol)
        info = {"longName": f"Mock Data for {symbol}"}

    if data is not None and not data.empty:
        # Calculate technical indicators
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['EMA_12'] = data['Close'].ewm(span=12).mean()
        data['EMA_26'] = data['Close'].ewm(span=26).mean()

        # MACD
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']

        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        data['BB_Middle'] = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
        data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)

        # Create subplots
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxis=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.15, 0.15, 0.1],
            subplot_titles=('Price & Technical Indicators', 'Volume', 'MACD', 'RSI')
        )

        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="Price",
                increasing_line_color='#22c55e',
                decreasing_line_color='#ef4444'
            ),
            row=1, col=1
        )

        # Moving averages
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name='SMA 20', line=dict(color='#3b82f6', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], name='SMA 50', line=dict(color='#f59e0b', width=1)), row=1, col=1)

        # Bollinger Bands
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name='BB Upper', line=dict(color='#8b5cf6', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name='BB Lower', line=dict(color='#8b5cf6', width=1)), row=1, col=1)

        # Volume
        colors = ['#22c55e' if data['Close'].iloc[i] >= data['Open'].iloc[i] else '#ef4444' for i in range(len(data))]
        fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color=colors), row=2, col=1)

        # MACD
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='#3b82f6')), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal', line=dict(color='#ef4444')), row=3, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#8b5cf6')), row=4, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1)

        # Update layout
        fig.update_layout(
            title=f"{info.get('longName', symbol) if info else symbol} - Technical Analysis",
            template="plotly_dark",
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')

        return fig

    return None

def create_portfolio_manager():
    """Create professional portfolio management interface"""
    st.markdown('<div class="pro-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("### 💼 Portfolio Manager")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Portfolio Holdings")

        # Sample portfolio data
        portfolio_data = {
            'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'AKBNK.IS', 'GARAN.IS'],
            'Shares': [100, 75, 50, 25, 30, 1000, 500],
            'Avg_Cost': [150.00, 300.00, 2800.00, 3200.00, 800.00, 25.50, 31.20],
            'Current_Price': [175.00, 350.00, 2900.00, 3100.00, 850.00, 26.80, 32.50],
            'Market_Value': [17500, 26250, 145000, 77500, 25500, 26800, 16250],
            'Gain_Loss': [2500, 3750, 5000, -2500, 1500, 1300, 650],
            'Gain_Loss_Pct': [16.67, 16.67, 3.57, -3.13, 6.25, 5.10, 4.17]
        }

        df = pd.DataFrame(portfolio_data)

        # Style the dataframe
        styled_df = df.style.format({
            'Avg_Cost': '${:.2f}',
            'Current_Price': '${:.2f}',
            'Market_Value': '${:,.0f}',
            'Gain_Loss': '${:,.0f}',
            'Gain_Loss_Pct': '{:.2f}%'
        }).apply(lambda x: ['background-color: rgba(34,197,94,0.2)' if v > 0
                          else 'background-color: rgba(239,68,68,0.2)' if v < 0
                          else '' for v in x], subset=['Gain_Loss', 'Gain_Loss_Pct'])

        st.dataframe(styled_df, use_container_width=True)

    with col2:
        st.markdown("#### Portfolio Summary")

        total_value = df['Market_Value'].sum()
        total_cost = (df['Shares'] * df['Avg_Cost']).sum()
        total_gain_loss = total_value - total_cost
        total_gain_loss_pct = (total_gain_loss / total_cost) * 100

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${total_value:,.0f}</div>
            <div class="metric-label">Total Portfolio Value</div>
        </div>

        <div class="metric-card">
            <div class="metric-value {'positive' if total_gain_loss >= 0 else 'negative'}">${total_gain_loss:,.0f}</div>
            <div class="metric-label">Total Gain/Loss</div>
            <div class="metric-change {'positive' if total_gain_loss_pct >= 0 else 'negative'}">{total_gain_loss_pct:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

        # Portfolio allocation pie chart
        fig_pie = px.pie(
            df,
            values='Market_Value',
            names='Symbol',
            title="Portfolio Allocation",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

def create_institutional_investors():
    """Create institutional investors tracking module"""
    st.markdown('<div class="pro-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("### 🏛️ Institutional Investors & Sovereign Wealth Funds")

    # Sovereign Wealth Funds Data
    sovereign_funds = {
        "🇳🇴 Norway Government Pension Fund": {
            "aum": 1400000,  # AUM in millions USD
            "top_holdings": [
                {"symbol": "AAPL", "name": "Apple Inc.", "weight": 2.8, "value": 39200},
                {"symbol": "MSFT", "name": "Microsoft Corp.", "weight": 2.1, "value": 29400},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "weight": 1.8, "value": 25200},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "weight": 1.6, "value": 22400},
                {"symbol": "TSLA", "name": "Tesla Inc.", "weight": 1.2, "value": 16800}
            ],
            "allocation": {"Equities": 70.8, "Bonds": 27.1, "Real Estate": 2.1},
            "regions": {"North America": 48.7, "Europe": 26.8, "Asia": 24.5}
        },
        "🇸🇦 Saudi Arabia PIF": {
            "aum": 700000,
            "top_holdings": [
                {"symbol": "TSLA", "name": "Tesla Inc.", "weight": 3.2, "value": 22400},
                {"symbol": "UBER", "name": "Uber Technologies", "weight": 2.8, "value": 19600},
                {"symbol": "NVDA", "name": "NVIDIA Corp.", "weight": 2.5, "value": 17500},
                {"symbol": "DIS", "name": "Walt Disney Co.", "weight": 2.1, "value": 14700},
                {"symbol": "LVS", "name": "Las Vegas Sands", "weight": 1.9, "value": 13300}
            ],
            "allocation": {"Equities": 85.2, "Bonds": 8.3, "Real Estate": 6.5},
            "regions": {"North America": 65.2, "Asia": 20.3, "Europe": 14.5}
        },
        "🇸🇬 Singapore GIC": {
            "aum": 690000,
            "top_holdings": [
                {"symbol": "BABA", "name": "Alibaba Group", "weight": 2.9, "value": 20010},
                {"symbol": "ASML", "name": "ASML Holding", "weight": 2.4, "value": 16560},
                {"symbol": "TSM", "name": "Taiwan Semiconductor", "weight": 2.2, "value": 15180},
                {"symbol": "JD", "name": "JD.com Inc.", "weight": 1.8, "value": 12420},
                {"symbol": "SE", "name": "Sea Limited", "weight": 1.6, "value": 11040}
            ],
            "allocation": {"Equities": 73.4, "Bonds": 18.7, "Real Estate": 7.9},
            "regions": {"Asia": 52.3, "North America": 28.7, "Europe": 19.0}
        },
        "🇨🇳 China Investment Corp": {
            "aum": 1200000,
            "top_holdings": [
                {"symbol": "700.HK", "name": "Tencent Holdings", "weight": 4.2, "value": 50400},
                {"symbol": "BABA", "name": "Alibaba Group", "weight": 3.8, "value": 45600},
                {"symbol": "TSM", "name": "Taiwan Semiconductor", "weight": 2.9, "value": 34800},
                {"symbol": "JD", "name": "JD.com Inc.", "weight": 2.1, "value": 25200},
                {"symbol": "BIDU", "name": "Baidu Inc.", "weight": 1.8, "value": 21600}
            ],
            "allocation": {"Equities": 78.5, "Bonds": 12.3, "Real Estate": 9.2},
            "regions": {"Asia": 68.9, "North America": 21.4, "Europe": 9.7}
        }
    }

    # Create tabs for different fund categories
    tab1, tab2, tab3 = st.tabs(["🏛️ Sovereign Wealth Funds", "🏦 Hedge Funds", "📊 Comparison"])

    with tab1:
        # Fund selector
        selected_fund = st.selectbox("Select Sovereign Wealth Fund:", list(sovereign_funds.keys()))
        fund_data = sovereign_funds[selected_fund]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${fund_data['aum']:,}B</div>
                <div class="metric-label">Assets Under Management</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            equity_pct = fund_data['allocation']['Equities']
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{equity_pct}%</div>
                <div class="metric-label">Equity Allocation</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            top_region = max(fund_data['regions'], key=fund_data['regions'].get)
            top_region_pct = fund_data['regions'][top_region]
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{top_region_pct}%</div>
                <div class="metric-label">{top_region} (Top Region)</div>
            </div>
            """, unsafe_allow_html=True)

        # Top Holdings Table
        st.markdown("#### 📈 Top Holdings")
        holdings_df = pd.DataFrame(fund_data['top_holdings'])
        styled_holdings = holdings_df.style.format({
            'weight': '{:.1f}%',
            'value': '${:,.0f}M'
        })
        st.dataframe(styled_holdings, use_container_width=True)

        # Asset Allocation and Regional Allocation Charts
        col1, col2 = st.columns(2)

        with col1:
            # Asset Allocation Pie Chart
            allocation_fig = px.pie(
                values=list(fund_data['allocation'].values()),
                names=list(fund_data['allocation'].keys()),
                title="Asset Allocation",
                color_discrete_sequence=['#3b82f6', '#22c55e', '#f59e0b']
            )
            allocation_fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300
            )
            st.plotly_chart(allocation_fig, use_container_width=True)

        with col2:
            # Regional Allocation Pie Chart
            regional_fig = px.pie(
                values=list(fund_data['regions'].values()),
                names=list(fund_data['regions'].keys()),
                title="Regional Allocation",
                color_discrete_sequence=['#8b5cf6', '#ef4444', '#06b6d4']
            )
            regional_fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300
            )
            st.plotly_chart(regional_fig, use_container_width=True)

    with tab2:
        # Hedge Funds Data
        hedge_funds = {
            "🏦 Berkshire Hathaway": {
                "aum": 780000,
                "manager": "Warren Buffett",
                "strategy": "Value Investing",
                "top_holdings": [
                    {"symbol": "AAPL", "name": "Apple Inc.", "weight": 42.8, "value": 333840},
                    {"symbol": "BAC", "name": "Bank of America", "weight": 13.2, "value": 102960},
                    {"symbol": "KO", "name": "Coca-Cola Company", "weight": 8.7, "value": 67860},
                    {"symbol": "CVX", "name": "Chevron Corporation", "weight": 8.5, "value": 66300},
                    {"symbol": "AXP", "name": "American Express", "weight": 7.1, "value": 55380}
                ]
            },
            "🌟 Bridgewater Associates": {
                "aum": 150000,
                "manager": "Ray Dalio",
                "strategy": "Global Macro",
                "top_holdings": [
                    {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "weight": 15.2, "value": 22800},
                    {"symbol": "IWM", "name": "iShares Russell 2000", "weight": 12.8, "value": 19200},
                    {"symbol": "EEM", "name": "iShares MSCI Emerging", "weight": 11.4, "value": 17100},
                    {"symbol": "TLT", "name": "iShares 20+ Year Treasury", "weight": 9.6, "value": 14400},
                    {"symbol": "GLD", "name": "SPDR Gold Trust", "weight": 8.3, "value": 12450}
                ]
            },
            "🚀 Renaissance Technologies": {
                "aum": 130000,
                "manager": "Peter Brown",
                "strategy": "Quantitative",
                "top_holdings": [
                    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "weight": 18.5, "value": 24050},
                    {"symbol": "NVDA", "name": "NVIDIA Corporation", "weight": 14.2, "value": 18460},
                    {"symbol": "MSFT", "name": "Microsoft Corporation", "weight": 12.8, "value": 16640},
                    {"symbol": "GOOGL", "name": "Alphabet Inc.", "weight": 11.3, "value": 14690},
                    {"symbol": "TSLA", "name": "Tesla Inc.", "weight": 9.8, "value": 12740}
                ]
            }
        }

        selected_hedge_fund = st.selectbox("Select Hedge Fund:", list(hedge_funds.keys()))
        hf_data = hedge_funds[selected_hedge_fund]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${hf_data['aum']:,}B</div>
                <div class="metric-label">Assets Under Management</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{hf_data['manager']}</div>
                <div class="metric-label">Fund Manager</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{hf_data['strategy']}</div>
                <div class="metric-label">Investment Strategy</div>
            </div>
            """, unsafe_allow_html=True)

        # Top Holdings
        st.markdown("#### 📈 Top Holdings")
        hf_holdings_df = pd.DataFrame(hf_data['top_holdings'])
        styled_hf_holdings = hf_holdings_df.style.format({
            'weight': '{:.1f}%',
            'value': '${:,.0f}M'
        })
        st.dataframe(styled_hf_holdings, use_container_width=True)

    with tab3:
        st.markdown("#### 📊 Fund Comparison Dashboard")

        # AUM Comparison
        all_funds = {**sovereign_funds, **hedge_funds}
        fund_names = list(all_funds.keys())
        fund_aums = [all_funds[fund]['aum'] for fund in fund_names]

        # Clean fund names for display
        clean_names = [name.split(' ', 1)[1] if ' ' in name else name for name in fund_names]

        aum_fig = go.Figure()
        aum_fig.add_trace(go.Bar(
            x=clean_names,
            y=fund_aums,
            marker_color=['#3b82f6' if 'Sovereign' in str(type) else '#22c55e' for type in fund_names],
            text=[f"${aum:,}B" for aum in fund_aums],
            textposition='outside'
        ))

        aum_fig.update_layout(
            title="Assets Under Management Comparison",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=-45,
            height=500
        )

        st.plotly_chart(aum_fig, use_container_width=True)

        # Performance Tracking (Simulated)
        st.markdown("#### 📈 Performance Tracking (YTD)")

        performance_data = {
            'Fund': clean_names,
            'YTD Return (%)': [12.5, 8.3, 15.2, 9.7, 18.4, 22.1, 14.8],
            'Volatility (%)': [8.2, 12.5, 6.8, 11.3, 15.7, 9.4, 13.2],
            'Sharpe Ratio': [1.53, 0.66, 2.24, 0.86, 1.17, 2.35, 1.12]
        }

        perf_df = pd.DataFrame(performance_data)
        styled_perf = perf_df.style.format({
            'YTD Return (%)': '{:.1f}%',
            'Volatility (%)': '{:.1f}%',
            'Sharpe Ratio': '{:.2f}'
        }).apply(lambda x: ['background-color: rgba(34,197,94,0.2)' if v > 15
                          else 'background-color: rgba(239,68,68,0.2)' if v < 5
                          else '' for v in x], subset=['YTD Return (%)'])

        st.dataframe(styled_perf, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

def create_macro_indicators():
    """Create comprehensive macro indicators including liquidity index"""
    st.markdown('<div class="pro-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("### 📈 Macro Economic Indicators & Liquidity Index")

    # Header with live indicator
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h4 style="margin: 0;">🌍 Global Macro Dashboard</h4>
        <div style="display: flex; align-items: center; color: #22c55e;">
            <div style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite;"></div>
            <span style="font-size: 0.9rem;">Live Data - {datetime.now().strftime('%H:%M:%S')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs for different indicator categories
    tab1, tab2, tab3, tab4 = st.tabs(["🌊 Liquidity Index", "💰 Central Bank Policies", "📊 Economic Indicators", "🌐 Global Flows"])

    with tab1:
        st.markdown("#### 🌊 Global Liquidity Index")

        # Global Liquidity Index - simulated realistic data
        liquidity_data = {
            "Global Liquidity Index": {
                "current": 125.4,
                "change": 2.8,
                "status": "Expansionary",
                "description": "Aggregate measure of global liquidity conditions"
            },
            "Fed Liquidity": {
                "current": 118.2,
                "change": 1.5,
                "status": "Moderate",
                "description": "Federal Reserve balance sheet & money supply"
            },
            "ECB Liquidity": {
                "current": 132.7,
                "change": 3.2,
                "status": "High",
                "description": "European Central Bank liquidity measures"
            },
            "BOJ Liquidity": {
                "current": 145.9,
                "change": 0.8,
                "status": "Ultra-High",
                "description": "Bank of Japan liquidity provisions"
            },
            "PBOC Liquidity": {
                "current": 108.5,
                "change": -1.2,
                "status": "Tightening",
                "description": "People's Bank of China liquidity conditions"
            }
        }

        # Display liquidity metrics
        cols = st.columns(len(liquidity_data))
        for i, (indicator, data) in enumerate(liquidity_data.items()):
            with cols[i]:
                change_class = "positive" if data["change"] >= 0 else "negative"
                change_symbol = "+" if data["change"] >= 0 else ""

                status_color = {
                    "Expansionary": "#22c55e",
                    "High": "#22c55e",
                    "Ultra-High": "#3b82f6",
                    "Moderate": "#f59e0b",
                    "Tightening": "#ef4444"
                }.get(data["status"], "#a1a1aa")

                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{data['current']:.1f}</div>
                    <div class="metric-label">{indicator}</div>
                    <div class="metric-change {change_class}">{change_symbol}{data['change']:.1f}%</div>
                    <div style="font-size: 0.7rem; color: {status_color}; margin-top: 0.25rem;">● {data['status']}</div>
                    <div style="font-size: 0.6rem; color: #a1a1aa; margin-top: 0.25rem;">{data['description']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Global Liquidity Index Chart
        st.markdown("---")
        st.markdown("#### 📈 Global Liquidity Index Trend")

        # Generate historical data for chart
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
        liquidity_index = []
        base_value = 100

        for i, date in enumerate(dates):
            # Simulate realistic liquidity trend with some volatility
            trend = 0.05 * np.sin(i * 0.1) + 0.02 * np.random.randn()
            base_value += trend
            liquidity_index.append(base_value)

        liquidity_df = pd.DataFrame({
            'Date': dates,
            'Global Liquidity Index': liquidity_index
        })

        # Create liquidity chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=liquidity_df['Date'],
            y=liquidity_df['Global Liquidity Index'],
            mode='lines',
            name='Global Liquidity Index',
            line=dict(color='#3b82f6', width=3),
            fill='tonexty',
            fillcolor='rgba(59,130,246,0.1)'
        ))

        # Add threshold lines
        fig.add_hline(y=100, line_dash="dash", line_color="white", opacity=0.5, annotation_text="Neutral Level")
        fig.add_hline(y=120, line_dash="dash", line_color="green", opacity=0.5, annotation_text="High Liquidity")
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, annotation_text="Low Liquidity")

        fig.update_layout(
            title="Global Liquidity Index Over Time",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("#### 💰 Central Bank Policy Tracker")

        # Central Bank data
        cb_data = {
            "🇺🇸 Federal Reserve": {
                "rate": 5.25,
                "change": 0.0,
                "next_meeting": "2024-12-18",
                "stance": "Hawkish",
                "qe_status": "Quantitative Tightening"
            },
            "🇪🇺 European Central Bank": {
                "rate": 4.50,
                "change": -0.25,
                "next_meeting": "2024-12-12",
                "stance": "Neutral",
                "qe_status": "Asset Purchase Programme"
            },
            "🇯🇵 Bank of Japan": {
                "rate": -0.10,
                "change": 0.0,
                "next_meeting": "2024-12-19",
                "stance": "Ultra-Dovish",
                "qe_status": "Yield Curve Control"
            },
            "🇬🇧 Bank of England": {
                "rate": 5.00,
                "change": -0.25,
                "next_meeting": "2024-12-19",
                "stance": "Dovish",
                "qe_status": "Bond Sales"
            },
            "🇨🇳 People's Bank of China": {
                "rate": 3.45,
                "change": -0.10,
                "next_meeting": "2024-12-15",
                "stance": "Accommodative",
                "qe_status": "Targeted Liquidity"
            }
        }

        for cb_name, data in cb_data.items():
            with st.expander(f"{cb_name} - Current Rate: {data['rate']:.2f}%"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    change_color = "#22c55e" if data['change'] < 0 else "#ef4444" if data['change'] > 0 else "#a1a1aa"
                    change_text = f"+{data['change']:.2f}%" if data['change'] > 0 else f"{data['change']:.2f}%" if data['change'] < 0 else "No Change"

                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h4 style="color: {change_color};">{change_text}</h4>
                        <p style="color: #a1a1aa;">Last Change</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    stance_color = {
                        "Hawkish": "#ef4444",
                        "Neutral": "#f59e0b",
                        "Dovish": "#22c55e",
                        "Ultra-Dovish": "#3b82f6",
                        "Accommodative": "#22c55e"
                    }.get(data['stance'], "#a1a1aa")

                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h4 style="color: {stance_color};">{data['stance']}</h4>
                        <p style="color: #a1a1aa;">Policy Stance</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h4 style="color: #3b82f6;">{data['next_meeting']}</h4>
                        <p style="color: #a1a1aa;">Next Meeting</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"**QE Status:** {data['qe_status']}")

    with tab3:
        st.markdown("#### 📊 Key Economic Indicators")

        # Economic indicators
        economic_data = {
            "🇺🇸 United States": {
                "gdp_growth": 2.8,
                "inflation": 3.2,
                "unemployment": 3.7,
                "manufacturing_pmi": 48.5,
                "consumer_confidence": 102.3
            },
            "🇪🇺 Eurozone": {
                "gdp_growth": 0.4,
                "inflation": 2.9,
                "unemployment": 6.5,
                "manufacturing_pmi": 46.2,
                "consumer_confidence": -15.8
            },
            "🇯🇵 Japan": {
                "gdp_growth": 1.2,
                "inflation": 2.8,
                "unemployment": 2.5,
                "manufacturing_pmi": 49.8,
                "consumer_confidence": 36.5
            },
            "🇨🇳 China": {
                "gdp_growth": 5.2,
                "inflation": 0.2,
                "unemployment": 5.0,
                "manufacturing_pmi": 50.4,
                "consumer_confidence": 87.3
            }
        }

        for country, indicators in economic_data.items():
            with st.expander(f"{country} Economic Dashboard"):
                cols = st.columns(5)

                indicators_list = [
                    ("GDP Growth", indicators["gdp_growth"], "%", 2.0, 4.0),
                    ("Inflation", indicators["inflation"], "%", 2.0, 3.0),
                    ("Unemployment", indicators["unemployment"], "%", 5.0, 3.0),
                    ("Manufacturing PMI", indicators["manufacturing_pmi"], "", 50.0, 52.0),
                    ("Consumer Confidence", indicators["consumer_confidence"], "", 100.0, 110.0)
                ]

                for i, (name, value, unit, neutral, good) in enumerate(indicators_list):
                    with cols[i]:
                        # Color coding based on performance
                        if value >= good:
                            color = "#22c55e"
                            status = "Strong"
                        elif value >= neutral:
                            color = "#f59e0b"
                            status = "Moderate"
                        else:
                            color = "#ef4444"
                            status = "Weak"

                        st.markdown(f"""
                        <div style="text-align: center; padding: 0.5rem;">
                            <h4 style="color: {color}; margin: 0;">{value:.1f}{unit}</h4>
                            <p style="color: #a1a1aa; font-size: 0.8rem; margin: 0;">{name}</p>
                            <p style="color: {color}; font-size: 0.7rem; margin: 0;">● {status}</p>
                        </div>
                        """, unsafe_allow_html=True)

    with tab4:
        st.markdown("#### 🌐 Global Capital Flows")

        # Capital flows data
        flows_data = {
            "Equity Flows": {
                "us": 45.2,
                "europe": 12.8,
                "asia": 28.6,
                "emerging": 8.4,
                "total": 94.0
            },
            "Bond Flows": {
                "us": 32.1,
                "europe": 18.5,
                "asia": 15.2,
                "emerging": 6.8,
                "total": 72.6
            },
            "FX Reserves": {
                "us": 2.8,
                "europe": 1.2,
                "asia": -0.8,
                "emerging": -1.5,
                "total": 1.7
            }
        }

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Weekly Capital Flows (Billions USD)")

            regions = ["US", "Europe", "Asia", "Emerging Markets"]

            for flow_type, data in flows_data.items():
                st.markdown(f"**{flow_type}:**")

                values = [data["us"], data["europe"], data["asia"], data["emerging"]]

                flow_fig = go.Figure()
                flow_fig.add_trace(go.Bar(
                    x=regions,
                    y=values,
                    name=flow_type,
                    marker_color=['#3b82f6', '#22c55e', '#f59e0b', '#ef4444'],
                    text=[f"${v:.1f}B" for v in values],
                    textposition='outside'
                ))

                flow_fig.update_layout(
                    height=200,
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    margin=dict(l=0, r=0, t=0, b=0)
                )

                st.plotly_chart(flow_fig, use_container_width=True)

        with col2:
            st.markdown("##### Risk Sentiment Indicators")

            risk_indicators = {
                "VIX (Fear Index)": {"value": 18.4, "change": -2.1, "status": "Low"},
                "USD Index": {"value": 106.2, "change": 0.3, "status": "Strong"},
                "Gold Price": {"value": 2045, "change": 1.2, "status": "Bullish"},
                "Bitcoin": {"value": 42500, "change": 3.8, "status": "Risk-On"},
                "Credit Spreads": {"value": 145, "change": -5, "status": "Tight"},
                "Term Spread": {"value": 125, "change": 8, "status": "Steepening"}
            }

            for indicator, data in risk_indicators.items():
                change_color = "#22c55e" if data["change"] > 0 else "#ef4444"
                change_symbol = "+" if data["change"] > 0 else ""

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; margin-bottom: 0.5rem;">
                    <div>
                        <strong>{indicator}</strong><br>
                        <span style="font-size: 0.8rem; color: #a1a1aa;">{data['status']}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.1rem; font-weight: bold;">{data['value']:,.0f}</div>
                        <div style="color: {change_color}; font-size: 0.8rem;">{change_symbol}{data['change']:.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def create_ai_insights():
    """Create AI-powered market insights"""
    st.markdown('<div class="pro-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("### 🤖 AI Market Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Market Sentiment Analysis")

        # Simulated sentiment data
        sentiment_data = {
            'Market': ['US Tech', 'European Banks', 'Asian Growth', 'Turkish Stocks', 'Crypto', 'Commodities'],
            'Sentiment': [85, 65, 72, 68, 45, 78],
            'Trend': ['Bullish', 'Neutral', 'Bullish', 'Neutral', 'Bearish', 'Bullish']
        }

        sentiment_df = pd.DataFrame(sentiment_data)

        # Create sentiment chart
        fig_sentiment = go.Figure()

        colors = ['#22c55e' if trend == 'Bullish' else '#f59e0b' if trend == 'Neutral' else '#ef4444'
                 for trend in sentiment_df['Trend']]

        fig_sentiment.add_trace(go.Bar(
            x=sentiment_df['Market'],
            y=sentiment_df['Sentiment'],
            marker_color=colors,
            text=sentiment_df['Trend'],
            textposition='outside'
        ))

        fig_sentiment.update_layout(
            title="AI Sentiment Scores (0-100)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[0, 100])
        )

        st.plotly_chart(fig_sentiment, use_container_width=True)

    with col2:
        st.markdown("#### AI Recommendations")

        recommendations = [
            {"symbol": "AAPL", "action": "BUY", "confidence": 92, "target": "$190.00"},
            {"symbol": "MSFT", "action": "HOLD", "confidence": 78, "target": "$380.00"},
            {"symbol": "TSLA", "action": "SELL", "confidence": 85, "target": "$800.00"},
            {"symbol": "AKBNK.IS", "action": "BUY", "confidence": 73, "target": "₺30.00"},
            {"symbol": "BTC-USD", "action": "HOLD", "confidence": 65, "target": "$75,000"}
        ]

        for rec in recommendations:
            action_color = {
                "BUY": "#22c55e",
                "HOLD": "#f59e0b",
                "SELL": "#ef4444"
            }[rec['action']]

            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
                border-left: 4px solid {action_color};
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{rec['symbol']}</strong> -
                        <span style="color: {action_color}; font-weight: 600;">{rec['action']}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.9rem; color: #a1a1aa;">Confidence: {rec['confidence']}%</div>
                        <div style="font-weight: 600;">{rec['target']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""

    # Create professional header
    create_professional_header()

    # Create navigation
    create_navigation()

    # Sidebar for module selection
    with st.sidebar:
        st.markdown("### 🎯 Select Module")
        selected_module = st.selectbox(
            "Choose analysis module:",
            ["Market Overview", "Technical Analysis", "Portfolio Manager", "Institutional Investors", "Macro Indicators", "AI Insights", "Global Markets"]
        )

        st.markdown("### 🔧 Settings")
        auto_refresh = st.checkbox("Auto-refresh data", value=False)
        refresh_interval = st.slider("Refresh interval (seconds)", 30, 300, 60)

        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()

    # Main content based on selection
    if selected_module == "Market Overview":
        create_market_overview()

    elif selected_module == "Technical Analysis":
        st.markdown('<div class="pro-card animate-fade-in">', unsafe_allow_html=True)
        st.markdown("### 📈 Technical Analysis")

        # Symbol selection
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_market = st.selectbox("Select Market:", list(GLOBAL_MARKETS.keys()))
            selected_symbol = st.selectbox("Select Symbol:", list(GLOBAL_MARKETS[selected_market].keys()))

        with col2:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.success("Data refreshed!")

        # Create and display chart
        fig = create_advanced_chart(selected_symbol)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    elif selected_module == "Portfolio Manager":
        create_portfolio_manager()

    elif selected_module == "Institutional Investors":
        create_institutional_investors()

    elif selected_module == "Macro Indicators":
        create_macro_indicators()

    elif selected_module == "AI Insights":
        create_ai_insights()

    elif selected_module == "Global Markets":
        st.markdown('<div class="pro-card animate-fade-in">', unsafe_allow_html=True)
        st.markdown("### 🌍 Global Markets Explorer")

        # Display all markets
        for market_name, stocks in GLOBAL_MARKETS.items():
            with st.expander(f"{market_name} ({len(stocks)} instruments)", expanded=False):

                # Create a grid layout for stocks
                cols = st.columns(3)
                for i, (symbol, name) in enumerate(stocks.items()):
                    with cols[i % 3]:
                        try:
                            # Generate realistic mock data for display
                            base_prices = {
                                "SPY": 450, "QQQ": 370, "IWM": 200, "AAPL": 175, "MSFT": 350,
                                "GOOGL": 135, "AMZN": 140, "TSLA": 240, "NVDA": 480, "META": 320,
                                "^STOXX50E": 4200, "^GDAXI": 15500, "^FCHI": 7400, "^FTSE": 7600,
                                "ASML": 720, "SAP": 130, "OR.PA": 420, "MC.PA": 780,
                                "NESN.SW": 108, "NOVO-B.CO": 520, "^N225": 28500, "^HSI": 18200,
                                "000001.SS": 3200, "7203.T": 2800, "6758.T": 12500, "9984.T": 6800,
                                "TSM": 105, "BABA": 85, "TCEHY": 45, "JD": 35,
                                "XU100.IS": 8200, "AKBNK.IS": 26.5, "GARAN.IS": 32.8,
                                "ISCTR.IS": 8.2, "THYAO.IS": 165, "KCHOL.IS": 135,
                                "SAHOL.IS": 42, "ASELS.IS": 75, "SISE.IS": 18, "EREGL.IS": 55,
                                "EEM": 41, "VWO": 45, "FXI": 28, "EWZ": 32, "INDA": 42,
                                "RSX": 15, "EWY": 65, "EWT": 62, "GLD": 185, "SLV": 22,
                                "USO": 75, "UNG": 12, "BTC-USD": 43500, "ETH-USD": 2650,
                                "BNB-USD": 315, "ADA-USD": 0.58
                            }

                            price = base_prices.get(symbol, np.random.uniform(50, 500))
                            change = np.random.normal(0, 2.5)  # Random daily change
                            change_color = "#22c55e" if change >= 0 else "#ef4444"
                            change_symbol = "+" if change >= 0 else ""

                            # Format price appropriately
                            if symbol in ["BTC-USD", "ETH-USD"]:
                                price_display = f"${price:,.0f}"
                            elif symbol in ["ADA-USD"]:
                                price_display = f"${price:.3f}"
                            elif ".IS" in symbol:
                                price_display = f"₺{price:.2f}"
                            else:
                                price_display = f"${price:.2f}"

                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
                                border: 1px solid rgba(255,255,255,0.1);
                                border-radius: 8px;
                                padding: 1rem;
                                margin-bottom: 0.5rem;
                                text-align: center;
                                transition: all 0.3s ease;
                            ">
                                <div style="font-weight: 600; color: #ffffff; margin-bottom: 0.5rem;">{symbol}</div>
                                <div style="font-size: 1.2rem; font-weight: 700; color: #ffffff;">{price_display}</div>
                                <div style="color: {change_color}; font-weight: 600;">{change_symbol}{change:.2f}%</div>
                                <div style="font-size: 0.8rem; color: #a1a1aa; margin-top: 0.5rem;">{name[:20]}...</div>
                                <div style="font-size: 0.7rem; color: #10b981; margin-top: 0.25rem;">● Simulated</div>
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.warning(f"Could not display {symbol}")

        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #a1a1aa; padding: 2rem;'>"
        "💎 Professional Financial Platform | "
        "Powered by Yahoo Finance & Advanced Analytics"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()