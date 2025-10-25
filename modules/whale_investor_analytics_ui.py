"""
Whale Investor Analytics UI - Track legendary investors
Interactive interface for analyzing whale portfolios and moves
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List

from modules.whale_investor_analytics import WhaleInvestorAnalytics
from modules.insight_engine import generate_all_insights


class WhaleInvestorAnalyticsUI:
    """Streamlit UI for Whale Investor Analytics module"""

    def __init__(self):
        self.analytics = WhaleInvestorAnalytics()

    def render(self):
        """Main render method for Whale Analytics UI"""

        st.markdown("""
        ## 🐋 Whale Investor Analytics

        **Efsanevi yatırımcıların portföylerini takip edin:**
        - 💰 Warren Buffett, Bill Gates, Cathie Wood, Ray Dalio
        - 📊 13F SEC dosyaları analizi
        - 🎯 Büyük pozisyon değişimleri (whale signals)
        - 📈 Çeyreksel portföy kompozisyonu
        - 🔍 Yatırım stratejisi analizi

        **Kullanım:** "Smart money" ne yapıyor - kurumsal zekayı takip edin!
        """)

        st.markdown("---")

        # Investor selection
        col1, col2 = st.columns([1, 2])

        with col1:
            investor_key = st.selectbox(
                "Yatırımcı Seçin",
                options=list(self.analytics.WHALE_INVESTORS.keys()),
                format_func=lambda x: f"{self.analytics.WHALE_INVESTORS[x]['icon']} {self.analytics.WHALE_INVESTORS[x]['name']}",
                index=0
            )

            investor_info = self.analytics.WHALE_INVESTORS[investor_key]

            st.info(f"""
            **{investor_info['icon']} {investor_info['name']}**

            **Firma:** {investor_info['entity']}

            **Stil:** {investor_info['style']}

            **CIK:** {investor_info['cik']}
            """)

            quarters = ['2024Q3', '2024Q4']
            current_quarter = st.selectbox("Dönem Seç", quarters, index=1)

        with col2:
            st.markdown(f"""
            ### 📋 {investor_info['name']} Hakkında

            **Yatırım Felsefesi:**
            """)

            if investor_key == 'buffett':
                st.markdown("""
                - **Value Investing**: Ucuz, kaliteli şirketler
                - **Uzun vadeli**: 10+ yıl tutma
                - **Ekonomik hendek**: Rekabet avantajı olan şirketler
                - **Yönetim kalitesi**: İyi yönetilen şirketler
                """)
            elif investor_key == 'wood':
                st.markdown("""
                - **Disruptive Innovation**: Yenilikçi teknolojiler
                - **Yüksek büyüme**: 40%+ yıllık büyüme hedefi
                - **Tema bazlı**: AI, genomik, blockchain, otonom
                - **Yüksek volatilite**: Risk toleransı yüksek
                """)
            elif investor_key == 'dalio':
                st.markdown("""
                - **All Weather**: Her ekonomik durumda çalışan portföy
                - **Risk paritesi**: Risk dengeli dağılım
                - **Diversifikasyon**: 15+ varlık sınıfı
                - **Makro odaklı**: Global ekonomik trendler
                """)
            elif investor_key == 'gates':
                st.markdown("""
                - **Large cap quality**: Büyük, sağlam şirketler
                - **Healthcare ağırlık**: Sağlık ve biyoteknoloji
                - **Impact investing**: Sosyal etki + getiri
                - **Düşük volatilite**: Savunmacı yaklaşım
                """)

        # Analyze and display
        if st.button("🔍 Portföyü Analiz Et", type="primary", use_container_width=True):
            with st.spinner("Whale portföyü analiz ediliyor..."):
                self._analyze_and_display(investor_key, current_quarter, quarters)

    def _analyze_and_display(self, investor_key: str, current_quarter: str, quarters: List[str]):
        """Analyze and display whale portfolio"""

        # Load data
        df_current = self.analytics.load_whale_data(investor_key, current_quarter)

        if df_current is None or len(df_current) == 0:
            st.error("Veri yüklenemedi.")
            return

        # Previous quarter for comparison
        previous_idx = quarters.index(current_quarter) - 1 if current_quarter in quarters else -1
        df_previous = None

        if previous_idx >= 0:
            previous_quarter = quarters[previous_idx]
            df_previous = self.analytics.load_whale_data(investor_key, previous_quarter)

        # Summary metrics
        st.markdown("### 📊 Portföy Özeti")

        total_value = df_current['value_usd'].sum()
        num_holdings = len(df_current)
        concentration = self.analytics.calculate_portfolio_concentration(df_current)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Toplam Değer",
                f"${total_value/1e9:.1f}B",
                help="13F filinglerinde bildirilen toplam değer"
            )

        with col2:
            st.metric(
                "Holding Sayısı",
                f"{num_holdings}",
                help="Portföydeki farklı hisse sayısı"
            )

        with col3:
            st.metric(
                "Top 10 Konsantrasyon",
                f"{concentration['top10_concentration']:.1f}%",
                help="İlk 10 hissenin portföy ağırlığı"
            )

        with col4:
            st.metric(
                "Konsantrasyon",
                concentration['concentration_level'],
                help="Portföy konsantrasyon seviyesi"
            )

        st.markdown("---")

        # Portfolio composition
        st.markdown("### 🥧 Portföy Kompozisyonu")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Top 10 Holdings")

            top10 = df_current.nlargest(10, 'portfolio_weight')

            fig_pie = px.pie(
                top10,
                names='ticker',
                values='portfolio_weight',
                title=f"Top 10 Holdings",
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig_pie.update_traces(textinfo='label+percent', textposition='auto')

            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.markdown("#### Sektör Dağılımı")

            sector_alloc = self.analytics.analyze_sector_allocation(df_current)

            fig_sector = px.pie(
                sector_alloc,
                names='sector',
                values='total_weight',
                title="Sector Allocation",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig_sector.update_traces(textinfo='label+percent', textposition='auto')

            st.plotly_chart(fig_sector, use_container_width=True)

        # Top holdings table
        st.markdown("---")
        st.markdown("### 📋 En Büyük Pozisyonlar")

        top_holdings = df_current.nlargest(15, 'portfolio_weight')[
            ['ticker', 'sector', 'shares', 'value_usd', 'portfolio_weight']
        ].copy()

        top_holdings['shares'] = top_holdings['shares'].apply(lambda x: f"{x:,.0f}")
        top_holdings['value_usd'] = top_holdings['value_usd'].apply(lambda x: f"${x/1e6:.1f}M")
        top_holdings['portfolio_weight'] = top_holdings['portfolio_weight'].apply(lambda x: f"{x:.2f}%")

        top_holdings.columns = ['Ticker', 'Sektör', 'Hisse Sayısı', 'Değer', 'Ağırlık']

        st.dataframe(top_holdings, use_container_width=True, hide_index=True)

        # AI Insights
        st.markdown("---")
        st.markdown("### 🤖 AI İçgörüler")

        investor_info = self.analytics.WHALE_INVESTORS[investor_key]
        sector_alloc = self.analytics.analyze_sector_allocation(df_current)
        whale_moves_for_insights = []

        if df_previous is not None:
            changes = self.analytics.calculate_portfolio_changes(df_current, df_previous)
            whale_moves_for_insights = self.analytics.detect_whale_moves(changes, min_weight_change=0.5)

        try:
            insights = generate_all_insights(
                data_type='whale_investor',
                investor_name=investor_info['name'],
                investor_style=investor_info['style'],
                whale_moves=whale_moves_for_insights,
                concentration=concentration,
                sector_alloc=sector_alloc
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
                st.info("💡 İçgörü oluşturmak için daha fazla veri gerekiyor.")
        except Exception as e:
            st.warning(f"⚠️ İçgörü oluşturulurken hata: {str(e)}")

        # Quarter-over-quarter changes
        if df_previous is not None:
            st.markdown("---")
            st.markdown(f"### 📈 Çeyreksel Değişimler ({quarters[previous_idx]} → {current_quarter})")

            changes = self.analytics.calculate_portfolio_changes(df_current, df_previous)
            whale_moves = self.analytics.detect_whale_moves(changes, min_weight_change=0.5)

            # Summary of changes
            col1, col2, col3, col4 = st.columns(4)

            new_positions = (changes['position_status'] == 'NEW').sum()
            sold_positions = (changes['position_status'] == 'SOLD').sum()
            increased = (changes['position_status'] == 'INCREASED').sum()
            decreased = (changes['position_status'] == 'DECREASED').sum()

            with col1:
                st.metric("Yeni Pozisyonlar", new_positions, delta="Açıldı")

            with col2:
                st.metric("Kapatılan Pozisyonlar", sold_positions, delta="Satıldı", delta_color="inverse")

            with col3:
                st.metric("Artırılanlar", increased, delta="↑")

            with col4:
                st.metric("Azaltılanlar", decreased, delta="↓", delta_color="inverse")

            # Whale moves visualization
            st.markdown("#### 🐋 Büyük Hareketler (Whale Signals)")

            if whale_moves:
                # Bar chart of weight changes
                whale_df = pd.DataFrame(whale_moves).nlargest(15, lambda x: abs(x['weight_change']))

                fig_moves = go.Figure()

                colors = ['green' if x > 0 else 'red' for x in whale_df['weight_change']]

                fig_moves.add_trace(go.Bar(
                    x=whale_df['ticker'],
                    y=whale_df['weight_change'],
                    text=[f"{x:+.1f}%" for x in whale_df['weight_change']],
                    textposition='outside',
                    marker_color=colors,
                    name='Ağırlık Değişimi'
                ))

                fig_moves.update_layout(
                    title="Top 15 Portföy Değişimleri (Ağırlık %)",
                    xaxis_title="Ticker",
                    yaxis_title="Ağırlık Değişimi (%)",
                    showlegend=False,
                    height=400
                )

                st.plotly_chart(fig_moves, use_container_width=True)

                # Whale signals table
                st.markdown("#### 🎯 Yatırım Sinyalleri")

                for move in whale_moves[:10]:
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        if move['signal'] in ['STRONG_BUY', 'BUY']:
                            st.success(f"**{move['ticker']}** ({move['sector']}) - {move['signal']}")
                        else:
                            st.error(f"**{move['ticker']}** ({move['sector']}) - {move['signal']}")

                    with col2:
                        st.metric("Ağırlık", f"{move['current_weight']:.2f}%")

                    with col3:
                        st.metric("Değişim", f"{move['weight_change']:+.2f}%")

                    st.markdown(f"_{move['description']}_")
                    st.markdown("---")

            else:
                st.info("Bu dönemde büyük portföy değişikliği tespit edilmedi.")

        # Sector allocation changes
        if df_previous is not None:
            st.markdown("---")
            st.markdown("### 🔄 Sektörel Değişimler")

            sector_curr = self.analytics.analyze_sector_allocation(df_current)
            sector_prev = self.analytics.analyze_sector_allocation(df_previous)

            sector_comp = sector_curr.merge(
                sector_prev,
                on='sector',
                suffixes=('_curr', '_prev')
            )

            sector_comp['weight_change'] = (
                sector_comp['total_weight_curr'] - sector_comp['total_weight_prev']
            )

            sector_comp = sector_comp.sort_values('weight_change', ascending=False)

            fig_sector_change = go.Figure()

            colors = ['green' if x > 0 else 'red' for x in sector_comp['weight_change']]

            fig_sector_change.add_trace(go.Bar(
                x=sector_comp['sector'],
                y=sector_comp['weight_change'],
                text=[f"{x:+.1f}%" for x in sector_comp['weight_change']],
                textposition='outside',
                marker_color=colors
            ))

            fig_sector_change.update_layout(
                title="Sektör Ağırlık Değişimi",
                xaxis_title="Sektör",
                yaxis_title="Ağırlık Değişimi (%)",
                showlegend=False,
                height=350
            )

            st.plotly_chart(fig_sector_change, use_container_width=True)

        # Export data
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            csv = df_current.to_csv(index=False)
            st.download_button(
                label="📥 Mevcut Portföyü İndir (CSV)",
                data=csv,
                file_name=f"{investor_key}_{current_quarter}_holdings.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            if df_previous is not None and whale_moves:
                moves_df = pd.DataFrame(whale_moves)
                csv = moves_df.to_csv(index=False)
                st.download_button(
                    label="📥 Whale Signals İndir (CSV)",
                    data=csv,
                    file_name=f"{investor_key}_{current_quarter}_whale_signals.csv",
                    mime="text/csv",
                    use_container_width=True
                )


def render_whale_investor_analytics():
    """Main function to render Whale Investor Analytics UI"""
    ui = WhaleInvestorAnalyticsUI()
    ui.render()


if __name__ == "__main__":
    render_whale_investor_analytics()
