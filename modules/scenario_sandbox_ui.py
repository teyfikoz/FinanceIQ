"""
Scenario Sandbox UI - Interactive scenario simulation interface
Allows users to test portfolio performance under different macro scenarios
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
import numpy as np

from modules.scenario_sandbox import ScenarioSandbox
from modules.insight_engine import generate_all_insights


class ScenarioSandboxUI:
    """Streamlit UI for Scenario Sandbox module"""

    def __init__(self):
        self.sandbox = ScenarioSandbox()

    def render(self):
        """Main render method for the Scenario Sandbox UI"""

        st.markdown("""
        ## 🧪 Scenario Sandbox

        **Portföyünüzü farklı makro ekonomik senaryolar altında test edin:**
        - 📊 Faiz oranı değişimleri (TCMB/FED)
        - 💱 Döviz kuru şokları (USD/TRY, EUR/TRY)
        - 🛢️ Emtia fiyat hareketleri (Petrol, Altın)
        - 📈 Borsa şokları (S&P500, BIST100)
        - 🎯 Özel senaryolar (Kombinasyonlar)

        **Gelişmiş analiz araçları:**
        - Monte Carlo VaR simülasyonu
        - Stress test senaryoları
        - Sektörel etki analizi
        """)

        # Portfolio upload
        st.markdown("---")
        st.subheader("📂 Portföy Yükleme")

        uploaded_file = st.file_uploader(
            "Portföy dosyanızı yükleyin (CSV veya Excel)",
            type=['csv', 'xlsx'],
            help="Sütunlar: Symbol, Shares, Purchase_Price (opsiyonel: Sector, Purchase_Date)"
        )

        if uploaded_file is not None:
            # Load portfolio
            if uploaded_file.name.endswith('.csv'):
                portfolio_df = pd.read_csv(uploaded_file)
            else:
                portfolio_df = pd.read_excel(uploaded_file)

            # Display portfolio summary
            with st.expander("📊 Portföy Özeti", expanded=False):
                st.dataframe(portfolio_df, use_container_width=True)

                total_value = (portfolio_df['Shares'] * portfolio_df.get('Purchase_Price', 0)).sum()
                st.metric("Toplam Portföy Değeri", f"₺{total_value:,.0f}")

            # Main scenario interface
            st.markdown("---")

            # Tab navigation
            tab1, tab2, tab3 = st.tabs([
                "🎯 Tek Senaryo",
                "⚡ Stress Test",
                "🎲 Monte Carlo VaR"
            ])

            with tab1:
                self._render_single_scenario(portfolio_df)

            with tab2:
                self._render_stress_test(portfolio_df)

            with tab3:
                self._render_var_analysis(portfolio_df)

        else:
            st.info("👆 Portföy dosyanızı yükleyerek başlayın")

            # Sample data link
            st.markdown("""
            **Örnek dosya formatı:**
            ```
            Symbol,Shares,Purchase_Price,Sector
            THYAO,1000,150.5,Ulaşım
            TUPRS,500,420.0,Enerji
            AKBNK,2000,45.3,Finans
            ```
            """)

    def _render_single_scenario(self, portfolio_df: pd.DataFrame):
        """Render single scenario simulation interface"""

        st.markdown("### 🎯 Tek Senaryo Simülasyonu")
        st.markdown("Belirli bir senaryonun portföyünüz üzerindeki etkisini analiz edin.")

        col1, col2 = st.columns([1, 2])

        with col1:
            # Scenario type selection
            scenario_type = st.selectbox(
                "Senaryo Türü",
                options=list(self.sandbox.SCENARIO_TYPES.keys()),
                format_func=lambda x: self.sandbox.SCENARIO_TYPES[x]['name'],
                key='single_scenario_type'
            )

            st.markdown("---")
            st.markdown("**Parametre Ayarları:**")

            # Dynamic parameter inputs based on scenario type
            params = self._render_scenario_parameters(scenario_type)

            # Run simulation button
            run_button = st.button("▶️ Simülasyonu Çalıştır", type="primary", use_container_width=True)

        with col2:
            if run_button:
                with st.spinner("Senaryo simülasyonu yapılıyor..."):
                    # Create scenario
                    scenario = self.sandbox.create_scenario(
                        scenario_type=scenario_type,
                        parameters=params
                    )

                    # Simulate impact
                    result_df = self.sandbox.simulate_portfolio_impact(
                        portfolio_df=portfolio_df,
                        scenario=scenario
                    )

                    # Display results
                    self._display_scenario_results(result_df, scenario, params)

    def _render_scenario_parameters(self, scenario_type: str) -> Dict:
        """Render parameter inputs based on scenario type"""

        params = {}

        if scenario_type == 'interest_rate':
            params['tcmb_change_bp'] = st.slider(
                "TCMB Faiz Değişimi (baz puan)",
                min_value=-500,
                max_value=1000,
                value=0,
                step=50,
                help="Örnek: +100 bp = %1 faiz artışı"
            )
            params['fed_change_bp'] = st.slider(
                "FED Faiz Değişimi (baz puan)",
                min_value=-200,
                max_value=500,
                value=0,
                step=25,
                help="FED faiz kararının dolaylı etkisi"
            )

        elif scenario_type == 'currency_shock':
            params['usd_try_change_pct'] = st.slider(
                "USD/TRY Değişimi (%)",
                min_value=-30.0,
                max_value=50.0,
                value=0.0,
                step=1.0,
                help="Örnek: +10% = Dolar 10% değer kazandı"
            )
            params['eur_try_change_pct'] = st.slider(
                "EUR/TRY Değişimi (%)",
                min_value=-30.0,
                max_value=50.0,
                value=0.0,
                step=1.0
            )

        elif scenario_type == 'commodity_price':
            params['oil_change_pct'] = st.slider(
                "Petrol Fiyat Değişimi (%)",
                min_value=-50.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                help="Brent petrol referans alınır"
            )
            params['gold_change_pct'] = st.slider(
                "Altın Fiyat Değişimi (%)",
                min_value=-30.0,
                max_value=50.0,
                value=0.0,
                step=2.0
            )

        elif scenario_type == 'equity_shock':
            params['sp500_change_pct'] = st.slider(
                "S&P 500 Değişimi (%)",
                min_value=-40.0,
                max_value=30.0,
                value=0.0,
                step=2.0,
                help="Global piyasa risk iştahı göstergesi"
            )
            params['bist100_change_pct'] = st.slider(
                "BIST 100 Değişimi (%)",
                min_value=-50.0,
                max_value=50.0,
                value=0.0,
                step=2.0
            )

        elif scenario_type == 'combined':
            st.info("🎨 Özel senaryo - Tüm parametreleri ayarlayın")

            with st.expander("💰 Faiz Oranları", expanded=True):
                params['tcmb_change_bp'] = st.slider("TCMB (bp)", -500, 1000, 0, 50)
                params['fed_change_bp'] = st.slider("FED (bp)", -200, 500, 0, 25)

            with st.expander("💱 Döviz Kurları"):
                params['usd_try_change_pct'] = st.slider("USD/TRY (%)", -30.0, 50.0, 0.0, 1.0)
                params['eur_try_change_pct'] = st.slider("EUR/TRY (%)", -30.0, 50.0, 0.0, 1.0)

            with st.expander("🛢️ Emtia Fiyatları"):
                params['oil_change_pct'] = st.slider("Petrol (%)", -50.0, 100.0, 0.0, 5.0)
                params['gold_change_pct'] = st.slider("Altın (%)", -30.0, 50.0, 0.0, 2.0)

            with st.expander("📈 Borsa Endeksleri"):
                params['sp500_change_pct'] = st.slider("S&P 500 (%)", -40.0, 30.0, 0.0, 2.0)
                params['bist100_change_pct'] = st.slider("BIST 100 (%)", -50.0, 50.0, 0.0, 2.0)

        return params

    def _display_scenario_results(self, result_df: pd.DataFrame, scenario: Dict, params: Dict):
        """Display scenario simulation results"""

        # Summary metrics
        st.markdown("### 📊 Senaryo Sonuçları")

        col1, col2, col3, col4 = st.columns(4)

        total_impact_pct = result_df['Impact_Pct'].mean()
        portfolio_value = (result_df['Shares'] * result_df.get('Current_Price', result_df.get('Purchase_Price', 0))).sum()
        total_impact_tl = portfolio_value * (total_impact_pct / 100)

        positive_stocks = (result_df['Impact_Pct'] > 0).sum()
        negative_stocks = (result_df['Impact_Pct'] < 0).sum()

        with col1:
            st.metric(
                "Toplam Etki",
                f"{total_impact_pct:+.2f}%",
                delta=f"₺{total_impact_tl:+,.0f}",
                delta_color="normal"
            )

        with col2:
            st.metric(
                "Kazanan Hisse",
                f"{positive_stocks}",
                delta=f"{(positive_stocks/len(result_df)*100):.0f}%"
            )

        with col3:
            st.metric(
                "Kaybeden Hisse",
                f"{negative_stocks}",
                delta=f"{(negative_stocks/len(result_df)*100):.0f}%",
                delta_color="inverse"
            )

        with col4:
            worst_impact = result_df['Impact_Pct'].min()
            st.metric(
                "En Kötü Etki",
                f"{worst_impact:.2f}%",
                delta=result_df.loc[result_df['Impact_Pct'].idxmin(), 'Symbol']
            )

        # AI Insights
        st.markdown("---")
        st.markdown("#### 🤖 AI İçgörüler")

        try:
            insights = generate_all_insights(
                data_type='scenario',
                result_df=result_df,
                scenario=scenario,
                total_impact_pct=total_impact_pct
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

        # Visualizations
        st.markdown("---")

        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            # Waterfall chart
            st.markdown("#### 💧 Hisse Bazlı Etki (Waterfall)")
            waterfall_fig = self._create_waterfall_chart(result_df)
            st.plotly_chart(waterfall_fig, use_container_width=True)

        with viz_col2:
            # Sector heatmap
            st.markdown("#### 🔥 Sektör Etkisi (Heatmap)")
            heatmap_fig = self._create_sector_heatmap(result_df)
            st.plotly_chart(heatmap_fig, use_container_width=True)

        # Gauge chart for overall impact
        st.markdown("---")
        st.markdown("#### 🎯 Genel Portföy Etkisi")
        gauge_fig = self._create_impact_gauge(total_impact_pct)
        st.plotly_chart(gauge_fig, use_container_width=True)

        # Detailed results table
        st.markdown("---")
        st.markdown("#### 📋 Detaylı Sonuçlar")

        display_df = result_df[['Symbol', 'Sector', 'Shares', 'Impact_Pct', 'Estimated_New_Price']].copy()
        display_df = display_df.sort_values('Impact_Pct', ascending=False)
        display_df['Impact_Pct'] = display_df['Impact_Pct'].apply(lambda x: f"{x:+.2f}%")
        display_df['Estimated_New_Price'] = display_df['Estimated_New_Price'].apply(lambda x: f"₺{x:.2f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Export option
        csv = result_df.to_csv(index=False)
        st.download_button(
            label="📥 Sonuçları İndir (CSV)",
            data=csv,
            file_name=f"scenario_results_{scenario['type']}.csv",
            mime="text/csv"
        )

    def _render_stress_test(self, portfolio_df: pd.DataFrame):
        """Render stress test interface"""

        st.markdown("### ⚡ Stress Test Analizi")
        st.markdown("Portföyünüzü önceden tanımlı kriz senaryolarıyla test edin.")

        # Predefined scenarios
        st.markdown("#### 📚 Önceden Tanımlı Senaryolar")

        col1, col2 = st.columns([1, 2])

        with col1:
            scenario_preset = st.selectbox(
                "Senaryo Seçin",
                options=[
                    "2018 Döviz Krizi",
                    "2020 COVID-19 Şoku",
                    "2022 Faiz Artış Dönemi",
                    "Şiddetli Durgunluk",
                    "Hiper Enflasyon",
                    "Global Finansal Kriz"
                ]
            )

            # Preset descriptions
            preset_info = {
                "2018 Döviz Krizi": "USD/TRY +40%, TCMB +625 bp, BIST -20%",
                "2020 COVID-19 Şoku": "S&P -35%, BIST -25%, Petrol -60%",
                "2022 Faiz Artış Dönemi": "FED +425 bp, TCMB +1000 bp",
                "Şiddetli Durgunluk": "S&P -30%, BIST -40%, Petrol -40%",
                "Hiper Enflasyon": "USD/TRY +60%, TCMB +1500 bp",
                "Global Finansal Kriz": "S&P -40%, USD/TRY +35%, Petrol -50%"
            }

            st.info(f"**Parametreler:** {preset_info[scenario_preset]}")

            run_stress = st.button("▶️ Stress Test Çalıştır", type="primary", use_container_width=True)

        with col2:
            if run_stress:
                with st.spinner("Stress test senaryoları çalıştırılıyor..."):
                    # Map preset to scenario
                    preset_scenarios = {
                        "2018 Döviz Krizi": {
                            'type': 'combined',
                            'params': {'usd_try_change_pct': 40, 'tcmb_change_bp': 625, 'bist100_change_pct': -20}
                        },
                        "2020 COVID-19 Şoku": {
                            'type': 'combined',
                            'params': {'sp500_change_pct': -35, 'bist100_change_pct': -25, 'oil_change_pct': -60}
                        },
                        "2022 Faiz Artış Dönemi": {
                            'type': 'interest_rate',
                            'params': {'fed_change_bp': 425, 'tcmb_change_bp': 1000}
                        },
                        "Şiddetli Durgunluk": {
                            'type': 'combined',
                            'params': {'sp500_change_pct': -30, 'bist100_change_pct': -40, 'oil_change_pct': -40}
                        },
                        "Hiper Enflasyon": {
                            'type': 'combined',
                            'params': {'usd_try_change_pct': 60, 'tcmb_change_bp': 1500}
                        },
                        "Global Finansal Kriz": {
                            'type': 'combined',
                            'params': {'sp500_change_pct': -40, 'usd_try_change_pct': 35, 'oil_change_pct': -50}
                        }
                    }

                    selected = preset_scenarios[scenario_preset]
                    scenario = self.sandbox.create_scenario(
                        scenario_type=selected['type'],
                        parameters=selected['params']
                    )

                    result_df = self.sandbox.simulate_portfolio_impact(
                        portfolio_df=portfolio_df,
                        scenario=scenario
                    )

                    # Display results
                    self._display_scenario_results(result_df, scenario, selected['params'])

    def _render_var_analysis(self, portfolio_df: pd.DataFrame):
        """Render Monte Carlo VaR analysis interface"""

        st.markdown("### 🎲 Monte Carlo VaR Analizi")
        st.markdown("Rastgele senaryolar kullanarak portföy riskini ölçün (Value at Risk).")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Simülasyon Parametreleri:**")

            num_simulations = st.select_slider(
                "Simülasyon Sayısı",
                options=[100, 500, 1000, 5000, 10000],
                value=1000,
                help="Daha fazla simülasyon = Daha doğru sonuçlar (ama daha yavaş)"
            )

            confidence_level = st.slider(
                "Güven Düzeyi (%)",
                min_value=90,
                max_value=99,
                value=95,
                step=1,
                help="Örnek: %95 = En kötü %5'lik senaryolara karşı korunma"
            )

            time_horizon = st.selectbox(
                "Zaman Ufku",
                options=[1, 5, 10, 20, 30],
                format_func=lambda x: f"{x} gün",
                help="VaR hesaplaması için zaman periyodu"
            )

            run_var = st.button("▶️ VaR Hesapla", type="primary", use_container_width=True)

        with col2:
            if run_var:
                with st.spinner(f"{num_simulations} simülasyon çalıştırılıyor..."):
                    # Run VaR calculation
                    var_results = self.sandbox.calculate_var(
                        portfolio_df=portfolio_df,
                        num_simulations=num_simulations,
                        confidence_level=confidence_level / 100,
                        time_horizon_days=time_horizon
                    )

                    # Display VaR results
                    self._display_var_results(var_results, confidence_level, time_horizon)

    def _display_var_results(self, var_results: Dict, confidence_level: int, time_horizon: int):
        """Display Monte Carlo VaR results"""

        st.markdown("#### 📊 VaR Sonuçları")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                f"{confidence_level}% VaR",
                f"{var_results['var_pct']:.2f}%",
                help=f"En kötü %{100-confidence_level} senaryoda beklenen maksimum kayıp"
            )

        with col2:
            st.metric(
                "Conditional VaR (CVaR)",
                f"{var_results['cvar_pct']:.2f}%",
                help="VaR aşıldığında ortalama beklenen kayıp"
            )

        with col3:
            st.metric(
                "TL Cinsinden VaR",
                f"₺{var_results['var_amount']:,.0f}",
                help="Parasal olarak maksimum risk"
            )

        # Distribution histogram
        st.markdown("---")
        st.markdown("#### 📈 Getiri Dağılımı")

        fig = go.Figure()

        # Histogram of returns
        fig.add_trace(go.Histogram(
            x=var_results['simulation_returns'],
            nbinsx=50,
            name='Simülasyon Getirileri',
            marker_color='lightblue',
            opacity=0.7
        ))

        # VaR line
        fig.add_vline(
            x=var_results['var_pct'],
            line_dash="dash",
            line_color="red",
            annotation_text=f"VaR ({confidence_level}%): {var_results['var_pct']:.2f}%",
            annotation_position="top"
        )

        # CVaR line
        fig.add_vline(
            x=var_results['cvar_pct'],
            line_dash="dot",
            line_color="darkred",
            annotation_text=f"CVaR: {var_results['cvar_pct']:.2f}%",
            annotation_position="bottom"
        )

        fig.update_layout(
            title=f"{len(var_results['simulation_returns'])} Simülasyon - {time_horizon} Günlük Getiri Dağılımı",
            xaxis_title="Portföy Getirisi (%)",
            yaxis_title="Frekans",
            showlegend=True,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Risk interpretation
        st.markdown("---")
        st.markdown("#### 🎯 Risk Değerlendirmesi")

        if var_results['var_pct'] < -20:
            st.error(f"🔴 **Yüksek Risk**: {time_horizon} günlük dönemde portföyünüz %{confidence_level} olasılıkla {var_results['var_pct']:.2f}% veya daha fazla değer kaybedebilir. Risk yönetimi önlemleri alın!")
        elif var_results['var_pct'] < -10:
            st.warning(f"🟡 **Orta Risk**: {time_horizon} günlük dönemde %{confidence_level} olasılıkla maksimum {var_results['var_pct']:.2f}% kayıp bekleniyor. Portföy çeşitlendirmesi değerlendirin.")
        else:
            st.success(f"🟢 **Düşük Risk**: {time_horizon} günlük dönemde %{confidence_level} olasılıkla maksimum kayıp {var_results['var_pct']:.2f}%. Risk seviyeniz makul görünüyor.")

        # Worst scenarios
        st.markdown("#### 🔻 En Kötü 10 Senaryo")
        worst_scenarios = sorted(var_results['simulation_returns'])[:10]
        worst_df = pd.DataFrame({
            'Senaryo': [f"#{i+1}" for i in range(10)],
            'Kayıp (%)': [f"{x:.2f}%" for x in worst_scenarios]
        })
        st.dataframe(worst_df, use_container_width=True, hide_index=True)

    def _create_waterfall_chart(self, result_df: pd.DataFrame) -> go.Figure:
        """Create waterfall chart for stock-level impact"""

        # Sort by impact
        sorted_df = result_df.sort_values('Impact_Pct', ascending=False).head(15)

        fig = go.Figure(go.Waterfall(
            name="Etki",
            orientation="v",
            x=sorted_df['Symbol'],
            y=sorted_df['Impact_Pct'],
            text=[f"{x:+.2f}%" for x in sorted_df['Impact_Pct']],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#EF553B"}},
            increasing={"marker": {"color": "#00CC96"}},
            totals={"marker": {"color": "#636EFA"}}
        ))

        fig.update_layout(
            title="Top 15 Hisse - Senaryo Etkisi",
            xaxis_title="Hisse",
            yaxis_title="Etki (%)",
            showlegend=False,
            height=400
        )

        return fig

    def _create_sector_heatmap(self, result_df: pd.DataFrame) -> go.Figure:
        """Create sector impact heatmap"""

        # Group by sector
        sector_impact = result_df.groupby('Sector').agg({
            'Impact_Pct': 'mean',
            'Symbol': 'count'
        }).reset_index()
        sector_impact.columns = ['Sector', 'Avg_Impact', 'Count']
        sector_impact = sector_impact.sort_values('Avg_Impact', ascending=False)

        # Create heatmap-style bar chart
        fig = go.Figure(go.Bar(
            y=sector_impact['Sector'],
            x=sector_impact['Avg_Impact'],
            orientation='h',
            text=[f"{x:+.2f}%" for x in sector_impact['Avg_Impact']],
            textposition='auto',
            marker=dict(
                color=sector_impact['Avg_Impact'],
                colorscale='RdYlGn',
                cmin=-10,
                cmax=10,
                colorbar=dict(title="Etki (%)")
            )
        ))

        fig.update_layout(
            title="Sektör Bazlı Ortalama Etki",
            xaxis_title="Ortalama Etki (%)",
            yaxis_title="Sektör",
            height=400
        )

        return fig

    def _create_impact_gauge(self, total_impact_pct: float) -> go.Figure:
        """Create gauge chart for overall portfolio impact"""

        # Determine color based on impact
        if total_impact_pct < -10:
            color = "#EF553B"  # Red
        elif total_impact_pct < -5:
            color = "#FFA15A"  # Orange
        elif total_impact_pct < 0:
            color = "#FECB52"  # Yellow
        elif total_impact_pct < 5:
            color = "#00CC96"  # Light green
        else:
            color = "#00CC96"  # Green

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=total_impact_pct,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Toplam Portföy Etkisi (%)"},
            delta={'reference': 0, 'increasing': {'color': "#00CC96"}, 'decreasing': {'color': "#EF553B"}},
            gauge={
                'axis': {'range': [-30, 30], 'tickwidth': 1, 'tickcolor': "darkgray"},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [-30, -10], 'color': '#FFEBEE'},
                    {'range': [-10, -5], 'color': '#FFF3E0'},
                    {'range': [-5, 0], 'color': '#FFFDE7'},
                    {'range': [0, 5], 'color': '#E8F5E9'},
                    {'range': [5, 10], 'color': '#C8E6C9'},
                    {'range': [10, 30], 'color': '#A5D6A7'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': -10
                }
            }
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        return fig


def render_scenario_sandbox():
    """Main function to render the Scenario Sandbox UI"""
    ui = ScenarioSandboxUI()
    ui.render()


if __name__ == "__main__":
    render_scenario_sandbox()
