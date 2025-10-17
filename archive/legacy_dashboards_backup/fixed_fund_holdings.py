#!/usr/bin/env python3
"""
Fixed Fund Holdings Analysis - Düzeltilmiş Fon Analizi
Beyaz arka plan ve readability sorunları çözülmüş
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

# Page Configuration
st.set_page_config(
    page_title="💼 Fixed Fund Holdings Analysis",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Fixed CSS - Dark theme throughout
st.markdown("""
<style>
    /* Global Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0c1018 0%, #1a1f2e 50%, #2d3748 100%);
        color: #e2e8f0 !important;
    }

    /* Force all text to be light */
    .stApp, .stApp *, h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #e2e8f0 !important;
    }

    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
        color: white !important;
        text-align: center;
    }

    /* Card styling - All dark */
    .metric-card {
        background: linear-gradient(135deg, #2a4365 0%, #3182ce 100%);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        border: 1px solid #4299e1;
        margin: 0.5rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        color: white !important;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }

    /* Fund item styling - Dark */
    .fund-item {
        background: linear-gradient(135deg, #2a4365 0%, #3182ce 100%);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
        color: white !important;
    }

    .fund-item:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.4);
    }

    /* Stock item styling - Dark */
    .stock-item {
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.3rem 0;
        border: 1px solid #4a5568;
        transition: transform 0.2s ease;
        color: white !important;
    }

    .stock-item:hover {
        transform: translateY(-1px);
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1a202c;
        border-radius: 10px;
        padding: 0.5rem;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2a4365 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        color: white !important;
        border-radius: 8px 8px 0 0;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(45deg, #764ba2, #667eea);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a202c 0%, #2d3748 100%);
    }

    /* Performance indicators */
    .positive { color: #68d391 !important; font-weight: bold; }
    .negative { color: #fc8181 !important; font-weight: bold; }
    .neutral { color: #a0aec0 !important; font-weight: bold; }

    /* Analysis cards */
    .analysis-card {
        background: linear-gradient(135deg, #553c9a 0%, #805ad5 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #9f7aea;
        box-shadow: 0 6px 20px rgba(159, 122, 234, 0.2);
        color: white !important;
    }

    /* Warning cards */
    .warning-card {
        background: linear-gradient(135deg, #d69e2e 0%, #f6e05e 100%);
        color: #1a202c !important;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid #faf089;
        box-shadow: 0 4px 15px rgba(250, 240, 137, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Cache for data fetching
@st.cache_data(ttl=300)
def get_fund_data_cached(symbol):
    """Rate limiting ile fon verilerini çek"""
    try:
        time.sleep(random.uniform(0.1, 0.3))

        fund = yf.Ticker(symbol)
        data = fund.history(period="1y")
        info = fund.info

        return data, info
    except Exception as e:
        return None, None

# Expanded Fund Universe
def get_comprehensive_funds():
    """Kapsamlı fon listesi - 50+ ETF"""
    return {
        # Broad Market ETFs
        'SPY': 'SPDR S&P 500 ETF Trust',
        'VOO': 'Vanguard S&P 500 ETF',
        'IVV': 'iShares Core S&P 500 ETF',
        'VTI': 'Vanguard Total Stock Market ETF',
        'QQQ': 'Invesco QQQ Trust',
        'IWM': 'iShares Russell 2000 ETF',
        'VEA': 'Vanguard FTSE Developed Markets ETF',
        'VWO': 'Vanguard FTSE Emerging Markets ETF',

        # Sector ETFs
        'XLK': 'Technology Select Sector SPDR Fund',
        'XLF': 'Financial Select Sector SPDR Fund',
        'XLE': 'Energy Select Sector SPDR Fund',
        'XLV': 'Health Care Select Sector SPDR Fund',
        'XLI': 'Industrial Select Sector SPDR Fund',
        'XLY': 'Consumer Discretionary Select Sector SPDR Fund',
        'XLP': 'Consumer Staples Select Sector SPDR Fund',
        'XLU': 'Utilities Select Sector SPDR Fund',
        'XLB': 'Materials Select Sector SPDR Fund',
        'XLRE': 'Real Estate Select Sector SPDR Fund',
        'XLC': 'Communication Services Select Sector SPDR Fund',

        # Technology ETFs
        'VGT': 'Vanguard Information Technology ETF',
        'SOXX': 'iShares PHLX Semiconductor ETF',
        'SMH': 'VanEck Vectors Semiconductor ETF',
        'QTEC': 'First Trust NASDAQ-100 Technology Sector Index Fund',
        'FTEC': 'Fidelity MSCI Information Technology Index ETF',
        'IGM': 'iShares Expanded Tech Sector ETF',
        'IYW': 'iShares U.S. Technology ETF',

        # Bond ETFs
        'TLT': 'iShares 20+ Year Treasury Bond ETF',
        'IEF': 'iShares 7-10 Year Treasury Bond ETF',
        'SHY': 'iShares 1-3 Year Treasury Bond ETF',
        'LQD': 'iShares iBoxx $ Investment Grade Corporate Bond ETF',
        'HYG': 'iShares iBoxx $ High Yield Corporate Bond ETF',
        'AGG': 'iShares Core U.S. Aggregate Bond ETF',
        'BND': 'Vanguard Total Bond Market ETF',

        # International ETFs
        'EEM': 'iShares MSCI Emerging Markets ETF',
        'EFA': 'iShares MSCI EAFE ETF',
        'FXI': 'iShares China Large-Cap ETF',
        'EWJ': 'iShares MSCI Japan ETF',
        'EWG': 'iShares MSCI Germany ETF',
        'EWU': 'iShares MSCI United Kingdom ETF',
        'INDA': 'iShares MSCI India ETF',

        # Commodity ETFs
        'GLD': 'SPDR Gold Shares',
        'SLV': 'iShares Silver Trust',
        'USO': 'United States Oil Fund',
        'DBA': 'Invesco DB Agriculture Fund',
        'PDBC': 'Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF',

        # Dividend ETFs
        'SCHD': 'Schwab US Dividend Equity ETF',
        'VYM': 'Vanguard High Dividend Yield ETF',
        'DVY': 'iShares Select Dividend ETF',
        'HDV': 'iShares Core High Dividend ETF',
        'NOBL': 'ProShares S&P 500 Dividend Aristocrats ETF',
        'VIG': 'Vanguard Dividend Appreciation ETF',

        # Thematic ETFs
        'ARKK': 'ARK Innovation ETF',
        'ARKQ': 'ARK Autonomous Technology & Robotics ETF',
        'ARKW': 'ARK Next Generation Internet ETF',
        'ICLN': 'iShares Global Clean Energy ETF',
        'JETS': 'U.S. Global Jets ETF',
        'HACK': 'ETFMG Prime Cyber Security ETF',
        'ROBO': 'ROBO Global Robotics and Automation Index ETF',

        # Growth/Value ETFs
        'VUG': 'Vanguard Growth ETF',
        'VTV': 'Vanguard Value ETF',
        'IVW': 'iShares Core S&P 500 Growth ETF',
        'IVE': 'iShares Core S&P 500 Value ETF'
    }

# Simulated holdings data for demonstration
def get_simulated_holdings(fund_symbol):
    """Simulate fund holdings data"""

    # Sample holdings for different fund types
    holdings_data = {
        'SPY': {
            'AAPL': {'weight': 7.2, 'shares': 165_000_000, 'value': 28_800_000_000},
            'MSFT': {'weight': 6.8, 'shares': 45_000_000, 'value': 15_300_000_000},
            'GOOGL': {'weight': 4.1, 'shares': 12_000_000, 'value': 3_600_000_000},
            'AMZN': {'weight': 3.5, 'shares': 25_000_000, 'value': 3_400_000_000},
            'NVDA': {'weight': 3.2, 'shares': 8_500_000, 'value': 3_700_000_000},
            'TSLA': {'weight': 2.8, 'shares': 11_000_000, 'value': 2_800_000_000},
            'META': {'weight': 2.4, 'shares': 8_000_000, 'value': 2_400_000_000},
            'BRK-B': {'weight': 1.8, 'shares': 5_200_000, 'value': 1_800_000_000},
            'JNJ': {'weight': 1.6, 'shares': 10_200_000, 'value': 1_600_000_000},
            'UNH': {'weight': 1.4, 'shares': 2_800_000, 'value': 1_400_000_000}
        },
        'QQQ': {
            'AAPL': {'weight': 12.5, 'shares': 45_000_000, 'value': 18_000_000_000},
            'MSFT': {'weight': 11.2, 'shares': 25_000_000, 'value': 8_500_000_000},
            'GOOGL': {'weight': 8.8, 'shares': 15_000_000, 'value': 4_500_000_000},
            'AMZN': {'weight': 7.3, 'shares': 18_000_000, 'value': 2_500_000_000},
            'NVDA': {'weight': 6.9, 'shares': 12_000_000, 'value': 5_200_000_000},
            'TSLA': {'weight': 4.2, 'shares': 8_500_000, 'value': 1_800_000_000},
            'META': {'weight': 4.8, 'shares': 6_000_000, 'value': 1_900_000_000},
            'AVGO': {'weight': 3.1, 'shares': 2_200_000, 'value': 1_400_000_000},
            'COST': {'weight': 2.4, 'shares': 1_800_000, 'value': 1_200_000_000},
            'NFLX': {'weight': 2.2, 'shares': 2_500_000, 'value': 1_100_000_000}
        },
        'XLK': {
            'AAPL': {'weight': 23.8, 'shares': 25_000_000, 'value': 10_000_000_000},
            'MSFT': {'weight': 22.1, 'shares': 18_000_000, 'value': 6_100_000_000},
            'NVDA': {'weight': 8.4, 'shares': 5_000_000, 'value': 2_200_000_000},
            'AVGO': {'weight': 4.2, 'shares': 1_200_000, 'value': 680_000_000},
            'CRM': {'weight': 3.8, 'shares': 2_800_000, 'value': 560_000_000},
            'ORCL': {'weight': 3.5, 'shares': 4_200_000, 'value': 420_000_000},
            'ADBE': {'weight': 3.2, 'shares': 1_800_000, 'value': 900_000_000},
            'CSCO': {'weight': 2.9, 'shares': 12_000_000, 'value': 540_000_000},
            'ACN': {'weight': 2.1, 'shares': 1_500_000, 'value': 450_000_000},
            'TXN': {'weight': 1.9, 'shares': 2_200_000, 'value': 380_000_000}
        }
    }

    # Return holdings if available, otherwise generate random holdings
    if fund_symbol in holdings_data:
        return holdings_data[fund_symbol]
    else:
        # Generate random holdings for other funds
        stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'JNJ', 'UNH']
        holdings = {}
        remaining_weight = 100.0

        for i, stock in enumerate(stocks[:8]):
            if i == 7:  # Last stock gets remaining weight
                weight = remaining_weight
            else:
                weight = random.uniform(1, min(15, remaining_weight - (7-i)))
                remaining_weight -= weight

            holdings[stock] = {
                'weight': weight,
                'shares': random.randint(1_000_000, 50_000_000),
                'value': random.randint(500_000_000, 10_000_000_000)
            }

        return holdings

def calculate_fund_metrics(data):
    """Fund performance metrikleri"""
    if len(data) < 2:
        return {}

    returns = data['Close'].pct_change().dropna()

    # Performance metrics
    total_return = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
    ytd_return = total_return  # Simplified for demo
    volatility = returns.std() * np.sqrt(252) * 100

    # Risk metrics
    max_price = data['Close'].max()
    current_price = data['Close'].iloc[-1]
    max_drawdown = ((current_price - max_price) / max_price) * 100 if max_price > 0 else 0

    # Sharpe ratio (simplified)
    sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

    return {
        'total_return': total_return,
        'ytd_return': ytd_return,
        'volatility': volatility,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'avg_volume': data['Volume'].mean()
    }

def main():
    # Header
    st.markdown("""
    <div class="header-container">
        <h1>💼 Fixed Fund Holdings Analysis</h1>
        <p>Kapsamlı ETF ve Fon Analizi - Düzeltilmiş Tasarım</p>
        <p><strong>50+ ETF • Performance Metrics • Holdings Analysis • Risk Assessment</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # Fund selection
    funds = get_comprehensive_funds()

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        selected_fund = st.selectbox(
            "🔍 ETF/Fund Seçin",
            list(funds.keys()),
            format_func=lambda x: f"{x} - {funds[x]}"
        )

    with col2:
        period = st.selectbox("📅 Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)

    with col3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    if selected_fund:
        with st.spinner(f"📊 {selected_fund} analiz ediliyor..."):
            # Get fund data
            data, info = get_fund_data_cached(selected_fund)

            if data is None or data.empty:
                st.markdown("""
                <div class="warning-card">
                    <h3>⚠️ Veri Bulunamadı</h3>
                    <p>Bu fon için veri çekilemedi. Lütfen başka bir fon seçin veya daha sonra tekrar deneyin.</p>
                </div>
                """, unsafe_allow_html=True)
                return

            # Calculate metrics
            metrics = calculate_fund_metrics(data)
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
            daily_change = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0

            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{selected_fund}</h4>
                    <h2>${current_price:.2f}</h2>
                    <p class="{'positive' if daily_change >= 0 else 'negative'}">
                        {daily_change:+.2f}% today
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📈 Total Return</h4>
                    <h3 class="{'positive' if metrics.get('total_return', 0) >= 0 else 'negative'}">
                        {metrics.get('total_return', 0):+.1f}%
                    </h3>
                    <p>1 Year</p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📊 Volatility</h4>
                    <h3>{metrics.get('volatility', 0):.1f}%</h3>
                    <p>Annualized</p>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>⭐ Sharpe Ratio</h4>
                    <h3 class="{'positive' if metrics.get('sharpe_ratio', 0) > 1 else 'neutral'}">
                        {metrics.get('sharpe_ratio', 0):.2f}
                    </h3>
                    <p>Risk Adjusted</p>
                </div>
                """, unsafe_allow_html=True)

            # Price Chart
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Close'],
                mode='lines',
                name='Price',
                line=dict(color='#4299e1', width=2)
            ))

            fig.update_layout(
                title=f"📈 {selected_fund} Price Performance",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                template="plotly_dark",
                height=400,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # Tabs for detailed analysis
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Holdings", "📈 Performance", "⚠️ Risk Analysis", "ℹ️ Fund Info"])

            with tab1:
                st.markdown("""
                <div class="analysis-card">
                    <h3>📊 Top Holdings Analysis</h3>
                    <p>Fonun en büyük holdingleri ve ağırlıkları</p>
                </div>
                """, unsafe_allow_html=True)

                holdings = get_simulated_holdings(selected_fund)

                if holdings:
                    # Holdings pie chart
                    symbols = list(holdings.keys())
                    weights = [holdings[symbol]['weight'] for symbol in symbols]

                    fig_pie = px.pie(
                        values=weights,
                        names=symbols,
                        title=f"{selected_fund} Holdings Distribution",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

                    # Holdings table
                    st.markdown("### 📋 Detailed Holdings")

                    holdings_df = pd.DataFrame([
                        {
                            'Symbol': symbol,
                            'Weight (%)': f"{data['weight']:.1f}%",
                            'Shares': f"{data['shares']:,}",
                            'Value ($)': f"${data['value']:,.0f}"
                        }
                        for symbol, data in holdings.items()
                    ])

                    st.dataframe(holdings_df, use_container_width=True)

                    # Top holdings analysis
                    for symbol, holding_data in list(holdings.items())[:5]:
                        with st.container():
                            st.markdown(f"""
                            <div class="stock-item">
                                <h4>{symbol} - {holding_data['weight']:.1f}%</h4>
                                <p><strong>Shares:</strong> {holding_data['shares']:,}</p>
                                <p><strong>Value:</strong> ${holding_data['value']:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

            with tab2:
                st.markdown("""
                <div class="analysis-card">
                    <h3>📈 Performance Analysis</h3>
                    <p>Detaylı performans metrikleri ve karşılaştırma</p>
                </div>
                """, unsafe_allow_html=True)

                # Performance metrics
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>📊 Returns</h4>
                        <p><strong>Total Return:</strong> {metrics.get('total_return', 0):+.1f}%</p>
                        <p><strong>YTD Return:</strong> {metrics.get('ytd_return', 0):+.1f}%</p>
                        <p><strong>Max Drawdown:</strong> {metrics.get('max_drawdown', 0):.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>📊 Risk Metrics</h4>
                        <p><strong>Volatility:</strong> {metrics.get('volatility', 0):.1f}%</p>
                        <p><strong>Sharpe Ratio:</strong> {metrics.get('sharpe_ratio', 0):.2f}</p>
                        <p><strong>Avg Volume:</strong> {metrics.get('avg_volume', 0):,.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Returns distribution
                returns = data['Close'].pct_change().dropna() * 100

                fig_hist = px.histogram(
                    x=returns,
                    nbins=50,
                    title="Daily Returns Distribution",
                    template="plotly_dark",
                    labels={'x': 'Daily Returns (%)', 'y': 'Frequency'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with tab3:
                st.markdown("""
                <div class="analysis-card">
                    <h3>⚠️ Risk Analysis</h3>
                    <p>Comprehensive risk assessment ve volatility analizi</p>
                </div>
                """, unsafe_allow_html=True)

                # Risk score calculation
                risk_score = 0
                risk_factors = []

                volatility = metrics.get('volatility', 0)
                max_dd = abs(metrics.get('max_drawdown', 0))
                sharpe = metrics.get('sharpe_ratio', 0)

                if volatility > 25:
                    risk_score += 2
                    risk_factors.append("High volatility detected")
                elif volatility > 15:
                    risk_score += 1
                    risk_factors.append("Moderate volatility")

                if max_dd > 20:
                    risk_score += 2
                    risk_factors.append("Significant drawdown history")
                elif max_dd > 10:
                    risk_score += 1
                    risk_factors.append("Moderate drawdown risk")

                if sharpe < 0.5:
                    risk_score += 1
                    risk_factors.append("Low risk-adjusted returns")

                risk_level = "High" if risk_score >= 4 else "Medium" if risk_score >= 2 else "Low"
                risk_color = "warning-card" if risk_score >= 4 else "analysis-card" if risk_score >= 2 else "metric-card"

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    <div class="{risk_color}">
                        <h4>⚠️ Risk Assessment</h4>
                        <h3>Risk Level: {risk_level}</h3>
                        <p><strong>Risk Score:</strong> {risk_score}/5</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>📋 Risk Factors</h4>
                        {"<br>".join([f"• {factor}" for factor in risk_factors]) if risk_factors else "• No significant risk factors identified"}
                    </div>
                    """, unsafe_allow_html=True)

                # Volatility chart
                rolling_vol = data['Close'].pct_change().rolling(30).std() * np.sqrt(252) * 100

                fig_vol = go.Figure()
                fig_vol.add_trace(go.Scatter(
                    x=rolling_vol.index,
                    y=rolling_vol,
                    mode='lines',
                    name='30-Day Rolling Volatility',
                    line=dict(color='#f56565', width=2)
                ))

                fig_vol.update_layout(
                    title="Rolling Volatility Analysis",
                    xaxis_title="Date",
                    yaxis_title="Volatility (%)",
                    template="plotly_dark",
                    height=300
                )

                st.plotly_chart(fig_vol, use_container_width=True)

            with tab4:
                st.markdown("""
                <div class="analysis-card">
                    <h3>ℹ️ Fund Information</h3>
                    <p>Detailed fund characteristics ve metadata</p>
                </div>
                """, unsafe_allow_html=True)

                fund_name = funds.get(selected_fund, "Unknown Fund")

                # Fund info display
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>📋 Basic Information</h4>
                        <p><strong>Symbol:</strong> {selected_fund}</p>
                        <p><strong>Name:</strong> {fund_name}</p>
                        <p><strong>Current Price:</strong> ${current_price:.2f}</p>
                        <p><strong>Currency:</strong> USD</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    market_cap = info.get('totalAssets', 0) if info else 0
                    expense_ratio = info.get('annualReportExpenseRatio', 0) if info else 0

                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>💰 Fund Metrics</h4>
                        <p><strong>Assets Under Management:</strong> ${market_cap:,.0f}</p>
                        <p><strong>Expense Ratio:</strong> {expense_ratio:.2%}</p>
                        <p><strong>Holdings Count:</strong> ~{len(get_simulated_holdings(selected_fund))}</p>
                        <p><strong>Category:</strong> ETF</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Additional fund characteristics
                st.markdown(f"""
                <div class="analysis-card">
                    <h4>📊 Fund Characteristics</h4>
                    <p><strong>Investment Objective:</strong> Track performance of underlying index/sector</p>
                    <p><strong>Investment Style:</strong> Passive Index Tracking</p>
                    <p><strong>Benchmark:</strong> Relevant market index</p>
                    <p><strong>Inception Date:</strong> Various (most major ETFs established 2000+)</p>
                    <p><strong>Liquidity:</strong> High (daily trading volume)</p>
                </div>
                """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="margin-top: 3rem; padding: 2rem; background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%); border-radius: 15px; text-align: center;">
        <h3>💼 Fixed Fund Holdings Analysis</h3>
        <p>50+ ETF Coverage • Professional Analysis • Risk Assessment</p>
        <p><strong>Readability sorunları çözüldü - Bloomberg seviyesinde analiz</strong></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()