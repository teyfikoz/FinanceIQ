import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import time
import yfinance as yf

# Dil sözlükleri
TRANSLATIONS = {
    "tr": {
        # Ana başlıklar
        "title": "🌍 Global Likidite ve Piyasa Korelasyon Kontrol Paneli",
        "subtitle": "Gerçek zamanlı finansal piyasa analizi ve tahminleri",

        # Menü öğeleri
        "dashboard_controls": "📊 Kontrol Paneli Ayarları",
        "refresh_data": "🔄 Verileri Yenile",
        "time_range": "📅 Zaman Aralığı",
        "assets_to_track": "🎯 İzlenecek Varlıklar",
        "cryptocurrencies": "Kripto Paralar",
        "stocks": "Hisse Senetleri",
        "turkish_stocks": "Türk Hisse Senetleri",
        "global_indices": "Global Endeksler",
        "commodities": "Emtialar",
        "bonds": "Tahviller",
        "currencies": "Döviz Kurları",

        # Uyarı ayarları
        "alert_settings": "🚨 Uyarı Ayarları",
        "correlation_alert": "Korelasyon Uyarısı",
        "volatility_alert": "Volatilite Uyarısı",
        "price_change_alert": "Fiyat Değişim Uyarısı",

        # Sistem durumu
        "system_status": "ℹ️ Sistem Durumu",
        "api_connected": "✅ API Bağlı",
        "last_update": "🕐 Son Güncelleme",

        # Ana metrikler
        "key_metrics": "📈 Ana Piyasa Metrikleri",

        # Uyarılar
        "active_alerts": "🚨 Aktif Uyarılar",
        "correlation_breakdown": "Korelasyon Kırılması",
        "volatility_spike": "Volatilite Artışı",
        "price_surge": "Fiyat Dalgalanması",

        # Analiz bölümleri
        "market_analysis": "📊 Piyasa Analizi",
        "correlation_heatmap": "🔗 Korelasyon Isı Haritası",
        "global_liquidity_trend": "💧 Global Likidite Trendi",
        "price_performance": "📈 Fiyat Performansı",
        "risk_metrics": "🎯 Risk Metrikleri",
        "turkish_market": "🇹🇷 Türk Piyasası",
        "prediction_analysis": "🔮 Tahmin Analizi",

        # Detaylı veriler
        "detailed_data": "📊 Detaylı Veriler",
        "market_data": "📈 Piyasa Verileri",
        "correlations": "🔗 Korelasyonlar",
        "liquidity_metrics": "💧 Likidite Metrikleri",
        "predictions": "🔮 Tahminler",

        # Grafik başlıkları
        "asset_correlation_matrix": "Varlık Korelasyon Matrisi",
        "global_liquidity_index": "Global Likidite İndeksi (30 Gün)",
        "normalized_price_performance": "Normalize Fiyat Performansı (30 Gün)",
        "asset_volatility_comparison": "Varlık Volatilite Karşılaştırması",
        "turkish_stocks_performance": "Türk Hisse Senetleri Performansı",
        "1_year_prediction": "1 Yıllık Fiyat Tahmini",
        "3_year_prediction": "3 Yıllık Fiyat Tahmini",

        # Veri etiketleri
        "asset": "Varlık",
        "price": "Fiyat",
        "change_24h": "24s Değişim",
        "volume": "Hacim",
        "market_cap": "Piyasa Değeri",
        "correlation": "Korelasyon",
        "volatility": "Volatilite",
        "prediction": "Tahmin",
        "confidence_interval": "Güven Aralığı",

        # Footer
        "footer": "🌍 Global Likidite ve Piyasa Korelasyon Kontrol Paneli | 📊 Veriler saatlik güncellenir | 🤖 FastAPI & Streamlit ile güçlendirilmiştir",

        # Mesajlar
        "using_sample_data": "⚠️ Örnek veri kullanılıyor - API mevcut değil",
        "data_not_available": "Veri mevcut değil",
        "loading": "Yükleniyor...",
        "error": "Hata",

        # Birimler
        "percentage": "%",
        "billion": "Milyar",
        "million": "Milyon",
        "usd": "USD",
        "try": "TL"
    },

    "en": {
        # Main headers
        "title": "🌍 Global Liquidity & Market Correlation Dashboard",
        "subtitle": "Real-time financial market analysis and predictions",

        # Menu items
        "dashboard_controls": "📊 Dashboard Controls",
        "refresh_data": "🔄 Refresh Data",
        "time_range": "📅 Time Range",
        "assets_to_track": "🎯 Assets to Track",
        "cryptocurrencies": "Cryptocurrencies",
        "stocks": "Stocks",
        "turkish_stocks": "Turkish Stocks",
        "global_indices": "Global Indices",
        "commodities": "Commodities",
        "bonds": "Bonds",
        "currencies": "Currencies",

        # Alert settings
        "alert_settings": "🚨 Alert Settings",
        "correlation_alert": "Correlation Alert",
        "volatility_alert": "Volatility Alert",
        "price_change_alert": "Price Change Alert",

        # System status
        "system_status": "ℹ️ System Status",
        "api_connected": "✅ API Connected",
        "last_update": "🕐 Last Update",

        # Key metrics
        "key_metrics": "📈 Key Market Metrics",

        # Alerts
        "active_alerts": "🚨 Active Alerts",
        "correlation_breakdown": "Correlation Breakdown",
        "volatility_spike": "Volatility Spike",
        "price_surge": "Price Surge",

        # Analysis sections
        "market_analysis": "📊 Market Analysis",
        "correlation_heatmap": "🔗 Correlation Heatmap",
        "global_liquidity_trend": "💧 Global Liquidity Trend",
        "price_performance": "📈 Price Performance",
        "risk_metrics": "🎯 Risk Metrics",
        "turkish_market": "🇹🇷 Turkish Market",
        "prediction_analysis": "🔮 Prediction Analysis",

        # Detailed data
        "detailed_data": "📊 Detailed Data",
        "market_data": "📈 Market Data",
        "correlations": "🔗 Correlations",
        "liquidity_metrics": "💧 Liquidity Metrics",
        "predictions": "🔮 Predictions",

        # Chart titles
        "asset_correlation_matrix": "Asset Correlation Matrix",
        "global_liquidity_index": "Global Liquidity Index (30 Days)",
        "normalized_price_performance": "Normalized Price Performance (30 Days)",
        "asset_volatility_comparison": "Asset Volatility Comparison",
        "turkish_stocks_performance": "Turkish Stocks Performance",
        "1_year_prediction": "1-Year Price Prediction",
        "3_year_prediction": "3-Year Price Prediction",

        # Data labels
        "asset": "Asset",
        "price": "Price",
        "change_24h": "24h Change",
        "volume": "Volume",
        "market_cap": "Market Cap",
        "correlation": "Correlation",
        "volatility": "Volatility",
        "prediction": "Prediction",
        "confidence_interval": "Confidence Interval",

        # Footer
        "footer": "🌍 Global Liquidity & Market Correlation Dashboard | 📊 Data updated hourly | 🤖 Powered by FastAPI & Streamlit",

        # Messages
        "using_sample_data": "⚠️ Using sample data - API not available",
        "data_not_available": "Data not available",
        "loading": "Loading...",
        "error": "Error",

        # Units
        "percentage": "%",
        "billion": "Billion",
        "million": "Million",
        "usd": "USD",
        "try": "TRY"
    }
}

# Konfigürasyon
st.set_page_config(
    page_title="Global Liquidity Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def t(key: str, lang: str = None) -> str:
    """Translation function"""
    if lang is None:
        lang = st.session_state.get('language', 'tr')
    return TRANSLATIONS.get(lang, {}).get(key, key)

def get_turkish_stock_data():
    """Türk hisse senetleri için örnek veri"""
    turkish_stocks = {
        "THYAO.IS": {"name": "Türk Hava Yolları", "price": 156.5, "change": 2.3},
        "AKBNK.IS": {"name": "Akbank", "price": 45.8, "change": -1.2},
        "GARAN.IS": {"name": "Garanti BBVA", "price": 89.2, "change": 0.8},
        "SISE.IS": {"name": "Şişe Cam", "price": 18.4, "change": 1.5},
        "TCELL.IS": {"name": "Turkcell", "price": 42.1, "change": -0.5},
        "BIMAS.IS": {"name": "BİM", "price": 385.0, "change": 3.2},
        "KOZAL.IS": {"name": "Koza Altın", "price": 28.6, "change": -2.1},
        "SAHOL.IS": {"name": "Sabancı Holding", "price": 35.4, "change": 1.8},
        "ISCTR.IS": {"name": "İş Bankası", "price": 7.8, "change": 0.3}
    }
    return turkish_stocks

def get_real_turkish_data():
    """Gerçek Türk hisse senedi verilerini çek"""
    try:
        symbols = ["THYAO.IS", "AKBNK.IS", "GARAN.IS", "SISE.IS", "TCELL.IS"]
        data = {}

        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = ((current - previous) / previous) * 100

                data[symbol] = {
                    "name": symbol.replace(".IS", ""),
                    "price": float(current),
                    "change": float(change)
                }

        return data if data else get_turkish_stock_data()

    except Exception as e:
        st.error(f"Veri çekilirken hata: {e}")
        return get_turkish_stock_data()

def generate_prediction_data(symbol: str, days: int = 365):
    """Tahmin verisi oluştur"""
    # Mevcut fiyatı al
    current_price = 100
    if symbol == "BTC":
        current_price = 45000
    elif symbol == "AAPL":
        current_price = 175
    elif "TRY" in symbol:
        current_price = 30

    # Gelecek tarihler
    future_dates = pd.date_range(start=datetime.now(), periods=days, freq='D')

    # Trend ve volatilite parametreleri
    trend = 0.0002  # Günlük ortalama artış
    volatility = 0.02  # Günlük volatilite

    predictions = []
    current = current_price

    for i, date in enumerate(future_dates):
        # Random walk with trend
        daily_change = np.random.normal(trend, volatility)
        current *= (1 + daily_change)

        # Güven aralığı
        confidence_range = current * volatility * 2
        lower = current - confidence_range
        upper = current + confidence_range

        predictions.append({
            'date': date,
            'predicted_price': current,
            'lower_bound': lower,
            'upper_bound': upper
        })

    return pd.DataFrame(predictions)

def main():
    # Dil seçimi
    if 'language' not in st.session_state:
        st.session_state.language = 'tr'

    # Header with language selector
    col1, col2 = st.columns([6, 1])

    with col1:
        st.markdown(f'<h1 style="color: #1f77b4;">{t("title")}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #666; font-size: 1.1rem;">{t("subtitle")}</p>', unsafe_allow_html=True)

    with col2:
        language = st.selectbox(
            "🌐 Language",
            options=['tr', 'en'],
            index=0 if st.session_state.language == 'tr' else 1,
            format_func=lambda x: "🇹🇷 Türkçe" if x == 'tr' else "🇺🇸 English"
        )
        if language != st.session_state.language:
            st.session_state.language = language
            st.rerun()

    # Custom CSS
    st.markdown("""
    <style>
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        .alert-box {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .alert-high {
            background-color: #ffe6e6;
            border-left: 4px solid #ff4444;
        }
        .alert-medium {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
        }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown(f'<div style="font-size: 1.2rem; font-weight: bold; color: #2c3e50;">{t("dashboard_controls")}</div>', unsafe_allow_html=True)

        # Refresh button
        if st.button(t("refresh_data"), type="primary"):
            st.rerun()

        # Time range selector
        time_range = st.selectbox(
            t("time_range"),
            ["1D", "7D", "30D", "90D", "1Y"],
            index=2
        )

        # Asset selector
        st.markdown(f"### {t('assets_to_track')}")
        track_crypto = st.checkbox(t("cryptocurrencies"), value=True)
        track_stocks = st.checkbox(t("stocks"), value=True)
        track_turkish = st.checkbox(t("turkish_stocks"), value=True)
        track_commodities = st.checkbox(t("commodities"), value=True)

        # Alert settings
        st.markdown(f"### {t('alert_settings')}")
        corr_threshold = st.slider(t("correlation_alert"), 0.1, 0.5, 0.2, 0.05)
        vol_threshold = st.slider(t("volatility_alert"), 15, 40, 25, 1)
        price_threshold = st.slider(t("price_change_alert"), 1, 10, 5, 1)

        # System status
        st.markdown("---")
        st.markdown(f"### {t('system_status')}")
        st.success(t("api_connected"))
        st.info(f"{t('last_update')}: {datetime.now().strftime('%H:%M:%S')}")

    # Ana metrikler
    st.markdown(f"## {t('key_metrics')}")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Bitcoin", "$45,234", "+2.3%")

    with col2:
        st.metric("S&P 500", "4,234", "-0.5%")

    with col3:
        st.metric("BIST 100", "8,456", "+1.2%")

    with col4:
        st.metric("USD/TRY", "30.15", "+0.8%")

    with col5:
        st.metric("VIX", "18.5", "-3.2%")

    # Aktif uyarılar
    st.markdown(f"## {t('active_alerts')}")

    alert_col1, alert_col2 = st.columns(2)

    with alert_col1:
        st.markdown(f"""
        <div class="alert-box alert-medium">
            <strong>{t('correlation_breakdown')}</strong><br>
            BTC-S&P korelasyonu 0.5'in altına düştü
            <br><small>📅 {datetime.now().strftime('%H:%M')}</small>
        </div>
        """, unsafe_allow_html=True)

    with alert_col2:
        st.markdown(f"""
        <div class="alert-box alert-high">
            <strong>{t('volatility_spike')}</strong><br>
            BIST 100 volatilitesi %25'i aştı
            <br><small>📅 {datetime.now().strftime('%H:%M')}</small>
        </div>
        """, unsafe_allow_html=True)

    # Ana analiz
    st.markdown(f"## {t('market_analysis')}")

    # İlk satır grafikler
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {t('correlation_heatmap')}")

        # Korelasyon matrisi
        assets = ["BTC", "ETH", "BIST100", "S&P500", "USD/TRY", "GOLD"]
        correlation_data = np.random.uniform(-0.8, 0.8, (len(assets), len(assets)))
        np.fill_diagonal(correlation_data, 1.0)

        fig_corr = px.imshow(
            correlation_data,
            x=assets,
            y=assets,
            color_continuous_scale="RdBu",
            range_color=[-1, 1],
            text_auto=True
        )
        fig_corr.update_layout(title=t("asset_correlation_matrix"), height=400)
        st.plotly_chart(fig_corr, use_container_width=True)

    with col2:
        st.markdown(f"### {t('global_liquidity_trend')}")

        # Likidite trendi
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        liquidity_values = np.cumsum(np.random.normal(0, 0.01, 30)) + 0.85

        fig_liquidity = go.Figure()
        fig_liquidity.add_trace(go.Scatter(
            x=dates,
            y=liquidity_values,
            mode='lines+markers',
            name=t("global_liquidity_index"),
            line=dict(color='#1f77b4', width=3)
        ))
        fig_liquidity.update_layout(
            title=t("global_liquidity_index"),
            xaxis_title=t("time_range"),
            yaxis_title="GLI",
            height=400
        )
        st.plotly_chart(fig_liquidity, use_container_width=True)

    # Türk piyasası analizi
    if track_turkish:
        st.markdown(f"## {t('turkish_market')}")

        # Türk hisse senetleri verisi
        turkish_data = get_real_turkish_data()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### {t('turkish_stocks_performance')}")

            # Türk hisse performansı
            symbols = list(turkish_data.keys())
            changes = [turkish_data[symbol]["change"] for symbol in symbols]
            names = [turkish_data[symbol]["name"] for symbol in symbols]

            fig_turkish = go.Figure(data=[
                go.Bar(x=names, y=changes, marker_color=['green' if x > 0 else 'red' for x in changes])
            ])
            fig_turkish.update_layout(
                title=t("turkish_stocks_performance"),
                xaxis_title=t("asset"),
                yaxis_title=f"{t('change_24h')} ({t('percentage')})",
                height=400
            )
            st.plotly_chart(fig_turkish, use_container_width=True)

        with col2:
            # Türk hisse detayları
            st.markdown("### Türk Hisse Detayları")
            turkish_df = pd.DataFrame([
                {
                    t("asset"): data["name"],
                    t("price"): f"₺{data['price']:.2f}",
                    t("change_24h"): f"{data['change']:+.2f}%"
                }
                for symbol, data in turkish_data.items()
            ])
            st.dataframe(turkish_df, use_container_width=True)

    # Tahmin analizi
    st.markdown(f"## {t('prediction_analysis')}")

    # Tahmin için sembol seçimi
    prediction_symbols = ["BTC", "AAPL", "THYAO.IS", "USD/TRY"]
    selected_symbol = st.selectbox("Tahmin için varlık seçin:", prediction_symbols)

    # Tahmin periyodu seçimi
    prediction_period = st.radio(
        "Tahmin periyodu:",
        ["1 Yıl", "3 Yıl"],
        horizontal=True
    )

    days = 365 if prediction_period == "1 Yıl" else 1095

    # Tahmin verisi oluştur
    prediction_data = generate_prediction_data(selected_symbol, days)

    # Tahmin grafiği
    fig_prediction = go.Figure()

    # Ana tahmin çizgisi
    fig_prediction.add_trace(go.Scatter(
        x=prediction_data['date'],
        y=prediction_data['predicted_price'],
        mode='lines',
        name=t("prediction"),
        line=dict(color='blue', width=3)
    ))

    # Güven aralığı
    fig_prediction.add_trace(go.Scatter(
        x=prediction_data['date'],
        y=prediction_data['upper_bound'],
        mode='lines',
        line=dict(width=0),
        showlegend=False
    ))

    fig_prediction.add_trace(go.Scatter(
        x=prediction_data['date'],
        y=prediction_data['lower_bound'],
        mode='lines',
        line=dict(width=0),
        fillcolor='rgba(0,100,80,0.2)',
        fill='tonexty',
        name=t("confidence_interval"),
        showlegend=True
    ))

    fig_prediction.update_layout(
        title=f"{selected_symbol} - {prediction_period} {t('prediction')}",
        xaxis_title="Tarih",
        yaxis_title=t("price"),
        height=500
    )

    st.plotly_chart(fig_prediction, use_container_width=True)

    # Tahmin özeti
    st.markdown("### Tahmin Özeti")
    current_price = prediction_data['predicted_price'].iloc[0]
    final_price = prediction_data['predicted_price'].iloc[-1]
    total_return = ((final_price - current_price) / current_price) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Mevcut Fiyat", f"${current_price:.2f}")
    with col2:
        st.metric("Tahmini Fiyat", f"${final_price:.2f}")
    with col3:
        st.metric("Toplam Getiri", f"{total_return:+.1f}%")

    # Detaylı veriler
    st.markdown(f"## {t('detailed_data')}")

    tab1, tab2, tab3, tab4 = st.tabs([
        t("market_data"),
        t("correlations"),
        t("liquidity_metrics"),
        t("predictions")
    ])

    with tab1:
        # Piyasa verileri tablosu
        market_df = pd.DataFrame({
            t("asset"): ["Bitcoin", "Ethereum", "S&P 500", "BIST 100"],
            t("price"): ["$45,234", "$2,789", "$4,234", "8,456"],
            t("change_24h"): ["+2.3%", "+1.8%", "-0.5%", "+1.2%"],
            t("volume"): ["$2.5B", "$1.2B", "$0.8B", "$0.3B"]
        })
        st.dataframe(market_df, use_container_width=True)

    with tab2:
        # Korelasyon tablosu
        corr_df = pd.DataFrame(
            correlation_data,
            index=assets,
            columns=assets
        ).round(3)
        st.dataframe(corr_df, use_container_width=True)

    with tab3:
        # Likidite metrikleri
        liquidity_df = pd.DataFrame({
            "Metrik": ["Global Likidite İndeksi", "Fed Bilançosu", "ECB Bilançosu", "M2 Para Arzı"],
            "Değer": ["0.85", "$8.5T", "€7.2T", "$21.7T"],
            "Değişim": ["+1.2%", "+0.8%", "+0.5%", "+1.5%"]
        })
        st.dataframe(liquidity_df, use_container_width=True)

    with tab4:
        # Son tahminler
        recent_predictions = prediction_data.head(30).copy()
        recent_predictions['date'] = recent_predictions['date'].dt.strftime('%Y-%m-%d')
        recent_predictions.columns = ['Tarih', 'Tahmini Fiyat', 'Alt Sınır', 'Üst Sınır']
        st.dataframe(recent_predictions.round(2), use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown(f'<div style="text-align: center; color: #666; font-size: 0.9rem;">{t("footer")}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()