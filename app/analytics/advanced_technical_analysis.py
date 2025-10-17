#!/usr/bin/env python3
"""
Gelişmiş Teknik Analiz Modülü
RSI, MACD, Bollinger Bands, Moving Averages, Stochastic ve daha fazlası
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class AdvancedTechnicalAnalyzer:
    """Gelişmiş teknik analiz göstergeleri ve sinyalleri"""

    def __init__(self, symbol: str, period: str = "1y"):
        """
        Args:
            symbol: Hisse senedi sembolü
            period: Veri periyodu (1mo, 3mo, 6mo, 1y, 2y, 5y)
        """
        self.symbol = symbol.upper()
        self.period = period
        self.stock = yf.Ticker(self.symbol)
        self.data = self._fetch_data()

    def _fetch_data(self) -> pd.DataFrame:
        """Fiyat verilerini çek"""
        try:
            df = self.stock.history(period=self.period)
            if df.empty:
                raise ValueError("No data available")
            return df
        except Exception as e:
            raise ValueError(f"Failed to fetch data: {str(e)}")

    def get_complete_technical_analysis(self) -> Dict[str, Any]:
        """Tüm teknik analiz göstergelerini hesapla"""
        if self.data.empty:
            return {"error": "No data available"}

        return {
            "trend_indicators": self.calculate_trend_indicators(),
            "momentum_indicators": self.calculate_momentum_indicators(),
            "volatility_indicators": self.calculate_volatility_indicators(),
            "volume_indicators": self.calculate_volume_indicators(),
            "support_resistance": self.calculate_support_resistance(),
            "chart_patterns": self.detect_chart_patterns(),
            "trading_signals": self.generate_trading_signals(),
            "summary": self.generate_technical_summary()
        }

    def calculate_trend_indicators(self) -> Dict[str, Any]:
        """Trend göstergeleri: MA, EMA, MACD"""
        df = self.data.copy()

        # Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # Exponential Moving Averages
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()

        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        current = df.iloc[-1]

        # Trend analysis
        trend = "neutral"
        if current['Close'] > current['SMA_20'] > current['SMA_50']:
            trend = "strong_bullish"
        elif current['Close'] > current['SMA_20']:
            trend = "bullish"
        elif current['Close'] < current['SMA_20'] < current['SMA_50']:
            trend = "strong_bearish"
        elif current['Close'] < current['SMA_20']:
            trend = "bearish"

        return {
            "current_price": float(current['Close']),
            "sma_20": float(current['SMA_20']),
            "sma_50": float(current['SMA_50']),
            "sma_200": float(current['SMA_200']) if not pd.isna(current['SMA_200']) else None,
            "ema_12": float(current['EMA_12']),
            "ema_26": float(current['EMA_26']),
            "macd": float(current['MACD']),
            "macd_signal": float(current['MACD_Signal']),
            "macd_histogram": float(current['MACD_Histogram']),
            "trend": trend,
            "golden_cross": bool(current['SMA_50'] > current['SMA_200']) if not pd.isna(current['SMA_200']) else None,
            "price_vs_sma20": float((current['Close'] / current['SMA_20'] - 1) * 100),
            "price_vs_sma50": float((current['Close'] / current['SMA_50'] - 1) * 100)
        }

    def calculate_momentum_indicators(self) -> Dict[str, Any]:
        """Momentum göstergeleri: RSI, Stochastic, ROC"""
        df = self.data.copy()

        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Stochastic Oscillator
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        df['Stochastic_K'] = ((df['Close'] - low_14) / (high_14 - low_14)) * 100
        df['Stochastic_D'] = df['Stochastic_K'].rolling(window=3).mean()

        # Rate of Change (ROC)
        df['ROC'] = ((df['Close'] - df['Close'].shift(12)) / df['Close'].shift(12)) * 100

        # Williams %R
        df['Williams_R'] = ((high_14 - df['Close']) / (high_14 - low_14)) * -100

        current = df.iloc[-1]

        # RSI interpretation
        rsi_signal = "neutral"
        if current['RSI'] > 70:
            rsi_signal = "overbought"
        elif current['RSI'] < 30:
            rsi_signal = "oversold"
        elif 50 < current['RSI'] < 70:
            rsi_signal = "bullish"
        elif 30 < current['RSI'] < 50:
            rsi_signal = "bearish"

        # Stochastic interpretation
        stoch_signal = "neutral"
        if current['Stochastic_K'] > 80:
            stoch_signal = "overbought"
        elif current['Stochastic_K'] < 20:
            stoch_signal = "oversold"

        return {
            "rsi": float(current['RSI']),
            "rsi_signal": rsi_signal,
            "stochastic_k": float(current['Stochastic_K']),
            "stochastic_d": float(current['Stochastic_D']),
            "stochastic_signal": stoch_signal,
            "roc": float(current['ROC']),
            "williams_r": float(current['Williams_R']),
            "momentum_score": self._calculate_momentum_score(current)
        }

    def _calculate_momentum_score(self, current: pd.Series) -> float:
        """Momentum skoru hesapla (0-100)"""
        score = 0

        # RSI contribution (0-33)
        if current['RSI'] > 50:
            score += (current['RSI'] - 50) / 50 * 33
        else:
            score += current['RSI'] / 50 * 33

        # Stochastic contribution (0-33)
        score += current['Stochastic_K'] / 100 * 33

        # ROC contribution (0-34)
        roc_normalized = max(min(current['ROC'] / 20, 1), -1)
        score += (roc_normalized + 1) / 2 * 34

        return float(max(0, min(100, score)))

    def calculate_volatility_indicators(self) -> Dict[str, Any]:
        """Volatilite göstergeleri: Bollinger Bands, ATR"""
        df = self.data.copy()

        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100

        # Average True Range (ATR)
        df['TR'] = pd.concat([
            df['High'] - df['Low'],
            abs(df['High'] - df['Close'].shift()),
            abs(df['Low'] - df['Close'].shift())
        ], axis=1).max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()

        # Historical Volatility
        df['Returns'] = df['Close'].pct_change()
        df['HV'] = df['Returns'].rolling(window=20).std() * np.sqrt(252) * 100

        current = df.iloc[-1]

        # BB position
        bb_position = ((current['Close'] - current['BB_Lower']) /
                      (current['BB_Upper'] - current['BB_Lower'])) * 100

        bb_signal = "neutral"
        if bb_position > 95:
            bb_signal = "overbought"
        elif bb_position < 5:
            bb_signal = "oversold"
        elif current['BB_Width'] < df['BB_Width'].quantile(0.2):
            bb_signal = "squeeze"

        return {
            "bb_upper": float(current['BB_Upper']),
            "bb_middle": float(current['BB_Middle']),
            "bb_lower": float(current['BB_Lower']),
            "bb_width": float(current['BB_Width']),
            "bb_position": float(bb_position),
            "bb_signal": bb_signal,
            "atr": float(current['ATR']),
            "atr_percent": float((current['ATR'] / current['Close']) * 100),
            "historical_volatility": float(current['HV']),
            "volatility_rank": self._calculate_volatility_rank(df)
        }

    def _calculate_volatility_rank(self, df: pd.DataFrame) -> float:
        """Volatilite sıralaması (0-100)"""
        current_vol = df['HV'].iloc[-1]
        if pd.isna(current_vol):
            return 50.0

        vol_series = df['HV'].dropna()
        if len(vol_series) == 0:
            return 50.0

        rank = (vol_series < current_vol).sum() / len(vol_series) * 100
        return float(rank)

    def calculate_volume_indicators(self) -> Dict[str, Any]:
        """Hacim göstergeleri: OBV, Volume trends"""
        df = self.data.copy()

        # On-Balance Volume (OBV)
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

        # Volume Moving Average
        df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()

        # Volume Rate of Change
        df['Volume_ROC'] = ((df['Volume'] - df['Volume'].shift(1)) / df['Volume'].shift(1)) * 100

        current = df.iloc[-1]

        # Volume analysis
        volume_signal = "normal"
        volume_ratio = current['Volume'] / current['Volume_MA_20']

        if volume_ratio > 2:
            volume_signal = "very_high"
        elif volume_ratio > 1.5:
            volume_signal = "high"
        elif volume_ratio < 0.5:
            volume_signal = "very_low"
        elif volume_ratio < 0.75:
            volume_signal = "low"

        # OBV trend
        obv_trend = "neutral"
        obv_sma = df['OBV'].rolling(window=20).mean().iloc[-1]
        if current['OBV'] > obv_sma * 1.1:
            obv_trend = "strong_accumulation"
        elif current['OBV'] > obv_sma:
            obv_trend = "accumulation"
        elif current['OBV'] < obv_sma * 0.9:
            obv_trend = "strong_distribution"
        elif current['OBV'] < obv_sma:
            obv_trend = "distribution"

        return {
            "current_volume": int(current['Volume']),
            "volume_ma_20": float(current['Volume_MA_20']),
            "volume_ratio": float(volume_ratio),
            "volume_signal": volume_signal,
            "obv": float(current['OBV']),
            "obv_trend": obv_trend,
            "volume_trend": "increasing" if df['Volume'].iloc[-5:].mean() > df['Volume'].iloc[-20:-5].mean() else "decreasing"
        }

    def calculate_support_resistance(self) -> Dict[str, Any]:
        """Destek ve direnç seviyeleri"""
        df = self.data.copy()
        current_price = df['Close'].iloc[-1]

        # Son 200 günün high/low değerlerini bul
        recent_highs = df['High'].tail(200)
        recent_lows = df['Low'].tail(200)

        # Pivot noktaları bul
        resistance_levels = self._find_resistance_levels(recent_highs, current_price)
        support_levels = self._find_support_levels(recent_lows, current_price)

        return {
            "current_price": float(current_price),
            "immediate_support": float(support_levels[0]) if support_levels else None,
            "immediate_resistance": float(resistance_levels[0]) if resistance_levels else None,
            "support_levels": [float(x) for x in support_levels[:3]],
            "resistance_levels": [float(x) for x in resistance_levels[:3]],
            "distance_to_support": float((current_price / support_levels[0] - 1) * 100) if support_levels else None,
            "distance_to_resistance": float((resistance_levels[0] / current_price - 1) * 100) if resistance_levels else None
        }

    def _find_resistance_levels(self, highs: pd.Series, current_price: float) -> List[float]:
        """Direnç seviyelerini bul"""
        levels = []
        highs_above = highs[highs > current_price]

        if len(highs_above) > 0:
            # En yakın yüksek seviyeler
            for pct in [0.02, 0.05, 0.10]:  # %2, %5, %10 üstü
                level = current_price * (1 + pct)
                nearby = highs_above[(highs_above >= level * 0.98) & (highs_above <= level * 1.02)]
                if len(nearby) > 0:
                    levels.append(nearby.mean())

        levels.sort()
        return levels[:3]

    def _find_support_levels(self, lows: pd.Series, current_price: float) -> List[float]:
        """Destek seviyelerini bul"""
        levels = []
        lows_below = lows[lows < current_price]

        if len(lows_below) > 0:
            # En yakın düşük seviyeler
            for pct in [0.02, 0.05, 0.10]:  # %2, %5, %10 altı
                level = current_price * (1 - pct)
                nearby = lows_below[(lows_below >= level * 0.98) & (lows_below <= level * 1.02)]
                if len(nearby) > 0:
                    levels.append(nearby.mean())

        levels.sort(reverse=True)
        return levels[:3]

    def detect_chart_patterns(self) -> Dict[str, Any]:
        """Grafik paternlerini tespit et"""
        df = self.data.copy()

        patterns = []

        # Bullish patterns
        if self._detect_golden_cross(df):
            patterns.append({"name": "Golden Cross", "type": "bullish", "strength": "strong"})

        if self._detect_bullish_engulfing(df):
            patterns.append({"name": "Bullish Engulfing", "type": "bullish", "strength": "medium"})

        if self._detect_hammer(df):
            patterns.append({"name": "Hammer", "type": "bullish", "strength": "medium"})

        # Bearish patterns
        if self._detect_death_cross(df):
            patterns.append({"name": "Death Cross", "type": "bearish", "strength": "strong"})

        if self._detect_bearish_engulfing(df):
            patterns.append({"name": "Bearish Engulfing", "type": "bearish", "strength": "medium"})

        if self._detect_shooting_star(df):
            patterns.append({"name": "Shooting Star", "type": "bearish", "strength": "medium"})

        return {
            "patterns_detected": len(patterns),
            "patterns": patterns,
            "overall_pattern_signal": self._get_overall_pattern_signal(patterns)
        }

    def _detect_golden_cross(self, df: pd.DataFrame) -> bool:
        """Golden Cross: MA50 > MA200"""
        if len(df) < 200:
            return False

        ma50 = df['Close'].rolling(window=50).mean()
        ma200 = df['Close'].rolling(window=200).mean()

        if ma50.iloc[-2] <= ma200.iloc[-2] and ma50.iloc[-1] > ma200.iloc[-1]:
            return True
        return False

    def _detect_death_cross(self, df: pd.DataFrame) -> bool:
        """Death Cross: MA50 < MA200"""
        if len(df) < 200:
            return False

        ma50 = df['Close'].rolling(window=50).mean()
        ma200 = df['Close'].rolling(window=200).mean()

        if ma50.iloc[-2] >= ma200.iloc[-2] and ma50.iloc[-1] < ma200.iloc[-1]:
            return True
        return False

    def _detect_bullish_engulfing(self, df: pd.DataFrame) -> bool:
        """Bullish Engulfing pattern"""
        if len(df) < 2:
            return False

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        # Önceki mum düşüş, şimdiki yükseliş ve öncekini kapsıyor
        if (prev['Close'] < prev['Open'] and
            curr['Close'] > curr['Open'] and
            curr['Open'] < prev['Close'] and
            curr['Close'] > prev['Open']):
            return True
        return False

    def _detect_bearish_engulfing(self, df: pd.DataFrame) -> bool:
        """Bearish Engulfing pattern"""
        if len(df) < 2:
            return False

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        # Önceki mum yükseliş, şimdiki düşüş ve öncekini kapsıyor
        if (prev['Close'] > prev['Open'] and
            curr['Close'] < curr['Open'] and
            curr['Open'] > prev['Close'] and
            curr['Close'] < prev['Open']):
            return True
        return False

    def _detect_hammer(self, df: pd.DataFrame) -> bool:
        """Hammer pattern (yükseliş sinyali)"""
        if len(df) < 1:
            return False

        curr = df.iloc[-1]
        body = abs(curr['Close'] - curr['Open'])
        lower_shadow = min(curr['Open'], curr['Close']) - curr['Low']
        upper_shadow = curr['High'] - max(curr['Open'], curr['Close'])

        # Alt gölge uzun, üst gölge kısa, gövde küçük
        if lower_shadow > body * 2 and upper_shadow < body * 0.5:
            return True
        return False

    def _detect_shooting_star(self, df: pd.DataFrame) -> bool:
        """Shooting Star pattern (düşüş sinyali)"""
        if len(df) < 1:
            return False

        curr = df.iloc[-1]
        body = abs(curr['Close'] - curr['Open'])
        lower_shadow = min(curr['Open'], curr['Close']) - curr['Low']
        upper_shadow = curr['High'] - max(curr['Open'], curr['Close'])

        # Üst gölge uzun, alt gölge kısa, gövde küçük
        if upper_shadow > body * 2 and lower_shadow < body * 0.5:
            return True
        return False

    def _get_overall_pattern_signal(self, patterns: List[Dict]) -> str:
        """Genel pattern sinyali"""
        if not patterns:
            return "neutral"

        bullish_count = sum(1 for p in patterns if p['type'] == 'bullish')
        bearish_count = sum(1 for p in patterns if p['type'] == 'bearish')

        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        else:
            return "neutral"

    def generate_trading_signals(self) -> Dict[str, Any]:
        """Al/Sat sinyalleri üret"""
        trend = self.calculate_trend_indicators()
        momentum = self.calculate_momentum_indicators()
        volatility = self.calculate_volatility_indicators()
        volume = self.calculate_volume_indicators()

        signals = []
        signal_score = 0

        # Trend signals
        if trend['trend'] in ['strong_bullish', 'bullish']:
            signals.append({"indicator": "Trend", "signal": "BUY", "strength": "medium"})
            signal_score += 2
        elif trend['trend'] in ['strong_bearish', 'bearish']:
            signals.append({"indicator": "Trend", "signal": "SELL", "strength": "medium"})
            signal_score -= 2

        # MACD signals
        if trend['macd'] > trend['macd_signal'] and trend['macd_histogram'] > 0:
            signals.append({"indicator": "MACD", "signal": "BUY", "strength": "medium"})
            signal_score += 1
        elif trend['macd'] < trend['macd_signal'] and trend['macd_histogram'] < 0:
            signals.append({"indicator": "MACD", "signal": "SELL", "strength": "medium"})
            signal_score -= 1

        # RSI signals
        if momentum['rsi_signal'] == 'oversold':
            signals.append({"indicator": "RSI", "signal": "BUY", "strength": "strong"})
            signal_score += 3
        elif momentum['rsi_signal'] == 'overbought':
            signals.append({"indicator": "RSI", "signal": "SELL", "strength": "strong"})
            signal_score -= 3

        # Volume confirmation
        if volume['volume_signal'] in ['high', 'very_high']:
            signals.append({"indicator": "Volume", "signal": "CONFIRMATION", "strength": "medium"})
            signal_score += 1

        # Overall signal
        if signal_score >= 3:
            overall = "STRONG_BUY"
        elif signal_score >= 1:
            overall = "BUY"
        elif signal_score <= -3:
            overall = "STRONG_SELL"
        elif signal_score <= -1:
            overall = "SELL"
        else:
            overall = "HOLD"

        return {
            "overall_signal": overall,
            "signal_score": signal_score,
            "signals": signals,
            "confidence": self._calculate_signal_confidence(signals)
        }

    def _calculate_signal_confidence(self, signals: List[Dict]) -> str:
        """Sinyal güven seviyesi"""
        if len(signals) >= 4:
            return "high"
        elif len(signals) >= 2:
            return "medium"
        else:
            return "low"

    def generate_technical_summary(self) -> Dict[str, Any]:
        """Teknik analiz özeti"""
        trend = self.calculate_trend_indicators()
        momentum = self.calculate_momentum_indicators()
        volatility = self.calculate_volatility_indicators()
        signals = self.generate_trading_signals()

        # Overall rating
        ratings = []
        if trend['trend'] in ['strong_bullish', 'bullish']:
            ratings.append(1)
        elif trend['trend'] in ['strong_bearish', 'bearish']:
            ratings.append(-1)

        if momentum['rsi_signal'] in ['bullish', 'oversold']:
            ratings.append(1)
        elif momentum['rsi_signal'] in ['bearish', 'overbought']:
            ratings.append(-1)

        overall_rating = sum(ratings) / len(ratings) if ratings else 0

        return {
            "current_price": trend['current_price'],
            "trend_status": trend['trend'],
            "momentum_status": momentum['rsi_signal'],
            "volatility_status": volatility['bb_signal'],
            "overall_signal": signals['overall_signal'],
            "overall_rating": float(overall_rating),
            "recommendation": self._get_recommendation(overall_rating, signals['overall_signal'])
        }

    def _get_recommendation(self, rating: float, signal: str) -> str:
        """Yatırım tavsiyesi"""
        if signal == "STRONG_BUY":
            return "Güçlü alım fırsatı. Teknik göstergeler pozitif."
        elif signal == "BUY":
            return "Alım fırsatı. Teknik göstergeler olumlu."
        elif signal == "STRONG_SELL":
            return "Güçlü satış sinyali. Teknik göstergeler negatif."
        elif signal == "SELL":
            return "Satış sinyali. Teknik göstergeler olumsuz."
        else:
            return "Bekle ve gözle. Teknik göstergeler karışık."
