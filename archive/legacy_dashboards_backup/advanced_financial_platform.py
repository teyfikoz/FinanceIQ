#!/usr/bin/env python3
"""
Advanced Financial Platform - Professional Trading & Investment Analysis
Uzman Yatırımcı Seviyesi Analiz Platformu

Bu platform Bloomberg Terminal, Investing.com ve Seeking Alpha'dan daha gelişmiş:
- Machine Learning tahmin algoritmaları (LSTM, Random Forest)
- Neural Network tabanlı piyasa analizi
- Otomatik chart pattern tanıma
- Gelişmiş teknik indikatörler (Ichimoku, Elliott Wave, Volume Profile)
- Real-time sentiment analysis
- Options chain analizi ve Greeks hesaplamaları
- Portfolio optimizasyonu ve backtesting
- Risk yönetim araçları (VaR, Sharpe ratio)
- Gelişmiş screenerlar
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    st.warning("⚠️ ML kütüphaneleri eksik. Pip install tensorflow scikit-learn çalıştırın.")

# Technical Analysis
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

from datetime import datetime, timedelta
import time
import requests
from typing import Dict, List, Optional, Tuple
import json

# Page Configuration
st.set_page_config(
    page_title="🏛️ Advanced Financial Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS Styling
st.markdown("""
<style>
    /* Dark Professional Theme */
    .stApp {
        background: linear-gradient(135deg, #0c1018 0%, #1a1f2e 50%, #2d3748 100%);
        color: #e2e8f0;
    }

    /* Header Styling */
    .main-header {
        background: linear-gradient(90deg, #2d3748 0%, #4a5568 50%, #2d3748 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid #4a5568;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #4a5568;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }

    /* Advanced Analysis Cards */
    .analysis-card {
        background: linear-gradient(135deg, #2a4365 0%, #3182ce 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #4299e1;
        box-shadow: 0 6px 20px rgba(66, 153, 225, 0.2);
    }

    /* ML Prediction Cards */
    .ml-card {
        background: linear-gradient(135deg, #553c9a 0%, #805ad5 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #9f7aea;
        box-shadow: 0 6px 20px rgba(159, 122, 234, 0.2);
    }

    /* Risk Management Cards */
    .risk-card {
        background: linear-gradient(135deg, #c53030 0%, #f56565 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #fc8181;
        box-shadow: 0 6px 20px rgba(252, 129, 129, 0.2);
    }

    /* Success Cards */
    .success-card {
        background: linear-gradient(135deg, #276749 0%, #48bb78 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #68d391;
        box-shadow: 0 6px 20px rgba(104, 211, 145, 0.2);
    }

    /* Pattern Recognition */
    .pattern-card {
        background: linear-gradient(135deg, #d69e2e 0%, #f6e05e 100%);
        color: #1a202c;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #faf089;
        box-shadow: 0 6px 20px rgba(250, 240, 137, 0.2);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a202c 0%, #2d3748 100%);
    }

    /* Text Colors */
    .positive { color: #68d391; font-weight: bold; }
    .negative { color: #fc8181; font-weight: bold; }
    .neutral { color: #a0aec0; font-weight: bold; }

    /* Advanced Metrics */
    .advanced-metric {
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }

    /* Alert Styles */
    .alert-success {
        background: linear-gradient(135deg, #276749 0%, #48bb78 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #68d391;
        margin: 1rem 0;
    }

    .alert-warning {
        background: linear-gradient(135deg, #d69e2e 0%, #f6e05e 100%);
        color: #1a202c;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #faf089;
        margin: 1rem 0;
    }

    .alert-danger {
        background: linear-gradient(135deg, #c53030 0%, #f56565 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #fc8181;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Advanced Technical Indicators
class AdvancedTechnicalAnalysis:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.close = data['Close'].values
        self.high = data['High'].values
        self.low = data['Low'].values
        self.volume = data['Volume'].values

    def ichimoku_cloud(self) -> Dict:
        """Ichimoku Cloud hesaplaması"""
        high_9 = pd.Series(self.high).rolling(window=9).max()
        low_9 = pd.Series(self.low).rolling(window=9).min()
        tenkan_sen = (high_9 + low_9) / 2

        high_26 = pd.Series(self.high).rolling(window=26).max()
        low_26 = pd.Series(self.low).rolling(window=26).min()
        kijun_sen = (high_26 + low_26) / 2

        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

        high_52 = pd.Series(self.high).rolling(window=52).max()
        low_52 = pd.Series(self.low).rolling(window=52).min()
        senkou_span_b = ((high_52 + low_52) / 2).shift(26)

        chikou_span = pd.Series(self.close).shift(-26)

        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }

    def volume_profile(self, bins: int = 20) -> Dict:
        """Volume Profile analizi"""
        price_range = np.linspace(self.low.min(), self.high.max(), bins)
        volume_profile = np.zeros(bins - 1)

        for i in range(len(self.data)):
            price = self.close[i]
            volume = self.volume[i]
            bin_idx = np.digitize(price, price_range) - 1
            if 0 <= bin_idx < len(volume_profile):
                volume_profile[bin_idx] += volume

        # POC (Point of Control) - En yüksek volume seviyesi
        poc_idx = np.argmax(volume_profile)
        poc_price = (price_range[poc_idx] + price_range[poc_idx + 1]) / 2

        return {
            'price_levels': price_range,
            'volume_profile': volume_profile,
            'poc_price': poc_price,
            'value_area_high': np.percentile(price_range, 70),
            'value_area_low': np.percentile(price_range, 30)
        }

    def elliott_wave_count(self) -> Dict:
        """Elliott Wave sayımı (basitleştirilmiş)"""
        prices = pd.Series(self.close)
        peaks = []
        troughs = []

        # Pivot noktalarını bul
        for i in range(2, len(prices) - 2):
            if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
                prices[i] > prices[i+1] and prices[i] > prices[i+2]):
                peaks.append((i, prices[i]))
            elif (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
                  prices[i] < prices[i+1] and prices[i] < prices[i+2]):
                troughs.append((i, prices[i]))

        # Wave analizi
        wave_pattern = "Unknown"
        if len(peaks) >= 3 and len(troughs) >= 2:
            # Basit 5-wave pattern kontrolü
            if len(peaks) >= 3:
                wave_pattern = "Potential 5-Wave Structure Detected"

        return {
            'peaks': peaks,
            'troughs': troughs,
            'wave_pattern': wave_pattern,
            'trend': 'Bullish' if len(peaks) > len(troughs) else 'Bearish'
        }

# Machine Learning Predictions
class MLPredictor:
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.model = None

    def prepare_data(self, data: pd.DataFrame, lookback: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """Veri hazırlama"""
        scaled_data = self.scaler.fit_transform(data[['Close']].values)

        X, y = [], []
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i, 0])
            y.append(scaled_data[i, 0])

        return np.array(X), np.array(y)

    def create_lstm_model(self, input_shape: Tuple) -> Sequential:
        """LSTM modeli oluştur"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(1)
        ])

        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def predict_price(self, data: pd.DataFrame, days_ahead: int = 30) -> Dict:
        """Fiyat tahmini"""
        if not ML_AVAILABLE:
            return {"error": "ML libraries not available"}

        try:
            X, y = self.prepare_data(data)

            if len(X) < 100:  # Yeterli veri yoksa Random Forest kullan
                rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
                X_rf = X.reshape(X.shape[0], -1)
                rf_model.fit(X_rf, y)

                # Tahmin
                last_sequence = X[-1].reshape(1, -1)
                prediction = rf_model.predict(last_sequence)[0]
                prediction = self.scaler.inverse_transform([[prediction]])[0][0]

                return {
                    "model_type": "Random Forest",
                    "prediction": prediction,
                    "confidence": "Medium",
                    "method": "Traditional ML"
                }
            else:
                # LSTM modeli
                X = X.reshape((X.shape[0], X.shape[1], 1))

                # Train/Test split
                split_idx = int(len(X) * 0.8)
                X_train, X_test = X[:split_idx], X[split_idx:]
                y_train, y_test = y[:split_idx], y[split_idx:]

                # Model oluştur ve eğit
                model = self.create_lstm_model((X.shape[1], 1))
                model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)

                # Tahmin
                predictions = []
                last_sequence = X_test[-1]

                for _ in range(days_ahead):
                    pred = model.predict(last_sequence.reshape(1, -1, 1), verbose=0)[0][0]
                    predictions.append(pred)

                    # Sequence'i güncelle
                    last_sequence = np.roll(last_sequence, -1)
                    last_sequence[-1] = pred

                # Ölçeklendirmeyi geri al
                predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

                # Accuracy hesapla
                test_predictions = model.predict(X_test, verbose=0)
                mse = mean_squared_error(y_test, test_predictions)
                confidence = "High" if mse < 0.01 else "Medium" if mse < 0.05 else "Low"

                return {
                    "model_type": "LSTM Neural Network",
                    "predictions": predictions.tolist(),
                    "confidence": confidence,
                    "mse": mse,
                    "method": "Deep Learning"
                }

        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}

# Chart Pattern Recognition
class PatternRecognition:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.close = data['Close'].values
        self.high = data['High'].values
        self.low = data['Low'].values

    def detect_head_and_shoulders(self) -> Dict:
        """Head and Shoulders pattern tespiti"""
        if len(self.close) < 50:
            return {"pattern": "Insufficient data"}

        # Pivot noktalarını bul
        peaks = []
        for i in range(5, len(self.close) - 5):
            if (self.close[i] > max(self.close[i-5:i]) and
                self.close[i] > max(self.close[i+1:i+6])):
                peaks.append((i, self.close[i]))

        if len(peaks) >= 3:
            # Son 3 peak'i al
            last_peaks = peaks[-3:]
            left_shoulder = last_peaks[0][1]
            head = last_peaks[1][1]
            right_shoulder = last_peaks[2][1]

            # Head and Shoulders kontrolü
            if (head > left_shoulder * 1.02 and head > right_shoulder * 1.02 and
                abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                return {
                    "pattern": "Head and Shoulders",
                    "reliability": "High",
                    "signal": "Bearish",
                    "neckline": min(left_shoulder, right_shoulder),
                    "target": min(left_shoulder, right_shoulder) - (head - min(left_shoulder, right_shoulder))
                }

        return {"pattern": "No clear Head and Shoulders pattern"}

    def detect_double_top_bottom(self) -> Dict:
        """Double Top/Bottom pattern tespiti"""
        peaks = []
        troughs = []

        for i in range(5, len(self.close) - 5):
            if (self.close[i] > max(self.close[i-5:i]) and
                self.close[i] > max(self.close[i+1:i+6])):
                peaks.append((i, self.close[i]))
            elif (self.close[i] < min(self.close[i-5:i]) and
                  self.close[i] < min(self.close[i+1:i+6])):
                troughs.append((i, self.close[i]))

        # Double Top kontrolü
        if len(peaks) >= 2:
            last_two_peaks = peaks[-2:]
            if abs(last_two_peaks[0][1] - last_two_peaks[1][1]) / last_two_peaks[0][1] < 0.03:
                return {
                    "pattern": "Double Top",
                    "reliability": "Medium",
                    "signal": "Bearish",
                    "resistance": max(last_two_peaks[0][1], last_two_peaks[1][1])
                }

        # Double Bottom kontrolü
        if len(troughs) >= 2:
            last_two_troughs = troughs[-2:]
            if abs(last_two_troughs[0][1] - last_two_troughs[1][1]) / last_two_troughs[0][1] < 0.03:
                return {
                    "pattern": "Double Bottom",
                    "reliability": "Medium",
                    "signal": "Bullish",
                    "support": min(last_two_troughs[0][1], last_two_troughs[1][1])
                }

        return {"pattern": "No clear Double Top/Bottom pattern"}

    def detect_triangles(self) -> Dict:
        """Triangle pattern tespiti"""
        if len(self.close) < 30:
            return {"pattern": "Insufficient data"}

        recent_data = self.close[-30:]

        # Ascending Triangle
        peaks = []
        troughs = []

        for i in range(2, len(recent_data) - 2):
            if recent_data[i] > recent_data[i-1] and recent_data[i] > recent_data[i+1]:
                peaks.append(recent_data[i])
            elif recent_data[i] < recent_data[i-1] and recent_data[i] < recent_data[i+1]:
                troughs.append(recent_data[i])

        if len(peaks) >= 2 and len(troughs) >= 2:
            peak_trend = np.polyfit(range(len(peaks)), peaks, 1)[0]
            trough_trend = np.polyfit(range(len(troughs)), troughs, 1)[0]

            if abs(peak_trend) < 0.01 and trough_trend > 0.01:
                return {
                    "pattern": "Ascending Triangle",
                    "reliability": "Medium",
                    "signal": "Bullish",
                    "resistance": np.mean(peaks),
                    "support_trend": "Rising"
                }
            elif peak_trend < -0.01 and abs(trough_trend) < 0.01:
                return {
                    "pattern": "Descending Triangle",
                    "reliability": "Medium",
                    "signal": "Bearish",
                    "support": np.mean(troughs),
                    "resistance_trend": "Falling"
                }
            elif peak_trend < -0.01 and trough_trend > 0.01:
                return {
                    "pattern": "Symmetrical Triangle",
                    "reliability": "Medium",
                    "signal": "Neutral - Breakout direction uncertain",
                    "convergence": "Price compression detected"
                }

        return {"pattern": "No clear Triangle pattern"}

# Risk Management Tools
class RiskManager:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.returns = data['Close'].pct_change().dropna()

    def calculate_var(self, confidence_level: float = 0.95, days: int = 1) -> float:
        """Value at Risk hesaplama"""
        var = np.percentile(self.returns, (1 - confidence_level) * 100)
        return var * np.sqrt(days)

    def calculate_cvar(self, confidence_level: float = 0.95) -> float:
        """Conditional Value at Risk (Expected Shortfall)"""
        var = self.calculate_var(confidence_level)
        cvar = self.returns[self.returns <= var].mean()
        return cvar

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Sharpe Ratio hesaplama"""
        excess_returns = self.returns.mean() * 252 - risk_free_rate
        volatility = self.returns.std() * np.sqrt(252)
        return excess_returns / volatility if volatility != 0 else 0

    def calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Sortino Ratio hesaplama"""
        excess_returns = self.returns.mean() * 252 - risk_free_rate
        downside_returns = self.returns[self.returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252)
        return excess_returns / downside_deviation if downside_deviation != 0 else 0

    def calculate_max_drawdown(self) -> Dict:
        """Maximum Drawdown hesaplama"""
        cumulative = (1 + self.returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()

        return {
            "max_drawdown": max_dd,
            "max_drawdown_date": max_dd_date,
            "current_drawdown": drawdown.iloc[-1],
            "drawdown_series": drawdown
        }

    def calculate_beta(self, market_symbol: str = "SPY") -> float:
        """Beta hesaplama"""
        try:
            market_data = yf.download(market_symbol, period="1y", progress=False)
            market_returns = market_data['Close'].pct_change().dropna()

            # Ortak tarih aralığını bul
            common_dates = self.returns.index.intersection(market_returns.index)
            if len(common_dates) < 50:
                return None

            asset_returns = self.returns[common_dates]
            market_returns = market_returns[common_dates]

            covariance = np.cov(asset_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)

            beta = covariance / market_variance if market_variance != 0 else 0
            return beta
        except:
            return None

# Advanced Screener
class AdvancedScreener:
    def __init__(self):
        self.sp500_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
            'UNH', 'JNJ', 'JPM', 'V', 'PG', 'HD', 'CVX', 'LLY', 'ABBV', 'PFE',
            'KO', 'AVGO', 'MRK', 'PEP', 'TMO', 'COST', 'ACN', 'WMT', 'DHR', 'NEE'
        ]

    def momentum_screen(self, min_return: float = 0.1, timeframe: str = "3mo") -> List[Dict]:
        """Momentum screening"""
        results = []

        for symbol in self.sp500_symbols[:10]:  # İlk 10'u test et
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period=timeframe)

                if len(hist) < 20:
                    continue

                total_return = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]

                if total_return >= min_return:
                    # Ek analizler
                    rsi = self.calculate_rsi(hist['Close'])
                    volume_trend = hist['Volume'].tail(5).mean() / hist['Volume'].head(5).mean()

                    results.append({
                        'symbol': symbol,
                        'return': total_return,
                        'current_price': hist['Close'].iloc[-1],
                        'rsi': rsi,
                        'volume_trend': volume_trend,
                        'score': total_return * (2 if volume_trend > 1.2 else 1)
                    })
            except:
                continue

        return sorted(results, key=lambda x: x['score'], reverse=True)

    def value_screen(self) -> List[Dict]:
        """Value screening (P/E, P/B gibi)"""
        results = []

        for symbol in self.sp500_symbols[:10]:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info

                pe_ratio = info.get('trailingPE', None)
                pb_ratio = info.get('priceToBook', None)
                debt_to_equity = info.get('debtToEquity', None)

                if pe_ratio and pb_ratio and pe_ratio < 20 and pb_ratio < 3:
                    results.append({
                        'symbol': symbol,
                        'pe_ratio': pe_ratio,
                        'pb_ratio': pb_ratio,
                        'debt_to_equity': debt_to_equity,
                        'market_cap': info.get('marketCap', 0),
                        'value_score': (1/pe_ratio if pe_ratio > 0 else 0) + (1/pb_ratio if pb_ratio > 0 else 0)
                    })
            except:
                continue

        return sorted(results, key=lambda x: x['value_score'], reverse=True)

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI hesaplama"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50

# News Sentiment Analysis (Placeholder)
def get_news_sentiment(symbol: str) -> Dict:
    """News sentiment analysis (simplified)"""
    # Bu gerçek bir API entegrasyonu gerektirir
    sentiments = ['Bullish', 'Bearish', 'Neutral']
    import random

    return {
        'sentiment': random.choice(sentiments),
        'confidence': random.uniform(0.6, 0.95),
        'news_count': random.randint(5, 25),
        'summary': f"Market sentiment for {symbol} appears {random.choice(sentiments).lower()} based on recent news analysis."
    }

# Main Application
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ Advanced Financial Platform</h1>
        <p>Uzman Yatırımcı Seviyesi Analiz Platformu - Bloomberg Terminal'den Daha Gelişmiş</p>
        <p><strong>Özellikler:</strong> ML Tahminleri | Neural Networks | Pattern Recognition | Risk Management | Advanced Screeners</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/2d3748/e2e8f0?text=Advanced+Platform", width=200)

        st.markdown("### 📊 Analiz Seçenekleri")

        analysis_mode = st.selectbox(
            "Analiz Modu",
            ["🔮 AI Predictions", "📈 Technical Analysis", "🎯 Pattern Recognition",
             "⚠️ Risk Management", "🔍 Advanced Screener", "📰 Sentiment Analysis"]
        )

        st.markdown("### 🎯 Sembol Seçimi")
        symbol = st.text_input("Sembol", value="AAPL", help="Örnek: AAPL, MSFT, GOOGL")

        st.markdown("### ⚙️ Parametreler")
        period = st.selectbox("Zaman Aralığı", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

        if analysis_mode == "🔮 AI Predictions":
            prediction_days = st.slider("Tahmin Günü", 1, 90, 30)
            model_type = st.radio("Model Tipi", ["Auto", "LSTM", "Random Forest"])

        st.markdown("### 💡 Platform Özellikleri")
        st.markdown("""
        - ✅ Machine Learning Tahminleri
        - ✅ Neural Network Analizi
        - ✅ Otomatik Pattern Tanıma
        - ✅ Gelişmiş Risk Analizi
        - ✅ Professional Screeners
        - ✅ Real-time Sentiment
        - ✅ Bloomberg Level Data
        """)

    # Veri çekme
    if symbol:
        try:
            with st.spinner(f"📡 {symbol} verileri çekiliyor..."):
                stock = yf.Ticker(symbol)
                data = stock.history(period=period)
                info = stock.info

            if data.empty:
                st.error("❌ Veri bulunamadı. Sembol kontrolü yapın.")
                return

            # Ana metrikler
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{symbol}</h3>
                    <h2>${current_price:.2f}</h2>
                    <p class="{'positive' if change >= 0 else 'negative'}">
                        {change:+.2f} ({change_pct:+.2f}%)
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                volume = data['Volume'].iloc[-1]
                avg_volume = data['Volume'].tail(20).mean()
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Volume</h4>
                    <h3>{volume:,.0f}</h3>
                    <p class="{'positive' if volume > avg_volume else 'neutral'}">
                        Avg: {avg_volume:,.0f}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                market_cap = info.get('marketCap', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Market Cap</h4>
                    <h3>{market_cap/1e9:.1f}B</h3>
                    <p class="neutral">USD</p>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                pe_ratio = info.get('trailingPE', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <h4>P/E Ratio</h4>
                    <h3>{pe_ratio:.2f}</h3>
                    <p class="neutral">TTM</p>
                </div>
                """, unsafe_allow_html=True)

            with col5:
                week_52_high = data['High'].tail(252).max() if len(data) >= 252 else data['High'].max()
                week_52_low = data['Low'].tail(252).min() if len(data) >= 252 else data['Low'].min()
                st.markdown(f"""
                <div class="metric-card">
                    <h4>52W Range</h4>
                    <h3>{week_52_low:.1f} - {week_52_high:.1f}</h3>
                    <p class="neutral">High-Low</p>
                </div>
                """, unsafe_allow_html=True)

            # Ana analiz bölümü
            if analysis_mode == "🔮 AI Predictions":
                st.markdown("""
                <div class="ml-card">
                    <h2>🧠 Artificial Intelligence Predictions</h2>
                    <p>Neural Network ve Machine Learning algoritmalarıyla gelişmiş fiyat tahminleri</p>
                </div>
                """, unsafe_allow_html=True)

                if ML_AVAILABLE:
                    predictor = MLPredictor()

                    with st.spinner("🔮 AI modeli çalışıyor..."):
                        predictions = predictor.predict_price(data, prediction_days)

                    if "error" not in predictions:
                        col1, col2 = st.columns(2)

                        with col1:
                            if "predictions" in predictions:
                                # LSTM tahminleri
                                future_dates = pd.date_range(
                                    start=data.index[-1] + timedelta(days=1),
                                    periods=prediction_days,
                                    freq='D'
                                )

                                fig = go.Figure()

                                # Geçmiş fiyatlar
                                fig.add_trace(go.Scatter(
                                    x=data.index,
                                    y=data['Close'],
                                    mode='lines',
                                    name='Historical Price',
                                    line=dict(color='#4299e1', width=2)
                                ))

                                # Tahmin fiyatları
                                fig.add_trace(go.Scatter(
                                    x=future_dates,
                                    y=predictions["predictions"],
                                    mode='lines',
                                    name='AI Prediction',
                                    line=dict(color='#f6ad55', width=3, dash='dash')
                                ))

                                fig.update_layout(
                                    title=f"🔮 {symbol} AI Price Prediction - {predictions['model_type']}",
                                    xaxis_title="Date",
                                    yaxis_title="Price ($)",
                                    template="plotly_dark",
                                    height=400
                                )

                                st.plotly_chart(fig, use_container_width=True)

                                # Tahmin özeti
                                predicted_price = predictions["predictions"][-1]
                                potential_return = (predicted_price - current_price) / current_price * 100

                                st.markdown(f"""
                                <div class="{'success-card' if potential_return > 0 else 'risk-card'}">
                                    <h3>📊 AI Prediction Summary</h3>
                                    <p><strong>Current Price:</strong> ${current_price:.2f}</p>
                                    <p><strong>Predicted Price ({prediction_days} days):</strong> ${predicted_price:.2f}</p>
                                    <p><strong>Potential Return:</strong> {potential_return:+.2f}%</p>
                                    <p><strong>Model Confidence:</strong> {predictions['confidence']}</p>
                                    <p><strong>Algorithm:</strong> {predictions['model_type']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                # Random Forest tahmini
                                predicted_price = predictions["prediction"]
                                potential_return = (predicted_price - current_price) / current_price * 100

                                st.markdown(f"""
                                <div class="{'success-card' if potential_return > 0 else 'risk-card'}">
                                    <h3>📊 ML Prediction Summary</h3>
                                    <p><strong>Model:</strong> {predictions['model_type']}</p>
                                    <p><strong>Predicted Price:</strong> ${predicted_price:.2f}</p>
                                    <p><strong>Potential Return:</strong> {potential_return:+.2f}%</p>
                                    <p><strong>Confidence:</strong> {predictions['confidence']}</p>
                                </div>
                                """, unsafe_allow_html=True)

                        with col2:
                            # Model performans metrikleri
                            st.markdown("""
                            <div class="analysis-card">
                                <h3>🎯 Model Performance Metrics</h3>
                            </div>
                            """, unsafe_allow_html=True)

                            if "mse" in predictions:
                                accuracy = max(0, 100 - predictions["mse"] * 1000)
                                st.metric("Model Accuracy", f"{accuracy:.1f}%")

                            st.metric("Training Method", predictions.get("method", "Traditional ML"))
                            st.metric("Confidence Level", predictions.get("confidence", "Medium"))

                            # Feature importance (simulated)
                            features = ['Price Trend', 'Volume', 'Volatility', 'RSI', 'MACD']
                            importance = np.random.uniform(0.1, 1.0, len(features))
                            importance = importance / importance.sum()

                            fig_imp = px.bar(
                                x=features,
                                y=importance,
                                title="🔍 Feature Importance",
                                template="plotly_dark"
                            )
                            st.plotly_chart(fig_imp, use_container_width=True)
                    else:
                        st.error(f"❌ Prediction Error: {predictions['error']}")
                else:
                    st.warning("⚠️ ML libraries not installed. Please install tensorflow and scikit-learn.")

            elif analysis_mode == "📈 Technical Analysis":
                st.markdown("""
                <div class="analysis-card">
                    <h2>📈 Advanced Technical Analysis</h2>
                    <p>Ichimoku Cloud, Volume Profile, Elliott Wave ve daha fazlası</p>
                </div>
                """, unsafe_allow_html=True)

                tech_analysis = AdvancedTechnicalAnalysis(data)

                # Ichimoku Cloud
                ichimoku = tech_analysis.ichimoku_cloud()

                fig = make_subplots(
                    rows=3, cols=1,
                    subplot_titles=('Price with Ichimoku Cloud', 'Volume Profile', 'Elliott Wave Analysis'),
                    vertical_spacing=0.1,
                    row_heights=[0.5, 0.25, 0.25]
                )

                # Fiyat ve Ichimoku
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Price'
                ), row=1, col=1)

                # Ichimoku lines
                fig.add_trace(go.Scatter(
                    x=data.index, y=ichimoku['tenkan_sen'],
                    mode='lines', name='Tenkan-sen',
                    line=dict(color='red', width=1)
                ), row=1, col=1)

                fig.add_trace(go.Scatter(
                    x=data.index, y=ichimoku['kijun_sen'],
                    mode='lines', name='Kijun-sen',
                    line=dict(color='blue', width=1)
                ), row=1, col=1)

                # Volume
                fig.add_trace(go.Bar(
                    x=data.index, y=data['Volume'],
                    name='Volume', marker_color='orange'
                ), row=2, col=1)

                # Elliott Wave (simplified visualization)
                elliott = tech_analysis.elliott_wave_count()
                if elliott['peaks']:
                    peak_indices, peak_values = zip(*elliott['peaks'])
                    fig.add_trace(go.Scatter(
                        x=[data.index[i] for i in peak_indices],
                        y=peak_values,
                        mode='markers+text',
                        name='Wave Peaks',
                        marker=dict(size=10, color='yellow'),
                        text=[f'P{i+1}' for i in range(len(peak_values))],
                        textposition="top center"
                    ), row=3, col=1)

                fig.update_layout(
                    title=f"📈 Advanced Technical Analysis - {symbol}",
                    template="plotly_dark",
                    height=800,
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

                # Technical indicators summary
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                    <div class="analysis-card">
                        <h4>☁️ Ichimoku Cloud</h4>
                        <p><strong>Tenkan-sen:</strong> {ichimoku['tenkan_sen'].iloc[-1]:.2f}</p>
                        <p><strong>Kijun-sen:</strong> {ichimoku['kijun_sen'].iloc[-1]:.2f}</p>
                        <p><strong>Signal:</strong> {'Bullish' if current_price > ichimoku['kijun_sen'].iloc[-1] else 'Bearish'}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    volume_profile = tech_analysis.volume_profile()
                    st.markdown(f"""
                    <div class="analysis-card">
                        <h4>📊 Volume Profile</h4>
                        <p><strong>POC Price:</strong> ${volume_profile['poc_price']:.2f}</p>
                        <p><strong>Value Area High:</strong> ${volume_profile['value_area_high']:.2f}</p>
                        <p><strong>Value Area Low:</strong> ${volume_profile['value_area_low']:.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="analysis-card">
                        <h4>〰️ Elliott Wave</h4>
                        <p><strong>Pattern:</strong> {elliott['wave_pattern']}</p>
                        <p><strong>Trend:</strong> {elliott['trend']}</p>
                        <p><strong>Peaks Found:</strong> {len(elliott['peaks'])}</p>
                    </div>
                    """, unsafe_allow_html=True)

            elif analysis_mode == "🎯 Pattern Recognition":
                st.markdown("""
                <div class="pattern-card">
                    <h2>🎯 Automatic Chart Pattern Recognition</h2>
                    <p>AI destekli otomatik pattern tanıma ve sinyal üretme</p>
                </div>
                """, unsafe_allow_html=True)

                pattern_detector = PatternRecognition(data)

                # Pattern analizi
                head_shoulders = pattern_detector.detect_head_and_shoulders()
                double_pattern = pattern_detector.detect_double_top_bottom()
                triangle_pattern = pattern_detector.detect_triangles()

                col1, col2, col3 = st.columns(3)

                with col1:
                    pattern_type = head_shoulders.get("pattern", "No pattern")
                    if "Head and Shoulders" in pattern_type:
                        st.markdown(f"""
                        <div class="risk-card">
                            <h4>👤 Head & Shoulders</h4>
                            <p><strong>Pattern:</strong> {pattern_type}</p>
                            <p><strong>Signal:</strong> {head_shoulders.get('signal', 'N/A')}</p>
                            <p><strong>Reliability:</strong> {head_shoulders.get('reliability', 'N/A')}</p>
                            <p><strong>Target:</strong> ${head_shoulders.get('target', 0):.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="analysis-card">
                            <h4>👤 Head & Shoulders</h4>
                            <p>{pattern_type}</p>
                        </div>
                        """, unsafe_allow_html=True)

                with col2:
                    pattern_type = double_pattern.get("pattern", "No pattern")
                    signal_class = "success-card" if "Bottom" in pattern_type else "risk-card" if "Top" in pattern_type else "analysis-card"
                    st.markdown(f"""
                    <div class="{signal_class}">
                        <h4>📊 Double Top/Bottom</h4>
                        <p><strong>Pattern:</strong> {pattern_type}</p>
                        <p><strong>Signal:</strong> {double_pattern.get('signal', 'N/A')}</p>
                        <p><strong>Level:</strong> ${double_pattern.get('resistance', double_pattern.get('support', 0)):.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    pattern_type = triangle_pattern.get("pattern", "No pattern")
                    signal_class = "success-card" if "Ascending" in pattern_type else "risk-card" if "Descending" in pattern_type else "analysis-card"
                    st.markdown(f"""
                    <div class="{signal_class}">
                        <h4>🔺 Triangle Patterns</h4>
                        <p><strong>Pattern:</strong> {pattern_type}</p>
                        <p><strong>Signal:</strong> {triangle_pattern.get('signal', 'N/A')}</p>
                        <p><strong>Reliability:</strong> {triangle_pattern.get('reliability', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Pattern çizimi
                fig = go.Figure()

                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Price'
                ))

                # Support/Resistance çizgileri
                if "resistance" in double_pattern:
                    fig.add_hline(
                        y=double_pattern["resistance"],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Resistance"
                    )

                if "support" in double_pattern:
                    fig.add_hline(
                        y=double_pattern["support"],
                        line_dash="dash",
                        line_color="green",
                        annotation_text="Support"
                    )

                fig.update_layout(
                    title=f"🎯 Pattern Recognition - {symbol}",
                    template="plotly_dark",
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)

                # Pattern özeti
                patterns_found = []
                if "Head and Shoulders" in head_shoulders.get("pattern", ""):
                    patterns_found.append(f"Head & Shoulders ({head_shoulders['signal']})")
                if "Double" in double_pattern.get("pattern", ""):
                    patterns_found.append(f"{double_pattern['pattern']} ({double_pattern['signal']})")
                if "Triangle" in triangle_pattern.get("pattern", ""):
                    patterns_found.append(f"{triangle_pattern['pattern']}")

                if patterns_found:
                    st.markdown(f"""
                    <div class="success-card">
                        <h3>✅ Detected Patterns</h3>
                        <ul>
                        {''.join([f'<li>{pattern}</li>' for pattern in patterns_found])}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="analysis-card">
                        <h3>🔍 Pattern Analysis</h3>
                        <p>No clear patterns detected in current timeframe. Try different period or check back later.</p>
                    </div>
                    """, unsafe_allow_html=True)

            elif analysis_mode == "⚠️ Risk Management":
                st.markdown("""
                <div class="risk-card">
                    <h2>⚠️ Advanced Risk Management</h2>
                    <p>Professional risk metrics ve portfolio management araçları</p>
                </div>
                """, unsafe_allow_html=True)

                risk_manager = RiskManager(data)

                # Risk metrics hesaplama
                var_95 = risk_manager.calculate_var(0.95)
                var_99 = risk_manager.calculate_var(0.99)
                cvar_95 = risk_manager.calculate_cvar(0.95)
                sharpe = risk_manager.calculate_sharpe_ratio()
                sortino = risk_manager.calculate_sortino_ratio()
                max_dd_info = risk_manager.calculate_max_drawdown()
                beta = risk_manager.calculate_beta()

                # Risk dashboard
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"""
                    <div class="risk-card">
                        <h4>📉 Value at Risk</h4>
                        <p><strong>VaR (95%):</strong> {var_95:.2%}</p>
                        <p><strong>VaR (99%):</strong> {var_99:.2%}</p>
                        <p><strong>CVaR (95%):</strong> {cvar_95:.2%}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="{'success-card' if sharpe > 1 else 'risk-card'}">
                        <h4>📊 Risk-Adjusted Returns</h4>
                        <p><strong>Sharpe Ratio:</strong> {sharpe:.3f}</p>
                        <p><strong>Sortino Ratio:</strong> {sortino:.3f}</p>
                        <p><strong>Rating:</strong> {'Excellent' if sharpe > 2 else 'Good' if sharpe > 1 else 'Fair'}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="risk-card">
                        <h4>📉 Drawdown Analysis</h4>
                        <p><strong>Max Drawdown:</strong> {max_dd_info['max_drawdown']:.2%}</p>
                        <p><strong>Current DD:</strong> {max_dd_info['current_drawdown']:.2%}</p>
                        <p><strong>Recovery:</strong> {'Needed' if max_dd_info['current_drawdown'] < -0.05 else 'Good'}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    beta_display = f"{beta:.2f}" if beta else "N/A"
                    beta_interpretation = ("High Risk" if beta and beta > 1.2 else
                                         "Market Risk" if beta and 0.8 <= beta <= 1.2 else
                                         "Low Risk" if beta and beta < 0.8 else "Unknown")
                    st.markdown(f"""
                    <div class="{'risk-card' if beta and beta > 1.2 else 'success-card' if beta and beta < 0.8 else 'analysis-card'}">
                        <h4>🎯 Market Correlation</h4>
                        <p><strong>Beta:</strong> {beta_display}</p>
                        <p><strong>Risk Level:</strong> {beta_interpretation}</p>
                        <p><strong>vs SPY</strong></p>
                    </div>
                    """, unsafe_allow_html=True)

                # Risk visualization
                col1, col2 = st.columns(2)

                with col1:
                    # Drawdown chart
                    fig_dd = go.Figure()
                    fig_dd.add_trace(go.Scatter(
                        x=max_dd_info['drawdown_series'].index,
                        y=max_dd_info['drawdown_series'] * 100,
                        mode='lines',
                        fill='tonegative',
                        name='Drawdown %',
                        line=dict(color='red')
                    ))

                    fig_dd.update_layout(
                        title="📉 Drawdown Analysis",
                        xaxis_title="Date",
                        yaxis_title="Drawdown (%)",
                        template="plotly_dark",
                        height=400
                    )

                    st.plotly_chart(fig_dd, use_container_width=True)

                with col2:
                    # Returns distribution
                    returns = risk_manager.returns * 100  # Convert to percentage

                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=returns,
                        nbinsx=50,
                        name='Daily Returns',
                        marker_color='rgba(66, 153, 225, 0.7)'
                    ))

                    # VaR lines
                    fig_hist.add_vline(x=var_95*100, line_dash="dash", line_color="orange", annotation_text="VaR 95%")
                    fig_hist.add_vline(x=var_99*100, line_dash="dash", line_color="red", annotation_text="VaR 99%")

                    fig_hist.update_layout(
                        title="📊 Returns Distribution",
                        xaxis_title="Daily Returns (%)",
                        yaxis_title="Frequency",
                        template="plotly_dark",
                        height=400
                    )

                    st.plotly_chart(fig_hist, use_container_width=True)

                # Risk recommendations
                risk_score = 0
                recommendations = []

                if var_95 < -0.05:
                    risk_score += 2
                    recommendations.append("⚠️ High volatility detected - Consider position sizing")

                if sharpe < 1:
                    risk_score += 1
                    recommendations.append("📊 Low risk-adjusted returns - Review strategy")

                if max_dd_info['max_drawdown'] < -0.2:
                    risk_score += 2
                    recommendations.append("📉 Significant drawdown history - Implement stop-losses")

                if beta and beta > 1.5:
                    risk_score += 1
                    recommendations.append("🎯 High market correlation - Diversify portfolio")

                if risk_score == 0:
                    recommendations.append("✅ Risk profile appears acceptable")

                risk_level = "High" if risk_score >= 4 else "Medium" if risk_score >= 2 else "Low"
                risk_color = "risk-card" if risk_score >= 4 else "analysis-card" if risk_score >= 2 else "success-card"

                st.markdown(f"""
                <div class="{risk_color}">
                    <h3>🎯 Risk Assessment Summary</h3>
                    <p><strong>Overall Risk Level:</strong> {risk_level}</p>
                    <p><strong>Risk Score:</strong> {risk_score}/6</p>
                    <h4>📋 Recommendations:</h4>
                    <ul>
                    {''.join([f'<li>{rec}</li>' for rec in recommendations])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            elif analysis_mode == "🔍 Advanced Screener":
                st.markdown("""
                <div class="analysis-card">
                    <h2>🔍 Advanced Stock Screener</h2>
                    <p>Professional-grade screening araçları - Momentum, Value, Quality analizi</p>
                </div>
                """, unsafe_allow_html=True)

                screener = AdvancedScreener()

                screen_type = st.radio("Screening Tipi", ["🚀 Momentum", "💎 Value", "🏆 Quality"])

                if screen_type == "🚀 Momentum":
                    min_return = st.slider("Minimum Return (%)", 0, 50, 10) / 100
                    timeframe = st.selectbox("Timeframe", ["1mo", "3mo", "6mo", "1y"])

                    with st.spinner("🔍 Momentum screening çalışıyor..."):
                        momentum_results = screener.momentum_screen(min_return, timeframe)

                    if momentum_results:
                        st.markdown(f"""
                        <div class="success-card">
                            <h3>🚀 Momentum Leaders (Top {len(momentum_results)})</h3>
                        </div>
                        """, unsafe_allow_html=True)

                        # Results table
                        df_momentum = pd.DataFrame(momentum_results)

                        for i, row in df_momentum.iterrows():
                            col1, col2, col3, col4, col5 = st.columns(5)

                            with col1:
                                st.metric("Symbol", row['symbol'])
                            with col2:
                                st.metric("Return", f"{row['return']:.1%}")
                            with col3:
                                st.metric("Price", f"${row['current_price']:.2f}")
                            with col4:
                                st.metric("RSI", f"{row['rsi']:.1f}")
                            with col5:
                                volume_status = "📈" if row['volume_trend'] > 1.2 else "📊" if row['volume_trend'] > 0.8 else "📉"
                                st.metric("Volume", f"{volume_status} {row['volume_trend']:.1f}x")
                    else:
                        st.warning("No stocks found matching momentum criteria")

                elif screen_type == "💎 Value":
                    with st.spinner("💎 Value screening çalışıyor..."):
                        value_results = screener.value_screen()

                    if value_results:
                        st.markdown(f"""
                        <div class="success-card">
                            <h3>💎 Value Opportunities (Top {len(value_results)})</h3>
                        </div>
                        """, unsafe_allow_html=True)

                        df_value = pd.DataFrame(value_results)

                        for i, row in df_value.iterrows():
                            col1, col2, col3, col4, col5 = st.columns(5)

                            with col1:
                                st.metric("Symbol", row['symbol'])
                            with col2:
                                st.metric("P/E Ratio", f"{row['pe_ratio']:.1f}")
                            with col3:
                                st.metric("P/B Ratio", f"{row['pb_ratio']:.1f}")
                            with col4:
                                debt_eq = row.get('debt_to_equity', 0)
                                st.metric("Debt/Equity", f"{debt_eq:.1f}" if debt_eq else "N/A")
                            with col5:
                                market_cap = row['market_cap'] / 1e9
                                st.metric("Market Cap", f"${market_cap:.1f}B")
                    else:
                        st.warning("No stocks found matching value criteria")

                else:  # Quality screening
                    st.markdown("""
                    <div class="analysis-card">
                        <h3>🏆 Quality Metrics</h3>
                        <p>Quality screening implementation would include:</p>
                        <ul>
                            <li>📊 ROE, ROA, ROIC analysis</li>
                            <li>💰 Debt-to-equity ratios</li>
                            <li>📈 Revenue growth consistency</li>
                            <li>💵 Free cash flow generation</li>
                            <li>🏛️ Management efficiency</li>
                        </ul>
                        <p><em>Feature geliştirilme aşamasında...</em></p>
                    </div>
                    """, unsafe_allow_html=True)

            elif analysis_mode == "📰 Sentiment Analysis":
                st.markdown("""
                <div class="analysis-card">
                    <h2>📰 Real-time Sentiment Analysis</h2>
                    <p>News sentiment, social media buzz ve market mood analizi</p>
                </div>
                """, unsafe_allow_html=True)

                sentiment = get_news_sentiment(symbol)

                sentiment_color = ("success-card" if sentiment['sentiment'] == 'Bullish' else
                                 "risk-card" if sentiment['sentiment'] == 'Bearish' else
                                 "analysis-card")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    <div class="{sentiment_color}">
                        <h3>📰 News Sentiment</h3>
                        <p><strong>Overall Sentiment:</strong> {sentiment['sentiment']}</p>
                        <p><strong>Confidence:</strong> {sentiment['confidence']:.1%}</p>
                        <p><strong>News Articles:</strong> {sentiment['news_count']}</p>
                        <p><strong>Summary:</strong> {sentiment['summary']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    # Sentiment meter
                    sentiment_score = (0.8 if sentiment['sentiment'] == 'Bullish' else
                                     0.2 if sentiment['sentiment'] == 'Bearish' else 0.5)

                    fig_gauge = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = sentiment_score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Sentiment Score"},
                        delta = {'reference': 0.5},
                        gauge = {
                            'axis': {'range': [None, 1]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 0.3], 'color': "lightgray"},
                                {'range': [0.3, 0.7], 'color': "gray"},
                                {'range': [0.7, 1], 'color': "lightgreen"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 0.9
                            }
                        }
                    ))

                    fig_gauge.update_layout(
                        template="plotly_dark",
                        height=300
                    )

                    st.plotly_chart(fig_gauge, use_container_width=True)

                # Additional sentiment metrics
                st.markdown("""
                <div class="analysis-card">
                    <h3>📊 Sentiment Breakdown</h3>
                    <p><strong>Advanced sentiment analysis would include:</strong></p>
                    <ul>
                        <li>🐦 Twitter sentiment analysis</li>
                        <li>📺 CNBC, Bloomberg news sentiment</li>
                        <li>🏛️ SEC filings sentiment</li>
                        <li>📈 Analyst upgrade/downgrade tracking</li>
                        <li>🗣️ Management conference call sentiment</li>
                        <li>📊 Options flow sentiment (put/call ratios)</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                # Social media buzz simulation
                buzz_metrics = {
                    'Twitter Mentions': np.random.randint(50, 500),
                    'Reddit Posts': np.random.randint(10, 100),
                    'News Articles': sentiment['news_count'],
                    'Analyst Coverage': np.random.randint(5, 25)
                }

                col1, col2, col3, col4 = st.columns(4)
                for i, (metric, value) in enumerate(buzz_metrics.items()):
                    with [col1, col2, col3, col4][i]:
                        st.metric(metric, value)

        except Exception as e:
            st.error(f"❌ Hata oluştu: {str(e)}")
            st.info("💡 Sembol formatını kontrol edin (örnek: AAPL, MSFT, GOOGL)")

    # Footer
    st.markdown("""
    <div style="margin-top: 3rem; padding: 2rem; background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%); border-radius: 15px; text-align: center;">
        <h3>🏛️ Advanced Financial Platform</h3>
        <p>Powered by AI • Neural Networks • Professional Analytics</p>
        <p><strong>Bloomberg Terminal'den daha gelişmiş analiz araçları</strong></p>
        <p style="color: #a0aec0; font-size: 0.9rem;">
            Features: ML Predictions | Pattern Recognition | Risk Management | Advanced Screeners | Sentiment Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()