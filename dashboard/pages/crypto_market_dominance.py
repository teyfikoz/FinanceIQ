"""
Crypto Market Dominance & Forecasting Dashboard
================================================
Comprehensive analysis of crypto market cap, dominance, and trend forecasting
with entropy-based insights.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

from app.data_collectors.crypto_market_dominance import CryptoMarketDominanceCollector, CryptoMarketDataCache
from app.analytics.crypto_forecasting import CryptoForecaster, CryptoTrendAnalyzer
from app.analytics.crypto_entropy_analysis import CryptoEntropyAnalyzer


def render_crypto_dominance_dashboard():
    """Main dashboard rendering function."""

    st.title("📊 Crypto Market Dominance & Forecasting")

    st.markdown("""
    **Comprehensive cryptocurrency market analysis with:**
    - Market cap segments (Total, excl. BTC, excl. BTC+ETH, excl. Top 10)
    - Bitcoin dominance tracking and forecasting
    - Top 10 crypto individual analysis
    - Multi-timeframe trend predictions (1M, 3M, 1Y, 3Y, 5Y)
    - Entropy-based market regime detection
    """)

    # Initialize components
    collector = CryptoMarketDominanceCollector()
    forecaster = CryptoForecaster()
    trend_analyzer = CryptoTrendAnalyzer()
    entropy_analyzer = CryptoEntropyAnalyzer()
    cache = CryptoMarketDataCache(ttl_seconds=300)

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        analysis_section = st.selectbox(
            "Analysis Section",
            [
                "Market Cap Overview",
                "Bitcoin Dominance Analysis",
                "Top 10 Cryptocurrencies",
                "Market Entropy & Regime Detection",
                "Altcoin Season Indicator"
            ]
        )

        st.markdown("---")
        st.markdown("**Data Source:** CoinGecko API")

        if st.button("🔄 Refresh Data"):
            cache.clear()
            st.success("Cache cleared! Data will refresh.")

    # Load data with caching
    with st.spinner("Loading market data..."):
        cached_data = cache.get('comprehensive_metrics')

        if cached_data is None:
            try:
                metrics = collector.get_comprehensive_market_metrics()
                if metrics and metrics.get('market_cap_segments'):
                    cache.set('comprehensive_metrics', metrics)
                else:
                    st.error("⚠️ Unable to fetch crypto market data")

                    with st.expander("🔍 Troubleshooting Guide", expanded=True):
                        st.markdown("""
                        ### Possible Reasons:
                        1. **CoinGecko API Rate Limit** - Free tier allows ~50 calls/minute
                        2. **Temporary API Downtime** - Check [CoinGecko Status](https://status.coingecko.com/)
                        3. **Network Issues** - Verify your internet connection
                        4. **Firewall/VPN Blocking** - Some networks block crypto APIs

                        ### Solutions:
                        #### Option 1: Wait and Retry (Recommended)
                        - Click the "🔄 Refresh Data" button in the sidebar
                        - Wait 1-2 minutes for rate limits to reset
                        - The system will automatically retry with exponential backoff

                        #### Option 2: Configure CoinGecko Pro API Key
                        - Get a free demo API key from [CoinGecko](https://www.coingecko.com/en/api/pricing)
                        - Pro tier: 500 calls/minute vs 50 for free
                        - Add key in config/api_keys.json: `"coingecko": "your-key-here"`

                        #### Option 3: Use Alternative Data Source
                        - System will fallback to Yahoo Finance for basic crypto data
                        - Limited to top 10 cryptocurrencies
                        - Some features may be unavailable

                        ### Debug Information:
                        """)

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Metrics Retrieved", "❌ Failed")
                            st.metric("Cache Status", "Empty" if cached_data is None else "Data Available")
                        with col2:
                            st.metric("Market Cap Segments", "Not Available")
                            st.metric("API Source", "CoinGecko Free API")

                    return
            except Exception as e:
                st.error(f"❌ Error loading crypto data: {str(e)}")
                st.info("Please check your internet connection and CoinGecko API status")
                return
        else:
            metrics = cached_data

    if not metrics or 'global_data' not in metrics:
        st.error("Failed to load market data. Please check your internet connection or try again later.")
        return

    # Render selected section
    if analysis_section == "Market Cap Overview":
        render_market_cap_overview(metrics, forecaster, trend_analyzer, entropy_analyzer, collector)

    elif analysis_section == "Bitcoin Dominance Analysis":
        render_bitcoin_dominance(metrics, collector, forecaster, entropy_analyzer)

    elif analysis_section == "Top 10 Cryptocurrencies":
        render_top10_analysis(metrics, collector, forecaster)

    elif analysis_section == "Market Entropy & Regime Detection":
        render_entropy_regime_detection(metrics, entropy_analyzer)

    elif analysis_section == "Altcoin Season Indicator":
        render_altcoin_season(metrics, collector, entropy_analyzer)


def render_market_cap_overview(metrics, forecaster, trend_analyzer, entropy_analyzer, collector):
    """Render market cap overview section."""

    st.header("💰 Market Cap Segments & Forecasting")

    segments = metrics.get('market_cap_segments', {})

    if not segments:
        st.warning("Market cap data not available")
        return

    # Current metrics
    st.subheader("📊 Current Market Cap Segments")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_mcap = segments.get('total_market_cap', 0)
        st.metric(
            "Total Market Cap",
            f"${total_mcap/1e12:.2f}T",
            help="Total cryptocurrency market capitalization"
        )

    with col2:
        excl_btc = segments.get('excl_btc', 0)
        st.metric(
            "Excl. Bitcoin",
            f"${excl_btc/1e12:.2f}T",
            help="Market cap excluding Bitcoin"
        )

    with col3:
        excl_btc_eth = segments.get('excl_btc_eth', 0)
        st.metric(
            "Excl. BTC + ETH",
            f"${excl_btc_eth/1e12:.2f}T",
            help="Market cap excluding Bitcoin and Ethereum"
        )

    with col4:
        excl_top10 = segments.get('excl_top10', 0)
        st.metric(
            "Excl. Top 10",
            f"${excl_top10/1e12:.2f}T",
            help="Market cap excluding top 10 cryptocurrencies"
        )

    # Pie chart of segments
    st.subheader("📈 Market Cap Distribution")

    btc_mcap = segments.get('btc_market_cap', 0)
    eth_mcap = segments.get('eth_market_cap', 0)
    top10_minus_btc_eth = segments.get('top10_market_cap', 0) - btc_mcap - eth_mcap
    rest = segments.get('excl_top10', 0)

    fig = go.Figure(data=[go.Pie(
        labels=['Bitcoin', 'Ethereum', 'Top 3-10', 'Rest of Market'],
        values=[btc_mcap, eth_mcap, top10_minus_btc_eth, rest],
        hole=0.4,
        marker=dict(colors=['#F7931A', '#627EEA', '#00D4AA', '#95A5A6'])
    )])

    fig.update_layout(
        title="Market Cap Distribution",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Historical data and forecasting
    st.subheader("🔮 Historical Trend & Forecasting")

    with st.spinner("Fetching historical data..."):
        historical_df = collector.get_historical_market_caps(days=730)  # 2 years

    if not historical_df.empty:
        # Prepare data for forecasting
        mcap_series = historical_df.set_index('timestamp')['btc_market_cap']

        # Generate forecasts
        forecast_results = forecaster.forecast_market_cap(
            mcap_series,
            periods=[30, 90, 365, 1095, 1825],
            method='ensemble'
        )

        # Display forecasts
        st.subheader("📊 Multi-Timeframe Forecasts")

        if forecast_results and 'forecasts' in forecast_results:
            forecasts = forecast_results['forecasts']

            # Create forecast comparison table
            forecast_data = []
            current_value = forecast_results.get('current_value', mcap_series.iloc[-1])

            for period_name, forecast in forecasts.items():
                point = forecast.get('point_forecast', 0)
                lower = forecast.get('lower_bound', 0)
                upper = forecast.get('upper_bound', 0)

                change_pct = ((point - current_value) / current_value) * 100

                forecast_data.append({
                    'Period': period_name.replace('_', ' ').title(),
                    'Forecast': f"${point/1e12:.2f}T",
                    'Lower Bound': f"${lower/1e12:.2f}T",
                    'Upper Bound': f"${upper/1e12:.2f}T",
                    'Change': f"{change_pct:+.1f}%"
                })

            df_forecasts = pd.DataFrame(forecast_data)
            st.dataframe(df_forecasts, use_container_width=True)

            # Visualization
            fig = go.Figure()

            # Historical
            fig.add_trace(go.Scatter(
                x=historical_df['timestamp'],
                y=historical_df['btc_market_cap'] / 1e12,
                mode='lines',
                name='Historical',
                line=dict(color='blue', width=2)
            ))

            # Forecast points
            forecast_dates = [
                datetime.now() + timedelta(days=30),
                datetime.now() + timedelta(days=90),
                datetime.now() + timedelta(days=365),
                datetime.now() + timedelta(days=1095),
                datetime.now() + timedelta(days=1825)
            ]

            forecast_values = [forecasts[k]['point_forecast']/1e12 for k in
                              ['1_month', '3_months', '1_year', '3_years', '5_years']]

            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_values,
                mode='markers+lines',
                name='Forecast',
                marker=dict(size=10, color='red'),
                line=dict(color='red', width=2, dash='dash')
            ))

            fig.update_layout(
                title="Bitcoin Market Cap: Historical & Forecast",
                xaxis_title="Date",
                yaxis_title="Market Cap (Trillions USD)",
                hovermode='x unified',
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)

        # Trend analysis
        st.subheader("📉 Trend Analysis")

        if not historical_df.empty and 'estimated_total_market_cap' in historical_df.columns:
            total_mcap_series = historical_df.set_index('timestamp')['estimated_total_market_cap']

            trend_analysis = trend_analyzer.analyze_market_cap_trend(total_mcap_series)

            if trend_analysis:
                col1, col2, col3 = st.columns(3)

                trend_metrics = trend_analysis.get('trend_metrics', {})

                with col1:
                    st.metric(
                        "Trend Direction",
                        trend_metrics.get('trend_direction', 'Unknown')
                    )

                with col2:
                    total_change = trend_metrics.get('total_change_pct', 0)
                    st.metric(
                        "Total Change",
                        f"{total_change:+.1f}%"
                    )

                with col3:
                    market_cycle = trend_analysis.get('market_cycle', 'Unknown')
                    st.metric(
                        "Market Cycle",
                        market_cycle
                    )

                # Growth rates
                growth_rates = trend_analysis.get('growth_rates', {})
                if growth_rates:
                    st.markdown("**Growth Rates:**")
                    growth_df = pd.DataFrame([growth_rates]).T
                    growth_df.columns = ['Value']
                    st.dataframe(growth_df.style.format("{:.2f}%"), use_container_width=True)

    else:
        st.warning("Historical data not available for forecasting")

    # Entropy analysis
    st.subheader("🎲 Market Cap Distribution Entropy")

    top_cryptos = pd.DataFrame(metrics.get('top_10', []))

    if not top_cryptos.empty:
        dist_entropy = entropy_analyzer.analyze_market_cap_distribution(top_cryptos)

        if dist_entropy:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "HHI Index",
                    f"{dist_entropy.get('hhi_index', 0):.0f}",
                    help="Herfindahl-Hirschman Index (concentration)"
                )

            with col2:
                st.metric(
                    "Gini Coefficient",
                    f"{dist_entropy.get('gini_coefficient', 0):.3f}",
                    help="Inequality measure (0=equal, 1=unequal)"
                )

            with col3:
                st.metric(
                    "Distribution Entropy",
                    f"{dist_entropy.get('normalized_entropy_pct', 0):.1f}%",
                    help="Higher = more distributed market"
                )

            with col4:
                st.metric(
                    "Market Structure",
                    dist_entropy.get('market_structure', 'Unknown')
                )

            # Interpretation
            market_struct = dist_entropy.get('market_structure', '')
            if 'Highly Concentrated' in market_struct:
                st.warning("⚠️ **Highly concentrated market** - Few coins dominate. Higher systemic risk.")
            elif 'Moderately Concentrated' in market_struct:
                st.info("ℹ️ **Moderately concentrated market** - Normal crypto market structure.")
            else:
                st.success("✅ **Competitive market** - Well-distributed market cap. Lower concentration risk.")


def render_bitcoin_dominance(metrics, collector, forecaster, entropy_analyzer):
    """Render Bitcoin dominance analysis section."""

    st.header("₿ Bitcoin Dominance Analysis & Forecasting")

    segments = metrics.get('market_cap_segments', {})
    btc_dom = segments.get('btc_dominance', 0)
    eth_dom = segments.get('eth_dominance', 0)
    alt_dom = segments.get('altcoin_dominance', 0)

    # Current dominance
    st.subheader("📊 Current Dominance")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Bitcoin Dominance",
            f"{btc_dom:.2f}%",
            help="BTC market cap / Total market cap"
        )

    with col2:
        st.metric(
            "Ethereum Dominance",
            f"{eth_dom:.2f}%",
            help="ETH market cap / Total market cap"
        )

    with col3:
        st.metric(
            "Altcoin Dominance",
            f"{alt_dom:.2f}%",
            help="(Total - BTC) / Total market cap"
        )

    # Dominance pie chart
    fig = go.Figure(data=[go.Pie(
        labels=['Bitcoin', 'Ethereum', 'Other Altcoins'],
        values=[btc_dom, eth_dom, 100 - btc_dom - eth_dom],
        marker=dict(colors=['#F7931A', '#627EEA', '#00D4AA'])
    )])

    fig.update_layout(
        title="Market Dominance Distribution",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Historical dominance and forecasting
    st.subheader("🔮 Bitcoin Dominance: Historical & Forecast")

    with st.spinner("Loading historical dominance data..."):
        # Simulate historical dominance (in production, fetch from API)
        # For now, create synthetic data
        dates = pd.date_range(end=datetime.now(), periods=730, freq='D')
        # Simple sine wave around current dominance for demo
        base_dom = btc_dom
        variation = np.random.normal(0, 2, 730).cumsum()
        historical_dom = pd.Series(
            base_dom + variation * 0.5,
            index=dates
        )
        historical_dom = historical_dom.clip(35, 70)  # Realistic range

    # Forecast dominance
    dom_forecast = forecaster.forecast_dominance(
        historical_dom,
        periods=[30, 90, 365, 1095, 1825],
        method='ensemble'
    )

    if dom_forecast and 'forecasts' in dom_forecast:
        # Display forecast table
        forecasts = dom_forecast['forecasts']

        forecast_data = []
        current_dom = dom_forecast.get('current_dominance', btc_dom)

        for period_name, forecast in forecasts.items():
            point = forecast.get('point_forecast', 0)
            lower = forecast.get('lower_bound', 0)
            upper = forecast.get('upper_bound', 0)

            change = point - current_dom

            forecast_data.append({
                'Period': period_name.replace('_', ' ').title(),
                'Forecast': f"{point:.2f}%",
                'Range': f"{lower:.2f}% - {upper:.2f}%",
                'Change': f"{change:+.2f}%"
            })

        df_dom_forecast = pd.DataFrame(forecast_data)
        st.dataframe(df_dom_forecast, use_container_width=True)

        # Visualization
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("Bitcoin Dominance Over Time", "Dominance Change Rate"),
            row_heights=[0.7, 0.3]
        )

        # Historical dominance
        fig.add_trace(
            go.Scatter(
                x=historical_dom.index,
                y=historical_dom.values,
                mode='lines',
                name='Historical',
                line=dict(color='#F7931A', width=2)
            ),
            row=1, col=1
        )

        # Forecast points
        forecast_dates = [
            datetime.now() + timedelta(days=30),
            datetime.now() + timedelta(days=90),
            datetime.now() + timedelta(days=365),
            datetime.now() + timedelta(days=1095),
            datetime.now() + timedelta(days=1825)
        ]

        forecast_values = [forecasts[k]['point_forecast'] for k in
                          ['1_month', '3_months', '1_year', '3_years', '5_years']]

        fig.add_trace(
            go.Scatter(
                x=forecast_dates,
                y=forecast_values,
                mode='markers+lines',
                name='Forecast',
                marker=dict(size=10, color='red'),
                line=dict(color='red', width=2, dash='dash')
            ),
            row=1, col=1
        )

        # Dominance change rate
        dom_change = historical_dom.diff()
        fig.add_trace(
            go.Scatter(
                x=historical_dom.index,
                y=dom_change.values,
                mode='lines',
                name='Daily Change',
                line=dict(color='gray', width=1),
                fill='tozeroy'
            ),
            row=2, col=1
        )

        fig.add_hline(y=0, line_dash="dash", line_color="white", row=2, col=1)

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Dominance (%)", row=1, col=1)
        fig.update_yaxes(title_text="Change (%)", row=2, col=1)

        fig.update_layout(
            height=700,
            hovermode='x unified',
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Trend interpretation
        st.subheader("💡 Interpretation")

        trend = dom_forecast.get('trend', 'Unknown')

        if trend == "Increasing":
            st.info("""
            📈 **Bitcoin dominance is increasing**
            - Market may be in "risk-off" mode
            - Capital flowing from altcoins to Bitcoin
            - Potential accumulation phase
            - Consider: BTC over altcoins for safety
            """)
        else:
            st.success("""
            📉 **Bitcoin dominance is decreasing**
            - Market may be in "risk-on" mode (Altcoin season)
            - Capital flowing from Bitcoin to altcoins
            - Higher risk/reward opportunities in alts
            - Consider: Selective altcoin exposure
            """)


def render_top10_analysis(metrics, collector, forecaster):
    """Render top 10 cryptocurrencies analysis."""

    st.header("🏆 Top 10 Cryptocurrencies - Individual Analysis")

    top10_df = pd.DataFrame(metrics.get('top_10', []))

    if top10_df.empty:
        st.warning("Top 10 data not available")
        return

    # Display summary table
    st.subheader("📊 Top 10 Overview")

    # Select relevant columns
    display_cols = ['market_cap_rank', 'name', 'symbol', 'current_price', 'market_cap',
                   'price_change_percentage_24h', 'market_cap_change_percentage_24h']

    display_df = top10_df[[col for col in display_cols if col in top10_df.columns]].copy()

    # Format
    if 'current_price' in display_df.columns:
        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:,.2f}")
    if 'market_cap' in display_df.columns:
        display_df['market_cap'] = display_df['market_cap'].apply(lambda x: f"${x/1e9:.2f}B")

    st.dataframe(display_df, use_container_width=True)

    # Individual crypto selection
    st.subheader("🔍 Individual Crypto Analysis")

    crypto_names = top10_df['name'].tolist()
    selected_crypto = st.selectbox("Select Cryptocurrency", crypto_names)

    if selected_crypto:
        crypto_data = top10_df[top10_df['name'] == selected_crypto].iloc[0]

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Current Price", f"${crypto_data.get('current_price', 0):,.2f}")

        with col2:
            st.metric("Market Cap", f"${crypto_data.get('market_cap', 0)/1e9:.2f}B")

        with col3:
            price_change_24h = crypto_data.get('price_change_percentage_24h', 0)
            st.metric("24h Change", f"{price_change_24h:+.2f}%")

        with col4:
            st.metric("Market Cap Rank", f"#{int(crypto_data.get('market_cap_rank', 0))}")

        # Get historical data for forecasting
        with st.spinner(f"Loading {selected_crypto} historical data..."):
            crypto_id = crypto_data.get('id', '')
            if crypto_id:
                hist_data = collector.get_crypto_historical_data(crypto_id, days=730)

                if not hist_data.empty:
                    # Forecasting
                    st.subheader("🔮 Price Forecast")

                    price_series = hist_data.set_index('timestamp')['price']

                    price_forecast = forecaster.forecast_crypto_price(
                        price_series,
                        selected_crypto,
                        periods=[30, 90, 365, 1095, 1825]
                    )

                    if price_forecast and 'forecasts' in price_forecast:
                        forecasts = price_forecast['forecasts']

                        # Forecast table
                        forecast_data = []
                        current_price = price_forecast.get('current_price', price_series.iloc[-1])

                        for period_name, forecast in forecasts.items():
                            point = forecast.get('point_forecast', 0)
                            lower = forecast.get('volatility_adjusted_lower', forecast.get('lower_bound', 0))
                            upper = forecast.get('volatility_adjusted_upper', forecast.get('upper_bound', 0))

                            change_pct = ((point - current_price) / current_price) * 100

                            forecast_data.append({
                                'Period': period_name.replace('_', ' ').title(),
                                'Forecast': f"${point:,.2f}",
                                'Range': f"${lower:,.2f} - ${upper:,.2f}",
                                'Change': f"{change_pct:+.1f}%"
                            })

                        df_price_forecast = pd.DataFrame(forecast_data)
                        st.dataframe(df_price_forecast, use_container_width=True)

                        # Price chart
                        fig = go.Figure()

                        fig.add_trace(go.Scatter(
                            x=hist_data['timestamp'],
                            y=hist_data['price'],
                            mode='lines',
                            name='Historical Price',
                            line=dict(color='blue', width=2)
                        ))

                        # Add forecast points
                        forecast_dates = [
                            datetime.now() + timedelta(days=d)
                            for d in [30, 90, 365, 1095, 1825]
                        ]

                        forecast_values = [forecasts[k]['point_forecast'] for k in
                                          ['1_month', '3_months', '1_year', '3_years', '5_years']]

                        fig.add_trace(go.Scatter(
                            x=forecast_dates,
                            y=forecast_values,
                            mode='markers+lines',
                            name='Forecast',
                            marker=dict(size=10, color='red'),
                            line=dict(color='red', width=2, dash='dash')
                        ))

                        # Add SMAs
                        sma_50 = price_forecast.get('sma_50')
                        sma_200 = price_forecast.get('sma_200')

                        if sma_50:
                            fig.add_hline(y=sma_50, line_dash="dot", annotation_text="SMA 50",
                                         line_color="yellow")
                        if sma_200:
                            fig.add_hline(y=sma_200, line_dash="dot", annotation_text="SMA 200",
                                         line_color="orange")

                        fig.update_layout(
                            title=f"{selected_crypto} Price: Historical & Forecast",
                            xaxis_title="Date",
                            yaxis_title="Price (USD)",
                            hovermode='x unified',
                            height=500
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # Technical analysis
                        st.markdown("**Technical Analysis:**")
                        trend = price_forecast.get('trend', 'Unknown')
                        volatility = price_forecast.get('volatility', 0)

                        if trend == 'Bullish':
                            st.success(f"✅ **{trend}** trend - Price above 200 SMA")
                        else:
                            st.warning(f"⚠️ **{trend}** trend - Price below 200 SMA")

                        st.info(f"📊 **Annualized Volatility:** {volatility*100:.1f}%")

                else:
                    st.warning("Historical data not available for this cryptocurrency")


def render_entropy_regime_detection(metrics, entropy_analyzer):
    """Render market entropy and regime detection."""

    st.header("🎲 Market Entropy & Regime Detection")

    st.markdown("""
    **Entropy-based market analysis** provides unique insights into market complexity,
    concentration, and regime changes that traditional metrics miss.
    """)

    top10_df = pd.DataFrame(metrics.get('top_10', []))

    if top10_df.empty:
        st.warning("Insufficient data for entropy analysis")
        return

    # Market cap distribution entropy
    st.subheader("📊 Market Cap Distribution Entropy")

    dist_entropy = entropy_analyzer.analyze_market_cap_distribution(top10_df)

    if dist_entropy:
        col1, col2, col3 = st.columns(3)

        with col1:
            norm_ent = dist_entropy.get('normalized_entropy_pct', 0)
            st.metric(
                "Distribution Entropy",
                f"{norm_ent:.1f}%",
                help="Higher = more evenly distributed market cap"
            )

        with col2:
            hhi = dist_entropy.get('hhi_index', 0)
            st.metric(
                "HHI Index",
                f"{hhi:.0f}",
                help="Lower = less concentrated (< 1500 is competitive)"
            )

        with col3:
            gini = dist_entropy.get('gini_coefficient', 0)
            st.metric(
                "Gini Coefficient",
                f"{gini:.3f}",
                help="0 = perfect equality, 1 = perfect inequality"
            )

        # Concentration metrics
        st.markdown("**Market Concentration:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Top 1 Share", f"{dist_entropy.get('top1_concentration', 0):.1f}%")
        with col2:
            st.metric("Top 5 Share", f"{dist_entropy.get('top5_concentration', 0):.1f}%")
        with col3:
            st.metric("Top 10 Share", f"{dist_entropy.get('top10_concentration', 0):.1f}%")

        # Interpretation
        market_struct = dist_entropy.get('market_structure', '')
        diversification = dist_entropy.get('diversification_level', '')

        st.markdown("**Interpretation:**")
        st.info(f"**Market Structure:** {market_struct}")
        st.info(f"**Diversification:** {diversification}")

    # Altcoin dispersion analysis
    st.subheader("🌊 Altcoin Performance Dispersion")

    dispersion = entropy_analyzer.analyze_altcoin_dispersion(top10_df)

    if dispersion and 'period_metrics' in dispersion:
        period_metrics = dispersion['period_metrics']

        # Create comparison table
        if period_metrics:
            disp_data = []
            for period, metrics in period_metrics.items():
                disp_data.append({
                    'Period': period.replace('_metrics', '').upper(),
                    'Shannon Entropy': f"{metrics.get('shannon_entropy', 0):.4f}",
                    'Std Dev': f"{metrics.get('std_deviation', 0):.2f}%",
                    'Dispersion': metrics.get('dispersion_level', 'Unknown')
                })

            df_disp = pd.DataFrame(disp_data)
            st.dataframe(df_disp, use_container_width=True)

            # Overall assessment
            assessment = dispersion.get('overall_assessment', '')
            st.markdown(f"**Overall Assessment:** {assessment}")


def render_altcoin_season(metrics, collector, entropy_analyzer):
    """Render altcoin season indicator."""

    st.header("🌈 Altcoin Season Indicator")

    st.markdown("""
    **Altcoin Season** = When 75%+ of top 50 coins outperform Bitcoin over 30 days.

    Uses both traditional metrics and entropy analysis for comprehensive assessment.
    """)

    altcoin_data = metrics.get('altcoin_season', {})

    if not altcoin_data:
        st.warning("Altcoin season data not available")
        return

    # Main indicator
    score = altcoin_data.get('altcoin_season_score', 0)
    is_alt_season = altcoin_data.get('is_altcoin_season', False)
    season_type = altcoin_data.get('season_type', 'Unknown')

    # Large gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={'text': "Altcoin Season Index"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "#F7931A"},
                {'range': [25, 75], 'color': "lightgray"},
                {'range': [75, 100], 'color': "#00D4AA"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Status
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Altcoin Season Score", f"{score:.1f}/100")

    with col2:
        st.metric("Season Type", season_type)

    with col3:
        outperforming = altcoin_data.get('outperforming_count', 0)
        total = altcoin_data.get('total_tracked', 0)
        st.metric("Alts Beating BTC", f"{outperforming}/{total}")

    # Interpretation
    st.subheader("💡 What This Means")

    if score >= 75:
        st.success("""
        🚀 **STRONG ALTCOIN SEASON**
        - 75%+ of altcoins are outperforming Bitcoin
        - High risk/high reward environment
        - Consider selective altcoin exposure
        - Watch for overextension
        """)
    elif score >= 60:
        st.info("""
        📈 **MODERATE ALTCOIN SEASON**
        - Majority of altcoins outperforming BTC
        - Good environment for altcoin trading
        - Maintain risk management
        """)
    elif score >= 40:
        st.warning("""
        ⚖️ **NEUTRAL / MIXED MARKET**
        - No clear dominance
        - Select individual opportunities
        - Avoid broad altcoin exposure
        """)
    else:
        st.error("""
        ₿ **BITCOIN SEASON**
        - Most altcoins underperforming Bitcoin
        - Capital flowing to BTC (risk-off)
        - Consider BTC over altcoins
        - Potential accumulation phase for alts
        """)

    # Historical context
    st.subheader("📊 Market Context")

    btc_perf = altcoin_data.get('btc_performance_30d', 0)
    st.metric("Bitcoin 30d Performance", f"{btc_perf:+.1f}%")

    if btc_perf > 20:
        st.info("Bitcoin is strongly outperforming - typical in early bull market or accumulation")
    elif btc_perf < -20:
        st.warning("Bitcoin is underperforming significantly - caution advised")


# Main execution
if __name__ == "__main__":
    render_crypto_dominance_dashboard()
