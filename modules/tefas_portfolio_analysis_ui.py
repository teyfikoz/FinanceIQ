"""
TEFAS Portfolio Analysis UI
============================
Streamlit UI for analyzing TEFAS fund portfolio changes over time.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_collectors.tefas_portfolio_tracker import TEFASPortfolioTracker


def create_tefas_portfolio_analysis_ui():
    """Main UI function for TEFAS portfolio analysis."""

    st.title("📊 TEFAS Fon Portföy Analizi")

    st.markdown("""
    **TEFAS fonlarının portföy içeriklerinin aylık bazda nasıl değiştiğini analiz edin:**
    - Varlık dağılımı değişimleri (hisse, tahvil, repo, döviz vb.)
    - Eklenen ve çıkarılan menkul kıymetler
    - Ağırlık değişimleri
    - En büyük holdingler
    """)

    # Initialize tracker
    tracker = TEFASPortfolioTracker()

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Ayarlar")

        # Popular TEFAS funds
        popular_funds = {
            'TCD': 'İş Portföy Dow Jones İst. 30 End. His. Sen. Fonu',
            'AKG': 'Ak Portföy Kısa Vadeli Borçlanma Araçları Fonu',
            'YAT': 'Yapı Kredi Portföy Hisse Senedi Fonu',
            'FBA': 'Finans Portföy Birinci Hisse Senedi Fonu',
            'GAH': 'Garanti Portföy Hisse Senedi Fonu',
            'HVP': 'Halk Hayat ve Emeklilik Değişken Fon',
            'ZPE': 'Ziraat Portföy Hisse Senedi Fonu'
        }

        fund_selection = st.selectbox(
            "Fon Seçin",
            options=list(popular_funds.keys()),
            format_func=lambda x: f"{x} - {popular_funds[x]}"
        )

        custom_fund = st.text_input(
            "Veya Fon Kodunu Girin",
            help="TEFAS fon kodu (örn: TCD, AKG, YAT)"
        )

        fund_code = custom_fund.upper() if custom_fund else fund_selection

        months_to_analyze = st.slider(
            "Analiz Süresi (Ay)",
            min_value=3,
            max_value=24,
            value=12,
            help="Kaç aylık portföy değişimi analiz edilsin"
        )

        analyze_button = st.button("🔍 Analiz Et", type="primary", use_container_width=True)

        st.markdown("---")
        st.info("💡 **İpucu:** Aylık bazda portföy değişimlerini görebilirsiniz")

    state_key = "tefas_portfolio_last_run"
    state = st.session_state.get(state_key)
    summary = None

    if analyze_button:
        with st.spinner(f"{fund_code} fonu için portföy değişimleri analiz ediliyor..."):
            try:
                summary = tracker.generate_portfolio_summary(fund_code, months_to_analyze)
                if not summary:
                    st.error(f"⚠️ {fund_code} fonu için veri bulunamadı. Lütfen fon kodunu kontrol edin.")
                    return
                st.session_state[state_key] = {
                    "fund_code": fund_code,
                    "months_to_analyze": months_to_analyze,
                    "summary": summary,
                }
            except Exception as e:
                st.error(f"❌ Analiz sırasında hata oluştu: {str(e)}")
                st.exception(e)
                return
    elif state and state.get("fund_code") == fund_code and state.get("months_to_analyze") == months_to_analyze:
        summary = state.get("summary")
        st.caption("Son çalıştırılan TEFAS analizi gösteriliyor. Parametreleri değiştirdiyseniz yeniden analiz edin.")
    else:
        st.info("👆 Lütfen bir fon seçin ve 'Analiz Et' butonuna tıklayın")
        return

    try:
        # Display summary metrics
        st.header(f"📈 {fund_code} - Genel Bakış")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Portföy Değeri",
                f"₺{summary['latest_portfolio_value']:,.0f}",
                delta=f"₺{summary['portfolio_value_change']:,.0f}"
            )

        with col2:
            st.metric(
                "Yatırımcı Sayısı",
                f"{summary['latest_num_investors']:,}",
                delta=f"{summary['investor_change']:,}"
            )

        with col3:
            st.metric(
                "Eklenen Holding",
                summary['total_new_holdings'],
                help="Portföye eklenen menkul kıymet sayısı"
            )

        with col4:
            st.metric(
                "Çıkarılan Holding",
                summary['total_removed_holdings'],
                help="Portföyden çıkarılan menkul kıymet sayısı"
            )

        st.markdown(f"**Analiz Dönemi:** {summary['period']}")

        analysis_view = st.radio(
            "TEFAS Analysis View",
            [
                "📊 Varlık Dağılımı",
                "🔄 Portföy Değişimleri",
                "🏆 En Büyük Holdingleri",
                "📈 Detaylı Analiz"
            ],
            horizontal=True,
            key=f"tefas_analysis_view_{fund_code}",
            label_visibility="collapsed"
        )

        if analysis_view == "📊 Varlık Dağılımı":
            render_asset_allocation_tab(summary)
        elif analysis_view == "🔄 Portföy Değişimleri":
            render_portfolio_changes_tab(summary)
        elif analysis_view == "🏆 En Büyük Holdingleri":
            render_top_holdings_tab(summary)
        else:
            render_detailed_analysis_tab(summary)

    except Exception as e:
        st.error(f"❌ Analiz sırasında hata oluştu: {str(e)}")
        st.exception(e)


def render_asset_allocation_tab(summary: dict):
    """Render asset allocation analysis tab."""

    st.subheader("📊 Varlık Dağılımı Değişimi")

    current_alloc = summary['asset_allocation_current']
    initial_alloc = summary['asset_allocation_initial']

    # Asset class names in Turkish
    asset_names = {
        'stocks': 'Hisse Senetleri',
        'bonds': 'Tahviller',
        'bills': 'Bonolar',
        'repo': 'Repo',
        'fx': 'Döviz',
        'participation': 'Katılma Hesabı',
        'precious_metals': 'Kıymetli Madenler',
        'other': 'Diğer'
    }

    # Current vs Initial comparison
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Mevcut Dağılım")
        # Pie chart for current allocation
        current_data = {asset_names[k]: v for k, v in current_alloc.items() if v > 0}

        if current_data:
            fig_current = go.Figure(data=[go.Pie(
                labels=list(current_data.keys()),
                values=list(current_data.values()),
                hole=0.4,
                marker=dict(colors=px.colors.qualitative.Set3)
            )])

            fig_current.update_layout(
                height=400,
                showlegend=True,
                title_text="Güncel Portföy Dağılımı (%)"
            )

            st.plotly_chart(fig_current, use_container_width=True)

    with col2:
        st.markdown("### Başlangıç Dağılımı")
        # Pie chart for initial allocation
        initial_data = {asset_names[k]: v for k, v in initial_alloc.items() if v > 0}

        if initial_data:
            fig_initial = go.Figure(data=[go.Pie(
                labels=list(initial_data.keys()),
                values=list(initial_data.values()),
                hole=0.4,
                marker=dict(colors=px.colors.qualitative.Set3)
            )])

            fig_initial.update_layout(
                height=400,
                showlegend=True,
                title_text=f"Başlangıç Portföy Dağılımı (%)"
            )

            st.plotly_chart(fig_initial, use_container_width=True)

    # Monthly allocation changes
    st.subheader("📈 Aylık Değişimler")

    allocation_changes = summary['monthly_allocation_changes']

    if allocation_changes:
        df_changes = pd.DataFrame(allocation_changes)

        # Create stacked area chart
        fig_area = go.Figure()

        for asset_key, asset_label in asset_names.items():
            curr_col = f'{asset_key}_curr'
            if curr_col in df_changes.columns:
                fig_area.add_trace(go.Scatter(
                    x=df_changes['month'],
                    y=df_changes[curr_col],
                    name=asset_label,
                    mode='lines',
                    stackgroup='one',
                    fillcolor=px.colors.qualitative.Set3[list(asset_names.keys()).index(asset_key)]
                ))

        fig_area.update_layout(
            title="Varlık Dağılımının Zaman İçinde Değişimi",
            xaxis_title="Ay",
            yaxis_title="Oran (%)",
            height=500,
            hovermode='x unified'
        )

        st.plotly_chart(fig_area, use_container_width=True)

        # Changes table
        st.markdown("### 📋 Değişim Detayları")

        changes_display = []
        for _, row in df_changes.iterrows():
            month_data = {'Ay': row['month']}

            for asset_key, asset_label in asset_names.items():
                change_col = f'{asset_key}_change'
                if change_col in row:
                    change_val = row[change_col]
                    if abs(change_val) > 0.1:  # Show only significant changes
                        month_data[asset_label] = f"{change_val:+.2f}%"

            if len(month_data) > 1:  # Has changes
                changes_display.append(month_data)

        if changes_display:
            st.dataframe(pd.DataFrame(changes_display), use_container_width=True)


def render_portfolio_changes_tab(summary: dict):
    """Render portfolio changes tab."""

    st.subheader("🔄 Portföy Değişimleri (Eklenen/Çıkarılan Menkul Kıymetler)")

    holdings_changes = summary['holdings_changes_by_month']

    if not holdings_changes:
        st.info("Bu dönemde portföy değişikliği bulunamadı.")
        return

    for month, changes in sorted(holdings_changes.items(), reverse=True):
        with st.expander(f"📅 {month}", expanded=len(holdings_changes) <= 3):

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### ✅ Eklenen Holdingleri")
                new_holdings = changes['new_holdings']

                if new_holdings:
                    for holding in new_holdings:
                        st.success(f"**{holding['security_name']}** ({holding['security_code']})\n- Ağırlık: {holding['weight']:.2f}%")
                else:
                    st.info("Eklenen holding yok")

            with col2:
                st.markdown("#### ❌ Çıkarılan Holdingleri")
                removed_holdings = changes['removed_holdings']

                if removed_holdings:
                    for holding in removed_holdings:
                        st.error(f"**{holding['security_name']}** ({holding['security_code']})\n- Önceki Ağırlık: {holding['weight']:.2f}%")
                else:
                    st.info("Çıkarılan holding yok")

            with col3:
                st.markdown("#### 🔀 Önemli Ağırlık Değişimleri")
                weight_changes = changes['weight_changes']

                if weight_changes:
                    for change in weight_changes[:5]:  # Top 5
                        delta = change['change']
                        color = "🟢" if delta > 0 else "🔴"
                        st.write(f"{color} **{change['security_name']}**")
                        st.write(f"  {change['prev_weight']:.2f}% → {change['curr_weight']:.2f}% ({delta:+.2f}%)")
                else:
                    st.info("Önemli değişim yok")


def render_top_holdings_tab(summary: dict):
    """Render top holdings evolution tab."""

    st.subheader("🏆 En Büyük Holdinglerin Zaman İçinde Değişimi")

    top_holdings = summary['top_holdings_evolution']

    if not top_holdings:
        st.info("Top holdings verisi bulunamadı.")
        return

    df_top = pd.DataFrame(top_holdings)

    # Create heatmap showing top holdings evolution
    pivot = df_top.pivot(index='security_name', columns='month', values='weight')

    if not pivot.empty:
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='RdYlGn',
            text=pivot.values,
            texttemplate='%{text:.1f}%',
            textfont={"size": 10},
            colorbar=dict(title="Ağırlık (%)")
        ))

        fig.update_layout(
            title="Top Holdings Ağırlık Haritası",
            xaxis_title="Ay",
            yaxis_title="Menkul Kıymet",
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

    # Current top 10
    st.markdown("### 📊 Güncel Top 10 Holdings")

    latest_month = df_top['month'].max()
    latest_top = df_top[df_top['month'] == latest_month].sort_values('rank')

    if not latest_top.empty:
        # Bar chart
        fig_bar = go.Figure(data=[
            go.Bar(
                x=latest_top['weight'],
                y=latest_top['security_name'],
                orientation='h',
                marker=dict(
                    color=latest_top['weight'],
                    colorscale='Viridis',
                    showscale=True
                ),
                text=latest_top['weight'].apply(lambda x: f"{x:.2f}%"),
                textposition='auto'
            )
        ])

        fig_bar.update_layout(
            title=f"En Büyük 10 Holding - {latest_month}",
            xaxis_title="Portföy Ağırlığı (%)",
            yaxis_title="",
            height=500
        )

        st.plotly_chart(fig_bar, use_container_width=True)


def render_detailed_analysis_tab(summary: dict):
    """Render detailed analysis tab."""

    st.subheader("📈 Detaylı Analiz ve İstatistikler")

    # Summary statistics
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Portföy İstatistikleri")
        st.write(f"**Analiz Edilen Ay Sayısı:** {summary['total_months']}")
        st.write(f"**Toplam Eklenen Holding:** {summary['total_new_holdings']}")
        st.write(f"**Toplam Çıkarılan Holding:** {summary['total_removed_holdings']}")
        st.write(f"**Portföy Değer Değişimi:** ₺{summary['portfolio_value_change']:,.0f}")
        st.write(f"**Yatırımcı Sayısı Değişimi:** {summary['investor_change']:,}")

    with col2:
        st.markdown("### 📋 Varlık Sınıfı Değişimleri")

        current = summary['asset_allocation_current']
        initial = summary['asset_allocation_initial']

        asset_names = {
            'stocks': 'Hisse',
            'bonds': 'Tahvil',
            'bills': 'Bono',
            'repo': 'Repo',
            'fx': 'Döviz'
        }

        for key, name in asset_names.items():
            if key in current and key in initial:
                change = current[key] - initial[key]
                if abs(change) > 0.5:
                    st.write(f"**{name}:** {initial[key]:.2f}% → {current[key]:.2f}% ({change:+.2f}%)")

    # Download data
    st.markdown("---")
    st.markdown("### 💾 Veriyi İndir")

    col1, col2 = st.columns(2)

    with col1:
        if summary['monthly_allocation_changes']:
            df_alloc = pd.DataFrame(summary['monthly_allocation_changes'])
            csv_alloc = df_alloc.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Varlık Dağılımı (CSV)",
                data=csv_alloc,
                file_name=f"{summary['fund_code']}_asset_allocation.csv",
                mime="text/csv"
            )

    with col2:
        if summary['top_holdings_evolution']:
            df_holdings = pd.DataFrame(summary['top_holdings_evolution'])
            csv_holdings = df_holdings.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Top Holdings (CSV)",
                data=csv_holdings,
                file_name=f"{summary['fund_code']}_top_holdings.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    create_tefas_portfolio_analysis_ui()
