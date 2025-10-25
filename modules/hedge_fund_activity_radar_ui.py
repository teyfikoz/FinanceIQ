"""
Hedge Fund Activity Radar UI - Interactive interface for multi-source institutional tracking
Visualizes 13F filings, short interest, options data, and insider transactions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List

from modules.hedge_fund_activity_radar import (
    HedgeFundActivityRadar,
    quick_activity_radar_analysis
)
from modules.whale_investor_analytics import WhaleInvestorAnalytics


class HedgeFundActivityRadarUI:
    """Streamlit UI for Hedge Fund Activity Radar"""

    def __init__(self):
        self.radar = HedgeFundActivityRadar()
        self.whale_analytics = WhaleInvestorAnalytics()

    def render(self):
        """Main render method"""

        st.markdown("""
        ## 📡 Hedge Fund Activity Radar

        **Multi-source institutional activity tracking:**
        - 📊 13F filing analysis (whale moves)
        - 🔻 Short interest trends (FINRA data)
        - 📈 Put/Call ratio analysis (options sentiment)
        - 👔 Insider transaction monitoring (SEC Form 4)
        - 🎯 Composite activity score: -100 (bearish) to +100 (bullish)
        - 🚨 Unusual activity detection (>2σ anomalies)

        **Use Case:** Spot where hedge funds are positioning BEFORE the market reacts
        """)

        st.markdown("---")

        # Settings
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            tickers_input = st.text_input(
                "Ticker'lar (virgülle ayırın)",
                value="AAPL,TSLA,NVDA,META,GOOGL,MSFT,AMZN,JPM,BAC,KO",
                key="hedge_fund_tickers"
            )
            tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]

        with col2:
            quarters = ['2024Q3', '2024Q4']
            quarter = st.selectbox("13F Dönemi", quarters, index=1, key="hedge_fund_quarter")

        with col3:
            lookback_days = st.number_input(
                "Anomaly Lookback (days)",
                min_value=7,
                max_value=90,
                value=30,
                key="hedge_fund_lookback"
            )

        # Whale investor selection for 13F data
        st.markdown("### 🐋 Whale Yatırımcılar (13F Data)")
        all_investors = list(self.whale_analytics.WHALE_INVESTORS.keys())
        selected_investors = st.multiselect(
            "13F data için whale seçin",
            options=all_investors,
            default=['buffett', 'gates', 'wood', 'dalio'],
            format_func=lambda x: f"{self.whale_analytics.WHALE_INVESTORS[x]['icon']} {self.whale_analytics.WHALE_INVESTORS[x]['name']}",
            key="hedge_fund_investors"
        )

        # Analyze button
        if st.button("🔍 Hedge Fund Activity Analizi", type="primary", use_container_width=True):
            if len(tickers) < 3:
                st.error("❌ En az 3 ticker girin")
                return

            if len(selected_investors) < 2:
                st.error("❌ En az 2 whale seçin")
                return

            with st.spinner("Multi-source institutional activity analiz ediliyor..."):
                self._analyze_and_display(tickers, selected_investors, quarter, lookback_days)

    def _analyze_and_display(self, tickers, selected_investors, quarter, lookback_days):
        """Analyze and display results"""

        # Load 13F data from whale investors
        thirteenf_data_dict = {}
        for inv_key in selected_investors:
            df = self.whale_analytics.load_whale_data(inv_key, quarter)
            if df is not None and len(df) > 0:
                name = self.whale_analytics.WHALE_INVESTORS[inv_key]['name']

                # Convert to 13F summary format
                for ticker in tickers:
                    ticker_df = df[df['ticker'] == ticker]
                    if len(ticker_df) > 0:
                        if ticker not in thirteenf_data_dict:
                            thirteenf_data_dict[ticker] = {'net_buyers': 0, 'net_sellers': 0}

                        action = ticker_df.iloc[0].get('action', 'HOLD')
                        if action in ['NEW', 'INCREASED']:
                            thirteenf_data_dict[ticker]['net_buyers'] += 1
                        elif action in ['SOLD_OUT', 'REDUCED']:
                            thirteenf_data_dict[ticker]['net_sellers'] += 1

        # Run analysis
        results = quick_activity_radar_analysis(tickers, thirteenf_data_dict)

        # Display results
        self._display_market_activity_index(results['market_activity_index'])
        self._display_activity_scores(results['activity_scores'])
        self._display_unusual_activities(results['unusual_activities'])
        self._display_activity_heatmap(results['heatmap_data'])
        self._display_data_source_breakdown(results['activity_scores'])

    def _display_market_activity_index(self, market_index: Dict):
        """Display market-wide activity index"""
        st.markdown("---")
        st.markdown("### 📊 Market Activity Index")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Gauge chart for market index
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=market_index['market_activity_index'],
                title={'text': "Market Activity Index"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 35], 'color': "lightcoral"},
                        {'range': [35, 45], 'color': "lightyellow"},
                        {'range': [45, 55], 'color': "lightgray"},
                        {'range': [55, 65], 'color': "lightgreen"},
                        {'range': [65, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.metric("Sentiment", market_index['sentiment'])
            st.metric("Stocks Analyzed", market_index['total_analyzed'])

        with col3:
            st.metric("Bullish Stocks", market_index['bullish_stocks'],
                     delta=f"{market_index['bullish_stocks']/market_index['total_analyzed']*100:.0f}%")

        with col4:
            st.metric("Bearish Stocks", market_index['bearish_stocks'],
                     delta=f"-{market_index['bearish_stocks']/market_index['total_analyzed']*100:.0f}%",
                     delta_color="inverse")

        # Interpretation
        sentiment = market_index['sentiment']
        if sentiment == 'BULLISH':
            st.success("🟢 **Institutional sentiment is BULLISH** - Hedge funds are net buyers")
        elif sentiment == 'BEARISH':
            st.error("🔴 **Institutional sentiment is BEARISH** - Hedge funds are net sellers")
        else:
            st.info(f"🟡 **Institutional sentiment is {sentiment}** - Mixed signals from hedge funds")

    def _display_activity_scores(self, activity_scores: pd.DataFrame):
        """Display individual stock activity scores"""
        st.markdown("---")
        st.markdown("### 🎯 Stock Activity Scores")

        # Sort by activity score
        activity_scores = activity_scores.sort_values('activity_score', ascending=False)

        # Bar chart
        fig = go.Figure()

        colors = activity_scores['activity_score'].apply(
            lambda x: 'green' if x > 20 else 'red' if x < -20 else 'gray'
        )

        fig.add_trace(go.Bar(
            x=activity_scores['ticker'],
            y=activity_scores['activity_score'],
            marker_color=colors,
            text=activity_scores['signal'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Score: %{y:.1f}<br>Signal: %{text}<extra></extra>'
        ))

        fig.update_layout(
            title="Composite Activity Score (-100 to +100)",
            xaxis_title="Ticker",
            yaxis_title="Activity Score",
            height=400,
            showlegend=False
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        st.plotly_chart(fig, use_container_width=True)

        # Data table with breakdown
        st.markdown("#### 📋 Detailed Breakdown")

        display_df = activity_scores.copy()

        # Expand breakdown dict into columns
        for key in ['13f_score', 'short_score', 'options_score', 'insider_score']:
            display_df[key] = display_df['breakdown'].apply(lambda x: x.get(key, 0))

        display_df = display_df[['ticker', 'activity_score', 'signal',
                                 '13f_score', 'short_score', 'options_score', 'insider_score']]

        # Format scores
        for col in ['activity_score', '13f_score', 'short_score', 'options_score', 'insider_score']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    def _display_unusual_activities(self, unusual_activities: List[Dict]):
        """Display unusual activity alerts"""
        st.markdown("---")
        st.markdown("### 🚨 Unusual Activity Alerts")

        if len(unusual_activities) == 0:
            st.info("✅ No unusual activity detected (no >2σ anomalies)")
            return

        st.warning(f"⚠️ **{len(unusual_activities)} unusual activities detected!**")

        for anomaly in unusual_activities:
            activity_type = anomaly['activity_type']

            # Icon based on activity type
            if 'SHORT' in activity_type:
                icon = "🔻"
                color = "red"
            elif 'PUT_CALL' in activity_type:
                icon = "📈"
                color = "orange"
            elif 'INSIDER' in activity_type:
                icon = "👔"
                color = "green"
            else:
                icon = "🔔"
                color = "blue"

            with st.expander(f"{icon} {anomaly['ticker']} - {activity_type} (z={anomaly['z_score']:.1f}σ)"):
                st.markdown(f"**Description:** {anomaly['description']}")
                st.markdown(f"**Magnitude:** {anomaly['magnitude']:.2f}")
                st.markdown(f"**Z-Score:** {anomaly['z_score']:.2f}σ")

                if activity_type == 'SHORT_SPIKE':
                    st.error("🔻 **Bearish Signal**: Hedge funds are shorting aggressively")
                elif activity_type == 'SHORT_COVER':
                    st.success("🟢 **Bullish Signal**: Hedge funds are covering shorts")
                elif activity_type == 'PUT_CALL_ANOMALY':
                    if anomaly['z_score'] > 0:
                        st.warning("📉 **Bearish**: High put/call ratio (hedging/bearish bets)")
                    else:
                        st.success("📈 **Bullish**: Low put/call ratio (call buying)")
                elif activity_type == 'INSIDER_BUY_CLUSTER':
                    st.success("💼 **Bullish**: Multiple insiders buying (insider confidence)")

    def _display_activity_heatmap(self, heatmap_data: pd.DataFrame):
        """Display time × ticker activity heatmap"""
        st.markdown("---")
        st.markdown("### 🔥 Activity Heatmap (30-day)")

        if len(heatmap_data) == 0:
            st.info("No heatmap data available")
            return

        # Pivot for heatmap
        pivot = heatmap_data.pivot(
            index='ticker',
            columns='date',
            values='activity_score'
        )

        # Limit to 10 tickers for readability
        if len(pivot) > 10:
            pivot = pivot.head(10)

        fig = px.imshow(
            pivot,
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            aspect='auto',
            title="Activity Score Over Time"
        )

        fig.update_layout(height=400)
        fig.update_xaxes(title="Date")
        fig.update_yaxes(title="Ticker")

        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 **Yorumlama:** Yeşil = bullish activity, Kırmızı = bearish activity")

    def _display_data_source_breakdown(self, activity_scores: pd.DataFrame):
        """Display contribution of each data source"""
        st.markdown("---")
        st.markdown("### 📊 Data Source Contribution")

        # Calculate average contribution of each source
        avg_13f = activity_scores['breakdown'].apply(lambda x: abs(x.get('13f_score', 0))).mean()
        avg_short = activity_scores['breakdown'].apply(lambda x: abs(x.get('short_score', 0))).mean()
        avg_options = activity_scores['breakdown'].apply(lambda x: abs(x.get('options_score', 0))).mean()
        avg_insider = activity_scores['breakdown'].apply(lambda x: abs(x.get('insider_score', 0))).mean()

        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['13F Filings', 'Short Interest', 'Options Flow', 'Insider Transactions'],
            values=[avg_13f, avg_short, avg_options, avg_insider],
            marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        )])

        fig.update_layout(
            title="Average Contribution to Activity Score (Absolute)",
            height=350
        )

        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("13F Avg Impact", f"{avg_13f:.1f}")
        with col2:
            st.metric("Short Avg Impact", f"{avg_short:.1f}")
        with col3:
            st.metric("Options Avg Impact", f"{avg_options:.1f}")
        with col4:
            st.metric("Insider Avg Impact", f"{avg_insider:.1f}")


def render_hedge_fund_activity_radar():
    """Main render function"""
    ui = HedgeFundActivityRadarUI()
    ui.render()


if __name__ == "__main__":
    render_hedge_fund_activity_radar()
