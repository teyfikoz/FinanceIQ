import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from app.utils.logger import get_logger


class CorrelationAnalyzer:
    """Advanced correlation analysis for financial assets."""

    def __init__(self):
        self.logger = get_logger("analytics.correlations")

    def calculate_correlation_matrix(
        self,
        price_data: pd.DataFrame,
        method: str = "pearson",
        window: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for multiple assets.

        Args:
            price_data: DataFrame with columns as assets and timestamps as index
            method: Correlation method ('pearson', 'spearman', 'kendall')
            window: Rolling window size (None for full period)

        Returns:
            Correlation matrix as DataFrame
        """
        try:
            if window:
                # Rolling correlation
                correlations = price_data.rolling(window=window).corr(method=method)
                # Take the latest window
                latest_date = correlations.index.get_level_values(0)[-1]
                corr_matrix = correlations.loc[latest_date]
            else:
                # Full period correlation
                corr_matrix = price_data.corr(method=method)

            self.logger.info(f"Calculated {method} correlation matrix for {len(corr_matrix)} assets")
            return corr_matrix

        except Exception as e:
            self.logger.error(f"Failed to calculate correlation matrix", error=str(e))
            return pd.DataFrame()

    def rolling_correlation(
        self,
        asset1_prices: pd.Series,
        asset2_prices: pd.Series,
        window: int = 30
    ) -> pd.Series:
        """Calculate rolling correlation between two assets."""
        try:
            # Align series by index
            aligned_data = pd.DataFrame({
                'asset1': asset1_prices,
                'asset2': asset2_prices
            }).dropna()

            if len(aligned_data) < window:
                self.logger.warning(f"Insufficient data for rolling correlation (need {window}, got {len(aligned_data)})")
                return pd.Series(dtype=float)

            rolling_corr = aligned_data['asset1'].rolling(window=window).corr(aligned_data['asset2'])

            self.logger.info(f"Calculated rolling correlation for {len(rolling_corr)} periods")
            return rolling_corr

        except Exception as e:
            self.logger.error("Failed to calculate rolling correlation", error=str(e))
            return pd.Series(dtype=float)

    def correlation_breakdown_detection(
        self,
        correlations: pd.Series,
        threshold: float = 0.2,
        lookback_periods: int = 7
    ) -> Dict[str, Any]:
        """
        Detect correlation breakdowns (significant changes in correlation).

        Args:
            correlations: Time series of correlation values
            threshold: Minimum change to consider a breakdown
            lookback_periods: Number of periods to look back for comparison

        Returns:
            Dictionary with breakdown information
        """
        try:
            if len(correlations) < lookback_periods + 1:
                return {"breakdown_detected": False, "reason": "Insufficient data"}

            current_corr = correlations.iloc[-1]
            historical_corr = correlations.iloc[-(lookback_periods + 1):-1].mean()

            change = abs(current_corr - historical_corr)
            breakdown_detected = change >= threshold

            result = {
                "breakdown_detected": breakdown_detected,
                "current_correlation": current_corr,
                "historical_average": historical_corr,
                "absolute_change": change,
                "relative_change": change / abs(historical_corr) if historical_corr != 0 else 0,
                "threshold": threshold,
                "direction": "increase" if current_corr > historical_corr else "decrease",
                "significance": "high" if change >= threshold * 1.5 else "medium" if change >= threshold else "low"
            }

            if breakdown_detected:
                self.logger.warning(
                    f"Correlation breakdown detected: {change:.3f} change",
                    current=current_corr,
                    historical=historical_corr
                )

            return result

        except Exception as e:
            self.logger.error("Failed to detect correlation breakdown", error=str(e))
            return {"breakdown_detected": False, "error": str(e)}

    def correlation_regime_analysis(
        self,
        correlations: pd.Series,
        regime_window: int = 60
    ) -> Dict[str, Any]:
        """
        Analyze correlation regimes (high vs low correlation periods).

        Args:
            correlations: Time series of correlation values
            regime_window: Window for regime classification

        Returns:
            Dictionary with regime analysis
        """
        try:
            if len(correlations) < regime_window:
                return {"error": "Insufficient data for regime analysis"}

            # Calculate rolling statistics
            rolling_mean = correlations.rolling(window=regime_window).mean()
            rolling_std = correlations.rolling(window=regime_window).std()

            # Define regimes based on standard deviations from mean
            current_corr = correlations.iloc[-1]
            current_mean = rolling_mean.iloc[-1]
            current_std = rolling_std.iloc[-1]

            if pd.isna(current_mean) or pd.isna(current_std):
                return {"error": "Cannot calculate regime - insufficient historical data"}

            # Classify current regime
            z_score = (current_corr - current_mean) / current_std if current_std > 0 else 0

            if z_score > 1:
                regime = "high_correlation"
            elif z_score < -1:
                regime = "low_correlation"
            else:
                regime = "normal_correlation"

            # Calculate regime persistence
            regime_changes = 0
            regime_duration = 1

            for i in range(2, min(30, len(correlations))):  # Look back up to 30 periods
                past_corr = correlations.iloc[-i]
                past_mean = rolling_mean.iloc[-i]
                past_std = rolling_std.iloc[-i]

                if pd.isna(past_mean) or pd.isna(past_std):
                    break

                past_z_score = (past_corr - past_mean) / past_std if past_std > 0 else 0

                if past_z_score > 1:
                    past_regime = "high_correlation"
                elif past_z_score < -1:
                    past_regime = "low_correlation"
                else:
                    past_regime = "normal_correlation"

                if past_regime == regime:
                    regime_duration += 1
                else:
                    break

            result = {
                "current_regime": regime,
                "regime_duration": regime_duration,
                "z_score": z_score,
                "current_correlation": current_corr,
                "regime_mean": current_mean,
                "regime_std": current_std,
                "regime_confidence": min(abs(z_score), 3) / 3  # Normalize to 0-1
            }

            return result

        except Exception as e:
            self.logger.error("Failed to analyze correlation regimes", error=str(e))
            return {"error": str(e)}

    def correlation_significance_test(
        self,
        asset1_prices: pd.Series,
        asset2_prices: pd.Series,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Test statistical significance of correlation.

        Args:
            asset1_prices: Price series for first asset
            asset2_prices: Price series for second asset
            alpha: Significance level

        Returns:
            Dictionary with test results
        """
        try:
            # Align series and remove NaN values
            aligned_data = pd.DataFrame({
                'asset1': asset1_prices,
                'asset2': asset2_prices
            }).dropna()

            if len(aligned_data) < 3:
                return {"error": "Insufficient data for significance test"}

            # Calculate correlation and p-value
            correlation, p_value = stats.pearsonr(aligned_data['asset1'], aligned_data['asset2'])

            # Calculate confidence interval
            n = len(aligned_data)
            stderr = 1.0 / np.sqrt(n - 3)
            delta = stats.norm.ppf(1 - alpha / 2) * stderr
            lower_bound = np.tanh(np.arctanh(correlation) - delta)
            upper_bound = np.tanh(np.arctanh(correlation) + delta)

            result = {
                "correlation": correlation,
                "p_value": p_value,
                "is_significant": p_value < alpha,
                "confidence_level": 1 - alpha,
                "confidence_interval": [lower_bound, upper_bound],
                "sample_size": n,
                "standard_error": stderr
            }

            return result

        except Exception as e:
            self.logger.error("Failed to test correlation significance", error=str(e))
            return {"error": str(e)}

    def cross_asset_correlation_analysis(
        self,
        price_data: pd.DataFrame,
        target_asset: str,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze correlations between target asset and all other assets.

        Args:
            price_data: DataFrame with asset prices
            target_asset: Target asset column name
            top_n: Number of top correlations to return

        Returns:
            Dictionary with correlation analysis
        """
        try:
            if target_asset not in price_data.columns:
                return {"error": f"Target asset {target_asset} not found in data"}

            correlations = price_data.corr()[target_asset].drop(target_asset)
            correlations = correlations.dropna()

            # Sort by absolute correlation
            abs_correlations = correlations.abs().sort_values(ascending=False)

            # Get top positive and negative correlations
            top_positive = correlations.nlargest(top_n)
            top_negative = correlations.nsmallest(top_n)

            # Calculate correlation stability (using rolling windows)
            rolling_corrs = {}
            for asset in correlations.index[:5]:  # Top 5 to avoid too much computation
                rolling_corr = self.rolling_correlation(
                    price_data[target_asset],
                    price_data[asset],
                    window=30
                )
                if not rolling_corr.empty:
                    rolling_corrs[asset] = {
                        "current": rolling_corr.iloc[-1],
                        "mean": rolling_corr.mean(),
                        "std": rolling_corr.std(),
                        "stability": 1 - (rolling_corr.std() / abs(rolling_corr.mean())) if rolling_corr.mean() != 0 else 0
                    }

            result = {
                "target_asset": target_asset,
                "total_assets_analyzed": len(correlations),
                "top_positive_correlations": top_positive.to_dict(),
                "top_negative_correlations": top_negative.to_dict(),
                "highest_absolute_correlation": {
                    "asset": abs_correlations.index[0],
                    "correlation": correlations[abs_correlations.index[0]]
                },
                "rolling_correlation_analysis": rolling_corrs,
                "correlation_distribution": {
                    "mean": correlations.mean(),
                    "std": correlations.std(),
                    "min": correlations.min(),
                    "max": correlations.max()
                }
            }

            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze cross-asset correlations for {target_asset}", error=str(e))
            return {"error": str(e)}

    def correlation_clustering(
        self,
        correlation_matrix: pd.DataFrame,
        threshold: float = 0.7
    ) -> Dict[str, List[str]]:
        """
        Group assets into clusters based on correlation.

        Args:
            correlation_matrix: Asset correlation matrix
            threshold: Minimum correlation for clustering

        Returns:
            Dictionary with asset clusters
        """
        try:
            clusters = {}
            processed_assets = set()
            cluster_id = 1

            for asset in correlation_matrix.index:
                if asset in processed_assets:
                    continue

                # Find highly correlated assets
                high_corrs = correlation_matrix[asset][
                    (correlation_matrix[asset] >= threshold) &
                    (correlation_matrix[asset] < 1.0)  # Exclude self-correlation
                ].index.tolist()

                if high_corrs:
                    cluster_name = f"cluster_{cluster_id}"
                    clusters[cluster_name] = [asset] + high_corrs
                    processed_assets.update([asset] + high_corrs)
                    cluster_id += 1
                else:
                    # Asset doesn't cluster with others
                    clusters[f"singleton_{asset}"] = [asset]
                    processed_assets.add(asset)

            self.logger.info(f"Created {len(clusters)} correlation clusters")
            return clusters

        except Exception as e:
            self.logger.error("Failed to perform correlation clustering", error=str(e))
            return {}

    def generate_correlation_report(
        self,
        price_data: pd.DataFrame,
        window: int = 30
    ) -> Dict[str, Any]:
        """Generate comprehensive correlation analysis report."""
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_period": {
                    "start_date": price_data.index.min().isoformat(),
                    "end_date": price_data.index.max().isoformat(),
                    "total_days": len(price_data)
                },
                "correlation_matrix": {},
                "regime_analysis": {},
                "breakdown_alerts": [],
                "clustering": {},
                "summary_statistics": {}
            }

            # Calculate correlation matrix
            corr_matrix = self.calculate_correlation_matrix(price_data)
            if not corr_matrix.empty:
                report["correlation_matrix"] = corr_matrix.to_dict()

                # Clustering analysis
                report["clustering"] = self.correlation_clustering(corr_matrix)

                # Summary statistics
                corr_values = corr_matrix.values
                mask = np.triu(np.ones_like(corr_values, dtype=bool), k=1)
                upper_triangle = corr_values[mask]

                report["summary_statistics"] = {
                    "mean_correlation": np.mean(upper_triangle),
                    "median_correlation": np.median(upper_triangle),
                    "std_correlation": np.std(upper_triangle),
                    "max_correlation": np.max(upper_triangle),
                    "min_correlation": np.min(upper_triangle),
                    "high_correlation_pairs": int(np.sum(upper_triangle > 0.7)),
                    "negative_correlation_pairs": int(np.sum(upper_triangle < -0.3))
                }

            self.logger.info("Generated comprehensive correlation report")
            return report

        except Exception as e:
            self.logger.error("Failed to generate correlation report", error=str(e))
            return {"error": str(e)}