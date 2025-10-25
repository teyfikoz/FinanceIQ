"""
Whale Correlation Engine UI - Interactive correlation analysis interface
Compare whale investors and analyze user portfolio DNA
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Optional

import numpy as np

from modules.whale_correlation import WhaleCorrelationEngine, quick_correlation_analysis
from modules.whale_investor_analytics import WhaleInvestorAnalytics
from modules.insight_engine import generate_all_insights


class WhaleCorrelationUI:
    """Streamlit UI for Whale Correlation Engine"""

    def __init__(self):
        self.engine = WhaleCorrelationEngine()
        self.whale_analytics = WhaleInvestorAnalytics()

    def render(self):
        """Main render method for Whale Correlation UI"""

        st.markdown("""
        ## 🔗 Whale Correlation Engine

        **Balina yatırımcılar arası ilişkileri keşfedin:**
        - 📊 Portföy korelasyon matrisi
        - 🕸️ Yatırımcı ilişki ağı (network graph)
        - 🧬 Yatırım DNA benzerliği
        - 🤝 Ortak holding analizi
        - 👤 Kendi portföyünüzü balinalara kıyaslayın

        **Kullanım:** "Smart money" arasındaki ilişkileri görün, hangi yatırımcılar
        benzer stratejiler izliyor öğrenin!
        """)

        st.markdown("---")

        # Quarter selection
        col1, col2 = st.columns([1, 3])

        with col1:
            quarters = ['2024Q3', '2024Q4']
            selected_quarter = st.selectbox("Dönem Seç", quarters, index=1, key="whale_corr_quarter")

        with col2:
            # Investor selection
            all_investors = list(self.whale_analytics.WHALE_INVESTORS.keys())

            selected_investors = st.multiselect(
                "Analiz edilecek yatırımcıları seçin (en az 2)",
                options=all_investors,
                default=['buffett', 'gates', 'wood', 'dalio'],
                format_func=lambda x: f"{self.whale_analytics.WHALE_INVESTORS[x]['icon']} {self.whale_analytics.WHALE_INVESTORS[x]['name']}",
                key="whale_corr_investors"
            )

        # User portfolio upload (optional)
        st.markdown("### 👤 Kendi Portföyünüz (Opsiyonel)")

        uploaded_file = st.file_uploader(
            "Portföyünüzü yükleyin (CSV: ticker, portfolio_weight kolonları gerekli)",
            type=['csv'],
            help="Örnek: ticker,portfolio_weight\\nAAPL,15.5\\nMSFT,12.3",
            key="user_portfolio_upload"
        )

        user_df = None
        if uploaded_file is not None:
            try:
                user_df = pd.read_csv(uploaded_file)
                if 'ticker' not in user_df.columns or 'portfolio_weight' not in user_df.columns:
                    st.error("❌ CSV dosyası 'ticker' ve 'portfolio_weight' kolonlarını içermelidir.")
                    user_df = None
                else:
                    st.success(f"✅ Portföy yüklendi: {len(user_df)} holding")
            except Exception as e:
                st.error(f"❌ Dosya okuma hatası: {str(e)}")
                user_df = None

        # Analysis button
        if st.button("🔍 Korelasyon Analizi Yap", type="primary", use_container_width=True, key="whale_correlation___korelasyon_analizi_yap"):
            if len(selected_investors) < 2:
                st.error("❌ En az 2 yatırımcı seçmelisiniz.")
                return

            with st.spinner("Whale korelasyonları analiz ediliyor..."):
                self._analyze_and_display(selected_investors, selected_quarter, user_df)

    def _analyze_and_display(
        self,
        selected_investors: list,
        quarter: str,
        user_df: Optional[pd.DataFrame]
    ):
        """Analyze and display correlation results"""

        # Load whale data
        whale_data_dict = {}

        for investor_key in selected_investors:
            df = self.whale_analytics.load_whale_data(investor_key, quarter)
            if df is not None and len(df) > 0:
                investor_name = self.whale_analytics.WHALE_INVESTORS[investor_key]['name']
                whale_data_dict[investor_name] = df

        if len(whale_data_dict) < 2:
            st.error("❌ Yeterli veri yüklenemedi. En az 2 yatırımcı için veri gerekli.")
            return

        # Run analysis
        results = quick_correlation_analysis(whale_data_dict, user_df)

        # Display results
        self._display_correlation_matrix(results['correlation_matrix'])
        self._display_overlap_analysis(whale_data_dict)
        self._display_network_graph(results['correlation_matrix'])
        self._display_top_pairs(results['top_pairs'])
        self._display_clusters(results['clusters'])

        if user_df is not None and 'user_dna' in results:
            self._display_user_dna(results['user_dna'])

        # AI Insights
        self._display_insights(results, whale_data_dict)

    def _display_correlation_matrix(self, corr_matrix: pd.DataFrame):
        """Display correlation heatmap"""

        st.markdown("---")
        st.markdown("### 📊 Portföy Korelasyon Matrisi")

        st.markdown("""
        **Nasıl okunur:**
        - 🟢 **Yeşil (0.6-1.0)**: Yüksek korelasyon - benzer portföyler
        - 🟡 **Sarı (0.3-0.6)**: Orta korelasyon - kısmen benzer
        - 🔴 **Kırmızı (-1.0-0.3)**: Düşük/negatif korelasyon - farklı stratejiler
        """)

        fig = self.engine.plot_correlation_heatmap(corr_matrix)
        st.plotly_chart(fig, use_container_width=True)

        # Summary stats
        avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
        max_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].max()
        min_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].min()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Ortalama Korelasyon", f"{avg_corr:.2f}")

        with col2:
            st.metric("Maksimum Korelasyon", f"{max_corr:.2f}")

        with col3:
            st.metric("Minimum Korelasyon", f"{min_corr:.2f}")

    def _display_overlap_analysis(self, whale_data_dict: Dict[str, pd.DataFrame]):
        """Display portfolio overlap analysis"""

        st.markdown("---")
        st.markdown("### 🤝 Ortak Holdings Analizi")

        overlap_matrix = self.engine.build_overlap_matrix(whale_data_dict)

        fig = self.engine.plot_overlap_heatmap(overlap_matrix)
        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        💡 **Overlap %**: İki yatırımcının portföylerinde ortak olan
        hisselerin tüm benzersiz hisselere oranı.

        Örnek: Buffett 50 hisse, Gates 40 hisse, ortak 20 hisse → Overlap = 20/70 = 28.6%
        """)

    def _display_network_graph(self, corr_matrix: pd.DataFrame):
        """Display whale relationship network"""

        st.markdown("---")
        st.markdown("### 🕸️ Whale Relationship Network")

        # Threshold slider
        threshold = st.slider(
            "Korelasyon eşiği (minimum bağlantı gücü)",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            key="network_threshold"
        )

        st.markdown(f"""
        **Görselleştirme:**
        - 🔵 **Düğümler**: Yatırımcılar
        - 📏 **Çizgi kalınlığı**: Korelasyon gücü
        - 🔗 **Bağlantı**: Korelasyon ≥ {threshold:.2f}

        Yakın düğümler = benzer yatırım stratejileri
        """)

        fig = self.engine.plot_whale_network(
            corr_matrix,
            threshold=threshold,
            title=f"Whale Network (threshold={threshold:.2f})"
        )
        st.plotly_chart(fig, use_container_width=True)

    def _display_top_pairs(self, top_pairs: list):
        """Display top correlated pairs"""

        st.markdown("---")
        st.markdown("### 🏆 En Yüksek Korelasyonlu İkili")

        for i, pair in enumerate(top_pairs[:5], 1):
            corr = pair['correlation']
            interpretation = self.engine.get_correlation_interpretation(corr)

            # Color coding
            if corr >= 0.7:
                color = "🟢"
            elif corr >= 0.5:
                color = "🟡"
            else:
                color = "🔴"

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                {i}. {color} **{pair['investor_a']}** ⟷ **{pair['investor_b']}**

                _{interpretation}_
                """)

            with col2:
                st.metric("Korelasyon", f"{corr:.3f}")

            st.markdown("---")

    def _display_clusters(self, clusters: list):
        """Display investor clusters"""

        st.markdown("### 🎯 Yatırımcı Kümeleri")

        if not clusters or all(len(c) <= 1 for c in clusters):
            st.info("💡 Belirgin küme tespit edilmedi. Yatırımcılar birbirinden bağımsız hareket ediyor.")
            return

        st.markdown("""
        **Küme**: Birbirine benzer portföy stratejisi izleyen yatırımcı grupları.
        Aynı kümede olmak, benzer risk/getiri profiline sahip olduğunuzu gösterir.
        """)

        for i, cluster in enumerate(clusters, 1):
            if len(cluster) > 1:
                st.success(f"""
                **Küme {i}**: {', '.join(cluster)}

                _{len(cluster)} yatırımcı - Benzer strateji_
                """)

    def _display_user_dna(self, user_dna: dict):
        """Display user DNA analysis results"""

        st.markdown("---")
        st.markdown("### 🧬 Yatırım DNA Analizi")

        st.markdown(f"""
        ## {user_dna['top_match']} ile **%{user_dna['similarity_score']:.1f}** benzerlik!
        """)

        # Similarity breakdown
        st.markdown("#### 📊 Tüm Yatırımcılara Benzerlik")

        df = user_dna['similarity_breakdown']

        # Create bar chart
        fig = go.Figure()

        colors = ['#667eea' if i == 0 else '#cccccc' for i in range(len(df))]

        fig.add_trace(go.Bar(
            x=df['Investor'],
            y=df['Similarity_Score'],
            text=[f"{x:.1f}%" for x in df['Similarity_Score']],
            textposition='outside',
            marker_color=colors,
            hovertemplate='<b>%{x}</b><br>Similarity: %{y:.1f}%<br>Common: %{customdata} holdings<extra></extra>',
            customdata=df['Common_Holdings']
        ))

        fig.update_layout(
            title="Portföy Benzerlik Skoru",
            xaxis_title="Yatırımcı",
            yaxis_title="Benzerlik Skoru (%)",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Detailed table
        with st.expander("📋 Detaylı Karşılaştırma"):
            st.dataframe(df, use_container_width=True, hide_index=True)

        # Recommendations
        st.markdown("#### 💡 DNA Önerileri")

        for rec in user_dna['recommendations']:
            if rec.startswith("🎯"):
                st.success(rec)
            elif rec.startswith("🔍"):
                st.info(rec)
            else:
                st.warning(rec)

    def _display_insights(self, results: dict, whale_data_dict: dict):
        """Display AI-generated insights"""

        st.markdown("---")
        st.markdown("### 🤖 AI İçgörüler")

        try:
            # Generate insights
            insights = generate_all_insights(
                data_type='whale_correlation',
                correlation_matrix=results['correlation_matrix'],
                top_pairs=results['top_pairs'],
                clusters=results['clusters'],
                num_investors=results['num_investors']
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


def render_whale_correlation():
    """Main function to render Whale Correlation UI"""
    ui = WhaleCorrelationUI()
    ui.render()


if __name__ == "__main__":
    render_whale_correlation()
