"""
ETF-Whale Linkage UI - Interactive interface for ETF-whale overlap analysis
Visualizes passive/active investment ratios and institutional alignment
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict

from modules.etf_whale_linkage import ETFWhaleLinkage, quick_etf_whale_linkage
from modules.whale_investor_analytics import WhaleInvestorAnalytics


class ETFWhaleLinkageUI:
    """Streamlit UI for ETF-Whale Linkage analyzer"""

    def __init__(self):
        self.linkage = ETFWhaleLinkage()
        self.whale_analytics = WhaleInvestorAnalytics()

    def render(self):
        """Main render method"""

        st.markdown("""
        ## 🔗 ETF-Whale Linkage Analyzer

        **ETF ve whale portföyleri arasındaki çakışmaları keşfedin:**
        - 📊 QQQ, SPY, ARKK gibi major ETF'lerin whale portföyleriyle overlap'i
        - 🎯 Passive vs Active yatırım yo ğunluğu
        - 💼 Portföyünüzde ne kadar passive, ne kadar active pozisyon var?
        - 🔍 Hangi whale hangi ETF'e yakın?

        **Kullanım:** Kendi yatırım tarzınızı anlayın - passive mi, active mi?
        """)

        st.markdown("---")

        # Investor and period selection
        col1, col2 = st.columns([1, 2])

        with col1:
            quarters = ['2024Q3', '2024Q4']
            quarter = st.selectbox("Dönem", quarters, index=1, key="etf_whale_quarter")

        with col2:
            all_investors = list(self.whale_analytics.WHALE_INVESTORS.keys())
            selected_investors = st.multiselect(
                "Whale yatırımcılar",
                options=all_investors,
                default=['buffett', 'gates', 'wood', 'dalio'],
                format_func=lambda x: f"{self.whale_analytics.WHALE_INVESTORS[x]['icon']} {self.whale_analytics.WHALE_INVESTORS[x]['name']}",
                key="etf_whale_investors"
            )

        # User portfolio upload
        st.markdown("### 👤 Kendi Portföyünüz (Opsiyonel)")
        uploaded_file = st.file_uploader(
            "CSV yükleyin (ticker, portfolio_weight kolonları)",
            type=['csv'],
            key="etf_whale_user_upload"
        )

        user_df = None
        if uploaded_file:
            try:
                user_df = pd.read_csv(uploaded_file)
                if 'ticker' in user_df.columns and 'portfolio_weight' in user_df.columns:
                    st.success(f"✅ {len(user_df)} holding yüklendi")
                else:
                    st.error("❌ 'ticker' ve 'portfolio_weight' kolonları gerekli")
                    user_df = None
            except:
                st.error("❌ Dosya okunamadı")

        # Analyze button
        if st.button("🔍 ETF-Whale Linkage Analizi", type="primary", use_container_width=True, key="etf_whale_linkage___etf_whale_linkage_analizi"):
            if len(selected_investors) < 2:
                st.error("❌ En az 2 yatırımcı seçin")
                return

            with st.spinner("ETF-whale ilişkileri analiz ediliyor..."):
                self._analyze_and_display(selected_investors, quarter, user_df)

    def _analyze_and_display(self, selected_investors, quarter, user_df):
        """Analyze and display results"""

        # Load whale data
        whale_data = {}
        for inv_key in selected_investors:
            df = self.whale_analytics.load_whale_data(inv_key, quarter)
            if df is not None and len(df) > 0:
                name = self.whale_analytics.WHALE_INVESTORS[inv_key]['name']
                whale_data[name] = df

        if len(whale_data) < 2:
            st.error("❌ Yeterli veri yüklenemedi")
            return

        # Run analysis
        results = quick_etf_whale_linkage(whale_data, user_df)

        # Display results
        self._display_overview(results)
        self._display_whale_etf_matrix(results['alignment_analysis'])
        self._display_top_overlaps(results['top_overlaps'])
        self._display_etf_concentrations(results['etf_concentrations'])

        if user_df is not None and 'user_passive_active' in results:
            self._display_user_analysis(results['user_passive_active'])

    def _display_overview(self, results):
        """Display overview metrics"""
        st.markdown("---")
        st.markdown("### 📊 Genel Bakış")

        alignment = results['alignment_analysis']

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("ETF Analiz Edildi", alignment['etf_ticker'].nunique())

        with col2:
            st.metric("Whale Analiz Edildi", alignment['whale_name'].nunique())

        with col3:
            avg_overlap = alignment['overlap_pct'].mean()
            st.metric("Avg Overlap", f"{avg_overlap:.1f}%")

        with col4:
            max_exposure = alignment['whale_exposure_to_all_etf'].max()
            st.metric("Max Exposure", f"{max_exposure:.1f}%")

    def _display_whale_etf_matrix(self, alignment):
        """Display whale-ETF overlap matrix"""
        st.markdown("---")
        st.markdown("### 🔥 Whale-ETF Overlap Matrix")

        # Pivot for heatmap
        pivot = alignment.pivot(
            index='whale_name',
            columns='etf_ticker',
            values='whale_exposure_to_all_etf'
        ).fillna(0)

        fig = px.imshow(
            pivot,
            color_continuous_scale='YlOrRd',
            aspect='auto',
            title="Whale Portfolio Exposure to ETFs (%)"
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 **Yorumlama:** Yüksek değer = whale'in portföyü o ETF'in holdings'leriyle yüksek overlap")

    def _display_top_overlaps(self, top_overlaps):
        """Display top whale-ETF overlaps"""
        st.markdown("---")
        st.markdown("### 🏆 En Yüksek Overlap'lar")

        display_df = top_overlaps[['etf_ticker', 'whale_name', 'whale_exposure_to_all_etf', 'num_common']].copy()
        display_df.columns = ['ETF', 'Whale', 'Exposure %', 'Common Holdings']
        display_df['Exposure %'] = display_df['Exposure %'].apply(lambda x: f"{x:.1f}%")

        st.dataframe(display_df.head(10), use_container_width=True, hide_index=True)

    def _display_etf_concentrations(self, concentrations):
        """Display ETF concentration analysis"""
        st.markdown("---")
        st.markdown("### 🎯 ETF Konsantrasyonları")

        for etf, whales in concentrations.items():
            st.markdown(f"#### {etf} - {self.linkage.major_etfs[etf]['name']}")

            for whale in whales[:5]:
                level_color = "🔴" if whale['concentration_level'] == 'HIGH' else "🟡"
                st.markdown(f"{level_color} **{whale['whale_name']}**: {whale['exposure']:.1f}% exposure ({whale['num_common']} holdings)")

    def _display_user_analysis(self, passive_active):
        """Display user passive/active analysis"""
        st.markdown("---")
        st.markdown("### 👤 Sizin Portföy Analizi")

        st.markdown(f"""
        **Yatırım Tarzı:** {passive_active['investment_style']}
        """)

        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['Passive', 'Active'],
            values=[passive_active['passive_ratio'], passive_active['active_ratio']],
            marker=dict(colors=['lightblue', 'orange'])
        )])

        fig.update_layout(title="Passive vs Active Ratio", height=350)
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Passive Stocks", passive_active['num_passive_stocks'])
            st.metric("Passive Weight", f"{passive_active['passive_weight']:.1f}%")

        with col2:
            st.metric("Active Stocks", passive_active['num_active_stocks'])
            st.metric("Active Weight", f"{passive_active['active_weight']:.1f}%")


def render_etf_whale_linkage():
    """Main render function"""
    ui = ETFWhaleLinkageUI()
    ui.render()


if __name__ == "__main__":
    render_etf_whale_linkage()
