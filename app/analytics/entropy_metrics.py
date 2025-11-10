"""
Financial Entropy Metrics Module
=================================
Comprehensive entropy calculations for financial market analysis.

This module provides advanced entropy-based metrics for:
- Market predictability and chaos measurement
- Regime detection and volatility clustering
- Portfolio diversification optimization
- Causality and information flow analysis
- Anomaly detection and risk assessment
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from scipy import stats, signal
from scipy.spatial.distance import euclidean
from scipy.special import rel_entr
import warnings
warnings.filterwarnings('ignore')

from app.utils.logger import get_logger


class EntropyCalculator:
    """
    Advanced entropy metrics calculator for financial time series analysis.

    Implements multiple entropy measures to quantify market complexity,
    predictability, and information content.
    """

    def __init__(self):
        self.logger = get_logger("analytics.entropy_metrics")

    # ==================== SHANNON ENTROPY ====================

    def shannon_entropy(
        self,
        data: pd.Series,
        bins: int = 50,
        normalize: bool = True
    ) -> float:
        """
        Calculate Shannon Entropy - measures uncertainty/randomness in returns.

        H(X) = -Σ p(x) * log2(p(x))

        Low entropy → Predictable, trending market
        High entropy → Random, chaotic market

        Args:
            data: Price or return series
            bins: Number of bins for histogram
            normalize: Whether to normalize to [0,1]

        Returns:
            Shannon entropy value

        Financial Application:
            - Market regime identification
            - Volatility prediction
            - Trading opportunity detection
        """
        try:
            # Convert to returns if prices
            if data.max() > 10:  # Likely prices
                data = data.pct_change().dropna()

            # Create histogram
            hist, _ = np.histogram(data.dropna(), bins=bins, density=True)
            hist = hist[hist > 0]  # Remove zero bins

            # Calculate Shannon entropy
            entropy = -np.sum(hist * np.log2(hist + 1e-10))

            # Normalize to [0,1]
            if normalize:
                max_entropy = np.log2(bins)
                entropy = entropy / max_entropy if max_entropy > 0 else 0

            self.logger.debug(f"Shannon entropy calculated: {entropy:.4f}")
            return entropy

        except Exception as e:
            self.logger.error(f"Failed to calculate Shannon entropy: {e}")
            return np.nan

    # ==================== APPROXIMATE ENTROPY ====================

    def approximate_entropy(
        self,
        data: pd.Series,
        m: int = 2,
        r: Optional[float] = None
    ) -> float:
        """
        Calculate Approximate Entropy (ApEn) - measures time series regularity.

        Detects changes in market regime and volatility clustering.

        Args:
            data: Time series data
            m: Pattern length (typically 2-3)
            r: Tolerance (default: 0.2 * std)

        Returns:
            ApEn value (0 = perfectly regular, higher = more complex)

        Financial Application:
            - Bull/Bear market transitions
            - Volatility regime changes
            - Crisis detection
        """
        try:
            U = np.array(data.dropna())
            N = len(U)

            if r is None:
                r = 0.2 * np.std(U)

            def _maxdist(x_i, x_j):
                return max([abs(ua - va) for ua, va in zip(x_i, x_j)])

            def _phi(m):
                x = [[U[j] for j in range(i, i + m)] for i in range(N - m + 1)]
                C = [len([1 for x_j in x if _maxdist(x_i, x_j) <= r]) / (N - m + 1.0)
                     for x_i in x]
                return (N - m + 1.0)**(-1) * sum(np.log(C))

            apen = _phi(m) - _phi(m + 1)

            self.logger.debug(f"Approximate entropy (m={m}): {apen:.4f}")
            return apen

        except Exception as e:
            self.logger.error(f"Failed to calculate ApEn: {e}")
            return np.nan

    # ==================== SAMPLE ENTROPY ====================

    def sample_entropy(
        self,
        data: pd.Series,
        m: int = 2,
        r: Optional[float] = None
    ) -> float:
        """
        Calculate Sample Entropy (SampEn) - improved version of ApEn.

        More consistent than ApEn, less sensitive to data length.

        Args:
            data: Time series data
            m: Pattern length
            r: Tolerance

        Returns:
            SampEn value (lower = more regular)

        Financial Application:
            - Market complexity measurement
            - Predictability assessment
            - Risk-adjusted trading signals
        """
        try:
            U = np.array(data.dropna())
            N = len(U)

            if r is None:
                r = 0.2 * np.std(U)

            def _count_patterns(m):
                patterns = np.array([[U[j] for j in range(i, i + m)]
                                    for i in range(N - m)])
                count = 0
                for i in range(len(patterns)):
                    for j in range(i + 1, len(patterns)):
                        if np.max(np.abs(patterns[i] - patterns[j])) <= r:
                            count += 1
                return count

            A = _count_patterns(m)
            B = _count_patterns(m + 1)

            if A == 0 or B == 0:
                return np.inf

            sampen = -np.log(B / A)

            self.logger.debug(f"Sample entropy (m={m}): {sampen:.4f}")
            return sampen

        except Exception as e:
            self.logger.error(f"Failed to calculate SampEn: {e}")
            return np.nan

    # ==================== PERMUTATION ENTROPY ====================

    def permutation_entropy(
        self,
        data: pd.Series,
        order: int = 3,
        delay: int = 1,
        normalize: bool = True
    ) -> float:
        """
        Calculate Permutation Entropy - measures complexity of ordinal patterns.

        Fast and robust to noise, excellent for real-time analysis.

        Args:
            data: Time series data
            order: Embedding dimension (3-7 recommended)
            delay: Time delay
            normalize: Normalize to [0,1]

        Returns:
            Permutation entropy value

        Financial Application:
            - High-frequency trading signals
            - Market microstructure analysis
            - Flash crash detection
        """
        try:
            x = np.array(data.dropna())
            n = len(x)

            # Create permutation patterns
            permutations = {}
            for i in range(n - (order - 1) * delay):
                # Get pattern
                pattern = x[i:i + order * delay:delay]
                # Convert to ordinal pattern
                sorted_indices = tuple(np.argsort(pattern))
                permutations[sorted_indices] = permutations.get(sorted_indices, 0) + 1

            # Calculate entropy
            total = sum(permutations.values())
            probs = np.array([count / total for count in permutations.values()])
            h = -np.sum(probs * np.log2(probs + 1e-10))

            # Normalize
            if normalize:
                h_max = np.log2(np.math.factorial(order))
                h = h / h_max if h_max > 0 else 0

            self.logger.debug(f"Permutation entropy (order={order}): {h:.4f}")
            return h

        except Exception as e:
            self.logger.error(f"Failed to calculate permutation entropy: {e}")
            return np.nan

    # ==================== SPECTRAL ENTROPY ====================

    def spectral_entropy(
        self,
        data: pd.Series,
        method: str = 'welch',
        normalize: bool = True
    ) -> float:
        """
        Calculate Spectral Entropy - frequency domain complexity.

        Analyzes cyclical patterns and periodicities in price data.

        Args:
            data: Time series data
            method: 'fft' or 'welch'
            normalize: Normalize to [0,1]

        Returns:
            Spectral entropy value

        Financial Application:
            - Identify cyclical market patterns
            - Seasonality detection
            - Algorithmic trading optimization
        """
        try:
            x = np.array(data.dropna())

            # Compute power spectral density
            if method == 'welch':
                freqs, psd = signal.welch(x, nperseg=min(256, len(x)))
            else:
                fft = np.fft.fft(x)
                psd = np.abs(fft) ** 2
                freqs = np.fft.fftfreq(len(x))

            # Normalize PSD
            psd_norm = psd / np.sum(psd)
            psd_norm = psd_norm[psd_norm > 0]

            # Calculate entropy
            se = -np.sum(psd_norm * np.log2(psd_norm + 1e-10))

            # Normalize
            if normalize:
                se = se / np.log2(len(psd_norm)) if len(psd_norm) > 1 else 0

            self.logger.debug(f"Spectral entropy: {se:.4f}")
            return se

        except Exception as e:
            self.logger.error(f"Failed to calculate spectral entropy: {e}")
            return np.nan

    # ==================== TRANSFER ENTROPY ====================

    def transfer_entropy(
        self,
        source: pd.Series,
        target: pd.Series,
        k: int = 1,
        l: int = 1,
        bins: int = 10
    ) -> float:
        """
        Calculate Transfer Entropy - measures information flow from source to target.

        TE(X→Y) quantifies how much information X provides about future Y.

        Args:
            source: Source time series (e.g., BTC)
            target: Target time series (e.g., ETH)
            k: History length of target
            l: History length of source
            bins: Discretization bins

        Returns:
            Transfer entropy value (bits)

        Financial Application:
            - Detect market leadership (BTC → Alts)
            - Whale impact measurement
            - Causal relationships in portfolios
        """
        try:
            # Align series
            df = pd.DataFrame({'source': source, 'target': target}).dropna()
            X = df['source'].values
            Y = df['target'].values

            n = len(Y)
            if n < k + l + 1:
                return np.nan

            # Discretize data
            X_discrete = np.digitize(X, np.linspace(X.min(), X.max(), bins))
            Y_discrete = np.digitize(Y, np.linspace(Y.min(), Y.max(), bins))

            # Build probability distributions
            def joint_prob(*arrays):
                """Calculate joint probability distribution."""
                hist = {}
                for i in range(len(arrays[0])):
                    key = tuple(arr[i] for arr in arrays)
                    hist[key] = hist.get(key, 0) + 1
                total = sum(hist.values())
                return {k: v/total for k, v in hist.items()}

            # Create lagged series
            Y_future = Y_discrete[k+l:]
            Y_past = np.array([Y_discrete[i:n-k-l+i] for i in range(k)]).T
            X_past = np.array([X_discrete[i:n-k-l+i] for i in range(l)]).T

            # Calculate transfer entropy
            te = 0.0
            p_yfut_ypast_xpast = joint_prob(Y_future, *[Y_past[:, i] for i in range(k)],
                                            *[X_past[:, i] for i in range(l)])
            p_yfut_ypast = joint_prob(Y_future, *[Y_past[:, i] for i in range(k)])
            p_ypast_xpast = joint_prob(*[Y_past[:, i] for i in range(k)],
                                       *[X_past[:, i] for i in range(l)])
            p_ypast = joint_prob(*[Y_past[:, i] for i in range(k)])

            for key in p_yfut_ypast_xpast:
                p1 = p_yfut_ypast_xpast[key]
                key_ypast = key[1:k+1]
                key_yfut_ypast = key[:k+1]
                key_ypast_xpast = key[1:]

                p2 = p_yfut_ypast.get(key_yfut_ypast, 1e-10)
                p3 = p_ypast_xpast.get(key_ypast_xpast, 1e-10)
                p4 = p_ypast.get(key_ypast, 1e-10)

                if p1 > 0 and p2 > 0 and p3 > 0 and p4 > 0:
                    te += p1 * np.log2((p1 * p4) / (p2 * p3))

            self.logger.debug(f"Transfer entropy (source→target): {te:.4f}")
            return te

        except Exception as e:
            self.logger.error(f"Failed to calculate transfer entropy: {e}")
            return np.nan

    # ==================== CROSS ENTROPY ====================

    def cross_entropy(
        self,
        observed: pd.Series,
        expected: pd.Series,
        bins: int = 50
    ) -> float:
        """
        Calculate Cross-Entropy - measures difference between distributions.

        H(P, Q) = -Σ P(x) * log(Q(x))

        Args:
            observed: Observed distribution (actual returns)
            expected: Expected distribution (model/historical)
            bins: Number of bins

        Returns:
            Cross-entropy value

        Financial Application:
            - Anomaly detection
            - Model validation
            - Risk model accuracy
        """
        try:
            # Create histograms
            range_min = min(observed.min(), expected.min())
            range_max = max(observed.max(), expected.max())

            hist_obs, edges = np.histogram(observed.dropna(), bins=bins,
                                          range=(range_min, range_max), density=True)
            hist_exp, _ = np.histogram(expected.dropna(), bins=bins,
                                       range=(range_min, range_max), density=True)

            # Normalize
            hist_obs = hist_obs / (hist_obs.sum() + 1e-10)
            hist_exp = hist_exp / (hist_exp.sum() + 1e-10)

            # Calculate cross-entropy
            ce = -np.sum(hist_obs * np.log(hist_exp + 1e-10))

            self.logger.debug(f"Cross-entropy: {ce:.4f}")
            return ce

        except Exception as e:
            self.logger.error(f"Failed to calculate cross-entropy: {e}")
            return np.nan

    # ==================== RELATIVE ENTROPY (KL DIVERGENCE) ====================

    def kl_divergence(
        self,
        p: pd.Series,
        q: pd.Series,
        bins: int = 50
    ) -> float:
        """
        Calculate Kullback-Leibler Divergence - relative entropy between distributions.

        KL(P||Q) = Σ P(x) * log(P(x) / Q(x))

        Args:
            p: Distribution P (observed)
            q: Distribution Q (reference)
            bins: Number of bins

        Returns:
            KL divergence value (always ≥ 0)

        Financial Application:
            - Detect distribution shifts
            - Model drift detection
            - Regime change identification
        """
        try:
            # Create histograms
            range_min = min(p.min(), q.min())
            range_max = max(p.max(), q.max())

            hist_p, _ = np.histogram(p.dropna(), bins=bins,
                                    range=(range_min, range_max), density=True)
            hist_q, _ = np.histogram(q.dropna(), bins=bins,
                                    range=(range_min, range_max), density=True)

            # Normalize
            hist_p = hist_p / (hist_p.sum() + 1e-10)
            hist_q = hist_q / (hist_q.sum() + 1e-10)

            # Add small epsilon to avoid log(0)
            hist_p = hist_p + 1e-10
            hist_q = hist_q + 1e-10

            # Calculate KL divergence
            kl = np.sum(rel_entr(hist_p, hist_q))

            self.logger.debug(f"KL divergence: {kl:.4f}")
            return kl

        except Exception as e:
            self.logger.error(f"Failed to calculate KL divergence: {e}")
            return np.nan

    # ==================== CONDITIONAL ENTROPY ====================

    def conditional_entropy(
        self,
        X: pd.Series,
        Y: pd.Series,
        bins: int = 20
    ) -> float:
        """
        Calculate Conditional Entropy H(Y|X) - uncertainty of Y given X.

        H(Y|X) = H(X,Y) - H(X)

        Args:
            X: Conditioning variable
            Y: Target variable
            bins: Discretization bins

        Returns:
            Conditional entropy value

        Financial Application:
            - Information gain from indicators
            - Feature selection for ML models
            - Signal quality assessment
        """
        try:
            # Align series
            df = pd.DataFrame({'X': X, 'Y': Y}).dropna()
            x = df['X'].values
            y = df['Y'].values

            # Discretize
            x_bins = np.linspace(x.min(), x.max(), bins)
            y_bins = np.linspace(y.min(), y.max(), bins)

            x_discrete = np.digitize(x, x_bins)
            y_discrete = np.digitize(y, y_bins)

            # Calculate joint entropy H(X,Y)
            joint_hist, _, _ = np.histogram2d(x_discrete, y_discrete, bins=bins)
            joint_prob = joint_hist / joint_hist.sum()
            joint_prob = joint_prob[joint_prob > 0]
            h_xy = -np.sum(joint_prob * np.log2(joint_prob))

            # Calculate entropy H(X)
            x_hist, _ = np.histogram(x_discrete, bins=bins)
            x_prob = x_hist / x_hist.sum()
            x_prob = x_prob[x_prob > 0]
            h_x = -np.sum(x_prob * np.log2(x_prob))

            # Conditional entropy
            h_y_given_x = h_xy - h_x

            self.logger.debug(f"Conditional entropy H(Y|X): {h_y_given_x:.4f}")
            return h_y_given_x

        except Exception as e:
            self.logger.error(f"Failed to calculate conditional entropy: {e}")
            return np.nan

    # ==================== FUZZY ENTROPY ====================

    def fuzzy_entropy(
        self,
        data: pd.Series,
        m: int = 2,
        r: Optional[float] = None,
        n: float = 2.0
    ) -> float:
        """
        Calculate Fuzzy Entropy - robust to noise, uses fuzzy membership.

        Args:
            data: Time series data
            m: Pattern length
            r: Tolerance
            n: Fuzzy power (typically 2)

        Returns:
            Fuzzy entropy value

        Financial Application:
            - Noisy market analysis
            - Robust complexity measure
            - High-frequency data analysis
        """
        try:
            U = np.array(data.dropna())
            N = len(U)

            if r is None:
                r = 0.2 * np.std(U)

            def _fuzzy_membership(d, r, n):
                """Exponential fuzzy membership function."""
                return np.exp(-(d**n) / r)

            def _phi_fuzzy(m):
                patterns = np.array([[U[j] for j in range(i, i + m)]
                                    for i in range(N - m)])
                phi = 0
                for i in range(len(patterns)):
                    similarities = []
                    for j in range(len(patterns)):
                        if i != j:
                            d = np.max(np.abs(patterns[i] - patterns[j]))
                            similarities.append(_fuzzy_membership(d, r, n))
                    if similarities:
                        phi += np.log(np.mean(similarities))
                return phi / (N - m)

            fuzzyen = _phi_fuzzy(m) - _phi_fuzzy(m + 1)

            self.logger.debug(f"Fuzzy entropy: {fuzzyen:.4f}")
            return fuzzyen

        except Exception as e:
            self.logger.error(f"Failed to calculate fuzzy entropy: {e}")
            return np.nan

    # ==================== MULTISCALE ENTROPY ====================

    def multiscale_entropy(
        self,
        data: pd.Series,
        max_scale: int = 10,
        method: str = 'sample'
    ) -> Dict[int, float]:
        """
        Calculate Multiscale Entropy - complexity across multiple time scales.

        Reveals complexity patterns at different granularities.

        Args:
            data: Time series data
            max_scale: Maximum scale factor
            method: 'sample' or 'approximate'

        Returns:
            Dictionary of {scale: entropy}

        Financial Application:
            - Multi-timeframe analysis
            - Scale-dependent trading strategies
            - Fractal market analysis
        """
        try:
            results = {}
            x = np.array(data.dropna())

            for scale in range(1, max_scale + 1):
                # Coarse-grain the time series
                n = len(x) // scale
                coarse_grained = np.array([x[i*scale:(i+1)*scale].mean()
                                          for i in range(n)])

                # Calculate entropy
                if method == 'sample':
                    entropy = self.sample_entropy(pd.Series(coarse_grained))
                else:
                    entropy = self.approximate_entropy(pd.Series(coarse_grained))

                results[scale] = entropy

            self.logger.debug(f"Multiscale entropy calculated for {max_scale} scales")
            return results

        except Exception as e:
            self.logger.error(f"Failed to calculate multiscale entropy: {e}")
            return {}

    # ==================== PORTFOLIO ENTROPY ====================

    def portfolio_entropy(
        self,
        weights: Union[Dict[str, float], pd.Series, np.ndarray]
    ) -> float:
        """
        Calculate Portfolio Entropy - diversification measure.

        Maximum entropy = equally weighted portfolio (maximum diversification)
        Minimum entropy = concentrated portfolio

        Args:
            weights: Portfolio weights

        Returns:
            Portfolio entropy (0 to log(N))

        Financial Application:
            - Diversification optimization
            - Concentration risk measurement
            - Portfolio rebalancing signals
        """
        try:
            if isinstance(weights, dict):
                w = np.array(list(weights.values()))
            elif isinstance(weights, pd.Series):
                w = weights.values
            else:
                w = np.array(weights)

            # Normalize
            w = w / w.sum()
            w = w[w > 0]

            # Calculate entropy
            h = -np.sum(w * np.log(w))

            # Can normalize by log(N) for [0,1] range
            max_h = np.log(len(w))
            normalized_h = h / max_h if max_h > 0 else 0

            self.logger.debug(f"Portfolio entropy: {h:.4f} (normalized: {normalized_h:.4f})")
            return h

        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio entropy: {e}")
            return np.nan

    # ==================== COMPREHENSIVE ENTROPY REPORT ====================

    def comprehensive_entropy_report(
        self,
        data: pd.Series,
        reference_data: Optional[pd.Series] = None,
        asset_name: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive entropy analysis report.

        Args:
            data: Price or return series
            reference_data: Optional reference series for comparison metrics
            asset_name: Name of asset

        Returns:
            Comprehensive dictionary of all entropy metrics
        """
        try:
            self.logger.info(f"Generating comprehensive entropy report for {asset_name}")

            # Convert to returns if needed
            if data.max() > 10:
                returns = data.pct_change().dropna()
            else:
                returns = data.dropna()

            report = {
                "asset_name": asset_name,
                "timestamp": datetime.utcnow().isoformat(),
                "data_points": len(data),

                # Basic entropy metrics
                "shannon_entropy": self.shannon_entropy(returns),
                "approximate_entropy": self.approximate_entropy(returns),
                "sample_entropy": self.sample_entropy(returns),
                "permutation_entropy": self.permutation_entropy(returns),
                "spectral_entropy": self.spectral_entropy(returns),
                "fuzzy_entropy": self.fuzzy_entropy(returns),

                # Multiscale analysis
                "multiscale_entropy": self.multiscale_entropy(returns, max_scale=5),

                # Interpretation
                "complexity_score": None,
                "predictability_score": None,
                "market_regime": None,
                "risk_level": None
            }

            # Add comparison metrics if reference provided
            if reference_data is not None:
                if reference_data.max() > 10:
                    ref_returns = reference_data.pct_change().dropna()
                else:
                    ref_returns = reference_data.dropna()

                report["comparison_metrics"] = {
                    "kl_divergence": self.kl_divergence(returns, ref_returns),
                    "cross_entropy": self.cross_entropy(returns, ref_returns),
                    "conditional_entropy": self.conditional_entropy(ref_returns, returns)
                }

            # Calculate derived scores
            report["complexity_score"] = self._calculate_complexity_score(report)
            report["predictability_score"] = self._calculate_predictability_score(report)
            report["market_regime"] = self._identify_market_regime(report)
            report["risk_level"] = self._assess_entropy_risk(report)

            self.logger.info(f"Entropy report generated successfully for {asset_name}")
            return report

        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive entropy report: {e}")
            return {"error": str(e)}

    # ==================== HELPER METHODS ====================

    def _calculate_complexity_score(self, report: Dict) -> float:
        """
        Calculate overall complexity score (0-100).

        Higher = More complex/chaotic market
        """
        try:
            scores = []
            if report.get("shannon_entropy") is not None:
                scores.append(report["shannon_entropy"] * 100)
            if report.get("sample_entropy") is not None:
                # Normalize SampEn (typically 0-2)
                scores.append(min(report["sample_entropy"] * 50, 100))
            if report.get("permutation_entropy") is not None:
                scores.append(report["permutation_entropy"] * 100)

            return np.mean(scores) if scores else None
        except:
            return None

    def _calculate_predictability_score(self, report: Dict) -> float:
        """
        Calculate predictability score (0-100).

        Higher = More predictable (inverse of complexity)
        """
        try:
            complexity = report.get("complexity_score")
            if complexity is not None:
                return 100 - complexity
            return None
        except:
            return None

    def _identify_market_regime(self, report: Dict) -> str:
        """Identify current market regime based on entropy."""
        try:
            shannon = report.get("shannon_entropy", 0.5)
            apen = report.get("approximate_entropy", 1.0)

            if shannon < 0.3 and apen < 0.5:
                return "Strong Trend (Low Entropy)"
            elif shannon < 0.5 and apen < 1.0:
                return "Trending (Moderate Entropy)"
            elif shannon < 0.7:
                return "Mixed/Transitional (Medium Entropy)"
            elif shannon < 0.85:
                return "Choppy/Volatile (High Entropy)"
            else:
                return "Highly Chaotic (Very High Entropy)"
        except:
            return "Unknown"

    def _assess_entropy_risk(self, report: Dict) -> str:
        """Assess risk level based on entropy metrics."""
        try:
            complexity = report.get("complexity_score", 50)

            if complexity < 20:
                return "Very Low Risk (Predictable)"
            elif complexity < 40:
                return "Low Risk (Trending)"
            elif complexity < 60:
                return "Medium Risk (Normal)"
            elif complexity < 80:
                return "High Risk (Volatile)"
            else:
                return "Very High Risk (Chaotic)"
        except:
            return "Unknown"

    # ==================== WHALE TRACKING ENTROPY ====================

    def whale_influence_entropy(
        self,
        whale_activity: pd.Series,
        market_price: pd.Series,
        window: int = 20
    ) -> Dict[str, float]:
        """
        Measure information flow from whale activity to market price.

        Uses transfer entropy to quantify whale impact.

        Args:
            whale_activity: Whale transaction volume/count series
            market_price: Market price series
            window: Rolling window

        Returns:
            Dictionary with whale influence metrics
        """
        try:
            # Calculate transfer entropy
            te_whale_to_market = self.transfer_entropy(whale_activity, market_price)
            te_market_to_whale = self.transfer_entropy(market_price, whale_activity)

            # Net information flow
            net_influence = te_whale_to_market - te_market_to_whale

            # Rolling transfer entropy
            rolling_te = []
            for i in range(window, len(whale_activity)):
                window_te = self.transfer_entropy(
                    whale_activity.iloc[i-window:i],
                    market_price.iloc[i-window:i]
                )
                rolling_te.append(window_te)

            return {
                "whale_to_market_te": te_whale_to_market,
                "market_to_whale_te": te_market_to_whale,
                "net_whale_influence": net_influence,
                "average_rolling_influence": np.mean(rolling_te) if rolling_te else np.nan,
                "influence_volatility": np.std(rolling_te) if rolling_te else np.nan,
                "interpretation": "Whales Leading" if net_influence > 0.1 else
                                 "Market Leading" if net_influence < -0.1 else "Balanced"
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate whale influence entropy: {e}")
            return {}


# ==================== CONVENIENCE FUNCTIONS ====================

def quick_entropy_analysis(data: pd.Series, asset_name: str = "Asset") -> Dict[str, Any]:
    """
    Quick entropy analysis - returns key metrics only.

    Usage:
        >>> prices = yf.download('BTC-USD')['Close']
        >>> results = quick_entropy_analysis(prices, 'Bitcoin')
    """
    calc = EntropyCalculator()
    returns = data.pct_change().dropna() if data.max() > 10 else data

    return {
        "asset": asset_name,
        "shannon_entropy": calc.shannon_entropy(returns),
        "sample_entropy": calc.sample_entropy(returns),
        "complexity_score": calc.shannon_entropy(returns) * 100,
        "market_regime": calc._identify_market_regime({
            "shannon_entropy": calc.shannon_entropy(returns),
            "approximate_entropy": calc.approximate_entropy(returns)
        })
    }


def compare_assets_entropy(
    assets: Dict[str, pd.Series],
    metric: str = "shannon"
) -> pd.DataFrame:
    """
    Compare entropy metrics across multiple assets.

    Args:
        assets: Dictionary of {name: price_series}
        metric: Entropy metric to use

    Returns:
        DataFrame with comparison
    """
    calc = EntropyCalculator()
    results = []

    for name, data in assets.items():
        returns = data.pct_change().dropna() if data.max() > 10 else data

        if metric == "shannon":
            value = calc.shannon_entropy(returns)
        elif metric == "sample":
            value = calc.sample_entropy(returns)
        elif metric == "permutation":
            value = calc.permutation_entropy(returns)
        else:
            value = calc.shannon_entropy(returns)

        results.append({
            "Asset": name,
            "Entropy": value,
            "Complexity": "High" if value > 0.7 else "Medium" if value > 0.4 else "Low"
        })

    return pd.DataFrame(results).sort_values("Entropy", ascending=False)
