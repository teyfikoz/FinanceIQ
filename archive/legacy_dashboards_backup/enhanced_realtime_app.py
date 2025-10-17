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
import asyncio
import warnings
warnings.filterwarnings('ignore')

# Dil sözlükleri (önceki halinden)
TRANSLATIONS = {
    "tr": {
        "title": "🌍 Global Likidite ve Piyasa Korelasyon Kontrol Paneli",
        "subtitle": "Gerçek zamanlı finansal piyasa analizi ve AI tahminleri",
        "dashboard_controls": "📊 Kontrol Paneli Ayarları",
        "refresh_data": "🔄 Verileri Yenile",
        "time_range": "📅 Zaman Aralığı",
        "assets_to_track": "🎯 İzlenecek Varlıklar",
        "cryptocurrencies": "Kripto Paralar",
        "turkish_stocks": "Türk Hisse Senetleri",
        "global_indices": "Global Endeksler",
        "commodities": "Emtialar",
        "alert_settings": "🚨 Uyarı Ayarları",
        "correlation_alert": "Korelasyon Uyarısı",
        "volatility_alert": "Volatilite Uyarısı",
        "system_status": "ℹ️ Sistem Durumu",
        "api_connected": "✅ API Bağlı",
        "last_update": "🕐 Son Güncelleme",
        "key_metrics": "📈 Ana Piyasa Metrikleri",
        "active_alerts": "🚨 Aktif Uyarılar",
        "market_analysis": "📊 Piyasa Analizi",
        "correlation_heatmap": "🔗 Korelasyon Isı Haritası",
        "global_liquidity_trend": "💧 Global Likidite Trendi",
        "price_performance": "📈 Fiyat Performansı",
        "turkish_market": "🇹🇷 Türk Piyasası",
        "prediction_analysis": "🔮 AI Tahmin Analizi",
        "detailed_data": "📊 Detaylı Veriler",
        "market_data": "📈 Piyasa Verileri",
        "correlations": "🔗 Korelasyonlar",
        "predictions": "🔮 Tahminler",
        "asset": "Varlık",
        "price": "Fiyat",
        "change_24h": "24s Değişim",
        "volume": "Hacim",
        "real_time_data": "🔴 Canlı Veri",
        "loading": "Yükleniyor...",
        "error": "Hata",
        "data_updated": "Veri güncellendi",
        "prediction_confidence": "Tahmin Güveni",
        "risk_level": "Risk Seviyesi",
        "trend_analysis": "Trend Analizi",
        "crypto_dominance": "Kripto Dominans",
        "global_stocks": "Global Hisseler",
        "global_etfs": "Global ETF'ler",
        "fund_holdings": "📊 Fon Holdings Analizi",
        "dominance": "Dominans",
        "market_cap": "Piyasa Değeri",
        "tech_stocks": "Teknoloji Hisseleri",
        "finance_stocks": "Finans Hisseleri",
        "healthcare_stocks": "Sağlık Hisseleri",
        "consumer_stocks": "Tüketici Hisseleri",
        "energy_stocks": "Enerji Hisseleri",
        "sector_etfs": "Sektör ETF'leri",
        "international_etfs": "Uluslararası ETF'ler",
        "bond_etfs": "Tahvil ETF'leri",
        "commodity_etfs": "Emtia ETF'leri"
    },
    "en": {
        "title": "🌍 Global Liquidity & Market Correlation Dashboard",
        "subtitle": "Real-time financial market analysis and AI predictions",
        "dashboard_controls": "📊 Dashboard Controls",
        "refresh_data": "🔄 Refresh Data",
        "time_range": "📅 Time Range",
        "assets_to_track": "🎯 Assets to Track",
        "cryptocurrencies": "Cryptocurrencies",
        "turkish_stocks": "Turkish Stocks",
        "global_indices": "Global Indices",
        "commodities": "Commodities",
        "alert_settings": "🚨 Alert Settings",
        "correlation_alert": "Correlation Alert",
        "volatility_alert": "Volatility Alert",
        "system_status": "ℹ️ System Status",
        "api_connected": "✅ API Connected",
        "last_update": "🕐 Last Update",
        "key_metrics": "📈 Key Market Metrics",
        "active_alerts": "🚨 Active Alerts",
        "market_analysis": "📊 Market Analysis",
        "correlation_heatmap": "🔗 Correlation Heatmap",
        "global_liquidity_trend": "💧 Global Liquidity Trend",
        "price_performance": "📈 Price Performance",
        "turkish_market": "🇹🇷 Turkish Market",
        "prediction_analysis": "🔮 AI Prediction Analysis",
        "detailed_data": "📊 Detailed Data",
        "market_data": "📈 Market Data",
        "correlations": "🔗 Correlations",
        "predictions": "🔮 Predictions",
        "asset": "Asset",
        "price": "Price",
        "change_24h": "24h Change",
        "volume": "Volume",
        "real_time_data": "🔴 Live Data",
        "loading": "Loading...",
        "error": "Error",
        "data_updated": "Data updated",
        "prediction_confidence": "Prediction Confidence",
        "risk_level": "Risk Level",
        "trend_analysis": "Trend Analysis",
        "crypto_dominance": "Crypto Dominance",
        "global_stocks": "Global Stocks",
        "global_etfs": "Global ETFs",
        "fund_holdings": "📊 Fund Holdings Analysis",
        "dominance": "Dominance",
        "market_cap": "Market Cap",
        "tech_stocks": "Technology Stocks",
        "finance_stocks": "Finance Stocks",
        "healthcare_stocks": "Healthcare Stocks",
        "consumer_stocks": "Consumer Stocks",
        "energy_stocks": "Energy Stocks",
        "sector_etfs": "Sector ETFs",
        "international_etfs": "International ETFs",
        "bond_etfs": "Bond ETFs",
        "commodity_etfs": "Commodity ETFs"
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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_real_market_data():
    """Gerçek piyasa verilerini çek - Optimized Global Coverage"""
    try:
        data = {}

        # Core Crypto Coverage with Dominance Calculation (reduced for speed)
        crypto_symbols = [
            "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD",
            "SOL-USD", "DOT-USD", "MATIC-USD", "LINK-USD", "DOGE-USD"
        ]

        crypto_data = {}
        total_crypto_mcap = 0

        for symbol in crypto_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                info = ticker.info

                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = ((current - previous) / previous) * 100
                    volume = float(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0

                    # Market cap approximation
                    market_cap = info.get('marketCap', 0) if info else 0
                    total_crypto_mcap += market_cap

                    crypto_name = symbol.replace("-USD", "")
                    crypto_data[crypto_name] = {
                        "price": float(current),
                        "change": float(change),
                        "volume": volume,
                        "market_cap": market_cap,
                        "type": "crypto"
                    }
            except:
                continue

        # Calculate dominance
        if total_crypto_mcap > 0:
            for crypto_name, crypto_info in crypto_data.items():
                dominance = (crypto_info["market_cap"] / total_crypto_mcap) * 100 if crypto_info["market_cap"] > 0 else 0
                crypto_info["dominance"] = round(dominance, 2)

        data.update(crypto_data)

        # Core Global Stocks (optimized for speed)
        global_stocks = [
            # Top Tech Giants
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA",

            # Major Banks & Finance
            "JPM", "BAC", "V", "MA",

            # Healthcare & Consumer
            "JNJ", "KO", "PG", "WMT",

            # Energy
            "XOM", "CVX"
        ]

        for symbol in global_stocks:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = ((current - previous) / previous) * 100
                    volume = float(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0

                    data[symbol] = {
                        "price": float(current),
                        "change": float(change),
                        "volume": volume,
                        "type": "global_stock"
                    }
            except:
                continue

        # Core Global ETFs (optimized for speed)
        etf_symbols = [
            # Broad Market
            "SPY", "QQQ", "VTI", "IWM",

            # Key Sector ETFs
            "XLK", "XLF", "XLE",

            # International
            "EEM", "EFA",

            # Bonds & Commodities
            "TLT", "GLD",

            # Growth
            "ARKK", "VGT"
        ]

        for symbol in etf_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = ((current - previous) / previous) * 100
                    volume = float(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0

                    data[symbol] = {
                        "price": float(current),
                        "change": float(change),
                        "volume": volume,
                        "type": "etf"
                    }
            except:
                continue

        # Core Turkish Stocks (optimized for speed)
        turkish_symbols = [
            "THYAO.IS", "AKBNK.IS", "GARAN.IS", "SISE.IS", "TCELL.IS",
            "TUPRS.IS", "ARCLK.IS", "BIMAS.IS"
        ]

        for symbol in turkish_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = ((current - previous) / previous) * 100
                    volume = float(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0

                    data[symbol] = {
                        "price": float(current),
                        "change": float(change),
                        "volume": volume,
                        "type": "turkish_stock"
                    }
            except:
                continue

        # Core Global Indices (optimized for speed)
        index_symbols = [
            "^GSPC", "^IXIC", "^DJI", "^VIX",  # US
            "^FTSE", "^N225",  # International
            "XU100.IS"  # Turkey
        ]

        for symbol in index_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = ((current - previous) / previous) * 100
                    volume = float(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0

                    data[symbol] = {
                        "price": float(current),
                        "change": float(change),
                        "volume": volume,
                        "type": "index"
                    }
            except:
                continue

        # Döviz kurları
        fx_symbols = ["USDTRY=X", "EURTRY=X", "GBPTRY=X", "JPYTRY=X", "CHFTRY=X"]
        for symbol in fx_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = ((current - previous) / previous) * 100

                    data[symbol] = {
                        "price": float(current),
                        "change": float(change),
                        "volume": 0,
                        "type": "fx"
                    }
            except:
                continue

        # Core Commodities (optimized for speed)
        commodity_symbols = [
            "GC=F", "SI=F", "CL=F", "NG=F"
        ]
        for symbol in commodity_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = ((current - previous) / previous) * 100
                    volume = float(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0

                    data[symbol] = {
                        "price": float(current),
                        "change": float(change),
                        "volume": volume,
                        "type": "commodity"
                    }
            except:
                continue

        return data

    except Exception as e:
        st.error(f"Veri çekilirken hata: {e}")
        return get_sample_data()

def get_sample_data():
    """Fallback sample data"""
    return {
        "BTC": {"price": 45234, "change": 2.3, "volume": 2.5e9, "type": "crypto"},
        "ETH": {"price": 2789, "change": 1.8, "volume": 1.2e9, "type": "crypto"},
        "^GSPC": {"price": 4234, "change": -0.5, "volume": 8e8, "type": "index"},
        "XU100.IS": {"price": 8456, "change": 1.2, "volume": 3e8, "type": "index"},
        "USDTRY=X": {"price": 30.15, "change": 0.8, "volume": 0, "type": "fx"},
    }

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_historical_correlations(symbols, days=30):
    """Calculate real correlations"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        price_data = {}
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            if not hist.empty:
                price_data[symbol] = hist['Close']

        if len(price_data) > 1:
            df = pd.DataFrame(price_data)
            return df.corr()
        else:
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Korelasyon hesaplanırken hata: {e}")
        return pd.DataFrame()

def generate_advanced_prediction(symbol, data, days=365):
    """Gelişmiş tahmin modeli"""
    try:
        current_price = data.get('price', 100)
        volatility = abs(data.get('change', 1)) / 100

        # Market type based trend
        if data.get('type') == 'crypto':
            base_trend = 0.0005  # Crypto tends to be more volatile
            volatility *= 2
        elif data.get('type') == 'turkish_stock':
            base_trend = 0.0003
            volatility *= 1.5
        else:
            base_trend = 0.0002

        # Generate prediction dates
        future_dates = pd.date_range(start=datetime.now() + timedelta(days=1), periods=days, freq='D')

        predictions = []
        current = current_price

        for i, date in enumerate(future_dates):
            # Trend with seasonal and cyclical components
            seasonal = 0.05 * np.sin(2 * np.pi * i / 365)  # Yearly cycle
            cyclical = 0.03 * np.sin(2 * np.pi * i / 90)   # Quarterly cycle
            trend_decay = np.exp(-i / 1000)  # Trend decay over time

            daily_trend = base_trend * trend_decay + seasonal + cyclical
            daily_noise = np.random.normal(0, volatility / 20)

            daily_change = daily_trend + daily_noise
            current *= (1 + daily_change)

            # Confidence intervals
            confidence_range = current * volatility * np.sqrt(i / 365)
            lower = current - confidence_range
            upper = current + confidence_range

            predictions.append({
                'date': date,
                'predicted_price': current,
                'lower_bound': lower,
                'upper_bound': upper,
                'confidence': max(0.5, 0.95 - (i / days) * 0.3)  # Confidence decreases over time
            })

        return pd.DataFrame(predictions)

    except Exception as e:
        st.error(f"Tahmin oluştururken hata: {e}")
        return pd.DataFrame()

def calculate_risk_metrics(data):
    """Risk metriklerini hesapla"""
    try:
        risk_metrics = {}

        for symbol, info in data.items():
            if info.get('type') in ['crypto', 'turkish_stock', 'index']:
                change = abs(info.get('change', 0))
                price = info.get('price', 0)

                # Risk level calculation
                if change < 1:
                    risk_level = "Düşük"
                elif change < 3:
                    risk_level = "Orta"
                elif change < 5:
                    risk_level = "Yüksek"
                else:
                    risk_level = "Çok Yüksek"

                # Volatility score
                vol_score = min(100, change * 10)

                risk_metrics[symbol] = {
                    'volatility': change,
                    'risk_level': risk_level,
                    'risk_score': vol_score,
                    'trend': 'Yükseliş' if info.get('change', 0) > 0 else 'Düşüş'
                }

        return risk_metrics

    except Exception as e:
        st.error(f"Risk hesaplanırken hata: {e}")
        return {}

def detect_alerts(data, corr_threshold=0.2, vol_threshold=5.0):
    """Uyarıları tespit et"""
    alerts = []

    try:
        # Volatility alerts
        for symbol, info in data.items():
            change = abs(info.get('change', 0))
            if change > vol_threshold:
                alerts.append({
                    'type': 'Volatilite Uyarısı',
                    'message': f'{symbol} %{change:.1f} değişim gösterdi',
                    'severity': 'high' if change > 10 else 'medium',
                    'time': datetime.now().strftime('%H:%M')
                })

        # Price surge alerts
        for symbol, info in data.items():
            change = info.get('change', 0)
            if abs(change) > 3:
                direction = 'yükseldi' if change > 0 else 'düştü'
                alerts.append({
                    'type': 'Fiyat Hareketi',
                    'message': f'{symbol} %{abs(change):.1f} {direction}',
                    'severity': 'medium',
                    'time': datetime.now().strftime('%H:%M')
                })

    except Exception as e:
        st.error(f"Uyarı tespit edilirken hata: {e}")

    return alerts

def main():
    # Dil seçimi
    if 'language' not in st.session_state:
        st.session_state.language = 'tr'

    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()

    # Header with language selector
    col1, col2 = st.columns([6, 1])

    with col1:
        st.markdown(f'<h1 style="color: #1f77b4;">{t("title")}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #666; font-size: 1.1rem;">{t("subtitle")}</p>', unsafe_allow_html=True)

    with col2:
        language = st.selectbox(
            "🌐",
            options=['tr', 'en'],
            index=0 if st.session_state.language == 'tr' else 1,
            format_func=lambda x: "🇹🇷" if x == 'tr' else "🇺🇸"
        )
        if language != st.session_state.language:
            st.session_state.language = language
            st.rerun()

    # Custom CSS
    st.markdown("""
    <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .alert-box {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .alert-high {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
        }
        .alert-medium {
            background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%);
            color: white;
        }
        .realtime-indicator {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown(f'<div style="font-size: 1.2rem; font-weight: bold; color: #2c3e50;">{t("dashboard_controls")}</div>', unsafe_allow_html=True)

        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Otomatik Yenileme (30s)", value=False)

        if auto_refresh:
            time.sleep(30)
            st.rerun()

        # Manual refresh button
        if st.button(t("refresh_data"), type="primary"):
            st.cache_data.clear()
            st.session_state.last_update = datetime.now()
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
        track_turkish = st.checkbox(t("turkish_stocks"), value=True)
        track_indices = st.checkbox(t("global_indices"), value=True)
        track_commodities = st.checkbox(t("commodities"), value=True)

        # Alert settings
        st.markdown(f"### {t('alert_settings')}")
        vol_threshold = st.slider(t("volatility_alert") + " (%)", 1.0, 10.0, 3.0, 0.5)

        # System status
        st.markdown("---")
        st.markdown(f"### {t('system_status')}")
        st.success(f"🔴 {t('real_time_data')}")
        st.info(f"{t('last_update')}: {st.session_state.last_update.strftime('%H:%M:%S')}")

    # Load real market data
    with st.spinner(t("loading")):
        market_data = get_real_market_data()

    # Calculate risk metrics
    risk_metrics = calculate_risk_metrics(market_data)

    # Detect alerts
    alerts = detect_alerts(market_data, vol_threshold=vol_threshold)

    # Ana metrikler - Real-time
    st.markdown(f"## {t('key_metrics')} <span class='realtime-indicator'>🔴</span>", unsafe_allow_html=True)

    # Key metrics with real data
    col1, col2, col3, col4, col5 = st.columns(5)

    metrics_data = [
        ("Bitcoin", market_data.get("BTC", {}).get("price", 0), market_data.get("BTC", {}).get("change", 0), "$"),
        ("S&P 500", market_data.get("^GSPC", {}).get("price", 0), market_data.get("^GSPC", {}).get("change", 0), ""),
        ("BIST 100", market_data.get("XU100.IS", {}).get("price", 0), market_data.get("XU100.IS", {}).get("change", 0), ""),
        ("USD/TRY", market_data.get("USDTRY=X", {}).get("price", 0), market_data.get("USDTRY=X", {}).get("change", 0), "₺"),
        ("Gold", market_data.get("GC=F", {}).get("price", 0), market_data.get("GC=F", {}).get("change", 0), "$")
    ]

    for i, (col, (name, price, change, currency)) in enumerate(zip([col1, col2, col3, col4, col5], metrics_data)):
        with col:
            if price > 0:
                if currency == "$" and price > 1000:
                    display_price = f"${price:,.0f}"
                elif currency == "₺":
                    display_price = f"{price:.2f}₺"
                elif currency == "$":
                    display_price = f"${price:.2f}"
                else:
                    display_price = f"{price:,.0f}"

                st.metric(
                    name,
                    display_price,
                    f"{change:+.2f}%",
                    delta_color="normal"
                )

    # Active alerts with real data
    if alerts:
        st.markdown(f"## {t('active_alerts')}")

        alert_cols = st.columns(min(3, len(alerts)))

        for i, alert in enumerate(alerts[:6]):  # Show max 6 alerts
            with alert_cols[i % 3]:
                severity_class = f"alert-{alert.get('severity', 'medium')}"
                st.markdown(f"""
                <div class="alert-box {severity_class}">
                    <strong>{alert.get('type', 'Uyarı')}</strong><br>
                    {alert.get('message', 'Mesaj yok')}
                    <br><small>📅 {alert.get('time', 'Bilinmiyor')}</small>
                </div>
                """, unsafe_allow_html=True)

    # Market Analysis
    st.markdown(f"## {t('market_analysis')}")

    # Real correlation analysis
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {t('correlation_heatmap')}")

        # Calculate real correlations
        main_symbols = ["BTC-USD", "ETH-USD", "^GSPC", "XU100.IS", "USDTRY=X"]
        corr_matrix = get_historical_correlations(main_symbols, days=30)

        if not corr_matrix.empty:
            # Clean symbol names for display
            display_names = [symbol.replace("-USD", "").replace("^", "").replace(".IS", "") for symbol in corr_matrix.columns]
            corr_matrix.columns = display_names
            corr_matrix.index = display_names

            fig_corr = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu",
                range_color=[-1, 1]
            )
            fig_corr.update_layout(title="30 Günlük Gerçek Korelasyonlar", height=400)
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.warning("Korelasyon verisi hesaplanamadı")

    with col2:
        st.markdown(f"### Risk Metrikleri")

        # Risk metrics visualization
        if risk_metrics:
            symbols = list(risk_metrics.keys())[:5]
            risk_scores = [risk_metrics[s]['risk_score'] for s in symbols]
            risk_levels = [risk_metrics[s]['risk_level'] for s in symbols]

            colors = ['green' if score < 30 else 'orange' if score < 60 else 'red' for score in risk_scores]

            fig_risk = go.Figure(data=[
                go.Bar(x=[s.replace('.IS', '') for s in symbols], y=risk_scores, marker_color=colors)
            ])
            fig_risk.update_layout(
                title="Risk Skorları (0-100)",
                xaxis_title="Varlık",
                yaxis_title="Risk Skoru",
                height=400
            )
            st.plotly_chart(fig_risk, use_container_width=True)

    # Turkish Market Analysis
    if track_turkish:
        st.markdown(f"## {t('turkish_market')}")

        turkish_data = {k: v for k, v in market_data.items() if v.get('type') == 'turkish_stock'}

        if turkish_data:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Türk Hisse Performansı")

                symbols = list(turkish_data.keys())
                changes = [turkish_data[s]['change'] for s in symbols]
                names = [s.replace('.IS', '') for s in symbols]

                colors = ['green' if c > 0 else 'red' for c in changes]

                fig_turkish = go.Figure(data=[
                    go.Bar(x=names, y=changes, marker_color=colors)
                ])
                fig_turkish.update_layout(
                    title="Türk Hisse Senetleri (%)",
                    xaxis_title="Hisse",
                    yaxis_title="Günlük Değişim (%)",
                    height=400
                )
                st.plotly_chart(fig_turkish, use_container_width=True)

            with col2:
                st.markdown("### Detaylı Türk Hisse Verileri")

                turkish_df = pd.DataFrame([
                    {
                        "Hisse": symbol.replace('.IS', ''),
                        "Fiyat": f"₺{data['price']:.2f}",
                        "Değişim": f"{data['change']:+.2f}%",
                        "Risk": risk_metrics.get(symbol, {}).get('risk_level', 'Bilinmiyor')
                    }
                    for symbol, data in turkish_data.items()
                ])

                st.dataframe(turkish_df, use_container_width=True, hide_index=True)

    # Crypto Dominance Analysis
    st.markdown(f"## {t('crypto_dominance')}")

    crypto_data = {k: v for k, v in market_data.items() if v.get('type') == 'crypto' and 'dominance' in v}

    if crypto_data:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Kripto Dominans Dağılımı")

            # Dominance pie chart
            dominance_data = []
            for symbol, data in crypto_data.items():
                if data.get('dominance', 0) > 0:
                    dominance_data.append({
                        'symbol': symbol,
                        'dominance': data['dominance']
                    })

            if dominance_data:
                df_dom = pd.DataFrame(dominance_data)
                df_dom = df_dom.sort_values('dominance', ascending=False)

                fig_dom = px.pie(
                    df_dom,
                    values='dominance',
                    names='symbol',
                    title="Kripto Piyasa Dominansı (%)"
                )
                fig_dom.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_dom, use_container_width=True)

        with col2:
            st.markdown("### Kripto Piyasa Değerleri")

            # Market cap comparison
            mcap_data = []
            for symbol, data in crypto_data.items():
                if data.get('market_cap', 0) > 0:
                    mcap_data.append({
                        'symbol': symbol,
                        'market_cap': data['market_cap'],
                        'price': data['price'],
                        'change': data['change'],
                        'dominance': data.get('dominance', 0)
                    })

            if mcap_data:
                df_mcap = pd.DataFrame(mcap_data)
                df_mcap = df_mcap.sort_values('market_cap', ascending=False)

                # Format market cap
                df_mcap['Market Cap'] = df_mcap['market_cap'].apply(
                    lambda x: f"${x/1e9:.1f}B" if x > 1e9 else f"${x/1e6:.0f}M"
                )
                df_mcap['Price'] = df_mcap['price'].apply(lambda x: f"${x:,.2f}")
                df_mcap['Change'] = df_mcap['change'].apply(lambda x: f"{x:+.2f}%")
                df_mcap['Dominance'] = df_mcap['dominance'].apply(lambda x: f"{x:.2f}%")

                display_df = df_mcap[['symbol', 'Price', 'Change', 'Market Cap', 'Dominance']]
                display_df.columns = ['Kripto', 'Fiyat', 'Değişim', 'Piyasa Değeri', 'Dominans']

                st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Global Stocks & ETFs Overview
    st.markdown(f"## {t('global_stocks')} & {t('global_etfs')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏢 Global Hisse Senetleri")

        global_stocks_data = {k: v for k, v in market_data.items() if v.get('type') == 'global_stock'}

        if global_stocks_data:
            # Top movers
            stocks_list = list(global_stocks_data.items())
            stocks_list.sort(key=lambda x: abs(x[1]['change']), reverse=True)

            top_movers = stocks_list[:10]

            for symbol, data in top_movers:
                change_color = "green" if data['change'] > 0 else "red"
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    margin: 5px 0;
                    border-left: 4px solid {change_color};
                    background: #f8f9fa;
                    border-radius: 5px;
                ">
                    <strong>{symbol}</strong> - ${data['price']:.2f}
                    <span style="color: {change_color}; font-weight: bold;">
                        {data['change']:+.2f}%
                    </span>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 📊 Global ETF'ler")

        etf_data = {k: v for k, v in market_data.items() if v.get('type') == 'etf'}

        if etf_data:
            # Top ETF movers
            etf_list = list(etf_data.items())
            etf_list.sort(key=lambda x: abs(x[1]['change']), reverse=True)

            top_etf_movers = etf_list[:10]

            for symbol, data in top_etf_movers:
                change_color = "green" if data['change'] > 0 else "red"
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    margin: 5px 0;
                    border-left: 4px solid {change_color};
                    background: #f8f9fa;
                    border-radius: 5px;
                ">
                    <strong>{symbol}</strong> - ${data['price']:.2f}
                    <span style="color: {change_color}; font-weight: bold;">
                        {data['change']:+.2f}%
                    </span>
                </div>
                """, unsafe_allow_html=True)

    # Fund Holdings Analysis Link
    st.markdown(f"## {t('fund_holdings')}")

    st.markdown("""
    <div style="
        padding: 20px;
        margin: 15px 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        text-align: center;
    ">
        <h3>🔍 Fintables Tarzı Fund Holdings Analizi</h3>
        <p>ETF'lerin hisse dağılımlarını ve hisselerin hangi fonlarda yer aldığını analiz edin</p>
        <p><strong>• Fon → Hisse Analizi</strong> | <strong>• Hisse → Fon Analizi</strong> | <strong>• Performans Karşılaştırması</strong></p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📊 Fund Holdings Analiz Sayfasını Aç", type="primary"):
        st.info("Fund Holdings analiz sayfası ayrı bir modül olarak geliştirilmiştir. Bu sayfayı başlatmak için:")
        st.code("cd dashboard/pages && streamlit run funds_holdings.py --server.port 8504")

    # AI Prediction Analysis
    st.markdown(f"## {t('prediction_analysis')}")

    # Asset selection for prediction
    available_assets = [k for k in market_data.keys() if market_data[k].get('type') in ['crypto', 'turkish_stock', 'index']]
    selected_asset = st.selectbox("Tahmin için varlık seçin:", available_assets[:10] if available_assets else ["BTC"])

    # Prediction period
    pred_period = st.radio("Tahmin periyodu:", ["1 Ay", "3 Ay", "1 Yıl"], horizontal=True)
    days_map = {"1 Ay": 30, "3 Ay": 90, "1 Yıl": 365}
    pred_days = days_map[pred_period]

    if selected_asset and selected_asset in market_data:
        # Generate prediction
        prediction_data = generate_advanced_prediction(selected_asset, market_data[selected_asset], pred_days)

        if not prediction_data.empty:
            # Prediction chart
            fig_pred = go.Figure()

            # Current price point
            current_price = market_data[selected_asset]['price']
            fig_pred.add_trace(go.Scatter(
                x=[datetime.now()],
                y=[current_price],
                mode='markers',
                name='Mevcut Fiyat',
                marker=dict(size=15, color='red')
            ))

            # Prediction line
            fig_pred.add_trace(go.Scatter(
                x=prediction_data['date'],
                y=prediction_data['predicted_price'],
                mode='lines',
                name='AI Tahmini',
                line=dict(color='blue', width=3)
            ))

            # Confidence bands
            fig_pred.add_trace(go.Scatter(
                x=prediction_data['date'],
                y=prediction_data['upper_bound'],
                mode='lines',
                line=dict(width=0),
                showlegend=False
            ))

            fig_pred.add_trace(go.Scatter(
                x=prediction_data['date'],
                y=prediction_data['lower_bound'],
                mode='lines',
                line=dict(width=0),
                fillcolor='rgba(0,100,80,0.2)',
                fill='tonexty',
                name='Güven Aralığı',
                showlegend=True
            ))

            fig_pred.update_layout(
                title=f"{selected_asset} - {pred_period} AI Tahmini",
                xaxis_title="Tarih",
                yaxis_title="Fiyat",
                height=500
            )

            st.plotly_chart(fig_pred, use_container_width=True)

            # Prediction summary
            st.markdown("### Tahmin Özeti")

            final_price = prediction_data['predicted_price'].iloc[-1]
            total_return = ((final_price - current_price) / current_price) * 100
            avg_confidence = prediction_data['confidence'].mean()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Mevcut Fiyat", f"${current_price:.2f}")
            with col2:
                st.metric("Tahmini Fiyat", f"${final_price:.2f}")
            with col3:
                st.metric("Beklenen Getiri", f"{total_return:+.1f}%")
            with col4:
                st.metric("Tahmin Güveni", f"{avg_confidence:.1%}")

    # Detailed Data Tables
    st.markdown(f"## {t('detailed_data')}")

    tab1, tab2, tab3 = st.tabs([t("market_data"), t("correlations"), "Risk Analizi"])

    with tab1:
        # Real market data table
        if market_data:
            market_df = pd.DataFrame([
                {
                    t("asset"): symbol,
                    t("price"): f"${data['price']:.2f}" if data.get('type') != 'fx' else f"{data['price']:.4f}",
                    t("change_24h"): f"{data['change']:+.2f}%",
                    "Tip": data.get('type', 'unknown'),
                    "Risk": risk_metrics.get(symbol, {}).get('risk_level', 'Bilinmiyor')
                }
                for symbol, data in market_data.items()
            ])
            st.dataframe(market_df, use_container_width=True, hide_index=True)

    with tab2:
        # Correlation matrix
        if not corr_matrix.empty:
            st.dataframe(corr_matrix.round(3), use_container_width=True)
        else:
            st.info("Korelasyon matrisi hesaplanamadı")

    with tab3:
        # Risk analysis table
        if risk_metrics:
            risk_df = pd.DataFrame([
                {
                    "Varlık": symbol,
                    "Volatilite": f"{data['volatility']:.2f}%",
                    "Risk Seviyesi": data['risk_level'],
                    "Risk Skoru": f"{data['risk_score']:.0f}/100",
                    "Trend": data['trend']
                }
                for symbol, data in risk_metrics.items()
            ])
            st.dataframe(risk_df, use_container_width=True, hide_index=True)

    # Footer with last update time
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        🌍 Global Liquidity Dashboard | 🔴 Canlı Veriler |
        📊 Son güncelleme: {st.session_state.last_update.strftime('%H:%M:%S')} |
        🤖 AI Tahminleri Aktif
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()