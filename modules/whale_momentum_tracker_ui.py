"""
Whale Momentum Tracker UI - Interactive interface for institutional momentum analysis
Visualizes consensus buys/sells and momentum scores
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List

from modules.whale_momentum_tracker import WhaleMomentumTracker, quick_momentum_analysis
from modules.whale_investor_analytics import WhaleInvestorAnalytics
from modules.insight_engine import generate_all_insights


class WhaleMomentumTrackerUI:
    """Streamlit UI for Whale Momentum Tracker"""

    def __init__(self):
        self.tracker = WhaleMomentumTracker()
        self.whale_analytics = WhaleInvestorAnalytics()

    def render(self):
        """Main render method for Whale Momentum Tracker UI"""

        st.markdown("""
        ## 📈 Whale Momentum Tracker

        **Kurumsal alım/satım momentumunu takip edin:**
        - 🐋 Hangi balina yatırımcılar aynı hisseyi alıyor?
        - 📊 Institutional Consensus Indicator (0-100)
        - 🎯 Momentum Score ile en güçlü sinyaller
        - ⚡ Consensus Buy/Sell signals
        - 🔀 Divergence detection (balinalar çatışıyor)

        **Kullanım:** "Smart money" ne yönde hareket ediyor - momentum yakala!
        """)

        st.markdown("---")

        # Period selection
        col1, col2 = st.columns([1, 3])

        with col1:
            quarters = ['2024Q3', '2024Q4']
            current_quarter = st.selectbox(
                "Mevcut Dönem",
                quarters,
                index=1,
                key="momentum_current_quarter"
            )

            prev_idx = quarters.index(current_quarter) - 1 if current_quarter in quarters else -1
            if prev_idx >= 0:
                previous_quarter = quarters[prev_idx]
            else:
                st.error("Önceki dönem verisi yok")
                return

        with col2:
            # Investor selection
            all_investors = list(self.whale_analytics.WHALE_INVESTORS.keys())

            selected_investors = st.multiselect(
                "Analiz edilecek yatırımcılar (en az 3)",
                options=all_investors,
                default=['buffett', 'gates', 'wood', 'dalio'],
                format_func=lambda x: f"{self.whale_analytics.WHALE_INVESTORS[x]['icon']} {self.whale_analytics.WHALE_INVESTORS[x]['name']}",
                key="momentum_investors"
            )

        # Analysis button
        if st.button("📈 Momentum Analizi Yap", type="primary", use_container_width=True):
            if len(selected_investors) < 3:
                st.error("❌ En az 3 yatırımcı seçmelisiniz.")
                return

            with st.spinner("Whale momentum analiz ediliyor..."):
                self._analyze_and_display(
                    selected_investors,
                    current_quarter,
                    previous_quarter
                )

    def _analyze_and_display(
        self,
        selected_investors: List[str],
        current_quarter: str,
        previous_quarter: str
    ):
        """Analyze and display momentum results"""

        # Load whale data
        whale_data_current = {}
        whale_data_previous = {}

        for investor_key in selected_investors:
            df_curr = self.whale_analytics.load_whale_data(investor_key, current_quarter)
            df_prev = self.whale_analytics.load_whale_data(investor_key, previous_quarter)

            if df_curr is not None and len(df_curr) > 0 and df_prev is not None and len(df_prev) > 0:
                investor_name = self.whale_analytics.WHALE_INVESTORS[investor_key]['name']
                whale_data_current[investor_name] = df_curr
                whale_data_previous[investor_name] = df_prev

        if len(whale_data_current) < 3:
            st.error("❌ Yeterli veri yüklenemedi. En az 3 yatırımcı için iki dönem verisi gerekli.")
            return

        # Run momentum analysis
        results = quick_momentum_analysis(whale_data_current, whale_data_previous)

        # Display results
        self._display_consensus_indicator(results['consensus_indicator'])
        self._display_consensus_buys(results['consensus_buys'])
        self._display_consensus_sells(results['consensus_sells'])
        self._display_top_momentum(results['top_momentum_stocks'])
        self._display_divergences(results['divergences'])
        self._display_momentum_heatmap(results['aggregated_moves'])

        # AI Insights
        self._display_insights(results)

    def _display_consensus_indicator(self, consensus_indicator: Dict):
        """Display institutional consensus indicator"""

        st.markdown("---")
        st.markdown("### 🎯 Institutional Consensus Indicator")

        score = consensus_indicator['consensus_score']
        sentiment = consensus_indicator['market_sentiment']

        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Consensus Score"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 35], 'color': "lightcoral"},
                    {'range': [35, 45], 'color': "lightyellow"},
                    {'range': [45, 55], 'color': "lightgray"},
                    {'range': [55, 65], 'color': "lightgreen"},
                    {'range': [65, 100], 'color': "lightblue"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))

        fig.update_layout(height=300)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(f"""
            #### 📊 Consensus Metrics

            **Score:** {score:.1f}/100

            **Sentiment:** {sentiment}

            **Moves:** {consensus_indicator['total_moves']} total
            - 🟢 Buys: {consensus_indicator['num_buys']}
            - 🔴 Sells: {consensus_indicator['num_sells']}

            **Value-Weighted:** {consensus_indicator['value_weighted_score']:.1f}/100
            """)

            # Interpretation
            if score >= 65:
                st.success("✅ Güçlü kurumsal alım baskısı var!")
            elif score >= 55:
                st.info("📈 Pozitif eğilim ama güçlü değil")
            elif score >= 45:
                st.warning("⚠️ Nötr piyasa - yön belirsiz")
            elif score >= 35:
                st.warning("📉 Negatif eğilim başlıyor")
            else:
                st.error("🔴 Güçlü kurumsal satış baskısı!")

    def _display_consensus_buys(self, consensus_buys: List[Dict]):
        """Display consensus buy signals"""

        st.markdown("---")
        st.markdown("### 🟢 Consensus Buy Signals")

        if not consensus_buys:
            st.info("Bu dönemde 3+ whale tarafından alınan hisse yok.")
            return

        st.markdown(f"""
        **{len(consensus_buys)} hisse tespit edildi** (3+ whale aynı anda alıyor)
        """)

        # Create DataFrame for display
        buy_data = []
        for buy in consensus_buys[:10]:
            buy_data.append({
                'Ticker': buy['ticker'],
                'Whales': buy['num_buyers'],
                'Investors': ', '.join(buy['buyer_whales'][:3]) + ('...' if len(buy['buyer_whales']) > 3 else ''),
                'Total Value': f"${buy['total_value_change']/1e6:.1f}M",
                'Avg Weight Δ': f"{buy['avg_weight_change']:+.2f}%",
                'Strength': buy['signal_strength']
            })

        df = pd.DataFrame(buy_data)

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Bar chart
        fig = go.Figure()

        tickers = [b['ticker'] for b in consensus_buys[:10]]
        num_buyers = [b['num_buyers'] for b in consensus_buys[:10]]

        fig.add_trace(go.Bar(
            x=tickers,
            y=num_buyers,
            text=num_buyers,
            textposition='outside',
            marker_color='lightgreen',
            name='Number of Buyers'
        ))

        fig.update_layout(
            title="Top 10 Consensus Buys (Number of Whales)",
            xaxis_title="Ticker",
            yaxis_title="Number of Whale Buyers",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    def _display_consensus_sells(self, consensus_sells: List[Dict]):
        """Display consensus sell signals"""

        st.markdown("---")
        st.markdown("### 🔴 Consensus Sell Signals")

        if not consensus_sells:
            st.info("Bu dönemde 3+ whale tarafından satılan hisse yok.")
            return

        st.markdown(f"""
        **{len(consensus_sells)} hisse tespit edildi** (3+ whale aynı anda satıyor)
        """)

        # Create DataFrame
        sell_data = []
        for sell in consensus_sells[:10]:
            sell_data.append({
                'Ticker': sell['ticker'],
                'Whales': sell['num_sellers'],
                'Investors': ', '.join(sell['seller_whales'][:3]) + ('...' if len(sell['seller_whales']) > 3 else ''),
                'Total Value': f"${abs(sell['total_value_change'])/1e6:.1f}M",
                'Avg Weight Δ': f"{sell['avg_weight_change']:+.2f}%",
                'Strength': sell['signal_strength']
            })

        df = pd.DataFrame(sell_data)

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Bar chart
        fig = go.Figure()

        tickers = [s['ticker'] for s in consensus_sells[:10]]
        num_sellers = [s['num_sellers'] for s in consensus_sells[:10]]

        fig.add_trace(go.Bar(
            x=tickers,
            y=num_sellers,
            text=num_sellers,
            textposition='outside',
            marker_color='lightcoral',
            name='Number of Sellers'
        ))

        fig.update_layout(
            title="Top 10 Consensus Sells (Number of Whales)",
            xaxis_title="Ticker",
            yaxis_title="Number of Whale Sellers",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    def _display_top_momentum(self, top_momentum: pd.DataFrame):
        """Display top momentum stocks"""

        st.markdown("---")
        st.markdown("### ⚡ Top Momentum Stocks")

        st.markdown("""
        **Momentum Score Formülü:**
        ```
        Momentum = (Net Buy % + Overlap × Confidence) / 2
        ```
        - **Net Buy %**: Alıcı - Satıcı / Toplam
        - **Overlap**: Kaç whale involved
        - **Confidence**: Pozisyon büyüklüğü
        """)

        if len(top_momentum) == 0:
            st.info("Momentum verisi bulunamadı.")
            return

        # Display table
        display_df = top_momentum[['ticker', 'momentum_score', 'num_whales', 'buyers', 'sellers', 'net_direction']].copy()
        display_df.columns = ['Ticker', 'Momentum', 'Whales', 'Buyers', 'Sellers', 'Direction']
        display_df['Momentum'] = display_df['Momentum'].apply(lambda x: f"{x:.3f}")

        st.dataframe(display_df.head(15), use_container_width=True, hide_index=True)

        # Scatter plot
        fig = px.scatter(
            top_momentum.head(20),
            x='num_whales',
            y='momentum_score',
            text='ticker',
            size='confidence',
            color='net_direction',
            color_discrete_map={'BULLISH': 'green', 'NEUTRAL': 'gray', 'BEARISH': 'red'},
            title="Momentum Score vs Number of Whales"
        )

        fig.update_traces(textposition='top center')
        fig.update_layout(height=500)

        st.plotly_chart(fig, use_container_width=True)

    def _display_divergences(self, divergences: List[Dict]):
        """Display whale divergences"""

        st.markdown("---")
        st.markdown("### 🔀 Whale Divergences")

        if not divergences:
            st.info("Whale'ler arasında önemli görüş ayrılığı tespit edilmedi.")
            return

        st.markdown(f"""
        **{len(divergences)} hisse tespit edildi** (bazı whale'ler alıyor, bazıları satıyor)

        ⚠️ **Divergence = Volatilite Potansiyeli**
        """)

        # Create DataFrame
        div_data = []
        for div in divergences[:10]:
            div_data.append({
                'Ticker': div['ticker'],
                'Buyers': div['num_buyers'],
                'Sellers': div['num_sellers'],
                'Buyer Whales': ', '.join(div['buyer_whales'][:2]),
                'Seller Whales': ', '.join(div['seller_whales'][:2]),
                'Divergence Score': f"{div['divergence_score']:.2f}"
            })

        df = pd.DataFrame(div_data)

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.warning("""
        ⚠️ **Divergence Yorumu:**
        - Yüksek divergence = whale'ler arasında güçlü görüş ayrılığı
        - Birisi haklı çıkacak → fırsat veya risk!
        - Dikkatle takip edin
        """)

    def _display_momentum_heatmap(self, aggregated_moves: pd.DataFrame):
        """Display momentum heatmap"""

        st.markdown("---")
        st.markdown("### 🔥 Whale Activity Heatmap")

        if len(aggregated_moves) == 0:
            return

        # Create pivot table: whales × tickers
        # Count number of actions per whale-ticker pair
        heatmap_data = aggregated_moves.groupby(['whale', 'ticker']).size().reset_index(name='activity')

        # Get top 15 tickers by activity
        top_tickers = aggregated_moves['ticker'].value_counts().head(15).index.tolist()

        heatmap_data = heatmap_data[heatmap_data['ticker'].isin(top_tickers)]

        # Pivot
        pivot = heatmap_data.pivot(index='whale', columns='ticker', values='activity').fillna(0)

        # Heatmap
        fig = px.imshow(
            pivot,
            color_continuous_scale='Blues',
            aspect='auto',
            title="Whale Activity Heatmap (Top 15 Tickers)"
        )

        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)

    def _display_insights(self, results: Dict):
        """Display AI-generated insights"""

        st.markdown("---")
        st.markdown("### 🤖 AI İçgörüler")

        try:
            insights = generate_all_insights(
                data_type='whale_momentum',
                consensus_indicator=results['consensus_indicator'],
                consensus_buys=results['consensus_buys'],
                consensus_sells=results['consensus_sells'],
                divergences=results['divergences'],
                top_momentum=results['top_momentum_stocks']
            )

            if insights:
                for insight in insights:
                    if insight.startswith("🟢") or insight.startswith("💡"):
                        st.success(insight)
                    elif insight.startswith("⚠️") or insight.startswith("🟡"):
                        st.warning(insight)
                    elif insight.startswith("🔴"):
                        st.error(insight)
                    else:
                        st.info(insight)
            else:
                st.info("💡 Daha fazla veri ile içgörü oluşturulacak.")

        except Exception as e:
            st.warning(f"⚠️ İçgörü oluşturulurken hata: {str(e)}")


def render_whale_momentum_tracker():
    """Main function to render Whale Momentum Tracker UI"""
    ui = WhaleMomentumTrackerUI()
    ui.render()


if __name__ == "__main__":
    render_whale_momentum_tracker()
