"""
Global Stocks & ETFs Analytics Engine
Hisse senetleri ve ETF'ler için analiz motoru
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from app.utils.logger import get_logger


class StocksETFsAnalyzer:
    """Hisse senetleri ve ETF'ler için gelişmiş analiz motoru."""

    def __init__(self):
        self.logger = get_logger("analytics.stocks_etfs")

    def calculate_returns(
        self,
        prices: pd.Series,
        periods: List[str] = ["1W", "1M", "3M", "6M", "1Y"]
    ) -> Dict[str, float]:
        """Farklı periyotlar için getiri hesapla."""
        try:
            if len(prices) < 2:
                return {period: 0.0 for period in periods}

            returns = {}
            current_price = prices.iloc[-1]

            # Periyot mappings
            period_days = {
                "1W": 7,
                "1M": 30,
                "3M": 90,
                "6M": 180,
                "1Y": 252
            }

            for period in periods:
                days = period_days.get(period, 30)

                if len(prices) > days:
                    past_price = prices.iloc[-days-1]
                    period_return = ((current_price - past_price) / past_price) * 100
                    returns[period] = round(period_return, 2)
                else:
                    # Eğer yeterli veri yoksa, mevcut veriyle hesapla
                    past_price = prices.iloc[0]
                    period_return = ((current_price - past_price) / past_price) * 100
                    returns[period] = round(period_return, 2)

            return returns

        except Exception as e:
            self.logger.error("Failed to calculate returns", error=str(e))
            return {period: 0.0 for period in periods}

    def calculate_technical_indicators(
        self,
        ohlcv_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Teknik göstergeleri hesapla."""
        try:
            if ohlcv_data.empty or len(ohlcv_data) < 20:
                return {}

            indicators = {}

            # Moving Averages
            indicators["SMA_20"] = ohlcv_data["close"].rolling(window=20).mean().iloc[-1]
            indicators["SMA_50"] = ohlcv_data["close"].rolling(window=50).mean().iloc[-1] if len(ohlcv_data) >= 50 else None
            indicators["EMA_12"] = ohlcv_data["close"].ewm(span=12).mean().iloc[-1]
            indicators["EMA_26"] = ohlcv_data["close"].ewm(span=26).mean().iloc[-1]

            # RSI
            indicators["RSI"] = self._calculate_rsi(ohlcv_data["close"])

            # MACD
            macd_line, signal_line, histogram = self._calculate_macd(ohlcv_data["close"])
            indicators["MACD"] = {
                "macd_line": macd_line,
                "signal_line": signal_line,
                "histogram": histogram
            }

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(ohlcv_data["close"])
            indicators["Bollinger"] = {
                "upper": bb_upper,
                "middle": bb_middle,
                "lower": bb_lower,
                "position": self._get_bollinger_position(ohlcv_data["close"].iloc[-1], bb_upper, bb_lower)
            }

            # Volatility
            indicators["volatility"] = ohlcv_data["close"].pct_change().std() * np.sqrt(252) * 100

            # Volume indicators
            indicators["avg_volume_20"] = ohlcv_data["volume"].rolling(window=20).mean().iloc[-1]
            indicators["volume_ratio"] = ohlcv_data["volume"].iloc[-1] / indicators["avg_volume_20"] if indicators["avg_volume_20"] > 0 else 1

            # Support and Resistance levels
            indicators["support_resistance"] = self._find_support_resistance(ohlcv_data)

            return indicators

        except Exception as e:
            self.logger.error("Failed to calculate technical indicators", error=str(e))
            return {}

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI hesapla."""
        try:
            if len(prices) < period + 1:
                return 50.0

            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return round(rsi.iloc[-1], 2)

        except Exception:
            return 50.0

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[float, float, float]:
        """MACD hesapla."""
        try:
            if len(prices) < slow_period + signal_period:
                return 0.0, 0.0, 0.0

            ema_fast = prices.ewm(span=fast_period).mean()
            ema_slow = prices.ewm(span=slow_period).mean()

            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal_period).mean()
            histogram = macd_line - signal_line

            return (
                round(macd_line.iloc[-1], 4),
                round(signal_line.iloc[-1], 4),
                round(histogram.iloc[-1], 4)
            )

        except Exception:
            return 0.0, 0.0, 0.0

    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: int = 2
    ) -> Tuple[float, float, float]:
        """Bollinger Bands hesapla."""
        try:
            if len(prices) < period:
                current_price = prices.iloc[-1]
                return current_price * 1.02, current_price, current_price * 0.98

            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()

            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)

            return (
                round(upper_band.iloc[-1], 2),
                round(sma.iloc[-1], 2),
                round(lower_band.iloc[-1], 2)
            )

        except Exception:
            current_price = prices.iloc[-1]
            return current_price * 1.02, current_price, current_price * 0.98

    def _get_bollinger_position(self, current_price: float, upper: float, lower: float) -> str:
        """Bollinger Bands pozisyonu belirle."""
        try:
            if current_price >= upper:
                return "Üst Bantta (Aşırı Alım)"
            elif current_price <= lower:
                return "Alt Bantта (Aşırı Satım)"
            elif current_price > (upper + lower) / 2:
                return "Orta Üstü"
            else:
                return "Orta Altı"
        except:
            return "Bilinmiyor"

    def _find_support_resistance(self, ohlcv_data: pd.DataFrame) -> Dict[str, float]:
        """Destek ve direnç seviyelerini bul."""
        try:
            if len(ohlcv_data) < 20:
                current_price = ohlcv_data["close"].iloc[-1]
                return {
                    "resistance": current_price * 1.05,
                    "support": current_price * 0.95
                }

            # Son 50 günlük veri
            recent_data = ohlcv_data.tail(50)

            # Resistance: Son 50 günün en yüksekleri
            resistance = recent_data["high"].quantile(0.9)

            # Support: Son 50 günün en düşükleri
            support = recent_data["low"].quantile(0.1)

            return {
                "resistance": round(resistance, 2),
                "support": round(support, 2)
            }

        except Exception:
            current_price = ohlcv_data["close"].iloc[-1]
            return {
                "resistance": round(current_price * 1.05, 2),
                "support": round(current_price * 0.95, 2)
            }

    def calculate_stock_correlations(
        self,
        stock_prices: pd.Series,
        market_data: Dict[str, pd.Series],
        window: int = 30
    ) -> Dict[str, float]:
        """Hisse senedinin diğer varlıklarla korelasyonunu hesapla."""
        try:
            correlations = {}

            for asset_name, asset_prices in market_data.items():
                try:
                    # Veri setlerini hizala
                    aligned_data = pd.DataFrame({
                        'stock': stock_prices,
                        'asset': asset_prices
                    }).dropna()

                    if len(aligned_data) >= window:
                        # Rolling correlation
                        rolling_corr = aligned_data['stock'].rolling(window=window).corr(aligned_data['asset'])
                        correlations[asset_name] = round(rolling_corr.iloc[-1], 3)
                    else:
                        # Tüm veri ile korelasyon
                        if len(aligned_data) >= 10:
                            corr = aligned_data['stock'].corr(aligned_data['asset'])
                            correlations[asset_name] = round(corr, 3)

                except Exception as e:
                    self.logger.warning(f"Failed to calculate correlation with {asset_name}", error=str(e))
                    continue

            return correlations

        except Exception as e:
            self.logger.error("Failed to calculate correlations", error=str(e))
            return {}

    def analyze_stock_performance(
        self,
        ohlcv_data: pd.DataFrame,
        symbol: str
    ) -> Dict[str, Any]:
        """Hisse senedi performans analizi."""
        try:
            if ohlcv_data.empty:
                return {"error": "No data available for analysis"}

            prices = ohlcv_data["close"]

            # Getiri hesaplamaları
            returns = self.calculate_returns(prices)

            # Teknik göstergeler
            technical_indicators = self.calculate_technical_indicators(ohlcv_data)

            # Risk metrikleri
            risk_metrics = self._calculate_risk_metrics(prices)

            # Trend analizi
            trend_analysis = self._analyze_trend(prices)

            # Performans skoru
            performance_score = self._calculate_performance_score(returns, risk_metrics)

            analysis_result = {
                "symbol": symbol,
                "current_price": float(prices.iloc[-1]),
                "returns": returns,
                "technical_indicators": technical_indicators,
                "risk_metrics": risk_metrics,
                "trend_analysis": trend_analysis,
                "performance_score": performance_score,
                "analysis_date": datetime.utcnow().isoformat()
            }

            return analysis_result

        except Exception as e:
            self.logger.error(f"Failed to analyze performance for {symbol}", error=str(e))
            return {"error": str(e)}

    def _calculate_risk_metrics(self, prices: pd.Series) -> Dict[str, Any]:
        """Risk metriklerini hesapla."""
        try:
            returns = prices.pct_change().dropna()

            if len(returns) < 10:
                return {}

            risk_metrics = {
                "volatility_annual": round(returns.std() * np.sqrt(252) * 100, 2),
                "max_drawdown": round(self._calculate_max_drawdown(prices), 2),
                "var_95": round(np.percentile(returns, 5) * 100, 2),
                "skewness": round(returns.skew(), 2),
                "kurtosis": round(returns.kurtosis(), 2)
            }

            # Risk seviyesi
            volatility = risk_metrics["volatility_annual"]
            if volatility < 15:
                risk_level = "Düşük"
            elif volatility < 25:
                risk_level = "Orta"
            elif volatility < 40:
                risk_level = "Yüksek"
            else:
                risk_level = "Çok Yüksek"

            risk_metrics["risk_level"] = risk_level

            return risk_metrics

        except Exception as e:
            self.logger.error("Failed to calculate risk metrics", error=str(e))
            return {}

    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Maksimum düşüş hesapla."""
        try:
            cumulative_returns = (1 + prices.pct_change()).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            return drawdown.min() * 100

        except Exception:
            return 0.0

    def _analyze_trend(self, prices: pd.Series) -> Dict[str, Any]:
        """Trend analizi."""
        try:
            if len(prices) < 20:
                return {}

            # Kısa vadeli trend (20 gün)
            short_trend = self._calculate_trend_direction(prices.tail(20))

            # Orta vadeli trend (50 gün)
            medium_trend = self._calculate_trend_direction(prices.tail(50)) if len(prices) >= 50 else short_trend

            # Uzun vadeli trend (200 gün)
            long_trend = self._calculate_trend_direction(prices.tail(200)) if len(prices) >= 200 else medium_trend

            # Genel trend
            current_price = prices.iloc[-1]
            sma_20 = prices.rolling(20).mean().iloc[-1]
            sma_50 = prices.rolling(50).mean().iloc[-1] if len(prices) >= 50 else sma_20

            if current_price > sma_20 > sma_50:
                overall_trend = "Güçlü Yükseliş"
            elif current_price > sma_20:
                overall_trend = "Yükseliş"
            elif current_price < sma_20 < sma_50:
                overall_trend = "Güçlü Düşüş"
            else:
                overall_trend = "Düşüş"

            return {
                "short_term": short_trend,
                "medium_term": medium_trend,
                "long_term": long_trend,
                "overall_trend": overall_trend
            }

        except Exception as e:
            self.logger.error("Failed to analyze trend", error=str(e))
            return {}

    def _calculate_trend_direction(self, prices: pd.Series) -> str:
        """Trend yönünü hesapla."""
        try:
            if len(prices) < 5:
                return "Belirsiz"

            # Linear regression slope
            x = np.arange(len(prices))
            slope = np.polyfit(x, prices.values, 1)[0]

            if slope > prices.iloc[-1] * 0.001:  # %0.1'den fazla
                return "Yükseliş"
            elif slope < -prices.iloc[-1] * 0.001:  # -%0.1'den az
                return "Düşüş"
            else:
                return "Yatay"

        except Exception:
            return "Belirsiz"

    def _calculate_performance_score(
        self,
        returns: Dict[str, float],
        risk_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Performans skoru hesapla (0-100)."""
        try:
            score = 50  # Base score

            # Return'lere göre puan
            if "1M" in returns:
                monthly_return = returns["1M"]
                if monthly_return > 10:
                    score += 20
                elif monthly_return > 5:
                    score += 15
                elif monthly_return > 0:
                    score += 10
                elif monthly_return > -5:
                    score += 0
                else:
                    score -= 15

            # Risk'e göre puan düzeltme
            if "risk_level" in risk_metrics:
                risk_level = risk_metrics["risk_level"]
                if risk_level == "Düşük":
                    score += 10
                elif risk_level == "Orta":
                    score += 5
                elif risk_level == "Yüksek":
                    score -= 5
                else:  # Çok Yüksek
                    score -= 15

            # Score'u 0-100 arasında tut
            score = max(0, min(100, score))

            # Kategorilendirme
            if score >= 80:
                category = "Mükemmel"
            elif score >= 65:
                category = "İyi"
            elif score >= 50:
                category = "Orta"
            elif score >= 35:
                category = "Zayıf"
            else:
                category = "Çok Zayıf"

            return {
                "score": round(score, 1),
                "category": category
            }

        except Exception as e:
            self.logger.error("Failed to calculate performance score", error=str(e))
            return {"score": 50.0, "category": "Bilinmiyor"}

    def compare_stocks(
        self,
        stocks_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Hisse senetlerini karşılaştır."""
        try:
            comparison = {
                "symbols": list(stocks_data.keys()),
                "comparison_metrics": {},
                "rankings": {}
            }

            # Her metrik için karşılaştırma
            metrics_to_compare = ["1M", "3M", "6M", "1Y"]

            for metric in metrics_to_compare:
                metric_values = {}
                for symbol, data in stocks_data.items():
                    returns = data.get("returns", {})
                    if metric in returns:
                        metric_values[symbol] = returns[metric]

                if metric_values:
                    # Sıralama
                    sorted_stocks = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
                    comparison["rankings"][metric] = sorted_stocks
                    comparison["comparison_metrics"][metric] = metric_values

            return comparison

        except Exception as e:
            self.logger.error("Failed to compare stocks", error=str(e))
            return {}

    def generate_investment_signals(
        self,
        technical_indicators: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Yatırım sinyalleri üret."""
        try:
            signals = {
                "overall_signal": "NEUTRAL",
                "confidence": 50,
                "signals": []
            }

            signal_strength = 0
            signal_count = 0

            # RSI sinyali
            if "RSI" in technical_indicators:
                rsi = technical_indicators["RSI"]
                if rsi < 30:
                    signals["signals"].append("RSI aşırı satım bölgesinde - AL sinyali")
                    signal_strength += 2
                elif rsi > 70:
                    signals["signals"].append("RSI aşırı alım bölgesinde - SAT sinyali")
                    signal_strength -= 2
                signal_count += 1

            # MACD sinyali
            if "MACD" in technical_indicators:
                macd_data = technical_indicators["MACD"]
                if macd_data["histogram"] > 0:
                    signals["signals"].append("MACD pozitif - Yükseliş sinyali")
                    signal_strength += 1
                else:
                    signals["signals"].append("MACD negatif - Düşüş sinyali")
                    signal_strength -= 1
                signal_count += 1

            # Bollinger Bands sinyali
            if "Bollinger" in technical_indicators:
                bb_position = technical_indicators["Bollinger"]["position"]
                if "Aşırı Satım" in bb_position:
                    signals["signals"].append("Bollinger alt bantında - AL fırsatı")
                    signal_strength += 1
                elif "Aşırı Alım" in bb_position:
                    signals["signals"].append("Bollinger üst bantında - SAT fırsatı")
                    signal_strength -= 1
                signal_count += 1

            # Trend sinyali
            if "overall_trend" in trend_analysis:
                trend = trend_analysis["overall_trend"]
                if "Güçlü Yükseliş" in trend:
                    signals["signals"].append("Güçlü yükseliş trendi devam ediyor")
                    signal_strength += 3
                elif "Yükseliş" in trend:
                    signals["signals"].append("Yükseliş trendi mevcut")
                    signal_strength += 2
                elif "Güçlü Düşüş" in trend:
                    signals["signals"].append("Güçlü düşüş trendi devam ediyor")
                    signal_strength -= 3
                elif "Düşüş" in trend:
                    signals["signals"].append("Düşüş trendi mevcut")
                    signal_strength -= 2
                signal_count += 1

            # Genel sinyal belirleme
            if signal_count > 0:
                avg_signal = signal_strength / signal_count
                confidence = min(100, abs(avg_signal) * 20 + 50)

                if avg_signal > 1:
                    signals["overall_signal"] = "BUY"
                elif avg_signal < -1:
                    signals["overall_signal"] = "SELL"
                else:
                    signals["overall_signal"] = "HOLD"

                signals["confidence"] = round(confidence, 1)

            return signals

        except Exception as e:
            self.logger.error("Failed to generate investment signals", error=str(e))
            return {"overall_signal": "NEUTRAL", "confidence": 50, "signals": []}