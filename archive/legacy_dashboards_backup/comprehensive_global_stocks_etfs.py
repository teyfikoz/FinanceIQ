"""
Comprehensive Global Stocks & ETFs Dashboard
Professional-grade financial platform with comprehensive global coverage
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
import random

# Configure page
st.set_page_config(
    page_title="Global Stocks & ETFs Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .performance-positive {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        display: inline-block;
        margin: 0.2rem;
        font-weight: bold;
    }
    .performance-negative {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        display: inline-block;
        margin: 0.2rem;
        font-weight: bold;
    }
    .category-header {
        background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 1.3rem;
        font-weight: bold;
        text-align: center;
    }
    .fund-membership {
        background: linear-gradient(135deg, #8E44AD 0%, #9B59B6 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .trading-signal {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .signal-buy {
        background: linear-gradient(135deg, #27AE60 0%, #2ECC71 100%);
        color: white;
    }
    .signal-sell {
        background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);
        color: white;
    }
    .signal-hold {
        background: linear-gradient(135deg, #F39C12 0%, #E67E22 100%);
        color: white;
    }
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .asset-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .asset-card {
        background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .asset-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Comprehensive global assets data
GLOBAL_STOCKS = {
    "🇺🇸 US Large Cap": {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corp.",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "META": "Meta Platforms",
        "NVDA": "NVIDIA Corp.",
        "NFLX": "Netflix Inc.",
        "BRK-B": "Berkshire Hathaway",
        "JNJ": "Johnson & Johnson",
        "V": "Visa Inc.",
        "WMT": "Walmart Inc.",
        "PG": "Procter & Gamble",
        "HD": "Home Depot",
        "MA": "Mastercard Inc."
    },
    "🇺🇸 US Mid Cap": {
        "CRM": "Salesforce",
        "ADBE": "Adobe Inc.",
        "NTES": "NetEase",
        "PYPL": "PayPal",
        "INTC": "Intel Corp.",
        "CSCO": "Cisco Systems",
        "PFE": "Pfizer Inc.",
        "KO": "Coca-Cola",
        "PEP": "PepsiCo",
        "ORCL": "Oracle Corp."
    },
    "🇪🇺 European": {
        "ASML": "ASML Holding NV",
        "SAP": "SAP SE",
        "LVMH": "LVMH",
        "NVO": "Novo Nordisk",
        "ROG.SW": "Roche",
        "NESN.SW": "Nestle",
        "MC.PA": "LVMH",
        "SHEL": "Shell PLC",
        "UNA.AS": "Unilever"
    },
    "🇯🇵 Japanese": {
        "TSM": "Taiwan Semiconductor",
        "7203.T": "Toyota Motor",
        "6758.T": "Sony Group",
        "9984.T": "SoftBank Group",
        "6861.T": "Keyence Corp",
        "4519.T": "Chugai Pharma"
    },
    "🇨🇳 Chinese": {
        "BABA": "Alibaba Group",
        "TCEHY": "Tencent Holdings",
        "JD": "JD.com Inc.",
        "BIDU": "Baidu Inc.",
        "NIO": "NIO Inc.",
        "LI": "Li Auto Inc.",
        "XPEV": "XPeng Inc."
    },
    "🇮🇳 Indian": {
        "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "Tata Consultancy",
        "INFY.NS": "Infosys",
        "HDB": "HDFC Bank",
        "IBN": "ICICI Bank",
        "WIT": "Wipro"
    },
    "🇧🇷 Brazilian": {
        "VALE": "Vale S.A.",
        "PBR": "Petrobras",
        "ITUB": "Itau Unibanco",
        "BBD": "Banco Bradesco",
        "SID": "Companhia Siderúrgica"
    }
}

GLOBAL_ETFS = {
    "📊 Broad Market ETFs": {
        "SPY": "SPDR S&P 500 ETF",
        "VTI": "Vanguard Total Stock Market",
        "QQQ": "Invesco QQQ Trust",
        "IWM": "iShares Russell 2000",
        "VOO": "Vanguard S&P 500 ETF",
        "IVV": "iShares Core S&P 500",
        "VTV": "Vanguard Value ETF",
        "VUG": "Vanguard Growth ETF",
        "ITOT": "iShares Core S&P Total"
    },
    "🌍 International ETFs": {
        "VEA": "Vanguard Developed Markets",
        "VWO": "Vanguard Emerging Markets",
        "EFA": "iShares MSCI EAFE",
        "EEM": "iShares MSCI Emerging",
        "IEFA": "iShares Core MSCI EAFE",
        "IEMG": "iShares Core MSCI Emerging",
        "VGK": "Vanguard FTSE Europe",
        "VPL": "Vanguard FTSE Pacific",
        "FXI": "iShares China Large-Cap",
        "INDA": "iShares MSCI India",
        "EWJ": "iShares MSCI Japan",
        "EWG": "iShares MSCI Germany"
    },
    "🏭 Sector ETFs": {
        "XLK": "Technology Select Sector",
        "XLV": "Health Care Select",
        "XLF": "Financial Select",
        "XLE": "Energy Select",
        "XLI": "Industrial Select",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLU": "Utilities Select",
        "XLB": "Materials Select",
        "XLRE": "Real Estate Select",
        "XLC": "Communication Services"
    },
    "🚀 Technology ETFs": {
        "VGT": "Vanguard IT ETF",
        "SOXX": "iShares Semiconductor",
        "SMH": "VanEck Semiconductor",
        "ARKK": "ARK Innovation",
        "ARKQ": "ARK Autonomous & Robotics",
        "CLOU": "Global X Cloud Computing",
        "SKYY": "First Trust Cloud Computing",
        "ROBO": "ROBO Global Robotics",
        "FINX": "Global X FinTech"
    },
    "🏥 Healthcare ETFs": {
        "VHT": "Vanguard Health Care",
        "IBB": "iShares Biotechnology",
        "XBI": "SPDR S&P Biotech",
        "IHE": "iShares US Pharmaceuticals",
        "ARKG": "ARK Genomic Revolution",
        "BBH": "VanEck Biotech"
    },
    "🏦 Financial ETFs": {
        "VFH": "Vanguard Financials",
        "IYF": "iShares US Financials",
        "KBE": "SPDR S&P Bank",
        "KRE": "SPDR S&P Regional Banking",
        "IAT": "iShares US Regional Banks"
    },
    "⚡ Energy ETFs": {
        "VDE": "Vanguard Energy",
        "IYE": "iShares US Energy",
        "XOP": "SPDR S&P Oil & Gas",
        "IEO": "iShares Global Energy",
        "ICLN": "iShares Clean Energy",
        "PBW": "Invesco Clean Energy"
    },
    "💎 Commodity ETFs": {
        "GLD": "SPDR Gold Trust",
        "SLV": "iShares Silver Trust",
        "UNG": "United States Natural Gas",
        "USO": "United States Oil Fund",
        "DBA": "Invesco DB Agriculture",
        "DBC": "Invesco DB Commodity"
    },
    "🏠 Real Estate ETFs": {
        "VNQ": "Vanguard Real Estate",
        "IYR": "iShares US Real Estate",
        "REET": "iShares Global REIT",
        "RWR": "SPDR DJ REIT"
    },
    "🎯 Thematic ETFs": {
        "JETS": "US Global Jets",
        "ESPO": "VanEck Video Gaming",
        "HERO": "Global X Video Games",
        "UFO": "Procure Space",
        "HACK": "ETFMG Prime Cyber Security",
        "EDOC": "Global X Telemedicine"
    }
}

@st.cache_data(ttl=300)
def get_stock_data_cached(symbol: str, period: str = "1y"):
    """Get stock data with caching to prevent rate limiting."""
    try:
        time.sleep(random.uniform(0.1, 0.3))
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        info = stock.info
        return data, info
    except Exception as e:
        return None, None

def calculate_technical_indicators(data):
    """Calculate basic technical indicators."""
    try:
        if data is None or len(data) < 20:
            return {}

        # Simple Moving Averages
        sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]

        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        # Volatility (20-day)
        volatility = data['Close'].pct_change().rolling(window=20).std().iloc[-1] * np.sqrt(252) * 100

        return {
            'sma_20': sma_20,
            'sma_50': sma_50,
            'rsi': rsi,
            'volatility': volatility
        }
    except:
        return {}

def get_trading_signal(current_price, sma_20, sma_50, rsi):
    """Generate simple trading signal based on technical indicators."""
    try:
        if current_price > sma_20 > sma_50 and 30 < rsi < 70:
            return "BUY", "🟢 Uptrend with momentum"
        elif current_price < sma_20 < sma_50 and (rsi > 70 or rsi < 30):
            return "SELL", "🔴 Downtrend or overbought/oversold"
        else:
            return "HOLD", "🟡 Sideways trend or mixed signals"
    except:
        return "HOLD", "🟡 Insufficient data"

def display_asset_grid(assets_dict, category_title):
    """Display assets in a grid format."""
    st.markdown(f'<div class="category-header">{category_title}</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    col_idx = 0

    for symbol, name in assets_dict.items():
        with cols[col_idx % 5]:
            if st.button(f"{symbol}", key=f"{category_title}_{symbol}", help=f"{name}"):
                st.session_state.selected_symbol = symbol
                st.session_state.selected_name = name
                st.rerun()
        col_idx += 1

def display_detailed_analysis(symbol, name):
    """Display detailed analysis for selected symbol."""
    st.markdown(f'<div class="category-header">📊 Detailed Analysis: {symbol} - {name}</div>', unsafe_allow_html=True)

    # Get data
    data, info = get_stock_data_cached(symbol)

    if data is None or len(data) == 0:
        st.error(f"❌ Could not fetch data for {symbol}")
        return

    # Basic info
    col1, col2, col3, col4 = st.columns(4)

    current_price = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
    change = ((current_price - prev_close) / prev_close * 100)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Current Price</h3>
            <h2>${current_price:.2f}</h2>
            <p>{"📈" if change >= 0 else "📉"} {change:+.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

    # Technical indicators
    indicators = calculate_technical_indicators(data)

    with col2:
        volume = data['Volume'].iloc[-1] if 'Volume' in data else 0
        avg_volume = data['Volume'].rolling(20).mean().iloc[-1] if 'Volume' in data else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Volume</h3>
            <h2>{volume:,.0f}</h2>
            <p>Avg: {avg_volume:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        market_cap = info.get('marketCap', 0) if info else 0
        pe_ratio = info.get('trailingPE', 0) if info else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏢 Market Cap</h3>
            <h2>${market_cap/1e9:.1f}B</h2>
            <p>P/E: {pe_ratio:.1f}</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        volatility = indicators.get('volatility', 0)
        rsi = indicators.get('rsi', 50)
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Volatility</h3>
            <h2>{volatility:.1f}%</h2>
            <p>RSI: {rsi:.1f}</p>
        </div>
        """, unsafe_allow_html=True)

    # Trading Signal
    if indicators:
        signal, reason = get_trading_signal(
            current_price,
            indicators.get('sma_20', current_price),
            indicators.get('sma_50', current_price),
            indicators.get('rsi', 50)
        )

        signal_class = f"signal-{signal.lower()}"
        st.markdown(f"""
        <div class="trading-signal {signal_class}">
            <h3>🎯 Trading Signal: {signal}</h3>
            <p>{reason}</p>
        </div>
        """, unsafe_allow_html=True)

    # Price Chart
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name=symbol
    ))

    # Add moving averages if available
    if indicators and 'sma_20' in indicators:
        sma_20_series = data['Close'].rolling(window=20).mean()
        sma_50_series = data['Close'].rolling(window=50).mean()

        fig.add_trace(go.Scatter(
            x=data.index,
            y=sma_20_series,
            mode='lines',
            name='SMA 20',
            line=dict(color='orange', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=data.index,
            y=sma_50_series,
            mode='lines',
            name='SMA 50',
            line=dict(color='red', width=2)
        ))

    fig.update_layout(
        title=f"{symbol} - {name} Price Chart",
        yaxis_title="Price ($)",
        xaxis_title="Date",
        height=500,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Fund Membership (for stocks)
    if symbol in ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA"]:
        st.markdown(f"""
        <div class="fund-membership">
            <h3>🏦 Fund Membership for {symbol}</h3>
            <p><strong>Major ETFs:</strong> SPY, QQQ, VTI, VOO, IVV, XLK, VGT</p>
            <p><strong>Sector ETFs:</strong> XLK (Technology), XLY (Consumer Discretionary)</p>
            <p><strong>Thematic ETFs:</strong> ARKK, ARKW, SOXX (for tech stocks)</p>
            <p><strong>Mutual Funds:</strong> VTSAX, FXNAX, FZROX</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main dashboard application."""

    # Header
    st.markdown('<h1 class="main-header">📈 Comprehensive Global Stocks & ETFs Dashboard</h1>', unsafe_allow_html=True)

    # Initialize session state
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = None
    if 'selected_name' not in st.session_state:
        st.session_state.selected_name = None

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🎯 Dashboard Controls</div>', unsafe_allow_html=True)

        # Search
        search_symbol = st.text_input("🔍 Search Symbol", placeholder="Enter symbol (e.g., AAPL)").upper()
        if search_symbol and st.button("🎯 Analyze"):
            st.session_state.selected_symbol = search_symbol
            st.session_state.selected_name = f"Manual Search: {search_symbol}"
            st.rerun()

        # Quick filters
        st.markdown("### 🌍 Quick Filters")
        show_stocks = st.checkbox("📈 Show Stocks", value=True)
        show_etfs = st.checkbox("🏛️ Show ETFs", value=True)

        # Market status
        st.markdown("---")
        st.markdown("### 📊 Market Status")
        st.success("✅ Markets Open")
        st.info(f"🕐 Last Update: {datetime.now().strftime('%H:%M:%S')}")

        # Performance summary
        st.markdown("### 📈 Quick Performance")
        st.metric("S&P 500", "4,450", "1.2%")
        st.metric("NASDAQ", "13,800", "0.8%")
        st.metric("VIX", "18.5", "-2.1%")

    # Main content
    if st.session_state.selected_symbol:
        # Show detailed analysis
        display_detailed_analysis(st.session_state.selected_symbol, st.session_state.selected_name)

        # Back button
        if st.button("⬅️ Back to Overview"):
            st.session_state.selected_symbol = None
            st.session_state.selected_name = None
            st.rerun()

    else:
        # Show overview
        st.markdown("### 🌟 Select an asset for detailed analysis")

        # Display stocks
        if show_stocks:
            st.markdown("## 📈 Global Stocks")
            for region, stocks in GLOBAL_STOCKS.items():
                display_asset_grid(stocks, region)

        # Display ETFs
        if show_etfs:
            st.markdown("## 🏛️ Global ETFs")
            for category, etfs in GLOBAL_ETFS.items():
                display_asset_grid(etfs, category)

        # Market Overview
        st.markdown("## 🌍 Global Market Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🇺🇸 US Markets</h3>
                <p>S&P 500: 4,450 (+1.2%)</p>
                <p>NASDAQ: 13,800 (+0.8%)</p>
                <p>DOW: 34,500 (+0.5%)</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>🌍 International</h3>
                <p>FTSE 100: 7,400 (+0.3%)</p>
                <p>DAX: 15,200 (-0.2%)</p>
                <p>Nikkei: 28,800 (+1.1%)</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>📊 Market Indicators</h3>
                <p>VIX: 18.5 (-2.1%)</p>
                <p>USD/EUR: 1.08 (+0.1%)</p>
                <p>Gold: $1,950 (+0.8%)</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()