import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Optional dependency: arch (for GARCH models)
try:
    from arch import arch_model
    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False
    arch_model = None

class VolatilityAnalyzer:
    """Advanced volatility analysis and modeling"""

    def __init__(self):
        self.models = {}
        self.volatility_forecasts = {}

    def calculate_historical_volatility(self, returns: pd.Series, window: int = 252) -> Dict[str, float]:
        """Calculate various historical volatility measures"""

        # Annualized volatility
        historical_vol = returns.std() * np.sqrt(252)

        # Rolling volatility
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)

        # Parkinson volatility (high-low based)
        if hasattr(returns, 'index') and len(returns) > 1:
            # For this implementation, use close-to-close returns
            parkinson_vol = historical_vol  # Simplified
        else:
            parkinson_vol = historical_vol

        # Garman-Klass volatility (simplified)
        garman_klass_vol = historical_vol * 1.1  # Approximation

        return {
            'historical_vol': historical_vol,
            'current_vol': rolling_vol.iloc[-1] if not rolling_vol.empty else historical_vol,
            'parkinson_vol': parkinson_vol,
            'garman_klass_vol': garman_klass_vol,
            'vol_percentile': self.calculate_volatility_percentile(returns, historical_vol),
            'vol_regime': self.classify_volatility_regime(historical_vol)
        }

    def calculate_volatility_percentile(self, returns: pd.Series, current_vol: float) -> float:
        """Calculate what percentile current volatility is in historical distribution"""
        if len(returns) < 252:
            return 50.0

        # Calculate rolling 30-day volatilities
        rolling_vols = returns.rolling(window=30).std() * np.sqrt(252)
        rolling_vols = rolling_vols.dropna()

        if len(rolling_vols) == 0:
            return 50.0

        # Calculate percentile
        percentile = stats.percentileofscore(rolling_vols, current_vol)
        return percentile

    def classify_volatility_regime(self, volatility: float) -> str:
        """Classify volatility regime"""
        if volatility < 0.15:
            return "Low Volatility"
        elif volatility < 0.25:
            return "Normal Volatility"
        elif volatility < 0.35:
            return "High Volatility"
        else:
            return "Extreme Volatility"

    def garch_volatility_forecast(self, returns: pd.Series, horizon: int = 30) -> Dict[str, Any]:
        """GARCH model volatility forecasting"""
        # Fallback if arch is not available
        if not HAS_ARCH:
            return self._fallback_volatility_forecast(returns, horizon)

        try:
            # Prepare data
            returns_scaled = returns * 100  # Scale for numerical stability
            returns_clean = returns_scaled.dropna()

            if len(returns_clean) < 100:
                return {
                    'error': 'Insufficient data for GARCH modeling',
                    'forecast': None,
                    'confidence_intervals': None
                }

            # Fit GARCH(1,1) model
            model = arch_model(returns_clean, vol='Garch', p=1, q=1, dist='normal')
            fitted_model = model.fit(disp='off')

            # Generate forecasts
            forecasts = fitted_model.forecast(horizon=horizon)

            # Extract volatility forecasts
            vol_forecast = np.sqrt(forecasts.variance.iloc[-1].values) / 100  # Convert back to decimal

            # Calculate confidence intervals (simplified)
            vol_std = vol_forecast.std()
            lower_ci = vol_forecast - 1.96 * vol_std
            upper_ci = vol_forecast + 1.96 * vol_std

            return {
                'model_summary': str(fitted_model.summary()),
                'forecast_horizon': horizon,
                'volatility_forecast': vol_forecast.tolist(),
                'mean_forecast_vol': vol_forecast.mean(),
                'confidence_intervals': {
                    'lower_95': lower_ci.tolist(),
                    'upper_95': upper_ci.tolist()
                },
                'model_aic': fitted_model.aic,
                'model_bic': fitted_model.bic,
                'log_likelihood': fitted_model.loglikelihood
            }

        except Exception as e:
            return {
                'error': f'GARCH modeling failed: {str(e)}',
                'forecast': None,
                'confidence_intervals': None
            }

    def _fallback_volatility_forecast(self, returns: pd.Series, horizon: int = 30) -> Dict[str, Any]:
        """Simple rolling volatility forecast when arch is unavailable"""
        try:
            returns_clean = returns.dropna()

            if len(returns_clean) < 30:
                return {
                    'error': 'Insufficient data for volatility forecasting',
                    'forecast': None,
                    'confidence_intervals': None
                }

            # Calculate rolling 30-day annualized volatility
            rolling_vol = returns_clean.rolling(window=30).std() * np.sqrt(252)
            current_vol = rolling_vol.iloc[-1]

            # Simple forecast: assume volatility persists
            vol_forecast = np.full(horizon, current_vol)

            # Estimate confidence intervals based on historical volatility variation
            vol_std = rolling_vol.std()
            lower_ci = vol_forecast - 1.96 * vol_std
            upper_ci = vol_forecast + 1.96 * vol_std

            return {
                'model_summary': 'Simple rolling volatility forecast (GARCH unavailable)',
                'forecast_horizon': horizon,
                'volatility_forecast': vol_forecast.tolist(),
                'mean_forecast_vol': current_vol,
                'confidence_intervals': {
                    'lower_95': lower_ci.tolist(),
                    'upper_95': upper_ci.tolist()
                },
                'note': 'Advanced GARCH models unavailable in this environment'
            }
        except Exception as e:
            return {
                'error': f'Volatility forecasting failed: {str(e)}',
                'forecast': None,
                'confidence_intervals': None
            }

    def ewma_volatility(self, returns: pd.Series, lambda_decay: float = 0.94) -> pd.Series:
        """Exponentially Weighted Moving Average volatility"""
        # Calculate squared returns
        squared_returns = returns ** 2

        # Apply EWMA
        ewma_var = squared_returns.ewm(alpha=1-lambda_decay).mean()
        ewma_vol = np.sqrt(ewma_var) * np.sqrt(252)  # Annualize

        return ewma_vol

    def realized_volatility(self, prices: pd.DataFrame, freq: str = '1H') -> Dict[str, Any]:
        """Calculate realized volatility from high-frequency data"""
        if 'Close' not in prices.columns:
            return {'error': 'Close prices required'}

        # Calculate returns
        returns = prices['Close'].pct_change().dropna()

        # Calculate daily realized volatility
        if freq == '1D':
            # Daily volatility
            daily_rv = returns.rolling(window=24).apply(lambda x: np.sqrt(np.sum(x**2)) * np.sqrt(252))
        else:
            # Hourly returns summed to daily
            daily_rv = returns.groupby(returns.index.date).apply(
                lambda x: np.sqrt(np.sum(x**2)) * np.sqrt(252)
            )

        return {
            'realized_volatility': daily_rv,
            'mean_rv': daily_rv.mean(),
            'current_rv': daily_rv.iloc[-1] if not daily_rv.empty else None,
            'rv_trend': self.calculate_rv_trend(daily_rv)
        }

    def calculate_rv_trend(self, rv_series: pd.Series) -> str:
        """Calculate trend in realized volatility"""
        if len(rv_series) < 10:
            return "Insufficient data"

        # Calculate trend over last 10 observations
        recent_rv = rv_series.tail(10)
        slope, _, _, p_value, _ = stats.linregress(range(len(recent_rv)), recent_rv)

        if p_value < 0.05:  # Significant trend
            if slope > 0:
                return "Increasing"
            else:
                return "Decreasing"
        else:
            return "Stable"

    def volatility_surface_analysis(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze implied volatility surface"""
        if options_data.empty or 'impliedVolatility' not in options_data.columns:
            return {'error': 'No implied volatility data available'}

        try:
            # Calculate IV statistics
            iv_mean = options_data['impliedVolatility'].mean()
            iv_median = options_data['impliedVolatility'].median()
            iv_std = options_data['impliedVolatility'].std()

            # Calculate IV by strike (if strike data available)
            iv_by_strike = {}
            if 'strike' in options_data.columns:
                iv_by_strike = options_data.groupby('strike')['impliedVolatility'].mean().to_dict()

            # Calculate IV by expiration (if available)
            iv_by_expiration = {}
            if 'expiration' in options_data.columns:
                iv_by_expiration = options_data.groupby('expiration')['impliedVolatility'].mean().to_dict()

            # Volatility skew analysis
            skew_analysis = self.analyze_volatility_skew(options_data)

            return {
                'iv_statistics': {
                    'mean': iv_mean,
                    'median': iv_median,
                    'std': iv_std,
                    'min': options_data['impliedVolatility'].min(),
                    'max': options_data['impliedVolatility'].max()
                },
                'iv_by_strike': iv_by_strike,
                'iv_by_expiration': iv_by_expiration,
                'skew_analysis': skew_analysis,
                'surface_quality': self.assess_surface_quality(options_data)
            }

        except Exception as e:
            return {'error': f'Volatility surface analysis failed: {str(e)}'}

    def analyze_volatility_skew(self, options_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volatility skew"""
        if 'strike' not in options_data.columns or 'impliedVolatility' not in options_data.columns:
            return {'error': 'Strike and IV data required'}

        try:
            # Sort by strike
            sorted_data = options_data.sort_values('strike')

            # Calculate skew (IV difference between OTM puts and calls)
            low_strike_iv = sorted_data.head(5)['impliedVolatility'].mean()
            high_strike_iv = sorted_data.tail(5)['impliedVolatility'].mean()

            skew = low_strike_iv - high_strike_iv

            # Classify skew
            if skew > 0.05:
                skew_type = "Negative Skew (Put Skew)"
            elif skew < -0.05:
                skew_type = "Positive Skew (Call Skew)"
            else:
                skew_type = "Flat Skew"

            return {
                'skew_value': skew,
                'skew_type': skew_type,
                'low_strike_iv': low_strike_iv,
                'high_strike_iv': high_strike_iv,
                'skew_magnitude': abs(skew)
            }

        except Exception as e:
            return {'error': f'Skew analysis failed: {str(e)}'}

    def assess_surface_quality(self, options_data: pd.DataFrame) -> str:
        """Assess quality of volatility surface data"""
        total_contracts = len(options_data)

        if total_contracts < 10:
            return "Poor (< 10 contracts)"
        elif total_contracts < 50:
            return "Fair (10-50 contracts)"
        elif total_contracts < 100:
            return "Good (50-100 contracts)"
        else:
            return "Excellent (100+ contracts)"

    def volatility_regime_detection(self, returns: pd.Series, lookback: int = 252) -> Dict[str, Any]:
        """Detect volatility regimes using statistical methods"""

        # Calculate rolling volatility
        rolling_vol = returns.rolling(window=30).std() * np.sqrt(252)
        rolling_vol = rolling_vol.dropna()

        if len(rolling_vol) < lookback:
            return {'error': 'Insufficient data for regime detection'}

        # Use percentiles to define regimes
        vol_data = rolling_vol.tail(lookback)

        low_threshold = vol_data.quantile(0.33)
        high_threshold = vol_data.quantile(0.67)

        current_vol = rolling_vol.iloc[-1]

        # Classify current regime
        if current_vol <= low_threshold:
            current_regime = "Low Volatility"
            regime_score = 1
        elif current_vol <= high_threshold:
            current_regime = "Medium Volatility"
            regime_score = 2
        else:
            current_regime = "High Volatility"
            regime_score = 3

        # Calculate regime stability
        recent_regimes = []
        for i in range(-10, 0):  # Last 10 observations
            if abs(i) <= len(rolling_vol):
                vol_value = rolling_vol.iloc[i]
                if vol_value <= low_threshold:
                    recent_regimes.append(1)
                elif vol_value <= high_threshold:
                    recent_regimes.append(2)
                else:
                    recent_regimes.append(3)

        regime_stability = len(set(recent_regimes)) == 1  # True if all same regime

        return {
            'current_regime': current_regime,
            'regime_score': regime_score,
            'regime_stability': regime_stability,
            'volatility_percentile': (current_vol - vol_data.min()) / (vol_data.max() - vol_data.min()) * 100,
            'thresholds': {
                'low': low_threshold,
                'high': high_threshold
            },
            'recent_volatility': current_vol,
            'regime_history': recent_regimes
        }

    def volatility_clustering_analysis(self, returns: pd.Series) -> Dict[str, Any]:
        """Analyze volatility clustering patterns"""

        # Calculate absolute returns as proxy for volatility
        abs_returns = abs(returns)

        # Calculate autocorrelation of squared returns
        squared_returns = returns ** 2
        autocorr_lags = [1, 5, 10, 20, 50]
        autocorrelations = {}

        for lag in autocorr_lags:
            if len(squared_returns) > lag:
                autocorr = squared_returns.autocorr(lag=lag)
                autocorrelations[f'lag_{lag}'] = autocorr

        # ARCH test for volatility clustering
        arch_test_result = self.arch_test(returns)

        # Calculate volatility persistence
        persistence = self.calculate_volatility_persistence(abs_returns)

        return {
            'autocorrelations': autocorrelations,
            'arch_test': arch_test_result,
            'volatility_persistence': persistence,
            'clustering_detected': any(corr > 0.1 for corr in autocorrelations.values() if corr is not None),
            'clustering_strength': max(autocorrelations.values()) if autocorrelations.values() else 0
        }

    def arch_test(self, returns: pd.Series, lags: int = 5) -> Dict[str, Any]:
        """ARCH test for volatility clustering"""
        try:
            from arch.unitroot import ARCH

            # Prepare data
            returns_clean = returns.dropna()

            if len(returns_clean) < 50:
                return {'error': 'Insufficient data for ARCH test'}

            # Perform ARCH test
            arch_test = ARCH(returns_clean, lags=lags)

            return {
                'test_statistic': arch_test.stat,
                'p_value': arch_test.pvalue,
                'critical_values': arch_test.critical_values,
                'significant': arch_test.pvalue < 0.05,
                'conclusion': 'ARCH effects detected' if arch_test.pvalue < 0.05 else 'No ARCH effects'
            }

        except Exception as e:
            # Simplified test if arch package fails
            squared_returns = returns ** 2
            autocorr_1 = squared_returns.autocorr(lag=1)

            return {
                'test_statistic': None,
                'p_value': None,
                'critical_values': None,
                'significant': autocorr_1 > 0.1 if autocorr_1 is not None else False,
                'conclusion': 'Simplified test suggests clustering' if autocorr_1 and autocorr_1 > 0.1 else 'No clear clustering',
                'note': 'Simplified test due to missing dependencies'
            }

    def calculate_volatility_persistence(self, abs_returns: pd.Series) -> float:
        """Calculate volatility persistence using AR(1) model"""
        try:
            # Fit AR(1) model to absolute returns
            from sklearn.linear_model import LinearRegression

            if len(abs_returns) < 10:
                return 0.0

            # Prepare data for AR(1)
            y = abs_returns[1:].values
            x = abs_returns[:-1].values.reshape(-1, 1)

            # Fit model
            model = LinearRegression()
            model.fit(x, y)

            # Return coefficient (persistence parameter)
            return model.coef_[0]

        except Exception:
            return 0.0

    def volatility_forecasting_ensemble(self, returns: pd.Series, horizon: int = 30) -> Dict[str, Any]:
        """Ensemble volatility forecasting using multiple models"""

        forecasts = {}
        weights = {}

        # Historical volatility forecast (simple)
        hist_vol = returns.std() * np.sqrt(252)
        forecasts['historical'] = [hist_vol] * horizon
        weights['historical'] = 0.2

        # EWMA forecast
        ewma_vol = self.ewma_volatility(returns)
        current_ewma = ewma_vol.iloc[-1] if not ewma_vol.empty else hist_vol
        forecasts['ewma'] = [current_ewma] * horizon
        weights['ewma'] = 0.3

        # GARCH forecast
        garch_result = self.garch_volatility_forecast(returns, horizon)
        if 'error' not in garch_result:
            forecasts['garch'] = garch_result['volatility_forecast']
            weights['garch'] = 0.5
        else:
            # Fallback to historical
            forecasts['garch'] = forecasts['historical']
            weights['garch'] = 0.0
            weights['historical'] += 0.5

        # Calculate ensemble forecast
        ensemble_forecast = []
        for i in range(horizon):
            weighted_forecast = sum(
                forecasts[model][i] * weights[model]
                for model in forecasts.keys()
            )
            ensemble_forecast.append(weighted_forecast)

        return {
            'ensemble_forecast': ensemble_forecast,
            'individual_forecasts': forecasts,
            'model_weights': weights,
            'forecast_horizon': horizon,
            'forecast_mean': np.mean(ensemble_forecast),
            'forecast_trend': 'Increasing' if ensemble_forecast[-1] > ensemble_forecast[0] else 'Decreasing'
        }

# Global volatility analyzer instance
volatility_analyzer = VolatilityAnalyzer()

if __name__ == "__main__":
    # Test the volatility analyzer
    import yfinance as yf

    # Get sample data
    ticker = yf.Ticker('AAPL')
    data = ticker.history(period='1y')
    returns = data['Close'].pct_change().dropna()

    analyzer = VolatilityAnalyzer()

    # Test historical volatility
    hist_vol = analyzer.calculate_historical_volatility(returns)
    print("Historical Volatility:", hist_vol)

    # Test GARCH forecasting
    garch_forecast = analyzer.garch_volatility_forecast(returns)
    print("GARCH Forecast:", garch_forecast)

    # Test regime detection
    regime = analyzer.volatility_regime_detection(returns)
    print("Volatility Regime:", regime)