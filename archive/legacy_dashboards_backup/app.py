import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import time

# Configure page
st.set_page_config(
    page_title="Global Liquidity & Market Correlation Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .alert-high {
        background-color: #ffe6e6;
        border-left: 4px solid #ff4444;
    }
    .alert-medium {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def get_api_data(endpoint: str):
    """Fetch data from FastAPI backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: Unable to connect to API")
        return None

def create_sample_data():
    """Create sample data for demonstration when API is not available."""
    return {
        "market_data": {
            # US Large Cap
            "AAPL": {"price": 185.64, "change_24h": 1.2},
            "MSFT": {"price": 378.85, "change_24h": 0.8},
            "NVDA": {"price": 875.28, "change_24h": 3.2},
            "GOOGL": {"price": 142.56, "change_24h": -0.4},
            "AMZN": {"price": 153.40, "change_24h": 1.1},
            "TSLA": {"price": 248.42, "change_24h": 2.8},
            "META": {"price": 384.30, "change_24h": 0.9},
            "BRK-B": {"price": 442.18, "change_24h": 0.3},
            # ETFs
            "SPY": {"price": 423.45, "change_24h": -0.5},
            "QQQ": {"price": 386.74, "change_24h": 0.7},
            "VTI": {"price": 241.85, "change_24h": -0.2},
            "IWM": {"price": 198.56, "change_24h": -1.1},
            "EFA": {"price": 74.23, "change_24h": 0.4},
            "EEM": {"price": 40.18, "change_24h": 1.3},
            "VWO": {"price": 41.45, "change_24h": 1.2},
            "GLD": {"price": 185.23, "change_24h": 0.8},
            "SLV": {"price": 21.34, "change_24h": 1.5},
            "DBC": {"price": 18.92, "change_24h": 2.1},
            # International Stocks
            "ASML": {"price": 675.32, "change_24h": 1.8},
            "TSMC": {"price": 97.45, "change_24h": 2.1},
            "NVO": {"price": 112.78, "change_24h": 0.6},
            "SAP": {"price": 156.89, "change_24h": -0.3},
            "TM": {"price": 198.45, "change_24h": 0.9},
            # Crypto
            "BTC": {"price": 45234.56, "change_24h": 2.3},
            "ETH": {"price": 2789.12, "change_24h": 1.8},
            "MSTR": {"price": 1456.78, "change_24h": 5.2},
            "COIN": {"price": 245.67, "change_24h": 3.8},
            # Turkish Stocks (BIST-30)
            "AKBNK": {"price": 25.48, "change_24h": 1.4},
            "GARAN": {"price": 31.72, "change_24h": 0.8},
            "ISCTR": {"price": 7.89, "change_24h": -0.5},
            "THYAO": {"price": 164.50, "change_24h": 2.1},
            "KCHOL": {"price": 22.15, "change_24h": 1.2},
            "SAHOL": {"price": 12.34, "change_24h": 0.6},
            "ASELS": {"price": 89.75, "change_24h": 3.2},
            "SISE": {"price": 28.90, "change_24h": -1.1},
            "EREGL": {"price": 45.60, "change_24h": 1.8},
            "BIMAS": {"price": 105.20, "change_24h": 0.9},
        },
        "correlation_matrix": {
            "SPY": {"SPY": 1.0, "QQQ": 0.92, "VTI": 0.98, "EFA": 0.75, "EEM": 0.68, "GLD": -0.25, "BTC": 0.72},
            "QQQ": {"SPY": 0.92, "QQQ": 1.0, "VTI": 0.89, "EFA": 0.71, "EEM": 0.63, "GLD": -0.18, "BTC": 0.78},
            "VTI": {"SPY": 0.98, "QQQ": 0.89, "VTI": 1.0, "EFA": 0.76, "EEM": 0.69, "GLD": -0.23, "BTC": 0.71},
            "EFA": {"SPY": 0.75, "QQQ": 0.71, "VTI": 0.76, "EFA": 1.0, "EEM": 0.82, "GLD": -0.15, "BTC": 0.65},
            "EEM": {"SPY": 0.68, "QQQ": 0.63, "VTI": 0.69, "EFA": 0.82, "EEM": 1.0, "GLD": -0.08, "BTC": 0.58},
            "GLD": {"SPY": -0.25, "QQQ": -0.18, "VTI": -0.23, "EFA": -0.15, "EEM": -0.08, "GLD": 1.0, "BTC": 0.15},
            "BTC": {"SPY": 0.72, "QQQ": 0.78, "VTI": 0.71, "EFA": 0.65, "EEM": 0.58, "GLD": 0.15, "BTC": 1.0},
        },
        "liquidity_metrics": {
            "global_liquidity_index": 0.85,
            "fed_balance_sheet": 8.5e12,
            "ecb_balance_sheet": 7.2e12,
            "change_7d": 1.2,
        },
        "alerts": [
            {
                "type": "correlation_breakdown",
                "message": "BTC-SPY correlation dropped below 0.5",
                "severity": "medium",
                "created_at": "2024-01-15T10:30:00Z",
            },
            {
                "type": "volatility_spike",
                "message": "VIX increased above 25",
                "severity": "high",
                "created_at": "2024-01-15T09:15:00Z",
            },
        ]
    }

def main():
    """Main dashboard application."""

    # Header
    st.markdown('<h1 class="main-header">🌍 Global Liquidity & Market Correlation Dashboard</h1>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-title">📊 Dashboard Controls</div>', unsafe_allow_html=True)

        # Refresh button
        if st.button("🔄 Refresh Data", type="primary"):
            st.rerun()

        # Time range selector
        time_range = st.selectbox(
            "📅 Time Range",
            ["1D", "7D", "30D", "90D", "1Y"],
            index=2
        )

        # Asset selector
        st.markdown("### 🎯 Assets to Track")
        track_crypto = st.checkbox("Cryptocurrencies", value=True)
        track_stocks = st.checkbox("Stock Indices", value=True)
        track_commodities = st.checkbox("Commodities", value=True)
        track_bonds = st.checkbox("Bonds", value=True)

        # Alert settings
        st.markdown("### 🚨 Alert Thresholds")
        corr_threshold = st.slider("Correlation Alert", 0.1, 0.5, 0.2, 0.05)
        vol_threshold = st.slider("Volatility Alert", 15, 40, 25, 1)

        # Info
        st.markdown("---")
        st.markdown("### ℹ️ System Status")
        st.success("✅ API Connected")
        st.info(f"🕐 Last Update: {datetime.now().strftime('%H:%M:%S')}")

    # Try to get real data, fallback to sample data
    market_data = get_api_data("market-data")
    correlation_data = get_api_data("correlations")
    liquidity_data = get_api_data("liquidity")
    alerts_data = get_api_data("alerts")

    # Use sample data if API is not available
    if not market_data:
        sample_data = create_sample_data()
        market_data = {"data": sample_data["market_data"]}
        correlation_data = sample_data["correlation_matrix"]
        liquidity_data = {"metrics": sample_data["liquidity_metrics"]}
        alerts_data = {"alerts": sample_data["alerts"]}

        st.warning("⚠️ Using sample data - API not available")

    # Key Metrics Row
    st.markdown("## 📈 Key Market Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        btc_price = market_data.get("data", {}).get("BTC", {}).get("price", 45234)
        btc_change = market_data.get("data", {}).get("BTC", {}).get("change_24h", 2.3)
        st.metric(
            "Bitcoin",
            f"${btc_price:,.0f}",
            f"{btc_change:+.1f}%",
            delta_color="normal"
        )

    with col2:
        spy_price = market_data.get("data", {}).get("SPY", {}).get("price", 423)
        spy_change = market_data.get("data", {}).get("SPY", {}).get("change_24h", -0.5)
        st.metric(
            "S&P 500",
            f"${spy_price:.0f}",
            f"{spy_change:+.1f}%",
            delta_color="normal"
        )

    with col3:
        gli = liquidity_data.get("metrics", {}).get("global_liquidity_index", 0.85)
        gli_change = liquidity_data.get("metrics", {}).get("change_7d", 1.2)
        st.metric(
            "Global Liquidity Index",
            f"{gli:.2f}",
            f"{gli_change:+.1f}%",
            delta_color="normal"
        )

    with col4:
        vix_value = 18.5  # Placeholder
        st.metric(
            "VIX",
            f"{vix_value:.1f}",
            "-3.2%",
            delta_color="inverse"
        )

    with col5:
        dxy_value = 103.2  # Placeholder
        st.metric(
            "DXY",
            f"{dxy_value:.1f}",
            "+0.8%",
            delta_color="normal"
        )

    # Alerts Section
    if alerts_data and alerts_data.get("alerts"):
        st.markdown("## 🚨 Active Alerts")

        for alert in alerts_data["alerts"]:
            severity = alert.get("severity", "medium")
            alert_class = f"alert-{severity}" if severity in ["high", "medium"] else "alert-medium"

            st.markdown(f"""
            <div class="alert-box {alert_class}">
                <strong>{alert.get('type', 'Alert').replace('_', ' ').title()}</strong><br>
                {alert.get('message', 'No message')}
                <br><small>📅 {alert.get('created_at', 'Unknown time')}</small>
            </div>
            """, unsafe_allow_html=True)

    # Main Charts Row
    st.markdown("## 📊 Market Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔗 Correlation Heatmap")

        # Create correlation heatmap
        if isinstance(correlation_data, dict) and correlation_data:
            # Convert correlation data to DataFrame
            if "correlation_matrix" in correlation_data:
                corr_data = correlation_data["correlation_matrix"]
            else:
                corr_data = correlation_data

            # Create DataFrame from correlation data
            assets = list(corr_data.keys())
            corr_matrix = []
            for asset1 in assets:
                row = []
                for asset2 in assets:
                    corr_value = corr_data.get(asset1, {}).get(asset2, 0)
                    row.append(corr_value)
                corr_matrix.append(row)

            corr_df = pd.DataFrame(corr_matrix, index=assets, columns=assets)

            fig_corr = px.imshow(
                corr_df,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu",
                range_color=[-1, 1]
            )
            fig_corr.update_layout(
                title="Asset Correlation Matrix",
                height=400
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Correlation data not available")

    with col2:
        st.markdown("### 💧 Global Liquidity Trend")

        # Create sample liquidity trend data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        liquidity_values = np.random.normal(0.85, 0.05, 30)
        liquidity_values = np.cumsum(np.random.normal(0, 0.01, 30)) + 0.85

        fig_liquidity = go.Figure()
        fig_liquidity.add_trace(go.Scatter(
            x=dates,
            y=liquidity_values,
            mode='lines+markers',
            name='Global Liquidity Index',
            line=dict(color='#1f77b4', width=3)
        ))

        fig_liquidity.update_layout(
            title="Global Liquidity Index (30 Days)",
            xaxis_title="Date",
            yaxis_title="GLI Value",
            height=400
        )
        st.plotly_chart(fig_liquidity, use_container_width=True)

    # Secondary Charts Row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Price Performance")

        # Create sample price performance chart
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        btc_prices = np.cumsum(np.random.normal(0.01, 0.05, 30)) + 100
        spy_prices = np.cumsum(np.random.normal(0.005, 0.02, 30)) + 100

        fig_performance = go.Figure()
        fig_performance.add_trace(go.Scatter(
            x=dates,
            y=btc_prices,
            mode='lines',
            name='Bitcoin',
            line=dict(color='#ff7f0e')
        ))
        fig_performance.add_trace(go.Scatter(
            x=dates,
            y=spy_prices,
            mode='lines',
            name='S&P 500',
            line=dict(color='#2ca02c')
        ))

        fig_performance.update_layout(
            title="Normalized Price Performance (30 Days)",
            xaxis_title="Date",
            yaxis_title="Normalized Price",
            height=400
        )
        st.plotly_chart(fig_performance, use_container_width=True)

    with col2:
        st.markdown("### 🎯 Risk Metrics")

        # Create risk metrics chart
        assets = ['BTC', 'ETH', 'SPY', 'GLD']
        volatility = [65, 70, 18, 15]
        var_95 = [8.5, 9.2, 2.1, 1.8]

        fig_risk = go.Figure()
        fig_risk.add_trace(go.Bar(
            x=assets,
            y=volatility,
            name='Volatility (%)',
            marker_color='#ff7f0e'
        ))

        fig_risk.update_layout(
            title="Asset Volatility Comparison",
            xaxis_title="Asset",
            yaxis_title="Volatility (%)",
            height=400
        )
        st.plotly_chart(fig_risk, use_container_width=True)

    # Data Tables Section
    st.markdown("## 📊 Detailed Data")

    tab1, tab2, tab3 = st.tabs(["📈 Market Data", "🔗 Correlations", "💧 Liquidity Metrics"])

    with tab1:
        if market_data and "data" in market_data:
            # Convert market data to DataFrame
            market_df = pd.DataFrame.from_dict(market_data["data"], orient='index')
            market_df.index.name = 'Asset'
            market_df = market_df.reset_index()

            st.dataframe(
                market_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Market data not available")

    with tab2:
        if isinstance(correlation_data, dict):
            corr_display = corr_df if 'corr_df' in locals() else pd.DataFrame(correlation_data)
            st.dataframe(
                corr_display.round(3),
                use_container_width=True
            )
        else:
            st.info("Correlation data not available")

    with tab3:
        if liquidity_data and "metrics" in liquidity_data:
            liquidity_df = pd.DataFrame.from_dict(
                liquidity_data["metrics"],
                orient='index',
                columns=['Value']
            )
            liquidity_df.index.name = 'Metric'
            liquidity_df = liquidity_df.reset_index()

            st.dataframe(
                liquidity_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Liquidity data not available")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        🌍 Global Liquidity & Market Correlation Dashboard |
        📊 Data updated every hour |
        🤖 Powered by FastAPI & Streamlit
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()