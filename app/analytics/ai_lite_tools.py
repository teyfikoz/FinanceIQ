"""
🤖 Lightweight AI Functions - Phase 1 Game Changer Features
Monte Carlo Simulation, Backtesting Engine, Auto Chart Annotation, News Sentiment
All features use lightweight ML (numpy, pandas, scikit-learn) - NO paid APIs
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf
from scipy import stats
from sklearn.preprocessing import StandardScaler
import re
from utils.news_utils import normalize_yfinance_news


class AILiteTools:
    """Lightweight AI-powered tools for FinanceIQ"""

    def __init__(self):
        self.scaler = StandardScaler()

    # ========== 1. Monte Carlo Simulation ==========

    def monte_carlo_simulation(self, ticker, initial_investment=10000, num_simulations=10000, time_horizon=252):
        """
        Monte Carlo portfolio simulation
        Simulates 10,000+ random price paths based on historical volatility
        """
        st.subheader(f"🎲 Monte Carlo Simulation - {ticker}")

        try:
            # Fetch historical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2y")

            if hist.empty:
                st.error(f"No data available for {ticker}")
                return

            # Calculate returns statistics
            returns = hist['Close'].pct_change().dropna()
            mean_return = returns.mean()
            std_return = returns.std()

            st.markdown(f"""
            **Historical Statistics:**
            - Mean Daily Return: {mean_return*100:.4f}%
            - Daily Volatility: {std_return*100:.4f}%
            - Annualized Return: {mean_return*252*100:.2f}%
            - Annualized Volatility: {std_return*np.sqrt(252)*100:.2f}%
            """)

            # Run Monte Carlo simulation
            with st.spinner(f"Running {num_simulations:,} simulations..."):
                simulation_results = np.zeros((time_horizon, num_simulations))
                simulation_results[0] = initial_investment

                for t in range(1, time_horizon):
                    # Generate random returns from normal distribution
                    random_returns = np.random.normal(mean_return, std_return, num_simulations)
                    simulation_results[t] = simulation_results[t-1] * (1 + random_returns)

            # Calculate statistics
            final_values = simulation_results[-1]
            percentiles = {
                '5th': np.percentile(final_values, 5),
                '25th': np.percentile(final_values, 25),
                '50th': np.percentile(final_values, 50),
                '75th': np.percentile(final_values, 75),
                '95th': np.percentile(final_values, 95)
            }

            # Display results
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Initial Investment", f"${initial_investment:,.0f}")
            with col2:
                st.metric("Median Outcome", f"${percentiles['50th']:,.0f}",
                         delta=f"{(percentiles['50th']/initial_investment - 1)*100:+.1f}%")
            with col3:
                st.metric("95th Percentile", f"${percentiles['95th']:,.0f}",
                         delta=f"{(percentiles['95th']/initial_investment - 1)*100:+.1f}%")
            with col4:
                st.metric("5th Percentile", f"${percentiles['5th']:,.0f}",
                         delta=f"{(percentiles['5th']/initial_investment - 1)*100:+.1f}%")

            # Plot simulation paths
            fig = go.Figure()

            # Plot a sample of paths (100 out of 10,000)
            sample_indices = np.random.choice(num_simulations, 100, replace=False)
            for idx in sample_indices:
                fig.add_trace(go.Scatter(
                    y=simulation_results[:, idx],
                    mode='lines',
                    line=dict(width=0.5, color='rgba(100,100,255,0.1)'),
                    showlegend=False,
                    hoverinfo='skip'
                ))

            # Add percentile lines
            for percentile_name, percentile_value in [('50th', 50), ('95th', 95), ('5th', 5)]:
                percentile_path = np.percentile(simulation_results, percentile_value, axis=1)
                fig.add_trace(go.Scatter(
                    y=percentile_path,
                    mode='lines',
                    name=f'{percentile_name} Percentile',
                    line=dict(width=3)
                ))

            fig.update_layout(
                title=f"Monte Carlo Simulation: {num_simulations:,} Paths over {time_horizon} Trading Days",
                xaxis_title="Trading Days",
                yaxis_title="Portfolio Value ($)",
                height=500,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Distribution of final values
            st.markdown("### 📊 Distribution of Final Portfolio Values")

            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=final_values,
                nbinsx=50,
                name='Final Values',
                marker_color='skyblue'
            ))

            # Add percentile lines
            for name, value in percentiles.items():
                fig_hist.add_vline(
                    x=value,
                    line_dash="dash",
                    annotation_text=f"{name}: ${value:,.0f}",
                    annotation_position="top"
                )

            fig_hist.update_layout(
                title="Distribution of Final Portfolio Values",
                xaxis_title="Portfolio Value ($)",
                yaxis_title="Frequency",
                height=400
            )

            st.plotly_chart(fig_hist, use_container_width=True)

            # Risk metrics
            var_95 = initial_investment - percentiles['5th']
            prob_loss = (final_values < initial_investment).sum() / num_simulations * 100

            st.markdown("### ⚠️ Risk Metrics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Value at Risk (95%)", f"${var_95:,.0f}")
            with col2:
                st.metric("Probability of Loss", f"{prob_loss:.1f}%")
            with col3:
                expected_return = (percentiles['50th'] / initial_investment - 1) * 100
                st.metric("Expected Return", f"{expected_return:+.1f}%")

        except Exception as e:
            st.error(f"Error running Monte Carlo simulation: {e}")

    # ========== 2. Backtesting Engine ==========

    def backtest_strategy(self, ticker, strategy_type="SMA_Crossover", period="2y"):
        """
        Backtesting engine for common strategies
        Supports SMA crossover, RSI, MACD strategies
        """
        st.subheader(f"⚡ Strategy Backtesting - {ticker}")

        try:
            # Fetch historical data
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)

            if df.empty:
                st.error(f"No data available for {ticker}")
                return

            # Apply selected strategy
            if strategy_type == "SMA_Crossover":
                results = self._backtest_sma_crossover(df)
            elif strategy_type == "RSI":
                results = self._backtest_rsi(df)
            elif strategy_type == "MACD":
                results = self._backtest_macd(df)
            else:
                st.error("Unknown strategy type")
                return

            # Display results
            self._display_backtest_results(results, ticker, strategy_type)

        except Exception as e:
            st.error(f"Error backtesting strategy: {e}")

    def _backtest_sma_crossover(self, df, fast_period=50, slow_period=200):
        """Backtest SMA crossover strategy"""
        df = df.copy()
        df['SMA_Fast'] = df['Close'].rolling(window=fast_period).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=slow_period).mean()

        # Generate signals
        df['Signal'] = 0
        df.loc[df['SMA_Fast'] > df['SMA_Slow'], 'Signal'] = 1
        df.loc[df['SMA_Fast'] <= df['SMA_Slow'], 'Signal'] = -1

        # Calculate returns
        df['Market_Return'] = df['Close'].pct_change()
        df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']

        # Calculate cumulative returns
        df['Cumulative_Market'] = (1 + df['Market_Return']).cumprod()
        df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()

        return {
            'df': df,
            'strategy_name': f'SMA Crossover ({fast_period}/{slow_period})',
            'params': {'fast_period': fast_period, 'slow_period': slow_period}
        }

    def _backtest_rsi(self, df, rsi_period=14, oversold=30, overbought=70):
        """Backtest RSI strategy"""
        df = df.copy()

        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Generate signals
        df['Signal'] = 0
        df.loc[df['RSI'] < oversold, 'Signal'] = 1  # Buy
        df.loc[df['RSI'] > overbought, 'Signal'] = -1  # Sell

        # Calculate returns
        df['Market_Return'] = df['Close'].pct_change()
        df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']

        df['Cumulative_Market'] = (1 + df['Market_Return']).cumprod()
        df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()

        return {
            'df': df,
            'strategy_name': f'RSI ({rsi_period}, {oversold}/{overbought})',
            'params': {'rsi_period': rsi_period, 'oversold': oversold, 'overbought': overbought}
        }

    def _backtest_macd(self, df, fast=12, slow=26, signal=9):
        """Backtest MACD strategy"""
        df = df.copy()

        # Calculate MACD
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()

        # Generate signals
        df['Signal'] = 0
        df.loc[df['MACD'] > df['MACD_Signal'], 'Signal'] = 1
        df.loc[df['MACD'] <= df['MACD_Signal'], 'Signal'] = -1

        # Calculate returns
        df['Market_Return'] = df['Close'].pct_change()
        df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']

        df['Cumulative_Market'] = (1 + df['Market_Return']).cumprod()
        df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()

        return {
            'df': df,
            'strategy_name': f'MACD ({fast}/{slow}/{signal})',
            'params': {'fast': fast, 'slow': slow, 'signal': signal}
        }

    def _display_backtest_results(self, results, ticker, strategy_type):
        """Display backtest results with charts and metrics"""
        df = results['df'].dropna()

        # Calculate performance metrics
        total_return_market = (df['Cumulative_Market'].iloc[-1] - 1) * 100
        total_return_strategy = (df['Cumulative_Strategy'].iloc[-1] - 1) * 100

        sharpe_market = self._calculate_sharpe_ratio(df['Market_Return'])
        sharpe_strategy = self._calculate_sharpe_ratio(df['Strategy_Return'])

        max_drawdown_market = self._calculate_max_drawdown(df['Cumulative_Market'])
        max_drawdown_strategy = self._calculate_max_drawdown(df['Cumulative_Strategy'])

        # Display metrics
        st.markdown(f"### 📈 {results['strategy_name']} Performance")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Strategy Return", f"{total_return_strategy:+.2f}%")
            st.metric("Buy & Hold Return", f"{total_return_market:+.2f}%")
        with col2:
            st.metric("Strategy Sharpe Ratio", f"{sharpe_strategy:.2f}")
            st.metric("Buy & Hold Sharpe", f"{sharpe_market:.2f}")
        with col3:
            st.metric("Strategy Max Drawdown", f"{max_drawdown_strategy:.2f}%")
            st.metric("Buy & Hold Max DD", f"{max_drawdown_market:.2f}%")

        # Plot cumulative returns
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Cumulative_Market'],
            mode='lines',
            name='Buy & Hold',
            line=dict(color='gray', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Cumulative_Strategy'],
            mode='lines',
            name=results['strategy_name'],
            line=dict(color='blue', width=2)
        ))

        fig.update_layout(
            title=f"{ticker} - Strategy vs Buy & Hold",
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
            height=500,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Trade analysis
        trades = df[df['Signal'].diff() != 0]
        num_trades = len(trades)
        winning_trades = (df['Strategy_Return'] > 0).sum()
        win_rate = (winning_trades / len(df)) * 100 if len(df) > 0 else 0

        st.markdown("### 📊 Trade Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trades", num_trades)
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            alpha = total_return_strategy - total_return_market
            st.metric("Alpha", f"{alpha:+.2f}%")

    def _calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        """Calculate Sharpe ratio"""
        excess_returns = returns - (risk_free_rate / 252)
        if excess_returns.std() == 0:
            return 0
        return np.sqrt(252) * (excess_returns.mean() / excess_returns.std())

    def _calculate_max_drawdown(self, cumulative_returns):
        """Calculate maximum drawdown"""
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max * 100
        return drawdown.min()

    # ========== 3. Auto Chart Annotation ==========

    def auto_annotate_chart(self, ticker, period="1y"):
        """
        Automatically detect and annotate support/resistance levels
        Also marks significant events (new highs/lows, breakouts)
        """
        st.subheader(f"🎯 Auto-Annotated Chart - {ticker}")

        try:
            # Fetch data
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)

            if df.empty:
                st.error(f"No data available for {ticker}")
                return

            # Detect support and resistance
            support_levels, resistance_levels = self._detect_support_resistance(df)

            # Create annotated chart
            fig = go.Figure()

            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name=ticker
            ))

            # Add support levels
            for level in support_levels:
                fig.add_hline(
                    y=level,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"Support: ${level:.2f}",
                    annotation_position="right"
                )

            # Add resistance levels
            for level in resistance_levels:
                fig.add_hline(
                    y=level,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Resistance: ${level:.2f}",
                    annotation_position="right"
                )

            # Mark significant highs and lows
            highs = df[df['High'] == df['High'].rolling(20).max()]
            lows = df[df['Low'] == df['Low'].rolling(20).min()]

            fig.add_trace(go.Scatter(
                x=highs.index,
                y=highs['High'],
                mode='markers',
                marker=dict(size=10, color='red', symbol='triangle-down'),
                name='Local High',
                hovertemplate='High: $%{y:.2f}<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=lows.index,
                y=lows['Low'],
                mode='markers',
                marker=dict(size=10, color='green', symbol='triangle-up'),
                name='Local Low',
                hovertemplate='Low: $%{y:.2f}<extra></extra>'
            ))

            fig.update_layout(
                title=f"{ticker} - Auto-Annotated Chart with Support/Resistance",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=600,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display detected levels
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🟢 Support Levels:**")
                for level in support_levels:
                    st.write(f"${level:.2f}")
            with col2:
                st.markdown("**🔴 Resistance Levels:**")
                for level in resistance_levels:
                    st.write(f"${level:.2f}")

        except Exception as e:
            st.error(f"Error annotating chart: {e}")

    def _detect_support_resistance(self, df, num_levels=3):
        """Detect support and resistance levels using local extrema"""
        # Find local minima (support)
        local_mins = df['Low'].rolling(window=20, center=True).min()
        support_candidates = df[df['Low'] == local_mins]['Low'].values

        # Find local maxima (resistance)
        local_maxs = df['High'].rolling(window=20, center=True).max()
        resistance_candidates = df[df['High'] == local_maxs]['High'].values

        # Cluster nearby levels
        support_levels = self._cluster_levels(support_candidates, num_levels)
        resistance_levels = self._cluster_levels(resistance_candidates, num_levels)

        return support_levels, resistance_levels

    def _cluster_levels(self, levels, num_clusters):
        """Cluster price levels to find key support/resistance"""
        if len(levels) == 0:
            return []

        # Simple clustering by rounding
        unique_levels = np.unique(np.round(levels, 2))

        # Return top N levels by frequency
        level_counts = {}
        for level in levels:
            rounded = round(level, 2)
            level_counts[rounded] = level_counts.get(rounded, 0) + 1

        sorted_levels = sorted(level_counts.items(), key=lambda x: x[1], reverse=True)
        return [level for level, _ in sorted_levels[:num_clusters]]

    # ========== 4. News Sentiment Analysis ==========

    def news_sentiment_analysis(self, ticker):
        """
        Simple keyword-based sentiment scoring on yfinance news headlines
        No paid APIs - uses basic NLP on free news data
        """
        st.subheader(f"📰 News Sentiment Analysis - {ticker}")

        try:
            # Fetch news from yfinance
            stock = yf.Ticker(ticker)
            news = normalize_yfinance_news(stock.news or [])

            if not news:
                st.warning(f"No recent news found for {ticker}")
                return

            # Analyze sentiment
            sentiments = []
            for article in news[:20]:  # Analyze last 20 articles
                title = article.get('title', '')
                summary = article.get('summary', '')
                pub_time = article.get('publish_time', '')
                if isinstance(pub_time, (int, float)):
                    pub_time = datetime.fromtimestamp(pub_time)

                text = f"{title} {summary}".lower()
                sentiment_score = self._calculate_sentiment_score(text)

                sentiments.append({
                    'Title': title,
                    'Publisher': article.get('publisher', 'Unknown'),
                    'Published': pub_time,
                    'Sentiment': sentiment_score,
                    'Sentiment_Label': self._get_sentiment_label(sentiment_score),
                    'Link': article.get('link', '')
                })

            sentiment_df = pd.DataFrame(sentiments)

            # Overall sentiment
            avg_sentiment = sentiment_df['Sentiment'].mean()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Sentiment", f"{avg_sentiment:.2f}",
                         delta=self._get_sentiment_label(avg_sentiment))
            with col2:
                positive_pct = (sentiment_df['Sentiment'] > 0.1).sum() / len(sentiment_df) * 100
                st.metric("Positive News", f"{positive_pct:.0f}%")
            with col3:
                negative_pct = (sentiment_df['Sentiment'] < -0.1).sum() / len(sentiment_df) * 100
                st.metric("Negative News", f"{negative_pct:.0f}%")

            # Sentiment timeline
            fig = go.Figure()

            colors = ['green' if s > 0.1 else 'red' if s < -0.1 else 'gray'
                     for s in sentiment_df['Sentiment']]

            fig.add_trace(go.Bar(
                x=sentiment_df['Published'],
                y=sentiment_df['Sentiment'],
                marker_color=colors,
                name='Sentiment Score',
                hovertemplate='<b>%{text}</b><br>Score: %{y:.2f}<extra></extra>',
                text=sentiment_df['Title']
            ))

            fig.update_layout(
                title="News Sentiment Timeline",
                xaxis_title="Publication Date",
                yaxis_title="Sentiment Score",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # News table
            st.markdown("### 📋 Recent News")
            display_df = sentiment_df[['Title', 'Publisher', 'Published', 'Sentiment_Label']].copy()

            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "Title": st.column_config.TextColumn("Headline", width="large"),
                    "Publisher": st.column_config.TextColumn("Source", width="small"),
                    "Published": st.column_config.DatetimeColumn("Date", format="MMM DD, YYYY"),
                    "Sentiment_Label": st.column_config.TextColumn("Sentiment", width="small")
                },
                hide_index=True
            )

        except Exception as e:
            st.error(f"Error analyzing news sentiment: {e}")

    def _calculate_sentiment_score(self, text):
        """Simple keyword-based sentiment scoring"""
        positive_words = [
            'bullish', 'surge', 'rally', 'gain', 'profit', 'beat', 'exceed',
            'strong', 'growth', 'soar', 'jump', 'rise', 'upgrade', 'positive',
            'outperform', 'success', 'record', 'high', 'boom', 'recovery'
        ]

        negative_words = [
            'bearish', 'fall', 'drop', 'loss', 'miss', 'weak', 'decline',
            'plunge', 'crash', 'downgrade', 'negative', 'underperform',
            'concern', 'risk', 'warning', 'sell', 'low', 'recession', 'crisis'
        ]

        # Count occurrences
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        # Calculate score (-1 to 1)
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0

        score = (positive_count - negative_count) / total_count
        return score

    def _get_sentiment_label(self, score):
        """Convert sentiment score to label"""
        if score > 0.3:
            return "🟢 Positive"
        elif score > 0.1:
            return "🟡 Slightly Positive"
        elif score > -0.1:
            return "⚪ Neutral"
        elif score > -0.3:
            return "🟠 Slightly Negative"
        else:
            return "🔴 Negative"


def render_ai_lite_tools():
    """Main function to render AI lite tools UI"""
    ai = AILiteTools()

    st.title("🤖 AI-Powered Analysis Tools")

    tabs = st.tabs([
        "🎲 Monte Carlo",
        "⚡ Backtesting",
        "🎯 Chart Annotation",
        "📰 News Sentiment"
    ])

    with tabs[0]:
        ticker = st.text_input("Enter Ticker", "AAPL", key="mc_ticker")
        col1, col2 = st.columns(2)
        with col1:
            investment = st.number_input("Initial Investment ($)", 1000, 1000000, 10000)
        with col2:
            days = st.number_input("Time Horizon (days)", 30, 1000, 252)

        if st.button("Run Simulation", type="primary"):
            ai.monte_carlo_simulation(ticker.upper(), investment, 10000, days)

    with tabs[1]:
        ticker = st.text_input("Enter Ticker", "SPY", key="bt_ticker")
        strategy = st.selectbox(
            "Select Strategy",
            ["SMA_Crossover", "RSI", "MACD"]
        )
        period = st.selectbox("Backtest Period", ["1y", "2y", "3y", "5y"])

        if st.button("Run Backtest", type="primary"):
            ai.backtest_strategy(ticker.upper(), strategy, period)

    with tabs[2]:
        ticker = st.text_input("Enter Ticker", "TSLA", key="chart_ticker")
        period = st.selectbox("Chart Period", ["3mo", "6mo", "1y", "2y"], key="chart_period")

        if st.button("Annotate Chart", type="primary"):
            ai.auto_annotate_chart(ticker.upper(), period)

    with tabs[3]:
        ticker = st.text_input("Enter Ticker", "NVDA", key="news_ticker")

        if st.button("Analyze News", type="primary"):
            ai.news_sentiment_analysis(ticker.upper())


if __name__ == "__main__":
    render_ai_lite_tools()
