"""
Portfolio Health Score - Streamlit UI
Visualization and user interface components
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from modules.portfolio_health import PortfolioHealthScore
from modules.insight_engine import generate_all_insights
from io import BytesIO
import base64


class PortfolioHealthUI:
    """Streamlit UI for Portfolio Health Score"""

    def __init__(self):
        self.calculator = PortfolioHealthScore()

    def render(self):
        """Main render function"""
        st.title("📊 Portfolio Health Score")
        st.markdown("""
        **Portföyünüzün sağlık durumunu 8 farklı metrikle analiz edin.**
        Bloomberg Terminal kalitesinde profesyonel analiz.
        """)

        # File upload or use sample
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_file = st.file_uploader(
                "Portföy CSV dosyanızı yükleyin",
                type=['csv'],
                help="Gerekli sütunlar: Symbol, Shares, Price, Value"
            )

        with col2:
            use_sample = st.button("📋 Örnek Portföy Kullan", use_container_width=True, key="portfolio_health____rnek_portf_y_kullan")

        # Load portfolio
        if uploaded_file or use_sample:
            if use_sample:
                portfolio_df = pd.read_csv('sample_data/sample_portfolio.csv')
                st.success("✅ Örnek portföy yüklendi!")
            else:
                portfolio_df = pd.read_csv(uploaded_file)
                st.success("✅ Portföy başarıyla yüklendi!")

            # Display portfolio
            with st.expander("📋 Portföy Detayları"):
                st.dataframe(portfolio_df, use_container_width=True)

            # Calculate health score
            if st.button("🚀 Sağlık Skoru Hesapla", type="primary", use_container_width=True, key="portfolio_health___sa_l_k_skoru_hesapla"):
                with st.spinner("Portföy analiz ediliyor... (Bu 30-60 saniye sürebilir)"):
                    self._calculate_and_display(portfolio_df)

    def _calculate_and_display(self, portfolio_df: pd.DataFrame):
        """Calculate and display health score"""
        try:
            # Load and enrich portfolio
            self.calculator.load_portfolio(portfolio_df)
            enriched_df = self.calculator.enrich_portfolio_data()

            # Calculate metrics
            self.calculator.calculate_all_metrics()
            summary = self.calculator.get_summary()

            # Display results
            self._display_score_overview(summary)
            self._display_metric_breakdown(summary)
            self._display_recommendations(summary)
            self._display_portfolio_analysis(enriched_df, summary)

            # Export buttons
            self._display_export_buttons(enriched_df, summary)

        except Exception as e:
            st.error(f"❌ Hata oluştu: {str(e)}")
            st.info("💡 İpucu: CSV dosyanızın Symbol, Shares, Price, Value sütunlarını içerdiğinden emin olun.")

    def _display_score_overview(self, summary: dict):
        """Display main health score with gauge"""
        st.markdown("---")
        st.subheader("🎯 Genel Sağlık Skoru")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=summary['total_score'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Health Score", 'font': {'size': 24}},
                delta={'reference': 70, 'increasing': {'color': "green"}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': self._get_score_color(summary['total_score'])},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 60], 'color': '#ffebee'},
                        {'range': [60, 80], 'color': '#fff9c4'},
                        {'range': [80, 100], 'color': '#c8e6c9'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))

            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=50, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                font={'color': "darkblue", 'family': "Arial"}
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.metric(
                "Skor",
                f"{summary['total_score']:.1f}/100",
                help="0-100 arası sağlık skoru"
            )
            st.markdown(f"### {summary['grade']}")

        with col3:
            stats = summary['portfolio_stats']
            st.metric("Hisse Sayısı", stats['num_stocks'])
            st.metric("Sektör Sayısı", stats['num_sectors'])
            st.metric("Ortalama Beta", f"{stats['avg_beta']:.2f}")

    def _display_metric_breakdown(self, summary: dict):
        """Display individual metric scores"""
        st.markdown("---")
        st.subheader("📊 Metrik Dağılımı")

        # Radar chart
        metrics = summary['metric_scores']
        metric_names_tr = {
            'diversification': 'Çeşitlendirme',
            'risk': 'Risk Yönetimi',
            'momentum': 'Momentum',
            'liquidity': 'Likidite',
            'tax_efficiency': 'Vergi Verimliliği',
            'balance': 'Denge',
            'duration_fit': 'Süre Uyumu',
            'sector_performance': 'Sektör Performansı'
        }

        # Prepare data
        categories = [metric_names_tr[k] for k in metrics.keys()]
        values = list(metrics.values())

        # Create radar chart
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Portföy',
            line_color='rgb(0, 102, 204)',
            fillcolor='rgba(0, 102, 204, 0.3)'
        ))

        # Add reference line (target: 80)
        fig.add_trace(go.Scatterpolar(
            r=[80] * len(categories),
            theta=categories,
            fill='toself',
            name='Hedef (80)',
            line_color='rgb(34, 139, 34)',
            fillcolor='rgba(34, 139, 34, 0.1)',
            line_dash='dash'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=500,
            title="Metrik Dağılımı (Radar Chart)"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Bar chart for metrics
        col1, col2 = st.columns(2)

        with col1:
            # Horizontal bar chart
            df_metrics = pd.DataFrame({
                'Metrik': categories,
                'Skor': values
            }).sort_values('Skor', ascending=True)

            fig_bar = px.bar(
                df_metrics,
                x='Skor',
                y='Metrik',
                orientation='h',
                color='Skor',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                title="Metrik Skorları"
            )

            fig_bar.update_layout(
                height=400,
                showlegend=False,
                xaxis_title="Skor (0-100)",
                yaxis_title=""
            )

            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            # Display metric details
            st.markdown("#### 📋 Metrik Detayları")

            for metric, score in metrics.items():
                metric_name = metric_names_tr[metric]
                color = self._get_score_color(score)
                emoji = self._get_score_emoji(score)

                st.markdown(f"""
                <div style='padding: 10px; border-left: 4px solid {color}; margin-bottom: 10px; background: rgba(0,0,0,0.02);'>
                    <strong>{emoji} {metric_name}</strong><br>
                    <span style='font-size: 24px; color: {color};'>{score:.1f}</span>/100
                </div>
                """, unsafe_allow_html=True)

    def _display_recommendations(self, summary: dict):
        """Display actionable recommendations"""
        st.markdown("---")
        st.subheader("💡 Öneriler ve İyileştirme Fırsatları")

        recommendations = summary['recommendations']

        if not recommendations:
            st.success("🎉 Tebrikler! Portföyünüz sağlıklı görünüyor. Belirgin bir iyileştirme noktası tespit edilmedi.")
        else:
            st.info(f"**{len(recommendations)} iyileştirme fırsatı tespit edildi:**")

            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"{i}. {rec}")

        # AI-Powered Insights
        st.markdown("---")
        st.subheader("🤖 AI İçgörüler")

        try:
            insights = generate_all_insights(
                data_type='portfolio',
                enriched_df=self.calculator.enriched_data,
                summary=summary
            )

            if insights:
                for insight in insights:
                    # Auto-detect card type from emoji
                    if insight.startswith("🟢"):
                        st.success(insight)
                    elif insight.startswith("⚠️") or insight.startswith("🟡"):
                        st.warning(insight)
                    elif insight.startswith("🔴"):
                        st.error(insight)
                    else:
                        st.info(insight)
            else:
                st.info("ℹ️ Şu anda ek içgörü bulunmuyor.")

        except Exception as e:
            st.warning(f"⚠️ İçgörüler yüklenirken hata: {e}")

        # Additional insights
        stats = summary['portfolio_stats']

        with st.expander("🔍 Detaylı İçgörüler"):
            st.markdown(f"""
            **Portföy Özellikleri:**
            - Toplam Değer: ₺{stats['total_value']:,.2f}
            - Ortalama 3 Aylık Getiri: %{stats['avg_return_3m']:.2f}
            - Ortalama Beta: {stats['avg_beta']:.2f}
            - Sektör Çeşitliliği: {stats['num_sectors']} farklı sektör

            **Skor Yorumu:**
            - **90-100**: Mükemmel - Portföy optimal durumda
            - **80-89**: Çok İyi - Küçük iyileştirmeler yapılabilir
            - **70-79**: İyi - Birkaç alanda gelişme gerekli
            - **60-69**: Orta - Dikkat gerektiren alanlar var
            - **0-59**: Zayıf - Önemli revizyonlar gerekli
            """)

    def _display_portfolio_analysis(self, enriched_df: pd.DataFrame, summary: dict):
        """Display detailed portfolio analysis"""
        st.markdown("---")
        st.subheader("📈 Detaylı Portföy Analizi")

        tab1, tab2, tab3 = st.tabs(["🎯 Pozisyonlar", "📊 Sektör Dağılımı", "⚠️ Risk Analizi"])

        with tab1:
            # Position analysis
            display_df = enriched_df[[
                'Symbol', 'Shares', 'Price', 'Value', 'Weight',
                'Sector', 'Beta', 'Return_3M', 'Volatility'
            ]].copy()

            display_df['Weight'] = display_df['Weight'].apply(lambda x: f"{x*100:.1f}%")
            display_df['Return_3M'] = display_df['Return_3M'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
            display_df['Volatility'] = display_df['Volatility'].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")
            display_df['Beta'] = display_df['Beta'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

            st.dataframe(
                display_df.sort_values('Value', ascending=False),
                use_container_width=True,
                height=400
            )

        with tab2:
            # Sector distribution
            sector_df = enriched_df.groupby('Sector').agg({
                'Value': 'sum',
                'Weight': 'sum',
                'Return_3M': lambda x: (x * enriched_df.loc[x.index, 'Weight']).sum() / enriched_df.loc[x.index, 'Weight'].sum()
            }).reset_index()

            sector_df.columns = ['Sektör', 'Toplam Değer', 'Ağırlık', 'Ort. Getiri']

            # Pie chart
            fig_pie = px.pie(
                sector_df,
                values='Toplam Değer',
                names='Sektör',
                title='Sektör Dağılımı',
                hole=0.4
            )

            st.plotly_chart(fig_pie, use_container_width=True)

            # Sector table
            sector_df['Ağırlık'] = sector_df['Ağırlık'].apply(lambda x: f"{x*100:.1f}%")
            sector_df['Ort. Getiri'] = sector_df['Ort. Getiri'].apply(lambda x: f"{x:.1f}%")
            sector_df['Toplam Değer'] = sector_df['Toplam Değer'].apply(lambda x: f"₺{x:,.0f}")

            st.dataframe(sector_df, use_container_width=True, hide_index=True)

        with tab3:
            # Risk analysis
            col1, col2 = st.columns(2)

            with col1:
                # Beta distribution
                fig_beta = px.scatter(
                    enriched_df,
                    x='Beta',
                    y='Volatility',
                    size='Value',
                    color='Return_3M',
                    hover_data=['Symbol', 'Sector'],
                    title='Risk Haritası (Beta vs Volatilite)',
                    labels={
                        'Beta': 'Beta (Piyasa Riski)',
                        'Volatility': 'Volatilite (Yıllık)',
                        'Return_3M': '3 Aylık Getiri'
                    },
                    color_continuous_scale='RdYlGn'
                )

                fig_beta.add_hline(y=enriched_df['Volatility'].median(), line_dash="dash", line_color="gray")
                fig_beta.add_vline(x=1.0, line_dash="dash", line_color="gray")

                st.plotly_chart(fig_beta, use_container_width=True)

            with col2:
                # Risk metrics
                st.markdown("#### ⚠️ Risk Metrikleri")

                avg_beta = (enriched_df['Beta'] * enriched_df['Weight']).sum()
                avg_vol = (enriched_df['Volatility'] * enriched_df['Weight']).sum()
                max_drawdown = enriched_df['Return_3M'].min()

                st.metric("Ortalama Beta", f"{avg_beta:.2f}")
                st.metric("Ortalama Volatilite", f"{avg_vol*100:.1f}%")
                st.metric("En Kötü Performans (3M)", f"{max_drawdown:.1f}%")

                # Risk interpretation
                if avg_beta > 1.3:
                    st.warning("⚠️ Portföy yüksek piyasa riskine sahip")
                elif avg_beta < 0.7:
                    st.info("ℹ️ Portföy savunma ağırlıklı")
                else:
                    st.success("✅ Portföy dengeli risk profiline sahip")

    def _display_export_buttons(self, enriched_df: pd.DataFrame, summary: dict):
        """Display export buttons"""
        st.markdown("---")
        st.subheader("📤 Dışa Aktar")

        col1, col2 = st.columns(2)

        with col1:
            # Excel export
            excel_buffer = self._create_excel_report(enriched_df, summary)
            st.download_button(
                label="📊 Excel Raporu İndir",
                data=excel_buffer,
                file_name=f"portfolio_health_report_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            # CSV export
            csv_buffer = enriched_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 CSV İndir",
                data=csv_buffer,
                file_name=f"portfolio_analysis_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    def _create_excel_report(self, enriched_df: pd.DataFrame, summary: dict) -> BytesIO:
        """Create Excel report with multiple sheets"""
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame({
                'Metrik': ['Toplam Skor', 'Not', 'Hisse Sayısı', 'Sektör Sayısı', 'Ortalama Beta', 'Ortalama Getiri (3M)'],
                'Değer': [
                    f"{summary['total_score']:.1f}/100",
                    summary['grade'],
                    summary['portfolio_stats']['num_stocks'],
                    summary['portfolio_stats']['num_sectors'],
                    f"{summary['portfolio_stats']['avg_beta']:.2f}",
                    f"{summary['portfolio_stats']['avg_return_3m']:.2f}%"
                ]
            })
            summary_df.to_excel(writer, sheet_name='Özet', index=False)

            # Metric scores sheet
            metrics_df = pd.DataFrame({
                'Metrik': list(summary['metric_scores'].keys()),
                'Skor': list(summary['metric_scores'].values())
            })
            metrics_df.to_excel(writer, sheet_name='Metrik Skorları', index=False)

            # Portfolio details
            enriched_df.to_excel(writer, sheet_name='Portföy Detayları', index=False)

            # Recommendations
            if summary['recommendations']:
                rec_df = pd.DataFrame({
                    'Öneri': summary['recommendations']
                })
                rec_df.to_excel(writer, sheet_name='Öneriler', index=False)

        output.seek(0)
        return output

    def _get_score_color(self, score: float) -> str:
        """Get color based on score"""
        if score >= 80:
            return '#4CAF50'  # Green
        elif score >= 60:
            return '#FFC107'  # Yellow
        else:
            return '#F44336'  # Red

    def _get_score_emoji(self, score: float) -> str:
        """Get emoji based on score"""
        if score >= 90:
            return '🏆'
        elif score >= 80:
            return '✅'
        elif score >= 70:
            return '👍'
        elif score >= 60:
            return '⚠️'
        else:
            return '❌'
