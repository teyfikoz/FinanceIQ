import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
from scipy.signal import find_peaks, argrelextrema
import warnings
warnings.filterwarnings('ignore')

class TrendAnalyzer:
    """Advanced trend analysis and pattern detection"""

    def __init__(self):
        self.trend_indicators = {}
        self.breakout_signals = {}
        self.support_resistance = {}

    def calculate_trend_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate various trend indicators"""
        if 'Close' not in data.columns:
            return {'error': 'Close price data required'}

        close_prices = data['Close']

        # Simple Moving Averages
        sma_20 = close_prices.rolling(window=20).mean()
        sma_50 = close_prices.rolling(window=50).mean()
        sma_200 = close_prices.rolling(window=200).mean()

        # Exponential Moving Averages
        ema_12 = close_prices.ewm(span=12).mean()
        ema_26 = close_prices.ewm(span=26).mean()

        # MACD
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - macd_signal

        # Trend strength
        trend_strength = self.calculate_trend_strength(close_prices)

        # Current trend direction
        current_trend = self.determine_trend_direction(sma_20, sma_50, sma_200)

        # Trend momentum
        momentum = self.calculate_momentum(close_prices)

        return {
            'sma_20': sma_20.iloc[-1] if not sma_20.empty else None,
            'sma_50': sma_50.iloc[-1] if not sma_50.empty else None,
            'sma_200': sma_200.iloc[-1] if not sma_200.empty else None,
            'ema_12': ema_12.iloc[-1] if not ema_12.empty else None,
            'ema_26': ema_26.iloc[-1] if not ema_26.empty else None,
            'macd_line': macd_line.iloc[-1] if not macd_line.empty else None,
            'macd_signal': macd_signal.iloc[-1] if not macd_signal.empty else None,
            'macd_histogram': macd_histogram.iloc[-1] if not macd_histogram.empty else None,
            'trend_strength': trend_strength,
            'current_trend': current_trend,
            'momentum': momentum,
            'price_position': self.analyze_price_position(close_prices, sma_20, sma_50, sma_200)
        }

    def calculate_trend_strength(self, prices: pd.Series, window: int = 20) -> Dict[str, Any]:
        """Calculate trend strength using multiple methods"""
        if len(prices) < window:
            return {'strength': 0, 'direction': 'neutral', 'confidence': 0}

        # Linear regression slope
        recent_prices = prices.tail(window)
        x = np.arange(len(recent_prices))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_prices)

        # Normalize slope
        avg_price = recent_prices.mean()
        normalized_slope = (slope / avg_price) * 100 if avg_price != 0 else 0

        # ADX-like calculation
        adx_strength = self.calculate_adx_simplified(prices, window)

        # Combine metrics
        strength = min(abs(normalized_slope) * 10, 100)
        confidence = abs(r_value) * 100

        direction = 'bullish' if slope > 0 else 'bearish' if slope < 0 else 'neutral'

        return {
            'strength': strength,
            'direction': direction,
            'confidence': confidence,
            'slope': normalized_slope,
            'r_squared': r_value**2,
            'adx_strength': adx_strength
        }

    def calculate_adx_simplified(self, prices: pd.Series, window: int = 14) -> float:
        """Simplified ADX calculation for trend strength"""
        if len(prices) < window + 1:
            return 0

        # Calculate True Range components
        high = prices.rolling(window=2).max()
        low = prices.rolling(window=2).min()
        close_prev = prices.shift(1)

        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)

        true_range = pd.DataFrame([tr1, tr2, tr3]).max()
        atr = true_range.rolling(window=window).mean()

        # Simplified directional movement
        up_move = prices.diff()
        down_move = -prices.diff()

        dm_plus = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        dm_minus = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        di_plus = 100 * pd.Series(dm_plus).rolling(window=window).mean() / atr
        di_minus = 100 * pd.Series(dm_minus).rolling(window=window).mean() / atr

        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
        adx = dx.rolling(window=window).mean()

        return adx.iloc[-1] if not adx.empty and not np.isnan(adx.iloc[-1]) else 0

    def determine_trend_direction(self, sma_20: pd.Series, sma_50: pd.Series, sma_200: pd.Series) -> str:
        """Determine overall trend direction using moving averages"""
        if sma_20.empty or sma_50.empty or sma_200.empty:
            return 'neutral'

        current_20 = sma_20.iloc[-1]
        current_50 = sma_50.iloc[-1]
        current_200 = sma_200.iloc[-1]

        if current_20 > current_50 > current_200:
            return 'strong_bullish'
        elif current_20 > current_50:
            return 'bullish'
        elif current_20 < current_50 < current_200:
            return 'strong_bearish'
        elif current_20 < current_50:
            return 'bearish'
        else:
            return 'neutral'

    def calculate_momentum(self, prices: pd.Series, periods: List[int] = [5, 10, 20]) -> Dict[str, float]:
        """Calculate momentum indicators"""
        momentum = {}

        for period in periods:
            if len(prices) > period:
                momentum[f'momentum_{period}'] = ((prices.iloc[-1] / prices.iloc[-period-1]) - 1) * 100
            else:
                momentum[f'momentum_{period}'] = 0

        # Rate of Change
        if len(prices) > 10:
            roc = ((prices.iloc[-1] / prices.iloc[-11]) - 1) * 100
            momentum['roc_10'] = roc

        return momentum

    def analyze_price_position(self, prices: pd.Series, sma_20: pd.Series,
                             sma_50: pd.Series, sma_200: pd.Series) -> Dict[str, Any]:
        """Analyze current price position relative to moving averages"""
        if prices.empty:
            return {}

        current_price = prices.iloc[-1]

        position = {
            'current_price': current_price,
            'vs_sma_20': ((current_price / sma_20.iloc[-1]) - 1) * 100 if not sma_20.empty else 0,
            'vs_sma_50': ((current_price / sma_50.iloc[-1]) - 1) * 100 if not sma_50.empty else 0,
            'vs_sma_200': ((current_price / sma_200.iloc[-1]) - 1) * 100 if not sma_200.empty else 0,
        }

        # Determine position strength
        above_all = (position['vs_sma_20'] > 0 and position['vs_sma_50'] > 0 and position['vs_sma_200'] > 0)
        below_all = (position['vs_sma_20'] < 0 and position['vs_sma_50'] < 0 and position['vs_sma_200'] < 0)

        if above_all:
            position['strength'] = 'strong_bullish'
        elif below_all:
            position['strength'] = 'strong_bearish'
        else:
            position['strength'] = 'mixed'

        return position

    def detect_support_resistance(self, data: pd.DataFrame, window: int = 20) -> Dict[str, Any]:
        """Detect support and resistance levels"""
        if 'High' not in data.columns or 'Low' not in data.columns:
            return {'error': 'High and Low price data required'}

        highs = data['High']
        lows = data['Low']

        # Find peaks and troughs
        peak_indices = argrelextrema(highs.values, np.greater, order=window//2)[0]
        trough_indices = argrelextrema(lows.values, np.less, order=window//2)[0]

        # Get recent peaks and troughs
        recent_peaks = highs.iloc[peak_indices[-min(5, len(peak_indices)):]] if len(peak_indices) > 0 else pd.Series()
        recent_troughs = lows.iloc[trough_indices[-min(5, len(trough_indices)):]] if len(trough_indices) > 0 else pd.Series()

        # Calculate levels
        resistance_levels = recent_peaks.tolist() if not recent_peaks.empty else []
        support_levels = recent_troughs.tolist() if not recent_troughs.empty else []

        # Find strongest levels (most touched)
        current_price = data['Close'].iloc[-1]

        return {
            'resistance_levels': resistance_levels,
            'support_levels': support_levels,
            'nearest_resistance': min(resistance_levels, key=lambda x: abs(x - current_price)) if resistance_levels else None,
            'nearest_support': min(support_levels, key=lambda x: abs(x - current_price)) if support_levels else None,
            'resistance_strength': self.calculate_level_strength(resistance_levels, highs),
            'support_strength': self.calculate_level_strength(support_levels, lows)
        }

    def calculate_level_strength(self, levels: List[float], price_series: pd.Series) -> Dict[str, int]:
        """Calculate strength of support/resistance levels"""
        strength = {}
        tolerance = price_series.std() * 0.02  # 2% of standard deviation

        for level in levels:
            touches = sum(1 for price in price_series if abs(price - level) <= tolerance)
            strength[level] = touches

        return strength

    def detect_breakouts(self, data: pd.DataFrame, window: int = 20, threshold: float = 0.02) -> Dict[str, Any]:
        """Detect price breakouts from support/resistance levels"""
        if 'Close' not in data.columns or 'Volume' not in data.columns:
            return {'error': 'Close price and Volume data required'}

        # Get support/resistance levels
        sr_levels = self.detect_support_resistance(data, window)

        if 'error' in sr_levels:
            return sr_levels

        close_prices = data['Close']
        volume = data['Volume']
        current_price = close_prices.iloc[-1]
        current_volume = volume.iloc[-1]
        avg_volume = volume.rolling(window=window).mean().iloc[-1]

        breakouts = []

        # Check resistance breakouts
        for resistance in sr_levels['resistance_levels']:
            if current_price > resistance * (1 + threshold):
                breakouts.append({
                    'type': 'resistance_breakout',
                    'level': resistance,
                    'current_price': current_price,
                    'strength': 'strong' if current_volume > avg_volume * 1.5 else 'weak',
                    'volume_confirmation': current_volume > avg_volume
                })

        # Check support breakdowns
        for support in sr_levels['support_levels']:
            if current_price < support * (1 - threshold):
                breakouts.append({
                    'type': 'support_breakdown',
                    'level': support,
                    'current_price': current_price,
                    'strength': 'strong' if current_volume > avg_volume * 1.5 else 'weak',
                    'volume_confirmation': current_volume > avg_volume
                })

        return {
            'breakouts': breakouts,
            'breakout_count': len(breakouts),
            'volume_analysis': {
                'current_volume': current_volume,
                'average_volume': avg_volume,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0
            }
        }

    def analyze_trend_channels(self, data: pd.DataFrame, window: int = 50) -> Dict[str, Any]:
        """Analyze trend channels and channel breakouts"""
        if 'High' not in data.columns or 'Low' not in data.columns or 'Close' not in data.columns:
            return {'error': 'OHLC data required'}

        if len(data) < window:
            return {'error': 'Insufficient data for channel analysis'}

        highs = data['High'].tail(window)
        lows = data['Low'].tail(window)
        closes = data['Close'].tail(window)

        # Linear regression on highs and lows
        x = np.arange(len(highs))

        # Upper channel line (resistance)
        slope_high, intercept_high, r_high, _, _ = stats.linregress(x, highs)
        upper_channel = slope_high * x + intercept_high

        # Lower channel line (support)
        slope_low, intercept_low, r_low, _, _ = stats.linregress(x, lows)
        lower_channel = slope_low * x + intercept_low

        # Current position in channel
        current_price = closes.iloc[-1]
        current_upper = upper_channel[-1]
        current_lower = lower_channel[-1]

        channel_width = current_upper - current_lower
        price_position = (current_price - current_lower) / channel_width if channel_width > 0 else 0.5

        # Channel direction
        channel_direction = 'ascending' if slope_high > 0 and slope_low > 0 else \
                           'descending' if slope_high < 0 and slope_low < 0 else 'sideways'

        return {
            'upper_channel': current_upper,
            'lower_channel': current_lower,
            'channel_width': channel_width,
            'price_position_pct': price_position * 100,
            'channel_direction': channel_direction,
            'upper_slope': slope_high,
            'lower_slope': slope_low,
            'channel_strength': (abs(r_high) + abs(r_low)) / 2,
            'breakout_probability': self.calculate_breakout_probability(price_position, channel_direction)
        }

    def calculate_breakout_probability(self, position: float, direction: str) -> Dict[str, float]:
        """Calculate probability of breakout based on position in channel"""
        if position > 0.8:
            upward_prob = 70 if direction == 'ascending' else 50
            downward_prob = 30
        elif position < 0.2:
            upward_prob = 30
            downward_prob = 70 if direction == 'descending' else 50
        else:
            upward_prob = 50
            downward_prob = 50

        return {
            'upward_breakout': upward_prob,
            'downward_breakout': downward_prob
        }

    def fibonacci_retracement(self, data: pd.DataFrame, trend_period: int = 50) -> Dict[str, Any]:
        """Calculate Fibonacci retracement levels"""
        if 'High' not in data.columns or 'Low' not in data.columns:
            return {'error': 'High and Low price data required'}

        if len(data) < trend_period:
            return {'error': 'Insufficient data'}

        recent_data = data.tail(trend_period)
        high_point = recent_data['High'].max()
        low_point = recent_data['Low'].min()

        # Fibonacci levels
        fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]

        # Calculate retracement levels
        diff = high_point - low_point
        retracements = {}

        for level in fib_levels:
            retracements[f'fib_{level}'] = high_point - (diff * level)

        # Current price analysis
        current_price = data['Close'].iloc[-1]

        # Find nearest levels
        distances = {level: abs(price - current_price) for level, price in retracements.items()}
        nearest_level = min(distances.keys(), key=lambda k: distances[k])

        return {
            'high_point': high_point,
            'low_point': low_point,
            'retracement_levels': retracements,
            'current_price': current_price,
            'nearest_level': nearest_level,
            'nearest_price': retracements[nearest_level],
            'trend_direction': 'bullish' if current_price > (high_point + low_point) / 2 else 'bearish'
        }

    def pattern_recognition(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Basic pattern recognition"""
        if len(data) < 20:
            return {'error': 'Insufficient data for pattern recognition'}

        patterns = []

        # Double top/bottom detection
        double_patterns = self.detect_double_patterns(data)
        if double_patterns:
            patterns.extend(double_patterns)

        # Head and shoulders detection
        hs_patterns = self.detect_head_shoulders(data)
        if hs_patterns:
            patterns.extend(hs_patterns)

        # Triangle patterns
        triangle_patterns = self.detect_triangles(data)
        if triangle_patterns:
            patterns.extend(triangle_patterns)

        return {
            'patterns_detected': len(patterns),
            'patterns': patterns,
            'most_recent': patterns[-1] if patterns else None
        }

    def detect_double_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect double top and double bottom patterns"""
        patterns = []

        if len(data) < 30:
            return patterns

        highs = data['High']
        lows = data['Low']

        # Find peaks and troughs
        peak_indices = argrelextrema(highs.values, np.greater, order=5)[0]
        trough_indices = argrelextrema(lows.values, np.less, order=5)[0]

        # Check for double tops
        if len(peak_indices) >= 2:
            for i in range(len(peak_indices) - 1):
                peak1 = highs.iloc[peak_indices[i]]
                peak2 = highs.iloc[peak_indices[i + 1]]

                if abs(peak1 - peak2) / peak1 < 0.03:  # Within 3%
                    patterns.append({
                        'type': 'double_top',
                        'strength': 'strong' if abs(peak1 - peak2) / peak1 < 0.01 else 'moderate',
                        'level': (peak1 + peak2) / 2,
                        'signal': 'bearish'
                    })

        # Check for double bottoms
        if len(trough_indices) >= 2:
            for i in range(len(trough_indices) - 1):
                trough1 = lows.iloc[trough_indices[i]]
                trough2 = lows.iloc[trough_indices[i + 1]]

                if abs(trough1 - trough2) / trough1 < 0.03:  # Within 3%
                    patterns.append({
                        'type': 'double_bottom',
                        'strength': 'strong' if abs(trough1 - trough2) / trough1 < 0.01 else 'moderate',
                        'level': (trough1 + trough2) / 2,
                        'signal': 'bullish'
                    })

        return patterns

    def detect_head_shoulders(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect head and shoulders patterns"""
        patterns = []

        if len(data) < 50:
            return patterns

        highs = data['High']
        peak_indices = argrelextrema(highs.values, np.greater, order=5)[0]

        if len(peak_indices) >= 3:
            for i in range(len(peak_indices) - 2):
                left_shoulder = highs.iloc[peak_indices[i]]
                head = highs.iloc[peak_indices[i + 1]]
                right_shoulder = highs.iloc[peak_indices[i + 2]]

                # Check for head and shoulders pattern
                if (head > left_shoulder and head > right_shoulder and
                    abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):

                    patterns.append({
                        'type': 'head_and_shoulders',
                        'strength': 'strong',
                        'left_shoulder': left_shoulder,
                        'head': head,
                        'right_shoulder': right_shoulder,
                        'signal': 'bearish'
                    })

        return patterns

    def detect_triangles(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect triangle patterns"""
        patterns = []

        if len(data) < 30:
            return patterns

        # Simplified triangle detection based on converging trend lines
        highs = data['High'].tail(20)
        lows = data['Low'].tail(20)

        # Check if highs are decreasing and lows are increasing (symmetrical triangle)
        high_trend = np.polyfit(range(len(highs)), highs, 1)[0]
        low_trend = np.polyfit(range(len(lows)), lows, 1)[0]

        if high_trend < -0.01 and low_trend > 0.01:
            patterns.append({
                'type': 'symmetrical_triangle',
                'strength': 'moderate',
                'signal': 'neutral_breakout_pending'
            })
        elif high_trend < -0.01 and abs(low_trend) < 0.01:
            patterns.append({
                'type': 'descending_triangle',
                'strength': 'moderate',
                'signal': 'bearish'
            })
        elif abs(high_trend) < 0.01 and low_trend > 0.01:
            patterns.append({
                'type': 'ascending_triangle',
                'strength': 'moderate',
                'signal': 'bullish'
            })

        return patterns

    def comprehensive_trend_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive trend analysis"""
        analysis = {}

        # Basic trend indicators
        analysis['trend_indicators'] = self.calculate_trend_indicators(data)

        # Support and resistance
        analysis['support_resistance'] = self.detect_support_resistance(data)

        # Breakout analysis
        analysis['breakouts'] = self.detect_breakouts(data)

        # Trend channels
        analysis['channels'] = self.analyze_trend_channels(data)

        # Fibonacci levels
        analysis['fibonacci'] = self.fibonacci_retracement(data)

        # Pattern recognition
        analysis['patterns'] = self.pattern_recognition(data)

        # Overall trend assessment
        analysis['overall_assessment'] = self.generate_overall_assessment(analysis)

        return analysis

    def generate_overall_assessment(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall trend assessment"""
        bullish_signals = 0
        bearish_signals = 0
        neutral_signals = 0

        # Trend indicators assessment
        if 'trend_indicators' in analysis and 'current_trend' in analysis['trend_indicators']:
            trend = analysis['trend_indicators']['current_trend']
            if 'bullish' in trend:
                bullish_signals += 2 if 'strong' in trend else 1
            elif 'bearish' in trend:
                bearish_signals += 2 if 'strong' in trend else 1
            else:
                neutral_signals += 1

        # Breakout assessment
        if 'breakouts' in analysis and analysis['breakouts'].get('breakouts'):
            for breakout in analysis['breakouts']['breakouts']:
                if breakout['type'] == 'resistance_breakout':
                    bullish_signals += 1
                else:
                    bearish_signals += 1

        # Pattern assessment
        if 'patterns' in analysis and analysis['patterns'].get('patterns'):
            for pattern in analysis['patterns']['patterns']:
                if pattern.get('signal') == 'bullish':
                    bullish_signals += 1
                elif pattern.get('signal') == 'bearish':
                    bearish_signals += 1
                else:
                    neutral_signals += 1

        # Final assessment
        total_signals = bullish_signals + bearish_signals + neutral_signals

        if total_signals == 0:
            overall_trend = 'neutral'
            confidence = 0
        else:
            if bullish_signals > bearish_signals:
                overall_trend = 'bullish'
                confidence = (bullish_signals / total_signals) * 100
            elif bearish_signals > bullish_signals:
                overall_trend = 'bearish'
                confidence = (bearish_signals / total_signals) * 100
            else:
                overall_trend = 'neutral'
                confidence = 50

        return {
            'overall_trend': overall_trend,
            'confidence': confidence,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'neutral_signals': neutral_signals,
            'recommendation': self.generate_recommendation(overall_trend, confidence)
        }

    def generate_recommendation(self, trend: str, confidence: float) -> str:
        """Generate trading recommendation based on trend analysis"""
        if confidence < 30:
            return "Hold - Insufficient conviction in trend direction"
        elif trend == 'bullish' and confidence > 70:
            return "Strong Buy - Multiple bullish signals confirmed"
        elif trend == 'bullish' and confidence > 50:
            return "Buy - Bullish trend emerging"
        elif trend == 'bearish' and confidence > 70:
            return "Strong Sell - Multiple bearish signals confirmed"
        elif trend == 'bearish' and confidence > 50:
            return "Sell - Bearish trend emerging"
        else:
            return "Hold - Mixed signals, wait for clearer direction"

# Global trend analyzer instance
trend_analyzer = TrendAnalyzer()

if __name__ == "__main__":
    # Test the trend analyzer
    import yfinance as yf

    # Get sample data
    ticker = yf.Ticker('AAPL')
    data = ticker.history(period='6mo')

    analyzer = TrendAnalyzer()

    # Test comprehensive analysis
    analysis = analyzer.comprehensive_trend_analysis(data)
    print("=== COMPREHENSIVE TREND ANALYSIS ===")

    for key, value in analysis.items():
        print(f"\n{key.upper()}:")
        print(value)