"""Stock comparison utility for side-by-side analysis"""
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd


def create_stock_comparison():
    """Create stock comparison interface"""
    st.header("⚖️ Stock Comparison")

    col1, col2 = st.columns(2)
    with col1:
        symbol1 = st.text_input("Stock 1", "AAPL", key="comparison_stock1").upper()
    with col2:
        symbol2 = st.text_input("Stock 2", "MSFT", key="comparison_stock2").upper()

    period = st.selectbox("Time Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3, key="comparison_period")

    if st.button("Compare Stocks", type="primary"):
        try:
            # Fetch data for both stocks
            data1 = yf.Ticker(symbol1).history(period=period)
            data2 = yf.Ticker(symbol2).history(period=period)

            if data1.empty or data2.empty:
                st.error("Unable to fetch data for one or both symbols")
                return

            # Normalize prices to compare performance
            normalized1 = (data1['Close'] / data1['Close'].iloc[0]) * 100
            normalized2 = (data2['Close'] / data2['Close'].iloc[0]) * 100

            # Create comparison chart
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=data1.index,
                y=normalized1,
                name=f"{symbol1}",
                line=dict(color='cyan', width=2)
            ))

            fig.add_trace(go.Scatter(
                x=data2.index,
                y=normalized2,
                name=f"{symbol2}",
                line=dict(color='magenta', width=2)
            ))

            fig.update_layout(
                title=f"Performance Comparison: {symbol1} vs {symbol2}",
                xaxis_title="Date",
                yaxis_title="Normalized Performance (%)",
                template="plotly_dark",
                height=500,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Performance metrics
            st.subheader("📊 Performance Metrics")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### {symbol1}")
                perf1 = ((data1['Close'].iloc[-1] / data1['Close'].iloc[0]) - 1) * 100
                vol1 = data1['Close'].pct_change().std() * (252 ** 0.5) * 100  # Annualized volatility
                st.metric("Total Return", f"{perf1:.2f}%")
                st.metric("Volatility (Annual)", f"{vol1:.2f}%")
                st.metric("Sharpe Ratio", f"{(perf1/vol1):.2f}" if vol1 > 0 else "N/A")

            with col2:
                st.markdown(f"### {symbol2}")
                perf2 = ((data2['Close'].iloc[-1] / data2['Close'].iloc[0]) - 1) * 100
                vol2 = data2['Close'].pct_change().std() * (252 ** 0.5) * 100
                st.metric("Total Return", f"{perf2:.2f}%")
                st.metric("Volatility (Annual)", f"{vol2:.2f}%")
                st.metric("Sharpe Ratio", f"{(perf2/vol2):.2f}" if vol2 > 0 else "N/A")

            # Correlation analysis
            st.subheader("🔗 Correlation Analysis")
            returns1 = data1['Close'].pct_change().dropna()
            returns2 = data2['Close'].pct_change().dropna()

            # Align the series
            aligned_returns = pd.DataFrame({
                symbol1: returns1,
                symbol2: returns2
            }).dropna()

            if len(aligned_returns) > 0:
                correlation = aligned_returns[symbol1].corr(aligned_returns[symbol2])
                st.metric("Correlation Coefficient", f"{correlation:.3f}")

                # Interpretation
                if correlation > 0.7:
                    st.info("🔵 Strong positive correlation - stocks move together")
                elif correlation > 0.3:
                    st.info("🟡 Moderate positive correlation")
                elif correlation > -0.3:
                    st.info("⚪ Weak or no correlation")
                elif correlation > -0.7:
                    st.info("🟠 Moderate negative correlation")
                else:
                    st.info("🔴 Strong negative correlation - stocks move opposite")

        except Exception as e:
            st.error(f"Error comparing stocks: {str(e)}")
