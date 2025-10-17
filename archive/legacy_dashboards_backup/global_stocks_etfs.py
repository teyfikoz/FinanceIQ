"""
Global Stocks & ETFs Analysis Page
Kullanıcı dostu hisse senedi ve ETF analiz sayfası
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time

# Add project path
import sys
import os
from pathlib import Path

# Path setup
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.data_collectors.stocks_etfs import StocksETFsCollector
    from app.analytics.stocks_etfs import StocksETFsAnalyzer
except ImportError as e:
    import streamlit as st
    st.error(f"Import error: {e}")
    st.error(f"Project root: {project_root}")
    st.stop()

def get_stock_fund_membership(symbol):
    """Get list of funds/ETFs that hold this stock"""
    # Comprehensive fund universe from global market collector
    fund_universe = {
        'broad_market_etfs': ['SPY', 'VTI', 'QQQ', 'IWM', 'VEA', 'VWO', 'EFA', 'EEM', 'VOO', 'IVV', 'VTV', 'VUG', 'IJH', 'IJR'],
        'sector_etfs': ['XLK', 'XLV', 'XLF', 'XLE', 'XLI', 'XLY', 'XLP', 'XLRE', 'XLB', 'XLU', 'XLC', 'VGT', 'VHT', 'VFH', 'VDE', 'VIS', 'VCR', 'VDC', 'VNQ', 'VAW', 'VPU', 'VOX'],
        'international_etfs': ['VEA', 'VWO', 'EFA', 'EEM', 'IEFA', 'IEMG', 'VGK', 'VPL', 'VT', 'VXUS', 'IXUS', 'FTIHX', 'SCHA', 'SCHF', 'SCHE', 'SCHC'],
        'thematic_etfs': ['ARKK', 'ARKQ', 'ARKG', 'ICLN', 'JETS', 'ROBO', 'ESPO', 'UFO', 'HERO', 'ARKF', 'ARKW', 'CLOU', 'EDOC', 'FINX', 'HACK', 'SKYY', 'SOXX', 'SMH', 'XBI', 'IBB'],
        'technology_etfs': ['XLK', 'VGT', 'SOXX', 'SMH', 'QTEC', 'FTEC', 'IGM', 'IYW', 'TECL', 'TQQQ', 'QQQ', 'PSJ'],
        'healthcare_etfs': ['XLV', 'VHT', 'IBB', 'XBI', 'IYH', 'FHLC', 'IHE', 'CURE', 'BBH', 'RYH', 'PJP', 'PTH'],
        'financial_etfs': ['XLF', 'VFH', 'IYF', 'FNCL', 'FAS', 'KBE', 'KRE', 'IAT', 'PFI', 'UYG', 'KBWB', 'KBWR'],
        'energy_etfs': ['XLE', 'VDE', 'IYE', 'FENY', 'ERX', 'XOP', 'GUSH', 'IEO', 'PXE', 'ICLN', 'PBW', 'FAN'],
        'vanguard_funds': ['VTSAX', 'VTIAX', 'VBTLX', 'VTWAX', 'VTSMX', 'VGTSX', 'VFWAX', 'VFWIX', 'VTMGX', 'VTWSX'],
        'fidelity_funds': ['FXNAX', 'FZROX', 'FZILX', 'FSKAX', 'FTEC', 'FREL', 'FXAIX', 'FZIPX', 'FNILX', 'FDVV']
    }

    # Mapping based on common holdings (simplified for demonstration)
    stock_to_funds = {
        'AAPL': {
            'broad_market': ['SPY', 'VTI', 'QQQ', 'VOO', 'IVV', 'VUG'],
            'technology': ['XLK', 'VGT', 'QQQ', 'SOXX', 'QTEC', 'FTEC'],
            'thematic': ['ARKK', 'ARKQ', 'ARKW'],
            'mutual_funds': ['VTSAX', 'FXNAX', 'FZROX', 'FSKAX']
        },
        'MSFT': {
            'broad_market': ['SPY', 'VTI', 'QQQ', 'VOO', 'IVV', 'VUG'],
            'technology': ['XLK', 'VGT', 'QQQ', 'SOXX', 'QTEC', 'FTEC'],
            'thematic': ['ARKK', 'ARKW', 'CLOU'],
            'mutual_funds': ['VTSAX', 'FXNAX', 'FZROX', 'FSKAX']
        },
        'GOOGL': {
            'broad_market': ['SPY', 'VTI', 'QQQ', 'VOO', 'IVV', 'VUG'],
            'technology': ['XLK', 'VGT', 'QQQ', 'QTEC', 'FTEC'],
            'thematic': ['ARKK', 'ARKW'],
            'mutual_funds': ['VTSAX', 'FXNAX', 'FZROX', 'FSKAX']
        },
        'TSLA': {
            'broad_market': ['SPY', 'VTI', 'QQQ', 'VOO', 'IVV', 'VUG'],
            'thematic': ['ARKK', 'ARKQ', 'ARKW', 'ICLN', 'PBW'],
            'sector': ['XLY'],
            'mutual_funds': ['VTSAX', 'FXNAX', 'FSKAX']
        },
        'AMZN': {
            'broad_market': ['SPY', 'VTI', 'QQQ', 'VOO', 'IVV', 'VUG'],
            'technology': ['XLK', 'VGT', 'QQQ'],
            'sector': ['XLY'],
            'thematic': ['ARKK', 'ARKW'],
            'mutual_funds': ['VTSAX', 'FXNAX', 'FZROX', 'FSKAX']
        },
        'META': {
            'broad_market': ['SPY', 'VTI', 'QQQ', 'VOO', 'IVV', 'VUG'],
            'technology': ['XLK', 'VGT', 'QQQ'],
            'sector': ['XLC'],
            'thematic': ['ARKK', 'ARKW'],
            'mutual_funds': ['VTSAX', 'FXNAX', 'FZROX', 'FSKAX']
        },
        'NVDA': {
            'broad_market': ['SPY', 'VTI', 'QQQ', 'VOO', 'IVV', 'VUG'],
            'technology': ['XLK', 'VGT', 'QQQ', 'SOXX', 'SMH'],
            'thematic': ['ARKK', 'ARKQ', 'ARKW', 'ROBO'],
            'mutual_funds': ['VTSAX', 'FXNAX', 'FSKAX']
        }
    }

    # Get funds for the symbol (default to broad market if not found)
    symbol_funds = stock_to_funds.get(symbol.upper(), {
        'broad_market': ['SPY', 'VTI', 'VOO', 'IVV'],
        'mutual_funds': ['VTSAX', 'FXNAX']
    })

    return symbol_funds

# Dil sözlükleri
TRANSLATIONS = {
    "tr": {
        "title": "📈 Global Hisse Senetleri ve ETF Analizi",
        "subtitle": "Dünya çapında hisse senetleri ve ETF'leri analiz edin",
        "search_symbol": "🔍 Hisse/ETF Ara",
        "symbol_placeholder": "Örn: AAPL, SPY, TSLA",
        "popular_stocks": "🔥 Popüler Hisse Senetleri",
        "popular_etfs": "🏆 Popüler ETF'ler",
        "analysis_period": "📅 Analiz Periyodu",
        "current_price": "Güncel Fiyat",
        "daily_change": "Günlük Değişim",
        "volume": "İşlem Hacmi",
        "market_cap": "Piyasa Değeri",
        "pe_ratio": "F/K Oranı",
        "dividend_yield": "Temettü Verimi",
        "52_week_range": "52 Hafta Aralığı",
        "price_chart": "📊 Fiyat Grafiği",
        "technical_analysis": "🔧 Teknik Analiz",
        "performance_summary": "📈 Performans Özeti",
        "risk_metrics": "⚠️ Risk Metrikleri",
        "correlation_analysis": "🔗 Korelasyon Analizi",
        "investment_signals": "💡 Yatırım Sinyalleri",
        "company_info": "🏢 Şirket Bilgileri",
        "returns": "Getiriler",
        "volatility": "Volatilite",
        "max_drawdown": "Maksimum Düşüş",
        "risk_level": "Risk Seviyesi",
        "trend_analysis": "📈 Trend Analizi",
        "support_resistance": "Destek/Direnç",
        "buy_signal": "🟢 AL SİNYALİ",
        "sell_signal": "🔴 SAT SİNYALİ",
        "hold_signal": "🟡 BEKLE",
        "loading": "Yükleniyor...",
        "error": "Hata",
        "no_data": "Veri bulunamadı",
        "sector": "Sektör",
        "industry": "Endüstri",
        "beta": "Beta",
        "rsi": "RSI",
        "macd": "MACD",
        "bollinger_bands": "Bollinger Bantları",
        "moving_averages": "Hareketli Ortalamalar",
        "short_term": "Kısa Vadeli",
        "medium_term": "Orta Vadeli",
        "long_term": "Uzun Vadeli",
        "overall_trend": "Genel Trend",
        "confidence": "Güven",
        "performance_score": "Performans Skoru",
        "compare_stocks": "📊 Hisse Karşılaştırma",
        "add_to_compare": "Karşılaştırmaya Ekle",
        "clear_comparison": "Karşılaştırmayı Temizle"
    },
    "en": {
        "title": "📈 Global Stocks & ETFs Analysis",
        "subtitle": "Analyze stocks and ETFs worldwide",
        "search_symbol": "🔍 Search Stock/ETF",
        "symbol_placeholder": "e.g: AAPL, SPY, TSLA",
        "popular_stocks": "🔥 Popular Stocks",
        "popular_etfs": "🏆 Popular ETFs",
        "analysis_period": "📅 Analysis Period",
        "current_price": "Current Price",
        "daily_change": "Daily Change",
        "volume": "Volume",
        "market_cap": "Market Cap",
        "pe_ratio": "P/E Ratio",
        "dividend_yield": "Dividend Yield",
        "52_week_range": "52 Week Range",
        "price_chart": "📊 Price Chart",
        "technical_analysis": "🔧 Technical Analysis",
        "performance_summary": "📈 Performance Summary",
        "risk_metrics": "⚠️ Risk Metrics",
        "correlation_analysis": "🔗 Correlation Analysis",
        "investment_signals": "💡 Investment Signals",
        "company_info": "🏢 Company Info",
        "returns": "Returns",
        "volatility": "Volatility",
        "max_drawdown": "Max Drawdown",
        "risk_level": "Risk Level",
        "trend_analysis": "📈 Trend Analysis",
        "support_resistance": "Support/Resistance",
        "buy_signal": "🟢 BUY SIGNAL",
        "sell_signal": "🔴 SELL SIGNAL",
        "hold_signal": "🟡 HOLD",
        "loading": "Loading...",
        "error": "Error",
        "no_data": "No data found",
        "sector": "Sector",
        "industry": "Industry",
        "beta": "Beta",
        "rsi": "RSI",
        "macd": "MACD",
        "bollinger_bands": "Bollinger Bands",
        "moving_averages": "Moving Averages",
        "short_term": "Short Term",
        "medium_term": "Medium Term",
        "long_term": "Long Term",
        "overall_trend": "Overall Trend",
        "confidence": "Confidence",
        "performance_score": "Performance Score",
        "compare_stocks": "📊 Stock Comparison",
        "add_to_compare": "Add to Compare",
        "clear_comparison": "Clear Comparison"
    }
}

def t(key: str, lang: str = None) -> str:
    """Translation function"""
    if lang is None:
        lang = st.session_state.get('language', 'tr')
    return TRANSLATIONS.get(lang, {}).get(key, key)

@st.cache_data(ttl=300)  # 5 dakika cache
def get_stock_data(symbol: str, period: str = "1y"):
    """Hisse senedi verisi çek ve cache'le."""
    try:
        collector = StocksETFsCollector()
        data = collector.fetch_stock_data_yf(symbol, period=period)
        return data
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return None

@st.cache_data(ttl=600)  # 10 dakika cache
def analyze_stock(symbol: str, period: str = "1y"):
    """Hisse senedi analizi yap ve cache'le."""
    try:
        # Veri çek
        collector = StocksETFsCollector()
        data = collector.fetch_stock_data_yf(symbol, period=period)

        if not data or "error" in data:
            return None

        # OHLCV DataFrame'i oluştur
        ohlcv_df = pd.DataFrame(data["ohlcv_data"])
        ohlcv_df["date"] = pd.to_datetime(ohlcv_df["date"])
        ohlcv_df = ohlcv_df.set_index("date")

        # Analiz yap
        analyzer = StocksETFsAnalyzer()
        analysis = analyzer.analyze_stock_performance(ohlcv_df, symbol)

        # Yatırım sinyalleri
        signals = analyzer.generate_investment_signals(
            analysis.get("technical_indicators", {}),
            analysis.get("trend_analysis", {})
        )

        analysis["investment_signals"] = signals
        analysis["raw_data"] = data

        return analysis

    except Exception as e:
        st.error(f"Analiz hatası: {e}")
        return None

def create_candlestick_chart(ohlcv_data: list, symbol: str, technical_indicators: dict = None):
    """Mum grafiği oluştur."""
    try:
        df = pd.DataFrame(ohlcv_data)
        df["date"] = pd.to_datetime(df["date"])

        # Subplot oluştur
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=[f'{symbol} Fiyat Grafiği', 'Hacim'],
            row_width=[0.7, 0.3]
        )

        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df["date"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name=symbol
            ),
            row=1, col=1
        )

        # Moving averages ekle
        if technical_indicators and "SMA_20" in technical_indicators:
            sma_20_values = df["close"].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=sma_20_values,
                    mode='lines',
                    name='SMA 20',
                    line=dict(color='orange', width=1)
                ),
                row=1, col=1
            )

        if technical_indicators and "SMA_50" in technical_indicators and len(df) >= 50:
            sma_50_values = df["close"].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=sma_50_values,
                    mode='lines',
                    name='SMA 50',
                    line=dict(color='blue', width=1)
                ),
                row=1, col=1
            )

        # Bollinger Bands ekle
        if technical_indicators and "Bollinger" in technical_indicators:
            bb = technical_indicators["Bollinger"]
            period = 20
            if len(df) >= period:
                sma = df["close"].rolling(window=period).mean()
                std = df["close"].rolling(window=period).std()

                upper_band = sma + (std * 2)
                lower_band = sma - (std * 2)

                fig.add_trace(
                    go.Scatter(
                        x=df["date"],
                        y=upper_band,
                        mode='lines',
                        name='Bollinger Üst',
                        line=dict(color='gray', width=1, dash='dash')
                    ),
                    row=1, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=df["date"],
                        y=lower_band,
                        mode='lines',
                        name='Bollinger Alt',
                        line=dict(color='gray', width=1, dash='dash'),
                        fill='tonexty',
                        fillcolor='rgba(128,128,128,0.1)'
                    ),
                    row=1, col=1
                )

        # Volume chart
        colors = ['red' if df["close"].iloc[i] < df["open"].iloc[i] else 'green' for i in range(len(df))]

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["volume"],
                name='Hacim',
                marker_color=colors
            ),
            row=2, col=1
        )

        # Layout güncelle
        fig.update_layout(
            title=f'{symbol} - Detaylı Teknik Analiz',
            yaxis_title='Fiyat ($)',
            yaxis2_title='Hacim',
            xaxis_rangeslider_visible=False,
            height=600,
            showlegend=True
        )

        return fig

    except Exception as e:
        st.error(f"Grafik oluşturma hatası: {e}")
        return None

def create_performance_chart(returns: dict):
    """Performans karşılaştırma grafiği."""
    try:
        periods = list(returns.keys())
        values = list(returns.values())

        colors = ['green' if v > 0 else 'red' for v in values]

        fig = go.Figure(data=[
            go.Bar(x=periods, y=values, marker_color=colors)
        ])

        fig.update_layout(
            title="Getiri Performansı (%)",
            xaxis_title="Periyot",
            yaxis_title="Getiri (%)",
            height=300
        )

        return fig

    except Exception as e:
        st.error(f"Performans grafiği hatası: {e}")
        return None

def create_technical_indicators_chart(ohlcv_data: list, technical_indicators: dict):
    """Teknik göstergeler grafiği."""
    try:
        df = pd.DataFrame(ohlcv_data)
        df["date"] = pd.to_datetime(df["date"])

        # RSI hesapla
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        rsi_values = calculate_rsi(df["close"])

        # Subplot oluştur
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=['RSI (14)', 'MACD']
        )

        # RSI
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=rsi_values,
                mode='lines',
                name='RSI',
                line=dict(color='purple')
            ),
            row=1, col=1
        )

        # RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)

        # MACD hesapla
        ema_12 = df["close"].ewm(span=12).mean()
        ema_26 = df["close"].ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line

        # MACD
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=macd_line,
                mode='lines',
                name='MACD',
                line=dict(color='blue')
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=signal_line,
                mode='lines',
                name='Signal',
                line=dict(color='red')
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=histogram,
                name='Histogram',
                marker_color=['green' if v > 0 else 'red' for v in histogram]
            ),
            row=2, col=1
        )

        fig.update_layout(
            title="Teknik Göstergeler",
            height=500,
            showlegend=True
        )

        return fig

    except Exception as e:
        st.error(f"Teknik göstergeler grafiği hatası: {e}")
        return None

def main():
    """Ana fonksiyon."""

    # Dil ayarı
    if 'language' not in st.session_state:
        st.session_state.language = 'tr'

    # Karşılaştırma listesi
    if 'comparison_list' not in st.session_state:
        st.session_state.comparison_list = []

    # Başlık
    st.markdown(f'<h1 style="color: #1f77b4;">{t("title")}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #666; font-size: 1.1rem;">{t("subtitle")}</p>', unsafe_allow_html=True)

    # CSS
    st.markdown("""
    <style>
        .metric-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin: 0.5rem 0;
        }
        .signal-buy {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            font-weight: bold;
        }
        .signal-sell {
            background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            font-weight: bold;
        }
        .signal-hold {
            background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar - Arama ve Seçenekler
    with st.sidebar:
        st.markdown(f"### {t('search_symbol')}")

        # Sembol arama
        symbol_input = st.text_input(
            "Sembol:",
            placeholder=t("symbol_placeholder"),
            help="Hisse senedi veya ETF sembolü girin"
        ).upper()

        # Analiz periyodu
        period = st.selectbox(
            t("analysis_period"),
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=3,
            format_func=lambda x: {
                "1mo": "1 Ay",
                "3mo": "3 Ay",
                "6mo": "6 Ay",
                "1y": "1 Yıl",
                "2y": "2 Yıl",
                "5y": "5 Yıl"
            }[x]
        )

        # Quick analysis button
        if symbol_input:
            if st.button("🎯 Analiz Et", type="primary"):
                st.session_state.analyze_symbol = symbol_input
                st.rerun()

        # Market Status
        st.markdown("---")
        st.markdown("### 📊 Piyasa Durumu")
        st.success("✅ Piyasalar Açık")
        st.info(f"🕐 Son Güncelleme: {datetime.now().strftime('%H:%M:%S')}")

        # Quick Performance
        st.markdown("### 📈 Hızlı Performans")
        st.metric("S&P 500", "4,450", "1.2%")
        st.metric("NASDAQ", "13,800", "0.8%")
        st.metric("VIX", "18.5", "-2.1%")

    # Initialize session state for symbol selection
    if 'analyze_symbol' not in st.session_state:
        st.session_state.analyze_symbol = None

    # Check if we should analyze a specific symbol
    analyze_symbol = st.session_state.analyze_symbol or symbol_input

    # Main content area
    if analyze_symbol:
        with st.spinner(t("loading")):
            analysis = analyze_stock(analyze_symbol, period)

        # Back button
        if st.button("⬅️ Geri Dön"):
            st.session_state.analyze_symbol = None
            st.rerun()

        if analysis and "error" not in analysis:
            raw_data = analysis["raw_data"]

            # Üst bilgi kartları
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                current_price = raw_data.get("current_price", 0)
                st.metric(
                    t("current_price"),
                    f"${current_price:.2f}",
                    f"{raw_data.get('price_change_percent', 0):+.2f}%"
                )

            with col2:
                volume = raw_data.get("volume", 0)
                if volume > 1e9:
                    volume_display = f"{volume/1e9:.1f}B"
                elif volume > 1e6:
                    volume_display = f"{volume/1e6:.1f}M"
                else:
                    volume_display = f"{volume:,.0f}"

                st.metric(t("volume"), volume_display)

            with col3:
                market_cap = raw_data.get("market_cap")
                if market_cap:
                    if market_cap > 1e12:
                        mc_display = f"${market_cap/1e12:.1f}T"
                    elif market_cap > 1e9:
                        mc_display = f"${market_cap/1e9:.1f}B"
                    else:
                        mc_display = f"${market_cap/1e6:.1f}M"
                    st.metric(t("market_cap"), mc_display)
                else:
                    st.metric(t("market_cap"), "N/A")

            with col4:
                pe_ratio = raw_data.get("pe_ratio")
                if pe_ratio:
                    st.metric(t("pe_ratio"), f"{pe_ratio:.1f}")
                else:
                    st.metric(t("pe_ratio"), "N/A")

            # Şirket bilgileri
            st.markdown(f"## {t('company_info')}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="metric-container">
                    <h4>{raw_data.get('name', symbol_input)}</h4>
                    <p><strong>{t('sector')}:</strong> {raw_data.get('sector', 'Bilinmiyor')}</p>
                    <p><strong>{t('industry')}:</strong> {raw_data.get('industry', 'Bilinmiyor')}</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                week_high = raw_data.get("52_week_high", 0)
                week_low = raw_data.get("52_week_low", 0)
                beta = raw_data.get("beta", 0)
                dividend_yield = raw_data.get("dividend_yield", 0)

                # Safe formatting for beta and dividend yield
                beta_display = f"{beta:.2f}" if beta is not None and beta != 0 else 'N/A'
                div_yield_display = f"{dividend_yield*100:.2f}%" if dividend_yield is not None and dividend_yield != 0 else 'N/A'

                st.markdown(f"""
                <div class="metric-container">
                    <p><strong>{t('52_week_range')}:</strong> ${week_low:.2f} - ${week_high:.2f}</p>
                    <p><strong>{t('beta')}:</strong> {beta_display}</p>
                    <p><strong>{t('dividend_yield')}:</strong> {div_yield_display}</p>
                </div>
                """, unsafe_allow_html=True)

            # Fund Membership Display
            st.markdown("### 🏦 Bu Hisse Senedini İçeren Fonlar")
            fund_membership = get_stock_fund_membership(analyze_symbol)

            for category, funds in fund_membership.items():
                if funds:
                    category_names = {
                        'broad_market': '🌍 Geniş Piyasa ETF\'leri',
                        'technology': '💻 Teknoloji ETF\'leri',
                        'sector': '🏭 Sektör ETF\'leri',
                        'thematic': '🎯 Tematik ETF\'ler',
                        'mutual_funds': '🏛️ Mutual Fonlar'
                    }

                    category_display = category_names.get(category, category.title())
                    st.markdown(f"**{category_display}:**")

                    # Display funds in columns
                    cols = st.columns(min(len(funds), 5))
                    for i, fund in enumerate(funds):
                        with cols[i % len(cols)]:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                padding: 0.5rem;
                                border-radius: 8px;
                                color: white;
                                text-align: center;
                                margin: 0.25rem 0;
                                font-weight: bold;
                            ">
                                {fund}
                            </div>
                            """, unsafe_allow_html=True)

            # Fiyat grafiği
            st.markdown(f"## {t('price_chart')}")

            if "ohlcv_data" in raw_data:
                candlestick_fig = create_candlestick_chart(
                    raw_data["ohlcv_data"],
                    analyze_symbol,
                    analysis.get("technical_indicators", {})
                )
                if candlestick_fig:
                    st.plotly_chart(candlestick_fig, use_container_width=True)

            # Performans ve teknik analiz
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### {t('performance_summary')}")

                returns = analysis.get("returns", {})
                if returns:
                    perf_fig = create_performance_chart(returns)
                    if perf_fig:
                        st.plotly_chart(perf_fig, use_container_width=True)

                    # Performans tablosu
                    perf_df = pd.DataFrame([
                        {"Periyot": period, "Getiri (%)": f"{return_val:+.2f}%"}
                        for period, return_val in returns.items()
                    ])
                    st.dataframe(perf_df, hide_index=True, use_container_width=True)

            with col2:
                st.markdown(f"### {t('risk_metrics')}")

                risk_metrics = analysis.get("risk_metrics", {})
                if risk_metrics:
                    st.markdown(f"""
                    <div class="metric-container">
                        <p><strong>{t('volatility')}:</strong> {risk_metrics.get('volatility_annual', 0):.1f}%</p>
                        <p><strong>{t('max_drawdown')}:</strong> {risk_metrics.get('max_drawdown', 0):.1f}%</p>
                        <p><strong>{t('risk_level')}:</strong> {risk_metrics.get('risk_level', 'Bilinmiyor')}</p>
                        <p><strong>VaR (95%):</strong> {risk_metrics.get('var_95', 0):.2f}%</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Performans skoru
                performance_score = analysis.get("performance_score", {})
                if performance_score:
                    score = performance_score.get("score", 50)
                    category = performance_score.get("category", "Bilinmiyor")

                    score_color = "green" if score >= 70 else "orange" if score >= 50 else "red"

                    st.markdown(f"""
                    <div class="metric-container">
                        <h4>{t('performance_score')}</h4>
                        <h2 style="color: {score_color};">{score:.1f}/100</h2>
                        <p>{category}</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Teknik göstergeler
            st.markdown(f"## {t('technical_analysis')}")

            if "ohlcv_data" in raw_data:
                tech_fig = create_technical_indicators_chart(
                    raw_data["ohlcv_data"],
                    analysis.get("technical_indicators", {})
                )
                if tech_fig:
                    st.plotly_chart(tech_fig, use_container_width=True)

            # Teknik göstergeler özeti
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### {t('technical_analysis')}")

                tech_indicators = analysis.get("technical_indicators", {})
                if tech_indicators:
                    rsi = tech_indicators.get("RSI", 50)
                    macd = tech_indicators.get("MACD", {})
                    bollinger = tech_indicators.get("Bollinger", {})

                    st.markdown(f"""
                    <div class="metric-container">
                        <p><strong>{t('rsi')} (14):</strong> {rsi:.1f}</p>
                        <p><strong>{t('macd')}:</strong> {macd.get('macd_line', 0):.4f}</p>
                        <p><strong>Signal:</strong> {macd.get('signal_line', 0):.4f}</p>
                        <p><strong>Bollinger:</strong> {bollinger.get('position', 'Bilinmiyor')}</p>
                    </div>
                    """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"### {t('trend_analysis')}")

                trend_analysis = analysis.get("trend_analysis", {})
                if trend_analysis:
                    st.markdown(f"""
                    <div class="metric-container">
                        <p><strong>{t('short_term')}:</strong> {trend_analysis.get('short_term', 'Bilinmiyor')}</p>
                        <p><strong>{t('medium_term')}:</strong> {trend_analysis.get('medium_term', 'Bilinmiyor')}</p>
                        <p><strong>{t('long_term')}:</strong> {trend_analysis.get('long_term', 'Bilinmiyor')}</p>
                        <p><strong>{t('overall_trend')}:</strong> {trend_analysis.get('overall_trend', 'Bilinmiyor')}</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Yatırım sinyalleri
            st.markdown(f"## {t('investment_signals')}")

            signals = analysis.get("investment_signals", {})
            if signals:
                overall_signal = signals.get("overall_signal", "NEUTRAL")
                confidence = signals.get("confidence", 50)
                signal_list = signals.get("signals", [])

                # Sinyal kartı
                if overall_signal == "BUY":
                    signal_class = "signal-buy"
                    signal_text = t("buy_signal")
                elif overall_signal == "SELL":
                    signal_class = "signal-sell"
                    signal_text = t("sell_signal")
                else:
                    signal_class = "signal-hold"
                    signal_text = t("hold_signal")

                st.markdown(f"""
                <div class="{signal_class}">
                    <h3>{signal_text}</h3>
                    <p>{t('confidence')}: {confidence:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)

                # Sinyal detayları
                if signal_list:
                    st.markdown("### Sinyal Detayları")
                    for i, signal in enumerate(signal_list, 1):
                        st.markdown(f"{i}. {signal}")

            # Karşılaştırma özelliği
            st.markdown(f"## {t('compare_stocks')}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(t("add_to_compare"), key="add_compare"):
                    if analyze_symbol not in st.session_state.comparison_list:
                        st.session_state.comparison_list.append(analyze_symbol)
                        st.success(f"{analyze_symbol} karşılaştırma listesine eklendi!")
                    else:
                        st.warning(f"{analyze_symbol} zaten listede!")

            with col2:
                if st.button(t("clear_comparison"), key="clear_compare"):
                    st.session_state.comparison_list = []
                    st.success("Karşılaştırma listesi temizlendi!")

            # Karşılaştırma listesi
            if st.session_state.comparison_list:
                st.markdown("### Karşılaştırma Listesi")

                comparison_data = []
                for comp_symbol in st.session_state.comparison_list:
                    comp_analysis = analyze_stock(comp_symbol, period)
                    if comp_analysis and "error" not in comp_analysis:
                        returns = comp_analysis.get("returns", {})
                        risk_metrics = comp_analysis.get("risk_metrics", {})

                        comparison_data.append({
                            "Sembol": comp_symbol,
                            "Güncel Fiyat": f"${comp_analysis.get('current_price', 0):.2f}",
                            "1M Getiri": f"{returns.get('1M', 0):+.2f}%",
                            "3M Getiri": f"{returns.get('3M', 0):+.2f}%",
                            "1Y Getiri": f"{returns.get('1Y', 0):+.2f}%",
                            "Volatilite": f"{risk_metrics.get('volatility_annual', 0):.1f}%",
                            "Risk Seviyesi": risk_metrics.get('risk_level', 'Bilinmiyor')
                        })

                if comparison_data:
                    comp_df = pd.DataFrame(comparison_data)
                    st.dataframe(comp_df, hide_index=True, use_container_width=True)

        else:
            st.error(f"{analyze_symbol} için veri bulunamadı veya hata oluştu.")

    else:
        # Grid layout for stocks and ETFs - organized like main page
        st.markdown("### 🌟 Analiz için bir hisse senedi veya ETF seçin")

        # Create comprehensive global assets dictionary
        GLOBAL_STOCKS = {
            "🇺🇸 US Large Cap": {
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corp.",
                "GOOGL": "Alphabet Inc.",
                "AMZN": "Amazon.com Inc.",
                "TSLA": "Tesla Inc.",
                "META": "Meta Platforms",
                "NVDA": "NVIDIA Corp.",
                "NFLX": "Netflix Inc.",
                "BRK-B": "Berkshire Hathaway",
                "JNJ": "Johnson & Johnson",
                "V": "Visa Inc.",
                "WMT": "Walmart Inc.",
                "PG": "Procter & Gamble",
                "HD": "Home Depot",
                "MA": "Mastercard Inc."
            },
            "🇺🇸 US Mid Cap": {
                "CRM": "Salesforce",
                "ADBE": "Adobe Inc.",
                "NTES": "NetEase",
                "PYPL": "PayPal",
                "INTC": "Intel Corp.",
                "CSCO": "Cisco Systems",
                "PFE": "Pfizer Inc.",
                "KO": "Coca-Cola",
                "PEP": "PepsiCo",
                "ORCL": "Oracle Corp."
            },
            "🇪🇺 European": {
                "ASML": "ASML Holding NV",
                "SAP": "SAP SE",
                "NVO": "Novo Nordisk",
                "SHEL": "Shell PLC",
                "UL": "Unilever PLC"
            },
            "🇯🇵 Japanese": {
                "TSM": "Taiwan Semiconductor",
                "TM": "Toyota Motor",
                "SONY": "Sony Group"
            },
            "🇨🇳 Chinese": {
                "BABA": "Alibaba Group",
                "TCEHY": "Tencent Holdings",
                "JD": "JD.com Inc.",
                "BIDU": "Baidu Inc.",
                "NIO": "NIO Inc.",
                "LI": "Li Auto Inc.",
                "XPEV": "XPeng Inc.",
                "PDD": "PDD Holdings Inc.",
                "BILI": "Bilibili Inc.",
                "TME": "Tencent Music Entertainment"
            },
            "🇮🇳 Indian": {
                "INFY": "Infosys Ltd ADR",
                "WIT": "Wipro Ltd ADR",
                "HDB": "HDFC Bank Ltd ADR",
                "IBN": "ICICI Bank Ltd ADR",
                "TTM": "Tata Motors Ltd ADR",
                "RDY": "Dr. Reddy's Laboratories",
                "VEDL": "Vedanta Limited ADR"
            },
            "🇧🇷 Brazilian": {
                "VALE": "Vale SA ADR",
                "PBR": "Petróleo Brasileiro SA",
                "BBD": "Banco Bradesco SA ADR",
                "ITUB": "Itaú Unibanco Holding SA",
                "ABEV": "Ambev SA ADR"
            },
            "🇨🇦 Canadian": {
                "SHOP": "Shopify Inc.",
                "CNQ": "Canadian Natural Resources",
                "SU": "Suncor Energy Inc.",
                "ENB": "Enbridge Inc.",
                "RY": "Royal Bank of Canada",
                "TD": "Toronto-Dominion Bank"
            },
            "🇦🇺 Australian": {
                "BHP": "BHP Group Ltd ADR",
                "RIO": "Rio Tinto Group ADR",
                "WBK": "Westpac Banking Corp ADR"
            },
            "🇰🇷 South Korean": {
                "LPL": "LG Display Co Ltd ADR",
                "KB": "KB Financial Group ADR"
            },
            "🌍 Global ADRs": {
                "ASML": "ASML Holding NV",
                "UL": "Unilever PLC ADR",
                "NVS": "Novartis AG ADR",
                "SNY": "Sanofi ADR",
                "AZN": "AstraZeneca PLC ADR"
            },
            "🇹🇷 Turkish Stocks (BIST)": {
                "AKBNK": "Akbank T.A.Ş.",
                "GARAN": "Türkiye Garanti Bankası A.Ş.",
                "ISCTR": "Türkiye İş Bankası A.Ş.",
                "THYAO": "Türk Hava Yolları A.O.",
                "KCHOL": "Koç Holding A.Ş.",
                "SAHOL": "Sabancı Holding A.Ş.",
                "ASELS": "Aselsan Elektronik San. ve Tic. A.Ş.",
                "SISE": "Şişe Cam Sanayii A.Ş.",
                "EREGL": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.",
                "BIMAS": "BIM Birleşik Mağazalar A.Ş.",
                "TOASO": "Tofaş Türk Otomobil Fabrikası A.Ş.",
                "TCELL": "Turkcell İletişim Hizmetleri A.Ş.",
                "KOZAL": "Koza Altın İşletmeleri A.Ş.",
                "PETKM": "Petkim Petrokimya Holding A.Ş.",
                "TUPRS": "Tüpraş-Türkiye Petrol Rafinerileri A.Ş.",
                "VAKBN": "Türkiye Vakıflar Bankası T.A.O.",
                "HALKB": "Türkiye Halk Bankası A.Ş.",
                "ARCLK": "Arçelik A.Ş.",
                "FROTO": "Ford Otomotiv Sanayi A.Ş.",
                "ODAS": "Odaş Elektrik Üretim Sanayi Ticaret A.Ş."
            }
        }

        GLOBAL_ETFS = {
            "📊 Broad Market ETFs": {
                "SPY": "SPDR S&P 500 ETF",
                "VTI": "Vanguard Total Stock Market",
                "QQQ": "Invesco QQQ Trust",
                "IWM": "iShares Russell 2000",
                "VOO": "Vanguard S&P 500 ETF",
                "IVV": "iShares Core S&P 500",
                "VTV": "Vanguard Value ETF",
                "VUG": "Vanguard Growth ETF"
            },
            "🌍 International ETFs": {
                "VEA": "Vanguard Developed Markets",
                "VWO": "Vanguard Emerging Markets",
                "EFA": "iShares MSCI EAFE",
                "EEM": "iShares MSCI Emerging",
                "IEFA": "iShares Core MSCI EAFE",
                "VGK": "Vanguard FTSE Europe",
                "FXI": "iShares China Large-Cap",
                "EWJ": "iShares MSCI Japan"
            },
            "🏭 Sector ETFs": {
                "XLK": "Technology Select Sector",
                "XLV": "Health Care Select",
                "XLF": "Financial Select",
                "XLE": "Energy Select",
                "XLI": "Industrial Select",
                "XLY": "Consumer Discretionary",
                "XLP": "Consumer Staples",
                "XLU": "Utilities Select",
                "XLB": "Materials Select",
                "XLRE": "Real Estate Select",
                "XLC": "Communication Services"
            },
            "🚀 Technology ETFs": {
                "VGT": "Vanguard IT ETF",
                "SOXX": "iShares Semiconductor",
                "SMH": "VanEck Semiconductor",
                "ARKK": "ARK Innovation",
                "ARKQ": "ARK Autonomous & Robotics",
                "CLOU": "Global X Cloud Computing",
                "SKYY": "First Trust Cloud Computing",
                "ROBO": "ROBO Global Robotics"
            },
            "🏥 Healthcare ETFs": {
                "VHT": "Vanguard Health Care",
                "IBB": "iShares Biotechnology",
                "XBI": "SPDR S&P Biotech",
                "ARKG": "ARK Genomic Revolution"
            },
            "🏦 Financial ETFs": {
                "VFH": "Vanguard Financials",
                "IYF": "iShares US Financials",
                "KBE": "SPDR S&P Bank",
                "KRE": "SPDR S&P Regional Banking"
            },
            "⚡ Energy ETFs": {
                "VDE": "Vanguard Energy",
                "IYE": "iShares US Energy",
                "XOP": "SPDR S&P Oil & Gas",
                "ICLN": "iShares Clean Energy",
                "PBW": "Invesco Clean Energy"
            },
            "💎 Commodity ETFs": {
                "GLD": "SPDR Gold Trust",
                "SLV": "iShares Silver Trust",
                "UNG": "United States Natural Gas",
                "USO": "United States Oil Fund",
                "DBA": "Invesco DB Agriculture"
            },
            "🎯 Thematic ETFs": {
                "JETS": "US Global Jets",
                "ESPO": "VanEck Video Gaming",
                "HERO": "Global X Video Games",
                "HACK": "ETFMG Prime Cyber Security",
                "ARKK": "ARK Innovation",
                "ARKQ": "ARK Autonomous Technology",
                "ARKG": "ARK Genomic Revolution",
                "ARKW": "ARK Next Generation Internet",
                "ICLN": "iShares Global Clean Energy",
                "UFO": "Procure Space ETF",
                "CLOU": "Global X Cloud Computing",
                "SKYY": "First Trust Cloud Computing"
            },
            "🏠 Real Estate ETFs": {
                "VNQ": "Vanguard Real Estate",
                "IYR": "iShares US Real Estate",
                "XLRE": "Real Estate Select",
                "REZ": "iShares Residential Real Estate",
                "REM": "iShares Mortgage Real Estate"
            },
            "💰 Bond ETFs": {
                "BND": "Vanguard Total Bond Market",
                "AGG": "iShares Core US Aggregate Bond",
                "TLT": "iShares 20+ Year Treasury",
                "IEF": "iShares 7-10 Year Treasury",
                "SHY": "iShares 1-3 Year Treasury",
                "LQD": "iShares iBoxx $ Investment Grade",
                "HYG": "iShares iBoxx $ High Yield"
            },
            "🏪 Consumer ETFs": {
                "XLY": "Consumer Discretionary Select",
                "XLP": "Consumer Staples Select",
                "VCR": "Vanguard Consumer Discretionary",
                "VDC": "Vanguard Consumer Staples",
                "IYK": "iShares US Consumer Goods"
            },
            "⚡ Utilities ETFs": {
                "XLU": "Utilities Select Sector",
                "VPU": "Vanguard Utilities",
                "IYU": "iShares US Utilities",
                "FUTY": "Fidelity MSCI Utilities"
            },
            "📞 Communication ETFs": {
                "XLC": "Communication Services Select",
                "VOX": "Vanguard Communication Services",
                "IYZ": "iShares US Telecommunications",
                "FCOM": "Fidelity MSCI Communication"
            },
            "🌾 Agriculture ETFs": {
                "DBA": "Invesco DB Agriculture",
                "CORN": "Teucrium Corn Fund",
                "SOYB": "Teucrium Soybean Fund",
                "WEAT": "Teucrium Wheat Fund"
            },
            "🚢 Transportation ETFs": {
                "IYT": "iShares Transportation Average",
                "JETS": "US Global Jets",
                "SHIP": "iShares Global Shipping"
            }
        }

        # Function to display asset grid
        def display_asset_grid(assets_dict, category_title):
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
                color: white;
                padding: 1rem;
                border-radius: 10px;
                margin: 1rem 0;
                font-size: 1.3rem;
                font-weight: bold;
                text-align: center;
            ">{category_title}</div>
            """, unsafe_allow_html=True)

            cols = st.columns(5)
            col_idx = 0

            for symbol, name in assets_dict.items():
                with cols[col_idx % 5]:
                    if st.button(f"{symbol}", key=f"{category_title}_{symbol}", help=f"{name}"):
                        st.session_state.analyze_symbol = symbol
                        st.rerun()
                col_idx += 1

        # Display stocks
        st.markdown("## 📈 Global Stocks")
        for region, stocks in GLOBAL_STOCKS.items():
            display_asset_grid(stocks, region)

        # Display ETFs
        st.markdown("## 🏛️ Global ETFs")
        for category, etfs in GLOBAL_ETFS.items():
            display_asset_grid(etfs, category)

        # Global Market Overview
        st.markdown("## 🌍 Global Market Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 15px;
                color: white;
                margin: 1rem 0;
            ">
                <h3>🇺🇸 US Markets</h3>
                <p>S&P 500: 4,450 (+1.2%)</p>
                <p>NASDAQ: 13,800 (+0.8%)</p>
                <p>DOW: 34,500 (+0.5%)</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 15px;
                color: white;
                margin: 1rem 0;
            ">
                <h3>🌍 International</h3>
                <p>FTSE 100: 7,400 (+0.3%)</p>
                <p>DAX: 15,200 (-0.2%)</p>
                <p>Nikkei: 28,800 (+1.1%)</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 15px;
                color: white;
                margin: 1rem 0;
            ">
                <h3>📊 Market Indicators</h3>
                <p>VIX: 18.5 (-2.1%)</p>
                <p>USD/EUR: 1.08 (+0.1%)</p>
                <p>Gold: $1,950 (+0.8%)</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()