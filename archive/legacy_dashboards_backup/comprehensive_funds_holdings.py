"""
Comprehensive Fund Holdings Analysis Dashboard
Professional-grade fund analysis with comprehensive global coverage
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
    page_title="Fund Holdings Analysis",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS with dark theme and good contrast
st.markdown("""
<style>
    /* Global dark theme styling */
    .stApp, .stApp * {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }

    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    /* Card styling with dark theme */
    .metric-card {
        background: linear-gradient(135deg, #2a4365 0%, #3182ce 100%) !important;
        padding: 1.5rem;
        border-radius: 15px;
        color: white !important;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }

    .metric-card h1, .metric-card h2, .metric-card h3,
    .metric-card h4, .metric-card h5, .metric-card h6,
    .metric-card p, .metric-card div, .metric-card span,
    .metric-card label {
        color: white !important;
    }

    /* Fund performance indicators */
    .performance-positive {
        background: linear-gradient(135deg, #38a169 0%, #48bb78 100%) !important;
        color: white !important;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        display: inline-block;
        margin: 0.2rem;
        font-weight: bold;
    }

    .performance-negative {
        background: linear-gradient(135deg, #e53e3e 0%, #f56565 100%) !important;
        color: white !important;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        display: inline-block;
        margin: 0.2rem;
        font-weight: bold;
    }

    /* Category headers */
    .category-header {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
        color: white !important;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 1.3rem;
        font-weight: bold;
        text-align: center;
    }

    /* ETF grid buttons */
    .etf-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    .etf-card {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
        color: white !important;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
        border: none;
    }

    .etf-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }

    /* Sidebar styling */
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #fafafa !important;
        margin-bottom: 1rem;
    }

    /* Streamlit component overrides */
    .stSelectbox > div > div {
        background-color: #2d3748 !important;
        color: white !important;
    }

    .stTextInput > div > div > input {
        background-color: #2d3748 !important;
        color: white !important;
    }

    /* Metric overrides */
    .metric-container .metric-value {
        color: #fafafa !important;
    }

    .metric-container .metric-delta {
        color: #fafafa !important;
    }

    /* Table styling */
    .dataframe {
        background-color: #2d3748 !important;
        color: white !important;
    }

    .dataframe th {
        background-color: #4a5568 !important;
        color: white !important;
    }

    .dataframe td {
        background-color: #2d3748 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Comprehensive global ETFs and funds database
COMPREHENSIVE_ETFS = {
    "📊 Broad Market ETFs": {
        "SPY": {"name": "SPDR S&P 500 ETF", "category": "US Large Cap", "expense_ratio": 0.0945},
        "VTI": {"name": "Vanguard Total Stock Market", "category": "US Total Market", "expense_ratio": 0.03},
        "QQQ": {"name": "Invesco QQQ Trust", "category": "NASDAQ 100", "expense_ratio": 0.20},
        "IWM": {"name": "iShares Russell 2000", "category": "US Small Cap", "expense_ratio": 0.19},
        "VOO": {"name": "Vanguard S&P 500 ETF", "category": "US Large Cap", "expense_ratio": 0.03},
        "IVV": {"name": "iShares Core S&P 500", "category": "US Large Cap", "expense_ratio": 0.03},
        "VTV": {"name": "Vanguard Value ETF", "category": "US Value", "expense_ratio": 0.04},
        "VUG": {"name": "Vanguard Growth ETF", "category": "US Growth", "expense_ratio": 0.04},
        "IJH": {"name": "iShares Core S&P Mid-Cap", "category": "US Mid Cap", "expense_ratio": 0.05},
        "IJR": {"name": "iShares Core S&P Small-Cap", "category": "US Small Cap", "expense_ratio": 0.06}
    },

    "🌍 International ETFs": {
        "VEA": {"name": "Vanguard Developed Markets", "category": "Developed Markets", "expense_ratio": 0.05},
        "VWO": {"name": "Vanguard Emerging Markets", "category": "Emerging Markets", "expense_ratio": 0.10},
        "EFA": {"name": "iShares MSCI EAFE", "category": "Europe/Asia", "expense_ratio": 0.32},
        "EEM": {"name": "iShares MSCI Emerging", "category": "Emerging Markets", "expense_ratio": 0.68},
        "IEFA": {"name": "iShares Core MSCI EAFE", "category": "Developed Markets", "expense_ratio": 0.07},
        "IEMG": {"name": "iShares Core MSCI Emerging", "category": "Emerging Markets", "expense_ratio": 0.11},
        "VGK": {"name": "Vanguard FTSE Europe", "category": "Europe", "expense_ratio": 0.08},
        "VPL": {"name": "Vanguard FTSE Pacific", "category": "Pacific", "expense_ratio": 0.08},
        "FXI": {"name": "iShares China Large-Cap", "category": "China", "expense_ratio": 0.74},
        "INDA": {"name": "iShares MSCI India", "category": "India", "expense_ratio": 0.80},
        "EWJ": {"name": "iShares MSCI Japan", "category": "Japan", "expense_ratio": 0.50},
        "EWG": {"name": "iShares MSCI Germany", "category": "Germany", "expense_ratio": 0.51}
    },

    "🏭 Sector ETFs": {
        "XLK": {"name": "Technology Select Sector", "category": "Technology", "expense_ratio": 0.12},
        "XLV": {"name": "Health Care Select", "category": "Healthcare", "expense_ratio": 0.12},
        "XLF": {"name": "Financial Select", "category": "Financials", "expense_ratio": 0.12},
        "XLE": {"name": "Energy Select", "category": "Energy", "expense_ratio": 0.12},
        "XLI": {"name": "Industrial Select", "category": "Industrials", "expense_ratio": 0.12},
        "XLY": {"name": "Consumer Discretionary", "category": "Consumer Disc.", "expense_ratio": 0.12},
        "XLP": {"name": "Consumer Staples", "category": "Consumer Staples", "expense_ratio": 0.12},
        "XLU": {"name": "Utilities Select", "category": "Utilities", "expense_ratio": 0.12},
        "XLB": {"name": "Materials Select", "category": "Materials", "expense_ratio": 0.12},
        "XLRE": {"name": "Real Estate Select", "category": "Real Estate", "expense_ratio": 0.12},
        "XLC": {"name": "Communication Services", "category": "Communications", "expense_ratio": 0.12}
    },

    "🚀 Technology ETFs": {
        "VGT": {"name": "Vanguard IT ETF", "category": "Technology", "expense_ratio": 0.10},
        "SOXX": {"name": "iShares Semiconductor", "category": "Semiconductors", "expense_ratio": 0.46},
        "SMH": {"name": "VanEck Semiconductor", "category": "Semiconductors", "expense_ratio": 0.35},
        "ARKK": {"name": "ARK Innovation", "category": "Innovation", "expense_ratio": 0.75},
        "ARKQ": {"name": "ARK Autonomous & Robotics", "category": "Robotics", "expense_ratio": 0.75},
        "CLOU": {"name": "Global X Cloud Computing", "category": "Cloud Computing", "expense_ratio": 0.68},
        "SKYY": {"name": "First Trust Cloud Computing", "category": "Cloud", "expense_ratio": 0.60},
        "ROBO": {"name": "ROBO Global Robotics", "category": "Robotics", "expense_ratio": 0.95},
        "FINX": {"name": "Global X FinTech", "category": "FinTech", "expense_ratio": 0.68}
    },

    "🏥 Healthcare ETFs": {
        "VHT": {"name": "Vanguard Health Care", "category": "Healthcare", "expense_ratio": 0.10},
        "IBB": {"name": "iShares Biotechnology", "category": "Biotechnology", "expense_ratio": 0.45},
        "XBI": {"name": "SPDR S&P Biotech", "category": "Biotech", "expense_ratio": 0.35},
        "IHE": {"name": "iShares US Pharmaceuticals", "category": "Pharmaceuticals", "expense_ratio": 0.42},
        "ARKG": {"name": "ARK Genomic Revolution", "category": "Genomics", "expense_ratio": 0.75},
        "BBH": {"name": "VanEck Biotech", "category": "Biotechnology", "expense_ratio": 0.35}
    },

    "🏦 Financial ETFs": {
        "VFH": {"name": "Vanguard Financials", "category": "Financials", "expense_ratio": 0.10},
        "IYF": {"name": "iShares US Financials", "category": "Financials", "expense_ratio": 0.42},
        "KBE": {"name": "SPDR S&P Bank", "category": "Banks", "expense_ratio": 0.35},
        "KRE": {"name": "SPDR S&P Regional Banking", "category": "Regional Banks", "expense_ratio": 0.35},
        "IAT": {"name": "iShares US Regional Banks", "category": "Regional Banks", "expense_ratio": 0.42}
    },

    "⚡ Energy ETFs": {
        "VDE": {"name": "Vanguard Energy", "category": "Energy", "expense_ratio": 0.10},
        "IYE": {"name": "iShares US Energy", "category": "Energy", "expense_ratio": 0.42},
        "XOP": {"name": "SPDR S&P Oil & Gas", "category": "Oil & Gas", "expense_ratio": 0.35},
        "IEO": {"name": "iShares Global Energy", "category": "Global Energy", "expense_ratio": 0.44},
        "ICLN": {"name": "iShares Clean Energy", "category": "Clean Energy", "expense_ratio": 0.42},
        "PBW": {"name": "Invesco Clean Energy", "category": "Clean Energy", "expense_ratio": 0.70}
    },

    "💎 Commodity ETFs": {
        "GLD": {"name": "SPDR Gold Trust", "category": "Gold", "expense_ratio": 0.40},
        "SLV": {"name": "iShares Silver Trust", "category": "Silver", "expense_ratio": 0.50},
        "UNG": {"name": "United States Natural Gas", "category": "Natural Gas", "expense_ratio": 1.28},
        "USO": {"name": "United States Oil Fund", "category": "Oil", "expense_ratio": 0.79},
        "DBA": {"name": "Invesco DB Agriculture", "category": "Agriculture", "expense_ratio": 0.93},
        "DBC": {"name": "Invesco DB Commodity", "category": "Commodities", "expense_ratio": 0.87}
    },

    "🏠 Real Estate ETFs": {
        "VNQ": {"name": "Vanguard Real Estate", "category": "REITs", "expense_ratio": 0.12},
        "IYR": {"name": "iShares US Real Estate", "category": "Real Estate", "expense_ratio": 0.42},
        "REET": {"name": "iShares Global REIT", "category": "Global REITs", "expense_ratio": 0.14},
        "RWR": {"name": "SPDR DJ REIT", "category": "REITs", "expense_ratio": 0.25}
    },

    "🎯 Thematic ETFs": {
        "JETS": {"name": "US Global Jets", "category": "Airlines", "expense_ratio": 0.60},
        "ESPO": {"name": "VanEck Video Gaming", "category": "Gaming", "expense_ratio": 0.55},
        "HERO": {"name": "Global X Video Games", "category": "Video Games", "expense_ratio": 0.50},
        "UFO": {"name": "Procure Space", "category": "Space", "expense_ratio": 0.75},
        "HACK": {"name": "ETFMG Prime Cyber Security", "category": "Cybersecurity", "expense_ratio": 0.60},
        "EDOC": {"name": "Global X Telemedicine", "category": "Telemedicine", "expense_ratio": 0.68}
    }
}

@st.cache_data(ttl=300)
def get_etf_data_cached(symbol: str):
    """Get ETF data with caching to prevent rate limiting."""
    try:
        time.sleep(random.uniform(0.1, 0.3))
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1y")

        if len(hist) > 0:
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close != 0 else 0

            return {
                'current_price': current_price,
                'change_pct': change_pct,
                'volume': hist['Volume'].iloc[-1] if 'Volume' in hist else 0,
                'market_cap': info.get('totalAssets', 0),
                'expense_ratio': info.get('annualReportExpenseRatio', 0),
                'holdings_count': info.get('holdingsCount', 0),
                'name': info.get('longName', symbol)
            }
    except Exception as e:
        return None

def display_etf_grid(etfs_dict, category_title):
    """Display ETFs in a professional grid format."""
    st.markdown(f'<div class="category-header">{category_title}</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    col_idx = 0

    for symbol, data in etfs_dict.items():
        with cols[col_idx % 5]:
            if st.button(f"{symbol}", key=f"{category_title}_{symbol}", help=f"{data['name']} - Expense Ratio: {data['expense_ratio']}%"):
                st.session_state.selected_etf = symbol
                st.session_state.selected_etf_data = data
                st.rerun()
        col_idx += 1

def display_detailed_etf_analysis(symbol, etf_static_data):
    """Display detailed analysis for selected ETF."""
    st.markdown(f'<div class="category-header">💼 Detailed Analysis: {symbol} - {etf_static_data["name"]}</div>', unsafe_allow_html=True)

    # Get live data
    live_data = get_etf_data_cached(symbol)

    if live_data:
        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            change_color = "positive" if live_data['change_pct'] >= 0 else "negative"
            st.markdown(f"""
            <div class="metric-card">
                <h3>💰 Current Price</h3>
                <h2>${live_data['current_price']:.2f}</h2>
                <div class="performance-{change_color}">{"📈" if live_data['change_pct'] >= 0 else "📉"} {live_data['change_pct']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            assets = live_data['market_cap']
            if assets > 1e9:
                assets_display = f"${assets/1e9:.1f}B"
            elif assets > 1e6:
                assets_display = f"${assets/1e6:.1f}M"
            else:
                assets_display = f"${assets:,.0f}"

            st.markdown(f"""
            <div class="metric-card">
                <h3>🏛️ Total Assets</h3>
                <h2>{assets_display}</h2>
                <p>Under Management</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Expense Ratio</h3>
                <h2>{etf_static_data['expense_ratio']:.2f}%</h2>
                <p>Annual Fee</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            volume = live_data['volume']
            if volume > 1e6:
                volume_display = f"{volume/1e6:.1f}M"
            elif volume > 1e3:
                volume_display = f"{volume/1e3:.1f}K"
            else:
                volume_display = f"{volume:,.0f}"

            st.markdown(f"""
            <div class="metric-card">
                <h3>📈 Volume</h3>
                <h2>{volume_display}</h2>
                <p>Holdings: {live_data['holdings_count']}</p>
            </div>
            """, unsafe_allow_html=True)

        # ETF Information
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📋 ETF Information</h3>
                <p><strong>Category:</strong> {etf_static_data['category']}</p>
                <p><strong>Full Name:</strong> {live_data['name']}</p>
                <p><strong>Ticker:</strong> {symbol}</p>
                <p><strong>Holdings Count:</strong> {live_data['holdings_count']:,}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>💡 Investment Highlights</h3>
                <p><strong>Low Cost:</strong> {"✅" if etf_static_data['expense_ratio'] < 0.20 else "⚠️"} {etf_static_data['expense_ratio']:.2f}% expense ratio</p>
                <p><strong>Liquidity:</strong> {"✅" if volume > 100000 else "⚠️"} Daily volume: {volume_display}</p>
                <p><strong>Assets:</strong> {"✅" if assets > 1e9 else "⚠️"} {assets_display} AUM</p>
                <p><strong>Diversification:</strong> {"✅" if live_data['holdings_count'] > 50 else "⚠️"} {live_data['holdings_count']} holdings</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.error(f"❌ Could not fetch live data for {symbol}")

def main():
    """Main dashboard application."""

    # Header
    st.markdown('<h1 class="main-header">💼 Comprehensive Fund Holdings Analysis</h1>', unsafe_allow_html=True)

    # Initialize session state
    if 'selected_etf' not in st.session_state:
        st.session_state.selected_etf = None
    if 'selected_etf_data' not in st.session_state:
        st.session_state.selected_etf_data = None

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🎯 Fund Analysis Controls</div>', unsafe_allow_html=True)

        # Search
        search_symbol = st.text_input("🔍 Search ETF Symbol", placeholder="Enter symbol (e.g., SPY)").upper()
        if search_symbol and st.button("🎯 Analyze"):
            # Find the ETF in our database
            found = False
            for category, etfs in COMPREHENSIVE_ETFS.items():
                if search_symbol in etfs:
                    st.session_state.selected_etf = search_symbol
                    st.session_state.selected_etf_data = etfs[search_symbol]
                    found = True
                    st.rerun()
                    break
            if not found:
                st.warning(f"ETF {search_symbol} not found in database")

        # Quick filters
        st.markdown("### 📊 Quick Filters")
        show_broad_market = st.checkbox("📊 Broad Market ETFs", value=True)
        show_international = st.checkbox("🌍 International ETFs", value=True)
        show_sector = st.checkbox("🏭 Sector ETFs", value=True)
        show_thematic = st.checkbox("🎯 Thematic ETFs", value=True)

        # Market status
        st.markdown("---")
        st.markdown("### 📊 Market Status")
        st.success("✅ Markets Open")
        st.info(f"🕐 Last Update: {datetime.now().strftime('%H:%M:%S')}")

        # ETF Statistics
        st.markdown("### 📈 ETF Statistics")
        total_etfs = sum(len(etfs) for etfs in COMPREHENSIVE_ETFS.values())
        st.metric("Total ETFs", total_etfs)
        st.metric("Categories", len(COMPREHENSIVE_ETFS))
        st.metric("Avg Expense Ratio", "0.35%")

    # Main content
    if st.session_state.selected_etf:
        # Show detailed analysis
        display_detailed_etf_analysis(st.session_state.selected_etf, st.session_state.selected_etf_data)

        # Back button
        if st.button("⬅️ Back to ETF Overview"):
            st.session_state.selected_etf = None
            st.session_state.selected_etf_data = None
            st.rerun()

    else:
        # Show overview
        st.markdown("### 🌟 Select an ETF for detailed holdings analysis")

        # Display ETFs based on filters
        if show_broad_market:
            display_etf_grid(COMPREHENSIVE_ETFS["📊 Broad Market ETFs"], "📊 Broad Market ETFs")

        if show_international:
            display_etf_grid(COMPREHENSIVE_ETFS["🌍 International ETFs"], "🌍 International ETFs")

        if show_sector:
            display_etf_grid(COMPREHENSIVE_ETFS["🏭 Sector ETFs"], "🏭 Sector ETFs")

        # Display Technology ETFs
        display_etf_grid(COMPREHENSIVE_ETFS["🚀 Technology ETFs"], "🚀 Technology ETFs")

        # Display Healthcare ETFs
        display_etf_grid(COMPREHENSIVE_ETFS["🏥 Healthcare ETFs"], "🏥 Healthcare ETFs")

        # Display Financial ETFs
        display_etf_grid(COMPREHENSIVE_ETFS["🏦 Financial ETFs"], "🏦 Financial ETFs")

        # Display Energy ETFs
        display_etf_grid(COMPREHENSIVE_ETFS["⚡ Energy ETFs"], "⚡ Energy ETFs")

        # Display Commodity ETFs
        display_etf_grid(COMPREHENSIVE_ETFS["💎 Commodity ETFs"], "💎 Commodity ETFs")

        # Display Real Estate ETFs
        display_etf_grid(COMPREHENSIVE_ETFS["🏠 Real Estate ETFs"], "🏠 Real Estate ETFs")

        if show_thematic:
            display_etf_grid(COMPREHENSIVE_ETFS["🎯 Thematic ETFs"], "🎯 Thematic ETFs")

        # Market Overview
        st.markdown("## 🌍 ETF Market Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>📊 Most Popular ETFs</h3>
                <p>SPY: $380.45 (+0.8%)</p>
                <p>QQQ: $340.12 (+1.2%)</p>
                <p>VTI: $220.85 (+0.6%)</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>🌍 International Leaders</h3>
                <p>VEA: $48.20 (+0.4%)</p>
                <p>EEM: $39.15 (-0.2%)</p>
                <p>VWO: $42.80 (+0.1%)</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>🎯 Sector Performance</h3>
                <p>XLK: Technology (+1.5%)</p>
                <p>XLV: Healthcare (+0.8%)</p>
                <p>XLE: Energy (-0.5%)</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()