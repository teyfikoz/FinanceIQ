"""
Fund Flow Radar UI - Track institutional money flows
Interactive interface for analyzing fund flow patterns
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
from datetime import datetime, timedelta

from modules.fund_flow_radar import FundFlowRadar
from modules.insight_engine import generate_all_insights


class FundFlowRadarUI:
    """Streamlit UI for Fund Flow Radar module"""

    def __init__(self):
        self.radar = FundFlowRadar()

    def render(self):
        """Main render method for Fund Flow Radar UI"""

        st.markdown("""
        ## 📡 Fund Flow Radar

        **Kurumsal yatırımcıların para akışlarını takip edin:**
        - 💰 Hangi sektörlere para giriyor/çıkıyor?
        - 📊 TEFAS fonları günlük akış analizi
        - 🎯 Kurumsal yatırımcı davranış sinyalleri
        - 🔍 Anormal akış tespiti

        **Kullanım:** Para akışı, fiyat hareketinden önce gelir - smart money'yi takip edin!
        """)

        st.markdown("---")

        # Period and fund selection
        col1, col2 = st.columns([1, 2])

        with col1:
            period = st.selectbox(
                "Analiz Dönemi",
                options=['7d', '30d', '90d', 'ytd'],
                format_func=lambda x: {
                    '7d': 'Son 7 Gün',
                    '30d': 'Son 30 Gün',
                    '90d': 'Son 3 Ay',
                    'ytd': 'Yıl Başından Beri'
                }[x],
                index=1
            )

            fund_category = st.selectbox(
                "Fon Kategorisi",
                options=[
                    'Hisse Senedi Fonları',
                    'Tahvil Bono Fonları',
                    'Değişken Fonlar',
                    'Para Piyasası Fonları',
                    'Tümü'
                ]
            )

        with col2:
            st.info("""
            **💡 İpucu:**
            - **Pozitif akış** = Yatırımcılar o sektöre para yatırıyor (bullish sinyal)
            - **Negatif akış** = Yatırımcılar o sektörden para çekiyor (bearish sinyal)
            - **Anormal akışlar** = Potansiyel trend değişimi
            """)

        # Fetch and analyze data
        if st.button("🔍 Analiz Et", type="primary", use_container_width=True):
            with st.spinner("Para akışları analiz ediliyor..."):
                # Sample data for demonstration
                analysis_results = self._run_flow_analysis(period, fund_category)

                if analysis_results:
                    self._display_flow_analysis(analysis_results, period)

    def _run_flow_analysis(self, period: str, category: str) -> Dict:
        """Run flow analysis for given period and category"""

        # Calculate date range
        end_date = datetime.now()

        if period == '7d':
            start_date = end_date - timedelta(days=7)
        elif period == '30d':
            start_date = end_date - timedelta(days=30)
        elif period == '90d':
            start_date = end_date - timedelta(days=90)
        elif period == 'ytd':
            start_date = datetime(end_date.year, 1, 1)
        else:
            start_date = end_date - timedelta(days=30)

        # Sample fund codes (in production, filter by category)
        fund_codes = self.radar.MAJOR_TEFAS_FUNDS[:10]

        # Fetch fund data
        fund_flows = self.radar.fetch_multiple_funds(
            fund_codes,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        if not fund_flows:
            st.error("Veri alınamadı. Lütfen tekrar deneyin.")
            return None

        # Mock sector mapping (in production, use real categorization)
        fund_sectors = {
            'AAV': 'Teknoloji', 'AEH': 'Finans', 'AFT': 'Sanayi',
            'AHE': 'Tüketim', 'AHU': 'Finans', 'AJZ': 'Teknoloji',
            'AKU': 'Sanayi', 'YAT': 'Mixed', 'GAH': 'Finans',
            'GBH': 'Tüketim'
        }

        # Aggregate by sector
        sector_flows = self.radar.aggregate_sector_flows(
            fund_flows,
            fund_sectors,
            period
        )

        # Generate signals
        signals = self.radar.generate_flow_signals(sector_flows)

        # Detect anomalies (use first fund as example)
        anomalies = []
        for fund_code, flow_df in list(fund_flows.items())[:3]:
            fund_anomalies = self.radar.detect_flow_anomalies(flow_df, threshold_std=2.0)
            for anomaly in fund_anomalies:
                anomaly['fund_code'] = fund_code
                anomalies.append(anomaly)

        return {
            'sector_flows': sector_flows,
            'signals': signals,
            'fund_flows': fund_flows,
            'fund_sectors': fund_sectors,
            'anomalies': anomalies
        }

    def _display_flow_analysis(self, results: Dict, period: str):
        """Display flow analysis results"""

        sector_flows = results['sector_flows']
        signals = results['signals']
        fund_flows = results['fund_flows']
        fund_sectors = results['fund_sectors']
        anomalies = results['anomalies']

        # Summary metrics
        st.markdown("### 📊 Genel Bakış")

        col1, col2, col3, col4 = st.columns(4)

        total_inflow = sector_flows[sector_flows['net_flow'] > 0]['net_flow'].sum()
        total_outflow = abs(sector_flows[sector_flows['net_flow'] < 0]['net_flow'].sum())
        net_flow = sector_flows['net_flow'].sum()

        with col1:
            st.metric(
                "Toplam Giriş",
                f"₺{total_inflow/1_000_000:.1f}M",
                delta="Para giren sektörler"
            )

        with col2:
            st.metric(
                "Toplam Çıkış",
                f"₺{total_outflow/1_000_000:.1f}M",
                delta="Para çıkan sektörler",
                delta_color="inverse"
            )

        with col3:
            st.metric(
                "Net Akış",
                f"₺{net_flow/1_000_000:+.1f}M",
                delta="Genel piyasa durumu"
            )

        with col4:
            st.metric(
                "Aktif Sinyal",
                len(signals),
                delta=f"{len([s for s in signals if s['strength'] == 'STRONG'])} güçlü"
            )

        st.markdown("---")

        # Top inflows and outflows
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ⬆️ En Çok Para Giren Sektörler")

            top_inflows = sector_flows[sector_flows['net_flow'] > 0].nlargest(5, 'net_flow')

            if len(top_inflows) > 0:
                # Bar chart
                fig = px.bar(
                    top_inflows,
                    x='net_flow',
                    y='sector',
                    orientation='h',
                    text=top_inflows['net_flow'].apply(lambda x: f"₺{x/1_000_000:.1f}M"),
                    color='net_flow',
                    color_continuous_scale='Greens'
                )

                fig.update_layout(
                    showlegend=False,
                    height=300,
                    xaxis_title="Net Akış (₺)",
                    yaxis_title="",
                    coloraxis_showscale=False
                )

                fig.update_traces(textposition='outside')

                st.plotly_chart(fig, use_container_width=True)

                # Table
                display_inflows = top_inflows[['sector', 'net_flow', 'num_funds']].copy()
                display_inflows['net_flow'] = display_inflows['net_flow'].apply(lambda x: f"₺{x/1_000_000:.1f}M")
                display_inflows.columns = ['Sektör', 'Net Akış', 'Fon Sayısı']

                st.dataframe(display_inflows, use_container_width=True, hide_index=True)
            else:
                st.info("Bu dönemde giriş yapan sektör yok.")

        with col2:
            st.markdown("#### ⬇️ En Çok Para Çıkan Sektörler")

            top_outflows = sector_flows[sector_flows['net_flow'] < 0].nsmallest(5, 'net_flow')

            if len(top_outflows) > 0:
                # Bar chart
                fig = px.bar(
                    top_outflows,
                    x='net_flow',
                    y='sector',
                    orientation='h',
                    text=top_outflows['net_flow'].apply(lambda x: f"₺{abs(x)/1_000_000:.1f}M"),
                    color='net_flow',
                    color_continuous_scale='Reds'
                )

                fig.update_layout(
                    showlegend=False,
                    height=300,
                    xaxis_title="Net Akış (₺)",
                    yaxis_title="",
                    coloraxis_showscale=False
                )

                fig.update_traces(textposition='outside')

                st.plotly_chart(fig, use_container_width=True)

                # Table
                display_outflows = top_outflows[['sector', 'net_flow', 'num_funds']].copy()
                display_outflows['net_flow'] = display_outflows['net_flow'].apply(lambda x: f"₺{abs(x)/1_000_000:.1f}M")
                display_outflows.columns = ['Sektör', 'Net Akış', 'Fon Sayısı']

                st.dataframe(display_outflows, use_container_width=True, hide_index=True)
            else:
                st.info("Bu dönemde çıkış yapan sektör yok.")

        # Sankey diagram
        st.markdown("---")
        st.markdown("### 🔀 Para Akış Haritası")

        fig_sankey = self.radar.create_flow_sankey(sector_flows, min_flow_threshold=0)
        st.plotly_chart(fig_sankey, use_container_width=True)

        # Flow heatmap
        st.markdown("---")
        st.markdown("### 🔥 Zamana Göre Akış Yoğunluğu")

        fig_heatmap = self.radar.create_flow_heatmap(fund_flows, fund_sectors)
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # AI Insights
        st.markdown("---")
        st.markdown("### 🤖 AI İçgörüler")

        try:
            insights = generate_all_insights(
                data_type='fund_flow',
                sector_flows=sector_flows,
                signals=signals,
                anomalies=anomalies
            )

            if insights:
                for insight in insights:
                    if insight.startswith("🟢"):
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

        # Investment signals
        st.markdown("---")
        st.markdown("### 🎯 Yatırım Sinyalleri")

        if signals:
            signal_df = pd.DataFrame(signals)

            for _, signal in signal_df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    if signal['signal'] == 'BULLISH':
                        st.success(f"**{signal['sector']}** - {signal['strength']} ALIŞ SİNYALİ")
                    else:
                        st.error(f"**{signal['sector']}** - {signal['strength']} SATIŞ SİNYALİ")

                with col2:
                    st.metric("Akış", f"₺{abs(signal['flow_amount'])/1_000_000:.1f}M")

                with col3:
                    st.metric("Oran", f"{signal['flow_pct']:.1f}%")

                st.markdown(f"""
                **Açıklama:** {signal['num_funds']} fon bu sektörde
                {'para biriktiriyor' if signal['signal'] == 'BULLISH' else 'para çekiyor'}.
                Akış oranı toplam akışın %{abs(signal['flow_pct']):.1f}'i.
                """)

                st.markdown("---")
        else:
            st.info("Bu dönemde güçlü sinyal yok.")

        # Anomalies
        if anomalies:
            st.markdown("### ⚠️ Anormal Akışlar")

            anomaly_df = pd.DataFrame(anomalies)

            st.markdown(f"""
            **{len(anomalies)} anormal akış** tespit edildi (>2 standart sapma).
            Bunlar potansiyel trend değişimine işaret edebilir.
            """)

            display_anomalies = anomaly_df[['date', 'fund_code', 'type', 'net_flow', 'magnitude']].copy()
            display_anomalies['date'] = pd.to_datetime(display_anomalies['date']).dt.strftime('%Y-%m-%d')
            display_anomalies['net_flow'] = display_anomalies['net_flow'].apply(lambda x: f"₺{x/1_000_000:+.1f}M")
            display_anomalies['type'] = display_anomalies['type'].map({
                'massive_inflow': '🟢 Büyük Giriş',
                'massive_outflow': '🔴 Büyük Çıkış'
            })
            display_anomalies['magnitude'] = display_anomalies['magnitude'].apply(lambda x: f"{x:.1f}σ")

            display_anomalies.columns = ['Tarih', 'Fon', 'Tip', 'Miktar', 'Şiddet']

            st.dataframe(display_anomalies, use_container_width=True, hide_index=True)

        # Export data
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            # Export sector flows
            csv = sector_flows.to_csv(index=False)
            st.download_button(
                label="📥 Sektör Akışlarını İndir (CSV)",
                data=csv,
                file_name=f"sector_flows_{period}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            # Export signals
            if signals:
                signals_df = pd.DataFrame(signals)
                csv = signals_df.to_csv(index=False)
                st.download_button(
                    label="📥 Sinyalleri İndir (CSV)",
                    data=csv,
                    file_name=f"flow_signals_{period}.csv",
                    mime="text/csv",
                    use_container_width=True
                )


def render_fund_flow_radar():
    """Main function to render Fund Flow Radar UI"""
    ui = FundFlowRadarUI()
    ui.render()


if __name__ == "__main__":
    render_fund_flow_radar()
