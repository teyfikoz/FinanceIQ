#!/usr/bin/env python3
"""
Turkish Markets Analysis - Dedicated page for Turkish stocks and funds
Türk Piyasaları Analizi - Türk hisse senetleri ve fonları için özel sayfa
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional, Any
import yfinance as yf

# Sayfa yapılandırması
st.set_page_config(
    page_title="🇹🇷 Türk Piyasaları",
    page_icon="🇹🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stil
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }

    .stock-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 5px solid #e74c3c;
    }

    .metric-card {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        color: white;
        margin: 0.5rem 0;
    }

    .bist-card {
        background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }

    .fund-card {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Türk hisse senetleri verileri
TURKISH_STOCKS = {
    "BIST-30 Hisseleri": {
        "AKBNK.IS": {"name": "Akbank T.A.Ş.", "sector": "Bankacılık", "price": 25.48, "change": 1.4},
        "GARAN.IS": {"name": "Türkiye Garanti Bankası A.Ş.", "sector": "Bankacılık", "price": 31.72, "change": 0.8},
        "ISCTR.IS": {"name": "Türkiye İş Bankası A.Ş.", "sector": "Bankacılık", "price": 7.89, "change": -0.5},
        "THYAO.IS": {"name": "Türk Hava Yolları A.O.", "sector": "Ulaştırma", "price": 164.50, "change": 2.1},
        "KCHOL.IS": {"name": "Koç Holding A.Ş.", "sector": "Holding", "price": 22.15, "change": 1.2},
        "SAHOL.IS": {"name": "Sabancı Holding A.Ş.", "sector": "Holding", "price": 12.34, "change": 0.6},
        "ASELS.IS": {"name": "Aselsan Elektronik San. ve Tic. A.Ş.", "sector": "Savunma", "price": 89.75, "change": 3.2},
        "SISE.IS": {"name": "Şişe Cam Sanayii A.Ş.", "sector": "Cam", "price": 28.90, "change": -1.1},
        "EREGL.IS": {"name": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.", "sector": "Çelik", "price": 45.60, "change": 1.8},
        "BIMAS.IS": {"name": "BIM Birleşik Mağazalar A.Ş.", "sector": "Perakende", "price": 105.20, "change": 0.9},
        "TOASO.IS": {"name": "Tofaş Türk Otomobil Fabrikası A.Ş.", "sector": "Otomotiv", "price": 67.80, "change": -0.3},
        "TCELL.IS": {"name": "Turkcell İletişim Hizmetleri A.Ş.", "sector": "Telekomünikasyon", "price": 42.15, "change": 1.5},
        "KOZAL.IS": {"name": "Koza Altın İşletmeleri A.Ş.", "sector": "Madencilik", "price": 28.30, "change": 2.7},
        "PETKM.IS": {"name": "Petkim Petrokimya Holding A.Ş.", "sector": "Petrokimya", "price": 15.85, "change": 0.4},
        "TUPRS.IS": {"name": "Tüpraş-Türkiye Petrol Rafinerileri A.Ş.", "sector": "Petrol", "price": 156.90, "change": 1.1}
    }
}

TURKISH_FUNDS = {
    "Hisse Senedi Fonları": [
        "AEH", "AEJ", "AGH", "AGJ", "ATH", "ATJ", "AZH", "AZJ",
        "GAH", "GAJ", "GEH", "GEJ", "HEH", "HEJ", "IEH", "IEJ"
    ],
    "Tahvil Fonları": [
        "ABH", "ABJ", "DBH", "DBJ", "FBH", "FBJ", "GBH", "GBJ",
        "HBH", "HBJ", "IBH", "IBJ", "KBH", "KBJ", "TBH", "TBJ"
    ],
    "Karma Fonlar": [
        "AMH", "AMJ", "DMH", "DMJ", "FMH", "FMJ", "GMH", "GMJ",
        "HMH", "HMJ", "IMH", "IMJ", "KMH", "KMJ", "TMH", "TMJ"
    ],
    "Para Piyasası Fonları": [
        "APH", "APJ", "DPH", "DPJ", "FPH", "FPJ", "GPH", "GPJ",
        "HPH", "HPJ", "IPH", "IPJ", "KPH", "KPJ", "TPH", "TPJ"
    ]
}

def create_bist_overview():
    """BIST genel bakış kartı"""
    st.markdown("""
    <div class="bist-card">
        <h2>📊 BIST Genel Bakış</h2>
        <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
            <div>
                <h3>BIST 100</h3>
                <p style="font-size: 1.2em;">8,547.23 ▲ +1.2%</p>
            </div>
            <div>
                <h3>BIST 30</h3>
                <p style="font-size: 1.2em;">8,234.56 ▲ +0.8%</p>
            </div>
            <div>
                <h3>USD/TRY</h3>
                <p style="font-size: 1.2em;">32.45 ▼ -0.3%</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_turkish_stocks():
    """Türk hisse senetlerini göster"""
    st.markdown("## 🏛️ BIST-30 Hisse Senetleri")

    # Sektör filtresi
    sectors = list(set([stock["sector"] for stocks in TURKISH_STOCKS.values() for stock in stocks.values()]))
    selected_sector = st.selectbox("🎯 Sektör Filtresi:", ["Tümü"] + sectors)

    # Hisse senetlerini göster
    cols = st.columns(3)
    col_idx = 0

    for category, stocks in TURKISH_STOCKS.items():
        for symbol, stock_data in stocks.items():
            if selected_sector == "Tümü" or stock_data["sector"] == selected_sector:
                with cols[col_idx % 3]:
                    change_color = "green" if stock_data["change"] >= 0 else "red"
                    change_icon = "▲" if stock_data["change"] >= 0 else "▼"

                    st.markdown(f"""
                    <div class="stock-card">
                        <h4>{symbol.replace('.IS', '')}</h4>
                        <p><strong>{stock_data['name']}</strong></p>
                        <p>Sektör: {stock_data['sector']}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 1.2em; font-weight: bold;">{stock_data['price']:.2f} ₺</span>
                            <span style="color: {change_color}; font-weight: bold;">
                                {change_icon} {stock_data['change']:+.1f}%
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"📊 {symbol.replace('.IS', '')} Analiz Et", key=f"analyze_{symbol}"):
                        analyze_turkish_stock(symbol, stock_data)

                col_idx += 1

def analyze_turkish_stock(symbol: str, stock_data: Dict):
    """Türk hisse senedi analizi"""
    st.markdown(f"### 📊 {stock_data['name']} ({symbol.replace('.IS', '')}) Analizi")

    # Temel metrikler
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>{stock_data['price']:.2f} ₺</h4>
            <p>Güncel Fiyat</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        color = "linear-gradient(135deg, #27ae60 0%, #229954 100%)" if stock_data['change'] >= 0 else "linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)"
        st.markdown(f"""
        <div class="metric-card" style="background: {color}">
            <h4>{stock_data['change']:+.1f}%</h4>
            <p>Günlük Değişim</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>{stock_data['sector']}</h4>
            <p>Sektör</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        # Mock piyasa değeri
        mock_market_cap = stock_data['price'] * 1000000000  # Mock hesaplama
        st.markdown(f"""
        <div class="metric-card">
            <h4>{mock_market_cap/1e9:.1f}B ₺</h4>
            <p>Piyasa Değeri</p>
        </div>
        """, unsafe_allow_html=True)

    # Mock grafik
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    base_price = stock_data['price']
    prices = np.random.normal(base_price, base_price*0.02, len(dates))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=symbol.replace('.IS', ''),
        line=dict(color='#e74c3c', width=2)
    ))

    fig.update_layout(
        title=f"{stock_data['name']} - Son 30 Gün",
        xaxis_title="Tarih",
        yaxis_title="Fiyat (₺)",
        template="plotly_white",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def display_turkish_funds():
    """Türk fonlarını göster"""
    st.markdown("## 💰 Türk Yatırım Fonları")

    # Fon kategorilerini göster
    for category, funds in TURKISH_FUNDS.items():
        with st.expander(f"📈 {category} ({len(funds)} adet)"):

            # Fonları 6'lı gruplar halinde göster
            funds_per_row = 6
            for i in range(0, len(funds), funds_per_row):
                cols = st.columns(funds_per_row)
                for j, fund in enumerate(funds[i:i+funds_per_row]):
                    with cols[j]:
                        # Mock performans verisi
                        mock_performance = np.random.uniform(-5, 15)
                        performance_color = "green" if mock_performance >= 0 else "red"
                        performance_icon = "▲" if mock_performance >= 0 else "▼"

                        st.markdown(f"""
                        <div style="background: white; padding: 1rem; border-radius: 8px;
                                   box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;
                                   border-left: 4px solid #f39c12;">
                            <h5>{fund}</h5>
                            <p style="color: {performance_color}; font-weight: bold; margin: 0;">
                                {performance_icon} {mock_performance:+.1f}%
                            </p>
                            <small>Yıllık Getiri</small>
                        </div>
                        """, unsafe_allow_html=True)

def create_sector_analysis():
    """Sektör analizi"""
    st.markdown("## 🏭 Sektör Analizi")

    # Sektör performansı
    sectors_data = {}
    for stocks in TURKISH_STOCKS.values():
        for stock_data in stocks.values():
            sector = stock_data["sector"]
            if sector not in sectors_data:
                sectors_data[sector] = []
            sectors_data[sector].append(stock_data["change"])

    # Sektör ortalama performansları
    sector_performance = {sector: np.mean(changes) for sector, changes in sectors_data.items()}

    # Grafik
    sectors = list(sector_performance.keys())
    performances = list(sector_performance.values())

    fig = go.Figure(data=[
        go.Bar(
            x=sectors,
            y=performances,
            marker_color=['#27ae60' if p >= 0 else '#e74c3c' for p in performances],
            text=[f"{p:+.1f}%" for p in performances],
            textposition='auto'
        )
    ])

    fig.update_layout(
        title="Sektör Performans Karşılaştırması",
        xaxis_title="Sektörler",
        yaxis_title="Ortalama Değişim (%)",
        template="plotly_white",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def main():
    """Ana uygulama"""

    # Başlık
    st.markdown("""
    <div class="main-header">
        <h1>🇹🇷 Türk Piyasaları</h1>
        <p>Borsa İstanbul ve Türk yatırım fonları analiz platformu</p>
    </div>
    """, unsafe_allow_html=True)

    # BIST genel bakış
    create_bist_overview()

    # Sekme yapısı
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 BIST Hisseleri",
        "💰 Yatırım Fonları",
        "🏭 Sektör Analizi",
        "📈 Piyasa Özeti"
    ])

    with tab1:
        display_turkish_stocks()

    with tab2:
        display_turkish_funds()

    with tab3:
        create_sector_analysis()

    with tab4:
        st.markdown("### 📈 Günlük Piyasa Özeti")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>🔥 Günün Kazananları</h4>
                <p>ASELS: +3.2%</p>
                <p>KOZAL: +2.7%</p>
                <p>THYAO: +2.1%</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)">
                <h4>📉 Günün Kaybedenleri</h4>
                <p>SISE: -1.1%</p>
                <p>ISCTR: -0.5%</p>
                <p>TOASO: -0.3%</p>
            </div>
            """, unsafe_allow_html=True)

        # Günlük işlem hacmi
        st.markdown("### 💹 İşlem Hacmi")
        volume_data = {
            "Hisse": ["AKBNK", "GARAN", "THYAO", "BIMAS", "ASELS"],
            "Hacim (M ₺)": [1250, 980, 750, 650, 580]
        }
        df_volume = pd.DataFrame(volume_data)

        fig_volume = px.bar(
            df_volume,
            x="Hisse",
            y="Hacim (M ₺)",
            title="En Yüksek İşlem Hacimli Hisseler",
            color="Hacim (M ₺)",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_volume, use_container_width=True)

if __name__ == "__main__":
    main()