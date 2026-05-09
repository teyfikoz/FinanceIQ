"""
ETF Holdings Weight Tracker - Streamlit UI
Bloomberg-level ETF holdings analysis interface
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from modules.etf_weight_tracker import ETFWeightTracker
from modules.insight_engine import generate_all_insights
from datetime import datetime
import numpy as np
import warnings
warnings.filterwarnings('ignore')


class ETFWeightTrackerUI:
    """Streamlit UI for ETF Weight Tracker"""

    def __init__(self):
        self.tracker = ETFWeightTracker()

    def render(self):
        """Main render function"""
        st.title("📊 ETF Holdings Weight Tracker")
        st.markdown("""
        **Bloomberg Terminal seviyesinde ETF analizi** - Hangi fonlarda hangi hisseler var?
        Ağırlık değişimlerini takip edin ve fon yöneticilerinin sinyallerini yakalayın.
        """)

        tracker_view = st.radio(
            "ETF Tracker View",
            [
                "🔍 Hisse Analizi",
                "📈 Ağırlık Geçmişi",
                "🎯 Fon Yöneticisi Sinyalleri",
                "⚙️ Veri Yönetimi"
            ],
            horizontal=True,
            key="etf_tracker_view_nav",
            label_visibility="collapsed"
        )

        if tracker_view == "🔍 Hisse Analizi":
            self._render_stock_lookup()
        elif tracker_view == "📈 Ağırlık Geçmişi":
            self._render_weight_history()
        elif tracker_view == "🎯 Fon Yöneticisi Sinyalleri":
            self._render_manager_signals()
        else:
            self._render_data_management()

    def _render_stock_lookup(self):
        """Stock lookup interface - reverse search"""
        st.subheader("🔍 Hisse Analizi: Bu Hisse Hangi Fonlarda?")

        col1, col2 = st.columns([2, 1])

        with col1:
            stock_symbol = st.text_input(
                "Hisse Sembolü",
                value="AAPL",
                help="Örnek: AAPL, MSFT, GOOGL, TSLA"
            ).upper()

        with col2:
            min_weight = st.slider(
                "Min Ağırlık (%)",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1,
                help="Sadece bu ağırlığın üzerindeki fonları göster"
            )

        if st.button("🔍 Analiz Et", type="primary", use_container_width=True, key="etf_weight_tracker___analiz_et"):
            holdings_df = self.tracker.get_funds_for_stock(stock_symbol, min_weight)
            action_signal = self.tracker.detect_fund_manager_actions(stock_symbol)
            st.session_state["etf_tracker_stock_lookup_state"] = {
                "stock_symbol": stock_symbol,
                "min_weight": min_weight,
                "holdings_df": holdings_df.copy() if hasattr(holdings_df, "copy") else holdings_df,
                "action_signal": action_signal,
            }

        state = st.session_state.get("etf_tracker_stock_lookup_state")
        if state:
            st.caption("Son çalıştırılan hisse analizi gösteriliyor.")
            self._display_stock_analysis_payload(
                state["stock_symbol"],
                state["holdings_df"],
                state["action_signal"],
            )

    def _display_stock_analysis(self, stock_symbol: str, min_weight: float):
        """Display comprehensive stock analysis"""
        # Get funds holding this stock
        holdings_df = self.tracker.get_funds_for_stock(stock_symbol, min_weight)
        action_signal = self.tracker.detect_fund_manager_actions(stock_symbol)
        self._display_stock_analysis_payload(stock_symbol, holdings_df, action_signal)

    def _display_stock_analysis_payload(self, stock_symbol: str, holdings_df: pd.DataFrame, action_signal: dict):
        """Render stock analysis from precomputed payload."""

        if len(holdings_df) == 0:
            st.warning(f"⚠️ {stock_symbol} için veri bulunamadı. Veri tabanını güncelleyin (Veri Yönetimi sekmesi).")
            return

        # Summary metrics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Toplam Fon", len(holdings_df))

        with col2:
            max_weight = holdings_df['weight_pct'].max()
            max_fund = holdings_df.loc[holdings_df['weight_pct'].idxmax(), 'fund_code']
            st.metric("En Yüksek Ağırlık", f"{max_weight:.2f}%", delta=max_fund)

        with col3:
            avg_weight = holdings_df['weight_pct'].mean()
            st.metric("Ortalama Ağırlık", f"{avg_weight:.2f}%")

        with col4:
            latest_date = holdings_df['report_date'].max()
            st.metric("Son Güncelleme", latest_date)

        # Holdings table
        st.markdown("### 📋 Fon Listesi")

        display_df = holdings_df[['fund_code', 'fund_name', 'weight_pct', 'report_date']].copy()
        display_df.columns = ['Fon Kodu', 'Fon Adı', 'Ağırlık (%)', 'Rapor Tarihi']
        display_df = display_df.sort_values('Ağırlık (%)', ascending=False)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )

        chart_view = st.radio(
            "ETF Visualization View",
            ["📊 Weight Bars", "🗺️ Treemap"],
            horizontal=True,
            key=f"etf_tracker_chart_view_{stock_symbol}",
            label_visibility="collapsed"
        )

        if chart_view == "📊 Weight Bars":
            fig_bar = px.bar(
                holdings_df.nlargest(15, 'weight_pct'),
                x='weight_pct',
                y='fund_code',
                orientation='h',
                title=f'{stock_symbol} - Fon Ağırlıkları (Top 15)',
                labels={'weight_pct': 'Ağırlık (%)', 'fund_code': 'Fon'},
                color='weight_pct',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(showlegend=False, height=500)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            fig_tree = px.treemap(
                holdings_df.nlargest(20, 'weight_pct'),
                path=['fund_code'],
                values='weight_pct',
                title=f'{stock_symbol} - Ağırlık Dağılımı (Treemap)',
                color='weight_pct',
                color_continuous_scale='RdYlGn'
            )
            fig_tree.update_layout(height=500)
            st.plotly_chart(fig_tree, use_container_width=True)

        st.markdown("### 🎯 Fon Yöneticisi Sinyali")

        signal_color = {
            'BULLISH': '🟢',
            'BEARISH': '🔴',
            'NEUTRAL': '⚪'
        }

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"### {signal_color.get(action_signal['signal'], '⚪')} {action_signal['signal']}")

        with col2:
            st.metric("Güven Skoru", f"{action_signal['confidence']:.1f}%")

        with col3:
            st.info(action_signal['details'])

        # Detailed breakdown
        if action_signal['total_funds'] > 0:
            with st.expander("📊 Detaylı Analiz"):
                st.markdown(f"""
                **Son 30 Günlük Hareketler:**
                - ⬆️ Ağırlık Artışı: {action_signal['increases']} fon
                - ⬇️ Ağırlık Azalışı: {action_signal['decreases']} fon
                - Toplam Fon: {action_signal['total_funds']}

                **Yorum:**
                """)

                if action_signal['signal'] == 'BULLISH':
                    st.success(f"""
                    Fonların çoğunluğu ({action_signal['increases']}/{action_signal['total_funds']})
                    {stock_symbol} ağırlığını artırmış. Bu genelde **pozitif sinyal** olarak yorumlanır.
                    Kurumsal yatırımcılar bu hisseyi biriktiriyor olabilir.
                    """)
                elif action_signal['signal'] == 'BEARISH':
                    st.warning(f"""
                    Fonların çoğunluğu ({action_signal['decreases']}/{action_signal['total_funds']})
                    {stock_symbol} ağırlığını azaltmış. Bu **negatif sinyal** olabilir.
                    Kurumsal yatırımcılar pozisyon azaltıyor.
                    """)
                else:
                    st.info("""
                    Karışık sinyaller var. Bazı fonlar alıyor, bazıları satıyor.
                    Net bir trend yok. Daha fazla veri için bekleyin.
                    """)

        # AI-Powered Insights
        st.markdown("---")
        st.subheader("🤖 AI İçgörüler")

        try:
            insights = generate_all_insights(
                data_type='etf',
                stock_symbol=stock_symbol,
                holdings_df=holdings_df,
                action_signal=action_signal
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
                st.info("ℹ️ Şu anda ek içgörü bulunmuyor.")

        except Exception as e:
            st.warning(f"⚠️ İçgörüler yüklenirken hata: {e}")

    def _render_weight_history(self):
        """Weight history tracking interface"""
        st.subheader("📈 Ağırlık Geçmişi ve Trend Analizi")

        col1, col2 = st.columns(2)

        with col1:
            stock_symbol = st.text_input(
                "Hisse Sembolü",
                value="NVDA",
                key="weight_history_stock"
            ).upper()

        with col2:
            # Get available funds for this stock
            available_funds = self.tracker.get_funds_for_stock(stock_symbol, min_weight=0.1)

            if len(available_funds) > 0:
                fund_options = available_funds['fund_code'].tolist()
                fund_code = st.selectbox(
                    "Fon Seçin",
                    options=fund_options,
                    key="weight_history_fund"
                )
            else:
                st.warning("Bu hisse için veri bulunamadı")
                fund_code = None

        if fund_code and st.button("📊 Geçmişi Göster", type="primary", use_container_width=True, key="etf_weight_tracker___ge_mi_i_g_ster"):
            history_df = self.tracker.get_weight_history(stock_symbol, fund_code)
            st.session_state["etf_tracker_weight_history_state"] = {
                "stock_symbol": stock_symbol,
                "fund_code": fund_code,
                "history_df": history_df.copy() if hasattr(history_df, "copy") else history_df,
            }

        history_state = st.session_state.get("etf_tracker_weight_history_state")
        if history_state:
            st.caption("Son çalıştırılan ağırlık geçmişi analizi gösteriliyor.")
            self._display_weight_history_payload(
                history_state["stock_symbol"],
                history_state["fund_code"],
                history_state["history_df"],
            )

    def _display_weight_history(self, stock_symbol: str, fund_code: str):
        """Display weight history chart"""
        history_df = self.tracker.get_weight_history(stock_symbol, fund_code)
        self._display_weight_history_payload(stock_symbol, fund_code, history_df)

    def _display_weight_history_payload(self, stock_symbol: str, fund_code: str, history_df: pd.DataFrame):
        """Render weight history from precomputed payload."""

        if len(history_df) == 0:
            st.warning("Bu hisse-fon kombinasyonu için geçmiş veri yok.")
            return

        st.markdown("---")

        # Summary stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            current_weight = history_df['weight_pct'].iloc[-1]
            st.metric("Mevcut Ağırlık", f"{current_weight:.2f}%")

        with col2:
            if len(history_df) > 1:
                weight_change = history_df['weight_change'].iloc[-1]
                st.metric("Son Değişim", f"{weight_change:+.2f}%")
            else:
                st.metric("Son Değişim", "N/A")

        with col3:
            max_weight = history_df['weight_pct'].max()
            st.metric("Maksimum Ağırlık", f"{max_weight:.2f}%")

        with col4:
            min_weight = history_df['weight_pct'].min()
            st.metric("Minimum Ağırlık", f"{min_weight:.2f}%")

        # Line chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=history_df['report_date'],
            y=history_df['weight_pct'],
            mode='lines+markers',
            name='Ağırlık (%)',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            hovertemplate='<b>Tarih:</b> %{x}<br><b>Ağırlık:</b> %{y:.2f}%<extra></extra>'
        ))

        # Add trend line if enough data points
        if len(history_df) >= 3:
            z = np.polyfit(range(len(history_df)), history_df['weight_pct'], 1)
            p = np.poly1d(z)
            trend = p(range(len(history_df)))

            fig.add_trace(go.Scatter(
                x=history_df['report_date'],
                y=trend,
                mode='lines',
                name='Trend',
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate='<b>Trend:</b> %{y:.2f}%<extra></extra>'
            ))

        fig.update_layout(
            title=f'{stock_symbol} Ağırlık Geçmişi - {fund_code}',
            xaxis_title='Tarih',
            yaxis_title='Ağırlık (%)',
            hovermode='x unified',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Weight change table
        st.markdown("### 📋 Ağırlık Değişim Tablosu")

        display_df = history_df[['report_date', 'weight_pct', 'weight_change']].copy()
        display_df.columns = ['Tarih', 'Ağırlık (%)', 'Değişim (%)']
        display_df['Değişim (%)'] = display_df['Değişim (%)'].apply(
            lambda x: f"{x:+.2f}" if pd.notna(x) else "N/A"
        )

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Trend interpretation
        if len(history_df) >= 3:
            trend_slope = z[0]  # Slope of trend line

            with st.expander("🔍 Trend Yorumu"):
                if trend_slope > 0.5:
                    st.success(f"""
                    ✅ **Yükselen Trend**

                    {fund_code} fonunda {stock_symbol} ağırlığı artış trendinde.
                    Fon yöneticisi bu hisseyi sürekli artırıyor.

                    **Yorum:** Genelde pozitif sinyal. Kurumsal yatırımcılar bu hisseyi tercih ediyor.
                    """)
                elif trend_slope < -0.5:
                    st.warning(f"""
                    ⚠️ **Düşen Trend**

                    {fund_code} fonunda {stock_symbol} ağırlığı azalış trendinde.
                    Fon yöneticisi pozisyon azaltıyor.

                    **Yorum:** Negatif sinyal olabilir. Kurumsal yatırımcılar çıkış yapıyor.
                    """)
                else:
                    st.info(f"""
                    ⚪ **Yatay Trend**

                    {fund_code} fonunda {stock_symbol} ağırlığı stabil.
                    Fon yöneticisi pozisyonu koruyor.

                    **Yorum:** Nötr. Önemli bir değişiklik yok.
                    """)

        # AI-Powered Insights for Weight History
        st.markdown("---")
        st.subheader("🤖 AI Trend İçgörüleri")

        try:
            insights = generate_all_insights(
                data_type='weight_history',
                stock_symbol=stock_symbol,
                history_df=history_df,
                fund_code=fund_code
            )

            if insights:
                for insight in insights:
                    if insight.startswith("📈") or insight.startswith("🟢"):
                        st.success(insight)
                    elif insight.startswith("📉") or insight.startswith("⚠️"):
                        st.warning(insight)
                    elif insight.startswith("⚡"):
                        st.info(insight)
                    else:
                        st.info(insight)
            else:
                st.info("ℹ️ Şu anda trend analizi için yetersiz veri.")

        except Exception as e:
            st.warning(f"⚠️ İçgörüler yüklenirken hata: {e}")

    def _render_manager_signals(self):
        """Fund manager action signals"""
        st.subheader("🎯 Fon Yöneticisi Sinyalleri")
        st.markdown("""
        Son 30 günde ağırlığı en çok değişen hisseleri görün.
        Kurumsal yatırımcıların hangi hisseleri biriktirdiğini/sattığını keşfedin.
        """)

        if st.button("🔍 En Aktif Hisseleri Bul", type="primary", use_container_width=True, key="etf_weight_tracker___en_aktif_hisseleri_bul"):
            changes_df = self.tracker.get_top_weight_changes(period_days=30, limit=30)
            st.session_state["etf_tracker_manager_signals_state"] = {
                "changes_df": changes_df.copy() if hasattr(changes_df, "copy") else changes_df,
            }

        signals_state = st.session_state.get("etf_tracker_manager_signals_state")
        if signals_state:
            st.caption("Son çalıştırılan fon yöneticisi sinyal analizi gösteriliyor.")
            self._display_top_changes_payload(signals_state["changes_df"])

    def _display_top_changes(self):
        """Display stocks with biggest weight changes"""
        changes_df = self.tracker.get_top_weight_changes(period_days=30, limit=30)
        self._display_top_changes_payload(changes_df)

    def _display_top_changes_payload(self, changes_df: pd.DataFrame):
        """Render manager signal changes from precomputed payload."""

        if len(changes_df) == 0:
            st.warning("⚠️ Yeterli veri yok. Lütfen veri tabanını güncelleyin.")
            return

        st.markdown("---")

        # Separate into increases and decreases
        increases = changes_df[changes_df['avg_weight_change'] > 0].nlargest(10, 'avg_weight_change')
        decreases = changes_df[changes_df['avg_weight_change'] < 0].nsmallest(10, 'avg_weight_change')

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ⬆️ En Çok Ağırlık Artan Hisseler")

            if len(increases) > 0:
                fig_inc = px.bar(
                    increases,
                    x='avg_weight_change',
                    y='stock_symbol',
                    orientation='h',
                    color='funds_increased',
                    title='Ağırlık Artışı (Son 30 Gün)',
                    labels={
                        'avg_weight_change': 'Ortalama Değişim (%)',
                        'stock_symbol': 'Hisse',
                        'funds_increased': 'Artış Yapan Fon Sayısı'
                    },
                    color_continuous_scale='Greens'
                )
                fig_inc.update_layout(height=500)
                st.plotly_chart(fig_inc, use_container_width=True)

                st.dataframe(
                    increases[['stock_symbol', 'num_funds_changed', 'avg_weight_change', 'funds_increased']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'stock_symbol': 'Hisse',
                        'num_funds_changed': 'Değişen Fon Sayısı',
                        'avg_weight_change': 'Ort. Değişim (%)',
                        'funds_increased': 'Artış Yapan Fon'
                    }
                )
            else:
                st.info("Son 30 günde ağırlık artışı yok.")

        with col2:
            st.markdown("### ⬇️ En Çok Ağırlık Azalan Hisseler")

            if len(decreases) > 0:
                fig_dec = px.bar(
                    decreases,
                    x='avg_weight_change',
                    y='stock_symbol',
                    orientation='h',
                    color='funds_decreased',
                    title='Ağırlık Azalışı (Son 30 Gün)',
                    labels={
                        'avg_weight_change': 'Ortalama Değişim (%)',
                        'stock_symbol': 'Hisse',
                        'funds_decreased': 'Azalış Yapan Fon Sayısı'
                    },
                    color_continuous_scale='Reds'
                )
                fig_dec.update_layout(height=500)
                st.plotly_chart(fig_dec, use_container_width=True)

                st.dataframe(
                    decreases[['stock_symbol', 'num_funds_changed', 'avg_weight_change', 'funds_decreased']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'stock_symbol': 'Hisse',
                        'num_funds_changed': 'Değişen Fon Sayısı',
                        'avg_weight_change': 'Ort. Değişim (%)',
                        'funds_decreased': 'Azalış Yapan Fon'
                    }
                )
            else:
                st.info("Son 30 günde ağırlık azalışı yok.")

    def _render_data_management(self):
        """Data management interface"""
        st.subheader("⚙️ Veri Yönetimi")

        # Database stats
        stats = self.tracker.get_summary_stats()

        st.markdown("### 📊 Veri Tabanı İstatistikleri")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Toplam Kayıt", f"{stats['total_records']:,}")

        with col2:
            st.metric("Benzersiz Hisse", stats['unique_stocks'])

        with col3:
            st.metric("Benzersiz Fon", stats['unique_funds'])

        with col4:
            st.metric("Son Güncelleme", stats['latest_update'])

        # ETF data fetching
        st.markdown("---")
        st.markdown("### 🔄 ETF Verilerini Güncelle")

        col1, col2 = st.columns([2, 1])

        with col1:
            etf_options = list(self.tracker.TRACKED_ETFS.keys())
            selected_etfs = st.multiselect(
                "Güncellenecek ETF'leri Seçin",
                options=['TÜMÜ'] + etf_options,
                default=['TÜMÜ'],
                help="TÜMÜ seçeneği tüm ETF'leri günceller (uzun sürebilir)"
            )

        with col2:
            force_refresh = st.checkbox(
                "Zorla Yenile",
                value=False,
                help="Cache'i atla ve API'den tekrar çek"
            )

        if st.button("🚀 Verileri Güncelle", type="primary", use_container_width=True, key="etf_weight_tracker___verileri_g_ncelle"):
            if 'TÜMÜ' in selected_etfs:
                etf_list = None  # Will fetch all
                st.info(f"Tüm ETF'ler güncelleniyor... Bu 5-10 dakika sürebilir.")
            else:
                etf_list = selected_etfs

            with st.spinner("Veriler çekiliyor... Lütfen bekleyin."):
                results = self.tracker.bulk_fetch_etf_holdings(etf_list, force_refresh=force_refresh)

                # Display results
                success_count = sum(1 for r in results.values() if r['success'])
                fail_count = len(results) - success_count

                st.success(f"✅ {success_count} ETF başarıyla güncellendi")

                if fail_count > 0:
                    st.warning(f"⚠️ {fail_count} ETF güncellenemedi")

                # Detailed results
                with st.expander("📋 Detaylı Sonuçlar"):
                    results_df = pd.DataFrame([
                        {
                            'ETF': etf,
                            'Durum': '✅ Başarılı' if data['success'] else '❌ Başarısız',
                            'Holding Sayısı': data.get('num_holdings', 'N/A'),
                            'En Büyük Holding': data.get('top_holding', 'N/A')
                        }
                        for etf, data in results.items()
                    ])

                    st.dataframe(results_df, use_container_width=True, hide_index=True)

        # Tracked ETFs list
        with st.expander("📋 Takip Edilen ETF Listesi"):
            etf_list_df = pd.DataFrame([
                {'Kod': code, 'Ad': name}
                for code, name in self.tracker.TRACKED_ETFS.items()
            ])
            st.dataframe(etf_list_df, use_container_width=True, hide_index=True, height=400)
