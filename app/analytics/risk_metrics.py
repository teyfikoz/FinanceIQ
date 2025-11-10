import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from app.utils.logger import get_logger
from app.analytics.entropy_metrics import EntropyCalculator


class RiskCalculator:
    """Comprehensive risk metrics calculator for financial assets."""

    def __init__(self):
        self.logger = get_logger("analytics.risk_metrics")
        self.entropy_calc = EntropyCalculator()

    def calculate_volatility(
        self,
        returns: pd.Series,
        window: Optional[int] = None,
        annualize: bool = True
    ) -> float:
        """
        Calculate volatility (standard deviation of returns).

        Args:
            returns: Series of returns
            window: Rolling window (None for full period)
            annualize: Whether to annualize the volatility

        Returns:
            Volatility value
        """
        try:
            if window:
                vol = returns.rolling(window=window).std().iloc[-1]
            else:
                vol = returns.std()

            if annualize:
                vol = vol * np.sqrt(252)  # Assuming 252 trading days per year

            return vol

        except Exception as e:
            self.logger.error("Failed to calculate volatility", error=str(e))
            return np.nan

    def value_at_risk(
        self,
        returns: pd.Series,
        confidence_level: float = 0.05,
        method: str = "historical"
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Series of returns
            confidence_level: Confidence level (e.g., 0.05 for 5%)
            method: Method to use ('historical', 'parametric', 'monte_carlo')

        Returns:
            VaR value (negative number representing loss)
        """
        try:
            if method == "historical":
                var = np.percentile(returns.dropna(), confidence_level * 100)
            elif method == "parametric":
                mean = returns.mean()
                std = returns.std()
                var = stats.norm.ppf(confidence_level, mean, std)
            else:
                # Monte Carlo method (simplified)
                mean = returns.mean()
                std = returns.std()
                simulated_returns = np.random.normal(mean, std, 10000)
                var = np.percentile(simulated_returns, confidence_level * 100)

            return var

        except Exception as e:
            self.logger.error(f"Failed to calculate VaR using {method} method", error=str(e))
            return np.nan

    def conditional_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.05
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.

        Args:
            returns: Series of returns
            confidence_level: Confidence level

        Returns:
            CVaR value
        """
        try:
            var = self.value_at_risk(returns, confidence_level, "historical")
            cvar = returns[returns <= var].mean()
            return cvar

        except Exception as e:
            self.logger.error("Failed to calculate CVaR", error=str(e))
            return np.nan

    def maximum_drawdown(self, prices: pd.Series) -> Dict[str, Any]:
        """
        Calculate maximum drawdown and related metrics.

        Args:
            prices: Series of asset prices

        Returns:
            Dictionary with drawdown metrics
        """
        try:
            # Calculate cumulative returns
            cumulative = (1 + prices.pct_change()).cumprod()

            # Calculate running maximum
            running_max = cumulative.expanding().max()

            # Calculate drawdown
            drawdown = (cumulative - running_max) / running_max

            # Find maximum drawdown
            max_dd = drawdown.min()
            max_dd_date = drawdown.idxmin()

            # Find recovery date (if recovered)
            recovery_date = None
            if max_dd_date is not None:
                after_max_dd = drawdown[drawdown.index > max_dd_date]
                recovery_points = after_max_dd[after_max_dd >= -0.001]  # Within 0.1% of recovery
                if not recovery_points.empty:
                    recovery_date = recovery_points.index[0]

            # Calculate duration
            peak_date = running_max[:max_dd_date].idxmax() if max_dd_date is not None else None
            duration_to_bottom = None
            total_duration = None

            if peak_date and max_dd_date:
                duration_to_bottom = (max_dd_date - peak_date).days
                if recovery_date:
                    total_duration = (recovery_date - peak_date).days

            result = {
                "max_drawdown": max_dd,
                "max_drawdown_date": max_dd_date.isoformat() if max_dd_date else None,
                "peak_date": peak_date.isoformat() if peak_date else None,
                "recovery_date": recovery_date.isoformat() if recovery_date else None,
                "duration_to_bottom_days": duration_to_bottom,
                "total_duration_days": total_duration,
                "current_drawdown": drawdown.iloc[-1],
                "is_recovered": recovery_date is not None
            }

            return result

        except Exception as e:
            self.logger.error("Failed to calculate maximum drawdown", error=str(e))
            return {}

    def sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        try:
            excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
            return excess_returns.mean() / excess_returns.std() * np.sqrt(252)

        except Exception as e:
            self.logger.error("Failed to calculate Sharpe ratio", error=str(e))
            return np.nan

    def sortino_ratio(
        self,
        returns: pd.Series,
        target_return: float = 0.0
    ) -> float:
        """
        Calculate Sortino ratio (downside deviation).

        Args:
            returns: Series of returns
            target_return: Target return (default 0)

        Returns:
            Sortino ratio
        """
        try:
            excess_returns = returns - target_return
            downside_returns = excess_returns[excess_returns < 0]

            if len(downside_returns) == 0:
                return np.inf

            downside_deviation = downside_returns.std()
            return excess_returns.mean() / downside_deviation * np.sqrt(252)

        except Exception as e:
            self.logger.error("Failed to calculate Sortino ratio", error=str(e))
            return np.nan

    def calmar_ratio(
        self,
        returns: pd.Series,
        prices: pd.Series
    ) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown).

        Args:
            returns: Series of returns
            prices: Series of prices

        Returns:
            Calmar ratio
        """
        try:
            annual_return = returns.mean() * 252
            max_dd_info = self.maximum_drawdown(prices)
            max_dd = abs(max_dd_info.get("max_drawdown", 0))

            if max_dd == 0:
                return np.inf

            return annual_return / max_dd

        except Exception as e:
            self.logger.error("Failed to calculate Calmar ratio", error=str(e))
            return np.nan

    def beta_calculation(
        self,
        asset_returns: pd.Series,
        market_returns: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate beta and related metrics.

        Args:
            asset_returns: Asset return series
            market_returns: Market return series

        Returns:
            Dictionary with beta metrics
        """
        try:
            # Align series
            aligned_data = pd.DataFrame({
                'asset': asset_returns,
                'market': market_returns
            }).dropna()

            if len(aligned_data) < 2:
                return {}

            # Calculate beta
            covariance = aligned_data['asset'].cov(aligned_data['market'])
            market_variance = aligned_data['market'].var()
            beta = covariance / market_variance if market_variance != 0 else 0

            # Calculate alpha
            asset_mean = aligned_data['asset'].mean() * 252
            market_mean = aligned_data['market'].mean() * 252
            risk_free_rate = 0.02  # Assume 2% risk-free rate
            alpha = asset_mean - (risk_free_rate + beta * (market_mean - risk_free_rate))

            # Calculate correlation
            correlation = aligned_data['asset'].corr(aligned_data['market'])

            # Calculate R-squared
            r_squared = correlation ** 2

            return {
                "beta": beta,
                "alpha": alpha,
                "correlation": correlation,
                "r_squared": r_squared,
                "tracking_error": (aligned_data['asset'] - beta * aligned_data['market']).std() * np.sqrt(252)
            }

        except Exception as e:
            self.logger.error("Failed to calculate beta", error=str(e))
            return {}

    def skewness_kurtosis(self, returns: pd.Series) -> Dict[str, float]:
        """
        Calculate skewness and kurtosis of returns.

        Args:
            returns: Series of returns

        Returns:
            Dictionary with skewness and kurtosis
        """
        try:
            skew = stats.skew(returns.dropna())
            kurt = stats.kurtosis(returns.dropna())

            return {
                "skewness": skew,
                "kurtosis": kurt,
                "excess_kurtosis": kurt - 3,
                "jarque_bera_stat": stats.jarque_bera(returns.dropna())[0],
                "jarque_bera_pvalue": stats.jarque_bera(returns.dropna())[1]
            }

        except Exception as e:
            self.logger.error("Failed to calculate skewness and kurtosis", error=str(e))
            return {}

    def tail_ratio(self, returns: pd.Series) -> float:
        """
        Calculate tail ratio (95th percentile / 5th percentile).

        Args:
            returns: Series of returns

        Returns:
            Tail ratio
        """
        try:
            p95 = returns.quantile(0.95)
            p5 = returns.quantile(0.05)

            if p5 == 0:
                return np.inf

            return abs(p95 / p5)

        except Exception as e:
            self.logger.error("Failed to calculate tail ratio", error=str(e))
            return np.nan

    def rolling_risk_metrics(
        self,
        prices: pd.Series,
        window: int = 252
    ) -> pd.DataFrame:
        """
        Calculate rolling risk metrics.

        Args:
            prices: Series of prices
            window: Rolling window size

        Returns:
            DataFrame with rolling risk metrics
        """
        try:
            returns = prices.pct_change().dropna()

            if len(returns) < window:
                self.logger.warning(f"Insufficient data for rolling metrics (need {window}, got {len(returns)})")
                return pd.DataFrame()

            rolling_metrics = pd.DataFrame(index=returns.index)

            # Rolling volatility
            rolling_metrics['volatility'] = returns.rolling(window=window).std() * np.sqrt(252)

            # Rolling VaR
            rolling_metrics['var_5'] = returns.rolling(window=window).quantile(0.05)

            # Rolling Sharpe ratio
            rolling_metrics['sharpe_ratio'] = (
                returns.rolling(window=window).mean() / returns.rolling(window=window).std() * np.sqrt(252)
            )

            # Rolling beta (if market data available - placeholder)
            # rolling_metrics['beta'] = ...

            return rolling_metrics.dropna()

        except Exception as e:
            self.logger.error("Failed to calculate rolling risk metrics", error=str(e))
            return pd.DataFrame()

    def comprehensive_risk_report(
        self,
        prices: pd.Series,
        market_prices: Optional[pd.Series] = None,
        risk_free_rate: float = 0.02
    ) -> Dict[str, Any]:
        """
        Generate comprehensive risk analysis report.

        Args:
            prices: Asset price series
            market_prices: Market benchmark prices (optional)
            risk_free_rate: Annual risk-free rate

        Returns:
            Comprehensive risk metrics dictionary
        """
        try:
            returns = prices.pct_change().dropna()

            if len(returns) == 0:
                return {"error": "No valid returns data"}

            report = {
                "asset_name": prices.name if hasattr(prices, 'name') else "Unknown",
                "analysis_period": {
                    "start_date": prices.index.min().isoformat(),
                    "end_date": prices.index.max().isoformat(),
                    "total_observations": len(prices),
                    "trading_days": len(returns)
                },
                "return_statistics": {
                    "total_return": (prices.iloc[-1] / prices.iloc[0] - 1) * 100,
                    "annualized_return": returns.mean() * 252 * 100,
                    "volatility": self.calculate_volatility(returns) * 100,
                    "daily_mean_return": returns.mean() * 100,
                    "daily_std_return": returns.std() * 100
                },
                "risk_metrics": {
                    "var_95": self.value_at_risk(returns, 0.05) * 100,
                    "var_99": self.value_at_risk(returns, 0.01) * 100,
                    "cvar_95": self.conditional_var(returns, 0.05) * 100,
                    "maximum_drawdown": self.maximum_drawdown(prices),
                    "sharpe_ratio": self.sharpe_ratio(returns, risk_free_rate),
                    "sortino_ratio": self.sortino_ratio(returns),
                    "calmar_ratio": self.calmar_ratio(returns, prices)
                },
                "distribution_metrics": self.skewness_kurtosis(returns),
                "tail_metrics": {
                    "tail_ratio": self.tail_ratio(returns),
                    "left_tail_mean": returns.quantile(0.05),
                    "right_tail_mean": returns.quantile(0.95)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            # Add market-relative metrics if market data is provided
            if market_prices is not None:
                market_returns = market_prices.pct_change().dropna()
                beta_metrics = self.beta_calculation(returns, market_returns)
                report["market_metrics"] = beta_metrics

            # Add risk classification
            vol = report["return_statistics"]["volatility"]
            if vol < 10:
                risk_level = "Low"
            elif vol < 20:
                risk_level = "Medium"
            elif vol < 40:
                risk_level = "High"
            else:
                risk_level = "Very High"

            report["risk_classification"] = {
                "risk_level": risk_level,
                "volatility_percentile": self._classify_volatility_percentile(vol)
            }

            # Add entropy-based metrics
            try:
                entropy_metrics = {
                    "shannon_entropy": self.entropy_calc.shannon_entropy(returns),
                    "sample_entropy": self.entropy_calc.sample_entropy(returns),
                    "approximate_entropy": self.entropy_calc.approximate_entropy(returns),
                    "permutation_entropy": self.entropy_calc.permutation_entropy(returns),
                    "spectral_entropy": self.entropy_calc.spectral_entropy(returns),
                    "complexity_score": None,
                    "predictability_score": None,
                    "market_regime": None
                }

                # Calculate derived entropy scores
                shannon = entropy_metrics["shannon_entropy"]
                apen = entropy_metrics["approximate_entropy"]

                if shannon is not None and not np.isnan(shannon):
                    entropy_metrics["complexity_score"] = shannon * 100
                    entropy_metrics["predictability_score"] = (1 - shannon) * 100

                    # Market regime identification
                    if shannon < 0.3 and apen < 0.5:
                        entropy_metrics["market_regime"] = "Strong Trend"
                    elif shannon < 0.5:
                        entropy_metrics["market_regime"] = "Trending"
                    elif shannon < 0.7:
                        entropy_metrics["market_regime"] = "Mixed/Transitional"
                    elif shannon < 0.85:
                        entropy_metrics["market_regime"] = "Choppy/Volatile"
                    else:
                        entropy_metrics["market_regime"] = "Highly Chaotic"

                report["entropy_metrics"] = entropy_metrics

            except Exception as e:
                self.logger.warning(f"Could not calculate entropy metrics: {e}")
                report["entropy_metrics"] = None

            self.logger.info(f"Generated comprehensive risk report for {report['asset_name']}")
            return report

        except Exception as e:
            self.logger.error("Failed to generate comprehensive risk report", error=str(e))
            return {"error": str(e)}

    def _classify_volatility_percentile(self, volatility: float) -> str:
        """Classify volatility into percentiles based on typical market ranges."""
        if volatility < 5:
            return "Very Low (0-10th percentile)"
        elif volatility < 10:
            return "Low (10-25th percentile)"
        elif volatility < 15:
            return "Below Average (25-40th percentile)"
        elif volatility < 20:
            return "Average (40-60th percentile)"
        elif volatility < 30:
            return "Above Average (60-75th percentile)"
        elif volatility < 40:
            return "High (75-90th percentile)"
        else:
            return "Very High (90-100th percentile)"

    def portfolio_risk_metrics(
        self,
        portfolio_weights: Dict[str, float],
        asset_returns: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """
        Calculate portfolio risk metrics.

        Args:
            portfolio_weights: Dictionary of asset weights
            asset_returns: Dictionary of asset return series

        Returns:
            Portfolio risk metrics
        """
        try:
            # Combine returns into DataFrame
            returns_df = pd.DataFrame(asset_returns)
            returns_df = returns_df.dropna()

            if returns_df.empty:
                return {"error": "No valid returns data for portfolio"}

            # Calculate portfolio returns
            weights = pd.Series(portfolio_weights)
            portfolio_returns = (returns_df * weights).sum(axis=1)

            # Calculate portfolio risk metrics
            portfolio_risk = self.comprehensive_risk_report(
                (1 + portfolio_returns).cumprod()
            )

            # Add portfolio-specific metrics
            correlation_matrix = returns_df.corr()
            portfolio_variance = np.dot(weights, np.dot(correlation_matrix, weights))

            portfolio_risk["portfolio_metrics"] = {
                "portfolio_variance": portfolio_variance,
                "diversification_ratio": returns_df.std().dot(weights) / np.sqrt(portfolio_variance),
                "concentration_risk": max(weights.values),
                "effective_number_assets": 1 / (weights ** 2).sum()
            }

            return portfolio_risk

        except Exception as e:
            self.logger.error("Failed to calculate portfolio risk metrics", error=str(e))
            return {"error": str(e)}