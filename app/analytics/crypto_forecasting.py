"""
Crypto Market Forecasting Engine
==================================
Advanced time series forecasting for cryptocurrency markets with multiple models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from app.utils.logger import get_logger


class CryptoForecaster:
    """
    Multi-model forecasting engine for cryptocurrency market metrics.

    Implements:
    - Linear trend extrapolation
    - Exponential smoothing
    - Moving average projections
    - ARIMA-like simple forecasting
    - Ensemble predictions
    """

    def __init__(self):
        self.logger = get_logger("analytics.crypto_forecasting")

    def forecast_market_cap(
        self,
        historical_data: pd.Series,
        periods: List[int] = [30, 90, 365, 1095, 1825],
        method: str = 'ensemble'
    ) -> Dict[str, Any]:
        """
        Forecast market capitalization for multiple time horizons.

        Args:
            historical_data: Historical market cap series
            periods: Forecast periods in days [1mo, 3mo, 1yr, 3yr, 5yr]
            method: 'linear', 'exponential', 'moving_average', 'ensemble'

        Returns:
            Dictionary with forecasts and confidence intervals
        """
        try:
            if len(historical_data) < 30:
                self.logger.warning("Insufficient historical data for forecasting")
                return {}

            # Clean data
            data = historical_data.dropna()

            forecasts = {}

            for period in periods:
                period_name = self._period_to_name(period)

                if method == 'ensemble':
                    forecast = self._ensemble_forecast(data, period)
                elif method == 'linear':
                    forecast = self._linear_forecast(data, period)
                elif method == 'exponential':
                    forecast = self._exponential_forecast(data, period)
                elif method == 'moving_average':
                    forecast = self._moving_average_forecast(data, period)
                else:
                    forecast = self._ensemble_forecast(data, period)

                forecasts[period_name] = forecast

            # Add metadata
            result = {
                'timestamp': datetime.now(),
                'forecasts': forecasts,
                'current_value': data.iloc[-1],
                'historical_mean': data.mean(),
                'historical_std': data.std(),
                'data_points': len(data),
                'method': method
            }

            self.logger.info(f"Market cap forecast generated for {len(periods)} periods")
            return result

        except Exception as e:
            self.logger.error(f"Failed to forecast market cap: {e}")
            return {}

    def forecast_dominance(
        self,
        historical_dominance: pd.Series,
        periods: List[int] = [30, 90, 365, 1095, 1825],
        method: str = 'ensemble'
    ) -> Dict[str, Any]:
        """
        Forecast Bitcoin/crypto dominance metrics.

        Args:
            historical_dominance: Historical dominance percentage series
            periods: Forecast periods
            method: Forecasting method

        Returns:
            Dictionary with dominance forecasts
        """
        try:
            data = historical_dominance.dropna()

            if len(data) < 30:
                return {}

            forecasts = {}

            for period in periods:
                period_name = self._period_to_name(period)

                if method == 'ensemble':
                    forecast = self._ensemble_forecast(data, period)
                else:
                    forecast = self._linear_forecast(data, period)

                # Clip dominance to realistic range [0, 100]
                forecast['point_forecast'] = np.clip(forecast['point_forecast'], 0, 100)
                forecast['lower_bound'] = np.clip(forecast['lower_bound'], 0, 100)
                forecast['upper_bound'] = np.clip(forecast['upper_bound'], 0, 100)

                forecasts[period_name] = forecast

            result = {
                'timestamp': datetime.now(),
                'forecasts': forecasts,
                'current_dominance': data.iloc[-1],
                'historical_mean': data.mean(),
                'historical_min': data.min(),
                'historical_max': data.max(),
                'trend': self._determine_trend(data),
                'method': method
            }

            self.logger.info(f"Dominance forecast generated for {len(periods)} periods")
            return result

        except Exception as e:
            self.logger.error(f"Failed to forecast dominance: {e}")
            return {}

    def forecast_crypto_price(
        self,
        historical_prices: pd.Series,
        crypto_name: str,
        periods: List[int] = [30, 90, 365, 1095, 1825]
    ) -> Dict[str, Any]:
        """
        Forecast individual cryptocurrency price.

        Args:
            historical_prices: Historical price series
            crypto_name: Name of cryptocurrency
            periods: Forecast periods

        Returns:
            Dictionary with price forecasts
        """
        try:
            data = historical_prices.dropna()

            if len(data) < 30:
                return {}

            # Calculate returns for volatility estimation
            returns = data.pct_change().dropna()
            volatility = returns.std() * np.sqrt(365)  # Annualized

            forecasts = {}

            for period in periods:
                period_name = self._period_to_name(period)

                # Use ensemble method
                forecast = self._ensemble_forecast(data, period)

                # Add volatility-adjusted confidence intervals
                forecast['volatility'] = volatility
                forecast['volatility_adjusted_lower'] = forecast['point_forecast'] * (1 - volatility * np.sqrt(period/365))
                forecast['volatility_adjusted_upper'] = forecast['point_forecast'] * (1 + volatility * np.sqrt(period/365))

                forecasts[period_name] = forecast

            # Technical analysis
            current_price = data.iloc[-1]
            sma_50 = data.tail(50).mean() if len(data) >= 50 else data.mean()
            sma_200 = data.tail(200).mean() if len(data) >= 200 else data.mean()

            result = {
                'timestamp': datetime.now(),
                'crypto_name': crypto_name,
                'forecasts': forecasts,
                'current_price': current_price,
                'sma_50': sma_50,
                'sma_200': sma_200,
                'trend': 'Bullish' if current_price > sma_200 else 'Bearish',
                'volatility': volatility,
                'historical_high': data.max(),
                'historical_low': data.min()
            }

            self.logger.info(f"Price forecast generated for {crypto_name}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to forecast crypto price: {e}")
            return {}

    # ==================== FORECASTING METHODS ====================

    def _linear_forecast(self, data: pd.Series, periods: int) -> Dict[str, float]:
        """Simple linear regression forecast."""
        try:
            # Prepare data
            X = np.arange(len(data)).reshape(-1, 1)
            y = data.values

            # Fit linear model
            model = LinearRegression()
            model.fit(X, y)

            # Forecast
            future_X = np.arange(len(data), len(data) + periods).reshape(-1, 1)
            forecast = model.predict(future_X)[-1]

            # Calculate confidence interval
            residuals = y - model.predict(X)
            std_error = np.std(residuals)

            # 95% confidence interval
            confidence = 1.96 * std_error * np.sqrt(1 + 1/len(data) + (periods**2)/(12*len(data)**2))

            return {
                'point_forecast': forecast,
                'lower_bound': forecast - confidence,
                'upper_bound': forecast + confidence,
                'confidence_level': 0.95,
                'method': 'linear_regression'
            }

        except Exception as e:
            self.logger.error(f"Linear forecast failed: {e}")
            return {}

    def _exponential_forecast(self, data: pd.Series, periods: int) -> Dict[str, float]:
        """Exponential smoothing forecast."""
        try:
            # Simple exponential smoothing
            alpha = 0.3  # Smoothing parameter

            # Calculate smoothed values
            smoothed = [data.iloc[0]]
            for i in range(1, len(data)):
                smoothed.append(alpha * data.iloc[i] + (1 - alpha) * smoothed[-1])

            # Forecast (constant level)
            forecast = smoothed[-1]

            # Estimate uncertainty
            residuals = data.values - np.array(smoothed)
            std_error = np.std(residuals)

            # Confidence interval widens with horizon
            confidence = 1.96 * std_error * np.sqrt(periods / 30)

            return {
                'point_forecast': forecast,
                'lower_bound': forecast - confidence,
                'upper_bound': forecast + confidence,
                'confidence_level': 0.95,
                'method': 'exponential_smoothing'
            }

        except Exception as e:
            self.logger.error(f"Exponential forecast failed: {e}")
            return {}

    def _moving_average_forecast(self, data: pd.Series, periods: int) -> Dict[str, float]:
        """Moving average based forecast."""
        try:
            # Use last 30 days as forecast (mean reversion)
            window = min(30, len(data))
            forecast = data.tail(window).mean()

            # Calculate historical volatility
            returns = data.pct_change().dropna()
            volatility = returns.std()

            # Confidence interval based on volatility
            confidence = 1.96 * volatility * data.iloc[-1] * np.sqrt(periods)

            return {
                'point_forecast': forecast,
                'lower_bound': forecast - confidence,
                'upper_bound': forecast + confidence,
                'confidence_level': 0.95,
                'method': 'moving_average'
            }

        except Exception as e:
            self.logger.error(f"Moving average forecast failed: {e}")
            return {}

    def _ensemble_forecast(self, data: pd.Series, periods: int) -> Dict[str, float]:
        """Ensemble of multiple forecasting methods."""
        try:
            # Get forecasts from different methods
            linear = self._linear_forecast(data, periods)
            exponential = self._exponential_forecast(data, periods)
            ma = self._moving_average_forecast(data, periods)

            # Weighted ensemble (favor linear for longer horizons)
            if periods <= 90:
                weights = [0.4, 0.3, 0.3]  # Equal-ish for short term
            elif periods <= 365:
                weights = [0.5, 0.3, 0.2]  # More linear for medium term
            else:
                weights = [0.6, 0.25, 0.15]  # Heavy linear for long term

            forecasts = [linear, exponential, ma]

            # Weighted average
            point = sum(w * f['point_forecast'] for w, f in zip(weights, forecasts))
            lower = sum(w * f['lower_bound'] for w, f in zip(weights, forecasts))
            upper = sum(w * f['upper_bound'] for w, f in zip(weights, forecasts))

            return {
                'point_forecast': point,
                'lower_bound': lower,
                'upper_bound': upper,
                'confidence_level': 0.95,
                'method': 'ensemble',
                'component_forecasts': {
                    'linear': linear['point_forecast'],
                    'exponential': exponential['point_forecast'],
                    'moving_average': ma['point_forecast']
                }
            }

        except Exception as e:
            self.logger.error(f"Ensemble forecast failed: {e}")
            # Fallback to linear
            return self._linear_forecast(data, periods)

    # ==================== HELPER METHODS ====================

    def _period_to_name(self, days: int) -> str:
        """Convert days to period name."""
        if days <= 30:
            return "1_month"
        elif days <= 90:
            return "3_months"
        elif days <= 365:
            return "1_year"
        elif days <= 1095:
            return "3_years"
        else:
            return "5_years"

    def _determine_trend(self, data: pd.Series) -> str:
        """Determine overall trend direction."""
        if len(data) < 10:
            return "Unknown"

        # Compare recent vs older data
        recent = data.tail(30).mean() if len(data) >= 30 else data.tail(len(data)//2).mean()
        older = data.head(30).mean() if len(data) >= 60 else data.head(len(data)//2).mean()

        pct_change = ((recent - older) / older) * 100 if older != 0 else 0

        if pct_change > 10:
            return "Strong Uptrend"
        elif pct_change > 2:
            return "Uptrend"
        elif pct_change > -2:
            return "Sideways"
        elif pct_change > -10:
            return "Downtrend"
        else:
            return "Strong Downtrend"

    def calculate_forecast_accuracy(
        self,
        actual: pd.Series,
        forecasted: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate forecast accuracy metrics.

        Args:
            actual: Actual values
            forecasted: Forecasted values

        Returns:
            Dictionary with accuracy metrics
        """
        try:
            # Align series
            df = pd.DataFrame({'actual': actual, 'forecast': forecasted}).dropna()

            if df.empty:
                return {}

            # Calculate metrics
            mae = np.mean(np.abs(df['actual'] - df['forecast']))
            mape = np.mean(np.abs((df['actual'] - df['forecast']) / df['actual'])) * 100
            rmse = np.sqrt(np.mean((df['actual'] - df['forecast'])**2))

            # R-squared
            ss_res = np.sum((df['actual'] - df['forecast'])**2)
            ss_tot = np.sum((df['actual'] - df['actual'].mean())**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            return {
                'mae': mae,
                'mape': mape,
                'rmse': rmse,
                'r_squared': r_squared,
                'n_samples': len(df)
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate forecast accuracy: {e}")
            return {}


class CryptoTrendAnalyzer:
    """
    Analyze trends in crypto market metrics.
    """

    def __init__(self):
        self.logger = get_logger("analytics.crypto_trend_analyzer")

    def analyze_market_cap_trend(
        self,
        market_cap_series: pd.Series,
        segments: Optional[Dict[str, pd.Series]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive trend analysis for market cap.

        Args:
            market_cap_series: Total market cap time series
            segments: Optional dict of market cap segments (excl_btc, etc.)

        Returns:
            Dictionary with trend analysis
        """
        try:
            # Calculate trend metrics
            trend_metrics = self._calculate_trend_metrics(market_cap_series)

            # Segment analysis if provided
            segment_trends = {}
            if segments:
                for name, series in segments.items():
                    segment_trends[name] = self._calculate_trend_metrics(series)

            # Volatility analysis
            returns = market_cap_series.pct_change().dropna()
            volatility = {
                'daily_volatility': returns.std(),
                'annual_volatility': returns.std() * np.sqrt(365),
                'downside_volatility': returns[returns < 0].std() if len(returns[returns < 0]) > 0 else 0
            }

            # Growth rates
            growth_rates = self._calculate_growth_rates(market_cap_series)

            result = {
                'timestamp': datetime.now(),
                'current_market_cap': market_cap_series.iloc[-1],
                'trend_metrics': trend_metrics,
                'segment_trends': segment_trends,
                'volatility': volatility,
                'growth_rates': growth_rates,
                'market_cycle': self._identify_market_cycle(market_cap_series)
            }

            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze market cap trend: {e}")
            return {}

    def _calculate_trend_metrics(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate comprehensive trend metrics."""
        try:
            # Linear regression slope
            X = np.arange(len(series)).reshape(-1, 1)
            y = series.values
            model = LinearRegression()
            model.fit(X, y)
            slope = model.coef_[0]

            # Trend direction and strength
            current = series.iloc[-1]
            start = series.iloc[0]
            total_change_pct = ((current - start) / start) * 100 if start != 0 else 0

            # Moving averages
            ma_7 = series.tail(7).mean() if len(series) >= 7 else current
            ma_30 = series.tail(30).mean() if len(series) >= 30 else current
            ma_90 = series.tail(90).mean() if len(series) >= 90 else current

            # Trend classification
            if current > ma_30 > ma_90:
                trend = "Strong Uptrend"
            elif current > ma_30:
                trend = "Uptrend"
            elif current < ma_30 < ma_90:
                trend = "Strong Downtrend"
            elif current < ma_30:
                trend = "Downtrend"
            else:
                trend = "Sideways"

            return {
                'slope': slope,
                'total_change_pct': total_change_pct,
                'trend_direction': trend,
                'ma_7': ma_7,
                'ma_30': ma_30,
                'ma_90': ma_90,
                'current_vs_ma_30': ((current - ma_30) / ma_30) * 100 if ma_30 != 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate trend metrics: {e}")
            return {}

    def _calculate_growth_rates(self, series: pd.Series) -> Dict[str, float]:
        """Calculate various growth rates."""
        try:
            current = series.iloc[-1]

            # Calculate CAGR for different periods
            def cagr(start_val, end_val, periods):
                if start_val <= 0:
                    return 0
                return ((end_val / start_val) ** (365 / periods) - 1) * 100

            growth_rates = {}

            # 1 month
            if len(series) >= 30:
                growth_rates['1_month_growth'] = ((current - series.iloc[-30]) / series.iloc[-30]) * 100

            # 3 months
            if len(series) >= 90:
                growth_rates['3_month_growth'] = ((current - series.iloc[-90]) / series.iloc[-90]) * 100
                growth_rates['3_month_cagr'] = cagr(series.iloc[-90], current, 90)

            # 1 year
            if len(series) >= 365:
                growth_rates['1_year_growth'] = ((current - series.iloc[-365]) / series.iloc[-365]) * 100
                growth_rates['1_year_cagr'] = cagr(series.iloc[-365], current, 365)

            # All time
            growth_rates['total_growth'] = ((current - series.iloc[0]) / series.iloc[0]) * 100
            growth_rates['total_cagr'] = cagr(series.iloc[0], current, len(series))

            return growth_rates

        except Exception as e:
            self.logger.error(f"Failed to calculate growth rates: {e}")
            return {}

    def _identify_market_cycle(self, series: pd.Series) -> str:
        """Identify current market cycle phase."""
        try:
            # Calculate moving averages
            ma_50 = series.tail(50).mean() if len(series) >= 50 else series.mean()
            ma_200 = series.tail(200).mean() if len(series) >= 200 else series.mean()
            current = series.iloc[-1]

            # Recent trend
            recent_30 = series.tail(30)
            recent_slope = np.polyfit(range(len(recent_30)), recent_30.values, 1)[0]

            # Cycle identification
            if current > ma_200 and ma_50 > ma_200 and recent_slope > 0:
                return "Bull Market (Accumulation/Markup)"
            elif current > ma_200 and recent_slope < 0:
                return "Distribution Phase (Topping)"
            elif current < ma_200 and ma_50 < ma_200 and recent_slope < 0:
                return "Bear Market (Markdown)"
            elif current < ma_200 and recent_slope > 0:
                return "Accumulation Phase (Bottoming)"
            else:
                return "Transition/Consolidation"

        except Exception as e:
            self.logger.error(f"Failed to identify market cycle: {e}")
            return "Unknown"


# Convenience functions
def get_crypto_forecaster() -> CryptoForecaster:
    """Get CryptoForecaster instance."""
    return CryptoForecaster()


def get_trend_analyzer() -> CryptoTrendAnalyzer:
    """Get CryptoTrendAnalyzer instance."""
    return CryptoTrendAnalyzer()
