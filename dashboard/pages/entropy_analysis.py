"""
Entropy Analysis Dashboard Page
================================
Advanced entropy metrics visualization for market intelligence.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta

from app.analytics.entropy_metrics import EntropyCalculator, quick_entropy_analysis, compare_assets_entropy


def render_entropy_dashboard():
    """Render the main entropy analysis dashboard."""

    st.title("🎲 Entropy Analysis - Market Intelligence")
    st.markdown("""
    **Advanced complexity and predictability metrics for financial markets**

    Entropy measures provide unique insights into:
    - Market predictability vs chaos
    - Regime transitions (bull/bear)
    - Whale influence detection
    - Portfolio diversification quality
    """)

    # Initialize calculator
    calc = EntropyCalculator()

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        analysis_type = st.selectbox(
            "Analysis Type",
            ["Single Asset Analysis", "Multi-Asset Comparison", "Whale Influence", "Portfolio Entropy"]
        )

        if analysis_type in ["Single Asset Analysis", "Multi-Asset Comparison"]:
            # Asset selection
            if analysis_type == "Single Asset Analysis":
                symbol = st.text_input("Ticker Symbol", "BTC-USD")
                symbols = [symbol]
            else:
                default_symbols = "BTC-USD, ETH-USD, SPY, QQQ"
                symbols_input = st.text_area("Ticker Symbols (comma-separated)", default_symbols)
                symbols = [s.strip() for s in symbols_input.split(",")]

            # Time period
            period = st.selectbox(
                "Time Period",
                ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                index=3
            )

            # Entropy metrics to display
            st.subheader("Entropy Metrics")
            show_shannon = st.checkbox("Shannon Entropy", value=True)
            show_sample = st.checkbox("Sample Entropy", value=True)
            show_apen = st.checkbox("Approximate Entropy", value=True)
            show_perm = st.checkbox("Permutation Entropy", value=True)
            show_spectral = st.checkbox("Spectral Entropy", value=False)
            show_multiscale = st.checkbox("Multiscale Entropy", value=False)

    # Main content based on analysis type
    if analysis_type == "Single Asset Analysis":
        render_single_asset_analysis(
            symbols[0], period, calc,
            show_shannon, show_sample, show_apen, show_perm, show_spectral, show_multiscale
        )

    elif analysis_type == "Multi-Asset Comparison":
        render_multi_asset_comparison(symbols, period, calc)

    elif analysis_type == "Whale Influence":
        render_whale_influence_analysis(calc)

    elif analysis_type == "Portfolio Entropy":
        render_portfolio_entropy_analysis(calc)


def render_single_asset_analysis(symbol, period, calc, show_shannon, show_sample,
                                 show_apen, show_perm, show_spectral, show_multiscale):
    """Render single asset entropy analysis."""

    st.header(f"📊 Entropy Analysis: {symbol}")

    # Download data
    with st.spinner(f"Downloading {symbol} data..."):
        try:
            data = yf.download(symbol, period=period, progress=False)
            if data.empty:
                st.error(f"No data found for {symbol}")
                return

            prices = data['Close']
            returns = prices.pct_change().dropna()

        except Exception as e:
            st.error(f"Error downloading data: {e}")
            return

    # Calculate comprehensive report
    with st.spinner("Calculating entropy metrics..."):
        report = calc.comprehensive_entropy_report(prices, asset_name=symbol)

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Complexity Score",
            f"{report.get('complexity_score', 0):.1f}/100",
            help="Higher = More chaotic/unpredictable"
        )

    with col2:
        st.metric(
            "Predictability Score",
            f"{report.get('predictability_score', 0):.1f}/100",
            help="Higher = More predictable/trending"
        )

    with col3:
        market_regime = report.get('market_regime', 'Unknown')
        st.metric(
            "Market Regime",
            market_regime,
            help="Current market state based on entropy"
        )

    with col4:
        risk_level = report.get('risk_level', 'Unknown')
        st.metric(
            "Entropy Risk",
            risk_level,
            help="Risk assessment from entropy perspective"
        )

    # Detailed entropy metrics
    st.subheader("📈 Entropy Metrics")

    metrics_data = []
    if show_shannon:
        metrics_data.append({
            "Metric": "Shannon Entropy",
            "Value": f"{report.get('shannon_entropy', 0):.4f}",
            "Interpretation": "Information content / randomness"
        })

    if show_sample:
        metrics_data.append({
            "Metric": "Sample Entropy",
            "Value": f"{report.get('sample_entropy', 0):.4f}",
            "Interpretation": "Time series complexity (lower = more regular)"
        })

    if show_apen:
        metrics_data.append({
            "Metric": "Approximate Entropy",
            "Value": f"{report.get('approximate_entropy', 0):.4f}",
            "Interpretation": "Regularity measure (regime detection)"
        })

    if show_perm:
        metrics_data.append({
            "Metric": "Permutation Entropy",
            "Value": f"{report.get('permutation_entropy', 0):.4f}",
            "Interpretation": "Ordinal pattern complexity"
        })

    if show_spectral:
        metrics_data.append({
            "Metric": "Spectral Entropy",
            "Value": f"{report.get('spectral_entropy', 0):.4f}",
            "Interpretation": "Frequency domain complexity"
        })

    if metrics_data:
        st.dataframe(pd.DataFrame(metrics_data), use_container_width=True)

    # Multiscale entropy visualization
    if show_multiscale:
        st.subheader("🔍 Multiscale Entropy Analysis")

        mse = report.get('multiscale_entropy', {})
        if mse:
            scales = list(mse.keys())
            values = list(mse.values())

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=scales,
                y=values,
                mode='lines+markers',
                name='Sample Entropy',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))

            fig.update_layout(
                title="Multiscale Entropy - Complexity Across Time Scales",
                xaxis_title="Time Scale",
                yaxis_title="Sample Entropy",
                hovermode='x unified',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            st.info("""
            **Interpretation:**
            - Increasing trend → Long-range correlations
            - Decreasing trend → White noise characteristics
            - Flat line → Similar complexity at all scales
            """)

    # Rolling entropy visualization
    st.subheader("📉 Rolling Entropy Over Time")

    window = st.slider("Rolling Window (days)", 20, 200, 60)

    with st.spinner("Calculating rolling entropy..."):
        # Calculate rolling Shannon entropy
        rolling_entropy = []
        dates = []

        for i in range(window, len(returns)):
            window_returns = returns.iloc[i-window:i]
            entropy = calc.shannon_entropy(window_returns)
            rolling_entropy.append(entropy)
            dates.append(returns.index[i])

    # Create figure with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Price", "Rolling Shannon Entropy"),
        row_heights=[0.6, 0.4]
    )

    # Price chart
    fig.add_trace(
        go.Scatter(x=prices.index, y=prices, name="Price", line=dict(color='#17becf')),
        row=1, col=1
    )

    # Entropy chart
    fig.add_trace(
        go.Scatter(x=dates, y=rolling_entropy, name="Entropy",
                  line=dict(color='#ff7f0e', width=2),
                  fill='tozeroy', fillcolor='rgba(255,127,14,0.2)'),
        row=2, col=1
    )

    # Add entropy regime zones
    fig.add_hrect(y0=0, y1=0.3, fillcolor="green", opacity=0.1,
                 layer="below", line_width=0, row=2, col=1,
                 annotation_text="Trending", annotation_position="left")
    fig.add_hrect(y0=0.3, y1=0.7, fillcolor="yellow", opacity=0.1,
                 layer="below", line_width=0, row=2, col=1,
                 annotation_text="Mixed", annotation_position="left")
    fig.add_hrect(y0=0.7, y1=1.0, fillcolor="red", opacity=0.1,
                 layer="below", line_width=0, row=2, col=1,
                 annotation_text="Chaotic", annotation_position="left")

    fig.update_layout(
        height=700,
        hovermode='x unified',
        showlegend=True
    )

    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Entropy", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Trading insights
    st.subheader("💡 Trading Insights")

    current_entropy = rolling_entropy[-1] if rolling_entropy else report.get('shannon_entropy', 0.5)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Current Market State:**")
        if current_entropy < 0.3:
            st.success("🟢 **Low Entropy** - Strong trending environment. Trend-following strategies favored.")
        elif current_entropy < 0.5:
            st.info("🔵 **Moderate Entropy** - Trending with some noise. Use filters for signals.")
        elif current_entropy < 0.7:
            st.warning("🟡 **Medium-High Entropy** - Mixed conditions. Consider range-bound strategies.")
        else:
            st.error("🔴 **High Entropy** - Chaotic/unpredictable. Reduce position sizes, increase stops.")

    with col2:
        st.markdown("**Recommended Actions:**")
        if current_entropy < 0.4:
            st.markdown("""
            - ✅ Trend following strategies
            - ✅ Position trading
            - ✅ Larger position sizes OK
            """)
        elif current_entropy < 0.7:
            st.markdown("""
            - ⚠️ Use tighter stops
            - ⚠️ Shorter holding periods
            - ⚠️ Combine with other indicators
            """)
        else:
            st.markdown("""
            - ❌ Avoid new positions
            - ❌ Reduce exposure
            - ❌ Wait for clarity
            """)


def render_multi_asset_comparison(symbols, period, calc):
    """Render multi-asset entropy comparison."""

    st.header("🔄 Multi-Asset Entropy Comparison")

    # Download all data
    assets_data = {}

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, symbol in enumerate(symbols):
        status_text.text(f"Downloading {symbol}...")
        try:
            data = yf.download(symbol, period=period, progress=False)
            if not data.empty:
                assets_data[symbol] = data['Close']
        except Exception as e:
            st.warning(f"Could not download {symbol}: {e}")

        progress_bar.progress((i + 1) / len(symbols))

    status_text.empty()
    progress_bar.empty()

    if not assets_data:
        st.error("No data could be downloaded for any symbol")
        return

    # Calculate entropy for all assets
    results = []

    for symbol, prices in assets_data.items():
        with st.spinner(f"Analyzing {symbol}..."):
            returns = prices.pct_change().dropna()

            shannon = calc.shannon_entropy(returns)
            sample = calc.sample_entropy(returns)
            apen = calc.approximate_entropy(returns)
            perm = calc.permutation_entropy(returns)

            results.append({
                "Asset": symbol,
                "Shannon": shannon,
                "Sample": sample,
                "Approximate": apen,
                "Permutation": perm,
                "Complexity": shannon * 100,
                "Predictability": (1 - shannon) * 100
            })

    df_results = pd.DataFrame(results)

    # Display comparison table
    st.subheader("📊 Entropy Comparison Table")
    st.dataframe(df_results.style.background_gradient(cmap='RdYlGn_r', subset=['Complexity']),
                 use_container_width=True)

    # Visualizations
    st.subheader("📈 Entropy Metrics Comparison")

    # Bar chart comparison
    fig = go.Figure()

    metrics = ['Shannon', 'Sample', 'Approximate', 'Permutation']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    for i, metric in enumerate(metrics):
        fig.add_trace(go.Bar(
            name=metric,
            x=df_results['Asset'],
            y=df_results[metric],
            marker_color=colors[i]
        ))

    fig.update_layout(
        barmode='group',
        title="Entropy Metrics by Asset",
        xaxis_title="Asset",
        yaxis_title="Entropy Value",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Complexity vs Predictability scatter
    st.subheader("🎯 Complexity vs Predictability")

    fig = px.scatter(
        df_results,
        x='Complexity',
        y='Predictability',
        text='Asset',
        size='Sample',
        color='Shannon',
        color_continuous_scale='RdYlGn_r',
        title="Asset Positioning: Complexity vs Predictability"
    )

    fig.update_traces(textposition='top center', marker=dict(size=15))
    fig.update_layout(height=500)

    st.plotly_chart(fig, use_container_width=True)

    # Ranking
    st.subheader("🏆 Rankings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Most Predictable Assets**")
        most_predictable = df_results.nlargest(5, 'Predictability')[['Asset', 'Predictability']]
        st.dataframe(most_predictable, use_container_width=True)

    with col2:
        st.markdown("**Most Complex Assets**")
        most_complex = df_results.nlargest(5, 'Complexity')[['Asset', 'Complexity']]
        st.dataframe(most_complex, use_container_width=True)


def render_whale_influence_analysis(calc):
    """Render whale influence entropy analysis."""

    st.header("🐋 Whale Influence Analysis (Transfer Entropy)")

    st.info("""
    **Transfer Entropy** measures information flow from whale activity to market price.

    High TE → Whales are leading the market
    Low TE → Market is moving independently
    """)

    # Symbol selection
    symbol = st.text_input("Market Symbol", "BTC-USD")
    whale_metric = st.selectbox(
        "Whale Activity Metric",
        ["Volume", "Large Transactions", "Exchange Flows (Simulated)"]
    )

    period = st.selectbox("Time Period", ["1mo", "3mo", "6mo", "1y"], index=2)

    if st.button("🔍 Analyze Whale Influence"):
        with st.spinner("Downloading and analyzing data..."):
            try:
                # Download price data
                data = yf.download(symbol, period=period, progress=False)
                prices = data['Close']

                # Simulate whale activity (in real app, use actual whale data)
                if whale_metric == "Volume":
                    whale_activity = data['Volume']
                else:
                    # Simulate whale transactions (for demo)
                    returns = prices.pct_change().abs()
                    volume = data['Volume']
                    whale_activity = returns * volume  # Proxy for large moves

                # Calculate transfer entropy
                te_result = calc.whale_influence_entropy(whale_activity, prices, window=20)

                # Display results
                st.subheader("📊 Whale Influence Metrics")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Whale → Market TE",
                        f"{te_result.get('whale_to_market_te', 0):.4f}",
                        help="Information flow from whales to market"
                    )

                with col2:
                    st.metric(
                        "Market → Whale TE",
                        f"{te_result.get('market_to_whale_te', 0):.4f}",
                        help="Information flow from market to whales"
                    )

                with col3:
                    net_influence = te_result.get('net_whale_influence', 0)
                    st.metric(
                        "Net Influence",
                        f"{net_influence:.4f}",
                        delta=te_result.get('interpretation', ''),
                        help="Positive = Whales leading"
                    )

                # Interpretation
                st.subheader("💡 Interpretation")

                interpretation = te_result.get('interpretation', 'Balanced')

                if interpretation == "Whales Leading":
                    st.success("🐋 **Whales are leading the market!** Their activity provides information about future price movements.")
                elif interpretation == "Market Leading":
                    st.info("📊 **Market is leading whales.** Whales are following market trends.")
                else:
                    st.warning("⚖️ **Balanced influence.** No clear leader between whales and market.")

            except Exception as e:
                st.error(f"Error in analysis: {e}")


def render_portfolio_entropy_analysis(calc):
    """Render portfolio entropy analysis."""

    st.header("💼 Portfolio Entropy - Diversification Analysis")

    st.info("""
    **Portfolio Entropy** measures diversification quality.

    - Maximum entropy = equally weighted portfolio (maximum diversification)
    - Minimum entropy = concentrated portfolio (high risk)
    """)

    # Portfolio input
    st.subheader("Enter Portfolio Weights")

    num_assets = st.slider("Number of Assets", 2, 20, 5)

    weights = {}
    cols = st.columns(3)

    for i in range(num_assets):
        with cols[i % 3]:
            asset_name = st.text_input(f"Asset {i+1}", f"Asset_{i+1}", key=f"asset_{i}")
            weight = st.number_input(f"Weight {i+1} (%)", 0.0, 100.0, 100.0/num_assets, key=f"weight_{i}")
            weights[asset_name] = weight / 100

    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v/total_weight for k, v in weights.items()}

    # Calculate portfolio entropy
    portfolio_entropy = calc.portfolio_entropy(weights)
    max_entropy = np.log(len(weights))
    normalized_entropy = portfolio_entropy / max_entropy if max_entropy > 0 else 0

    # Display metrics
    st.subheader("📊 Portfolio Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Portfolio Entropy", f"{portfolio_entropy:.4f}")

    with col2:
        st.metric("Diversification Score", f"{normalized_entropy*100:.1f}%")

    with col3:
        max_concentration = max(weights.values())
        st.metric("Max Concentration", f"{max_concentration*100:.1f}%")

    # Visualization
    fig = go.Figure()

    # Pie chart
    fig.add_trace(go.Pie(
        labels=list(weights.keys()),
        values=list(weights.values()),
        hole=0.4
    ))

    fig.update_layout(
        title="Portfolio Weight Distribution",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Recommendations
    st.subheader("💡 Recommendations")

    if normalized_entropy > 0.9:
        st.success("✅ **Excellent diversification!** Your portfolio is well-balanced.")
    elif normalized_entropy > 0.7:
        st.info("ℹ️ **Good diversification.** Consider minor rebalancing.")
    elif normalized_entropy > 0.5:
        st.warning("⚠️ **Moderate concentration.** Consider adding more assets or rebalancing.")
    else:
        st.error("❌ **High concentration risk!** Your portfolio lacks diversification.")

    # Optimal portfolio comparison
    st.subheader("🎯 Comparison with Optimal Portfolio")

    equal_weights = {k: 1.0/len(weights) for k in weights.keys()}
    optimal_entropy = calc.portfolio_entropy(equal_weights)

    comparison_df = pd.DataFrame({
        "Portfolio": ["Current", "Equal-Weighted (Optimal)"],
        "Entropy": [portfolio_entropy, optimal_entropy],
        "Diversification": [normalized_entropy * 100, 100.0]
    })

    st.dataframe(comparison_df, use_container_width=True)


# Main execution
if __name__ == "__main__":
    render_entropy_dashboard()
