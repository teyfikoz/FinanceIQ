"""
Crypto-Specific Entropy Analysis
==================================
Entropy metrics specialized for cryptocurrency market analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.analytics.entropy_metrics import EntropyCalculator
from app.utils.logger import get_logger


class CryptoEntropyAnalyzer:
    """
    Specialized entropy analysis for cryptocurrency markets.

    Combines market cap distributions, dominance metrics,
    and information theory to detect market patterns.
    """

    def __init__(self):
        self.logger = get_logger("analytics.crypto_entropy")
        self.entropy_calc = EntropyCalculator()

    def analyze_market_cap_distribution(
        self,
        top_cryptos_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze entropy of market cap distribution.

        Low entropy = Concentrated market (few coins dominate)
        High entropy = Distributed market (many coins have similar caps)

        Args:
            top_cryptos_df: DataFrame with 'market_cap' column

        Returns:
            Dictionary with distribution entropy metrics
        """
        try:
            if 'market_cap' not in top_cryptos_df.columns:
                return {}

            market_caps = top_cryptos_df['market_cap'].values
            total_mcap = market_caps.sum()

            # Calculate market shares
            market_shares = market_caps / total_mcap

            # Portfolio entropy (market cap distribution)
            distribution_entropy = self.entropy_calc.portfolio_entropy(market_shares)

            # Maximum possible entropy for this number of assets
            n_assets = len(market_shares)
            max_entropy = np.log(n_assets)

            # Normalized (0-100%)
            normalized_entropy = (distribution_entropy / max_entropy) * 100 if max_entropy > 0 else 0

            # Herfindahl-Hirschman Index (HHI)
            hhi = np.sum(market_shares ** 2) * 10000

            # Gini coefficient (inequality measure)
            gini = self._calculate_gini(market_caps)

            # Top N concentration
            top1_share = market_shares[0] * 100
            top5_share = market_shares[:5].sum() * 100
            top10_share = market_shares[:10].sum() * 100

            result = {
                'timestamp': datetime.now(),
                'distribution_entropy': distribution_entropy,
                'normalized_entropy_pct': normalized_entropy,
                'max_possible_entropy': max_entropy,
                'hhi_index': hhi,
                'gini_coefficient': gini,
                'top1_concentration': top1_share,
                'top5_concentration': top5_share,
                'top10_concentration': top10_share,
                'market_structure': self._classify_market_structure(hhi, gini),
                'diversification_level': self._classify_diversification(normalized_entropy)
            }

            self.logger.info("Market cap distribution entropy analyzed")
            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze market cap distribution: {e}")
            return {}

    def analyze_dominance_entropy(
        self,
        dominance_history: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze entropy of Bitcoin/altcoin dominance over time.

        Args:
            dominance_history: DataFrame with 'btc_dominance' column

        Returns:
            Dictionary with dominance entropy metrics
        """
        try:
            if 'btc_dominance' not in dominance_history.columns:
                return {}

            btc_dom = dominance_history['btc_dominance'].dropna()

            # Shannon entropy of dominance distribution
            shannon = self.entropy_calc.shannon_entropy(btc_dom, bins=30)

            # Sample entropy (complexity of dominance changes)
            sampen = self.entropy_calc.sample_entropy(btc_dom)

            # Approximate entropy (regime detection)
            apen = self.entropy_calc.approximate_entropy(btc_dom)

            # Volatility of dominance
            dom_volatility = btc_dom.std()

            # Trend analysis
            recent_dom = btc_dom.tail(30).mean() if len(btc_dom) >= 30 else btc_dom.mean()
            older_dom = btc_dom.head(30).mean() if len(btc_dom) >= 60 else btc_dom.iloc[0]

            trend = "Increasing" if recent_dom > older_dom else "Decreasing"

            # Altcoin season indicator from entropy
            # Low dominance entropy + decreasing trend = Altcoin season
            altcoin_season_score = self._calculate_altcoin_season_from_entropy(
                shannon, apen, recent_dom
            )

            result = {
                'timestamp': datetime.now(),
                'current_btc_dominance': btc_dom.iloc[-1],
                'shannon_entropy': shannon,
                'sample_entropy': sampen,
                'approximate_entropy': apen,
                'dominance_volatility': dom_volatility,
                'dominance_trend': trend,
                'recent_avg_dominance': recent_dom,
                'altcoin_season_score': altcoin_season_score,
                'market_phase': self._identify_dominance_phase(recent_dom, shannon)
            }

            self.logger.info("Dominance entropy analyzed")
            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze dominance entropy: {e}")
            return {}

    def analyze_altcoin_dispersion(
        self,
        top_cryptos_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze dispersion and entropy of altcoin performance.

        High entropy = Altcoins moving in different directions (opportunity)
        Low entropy = Altcoins moving together (correlation)

        Args:
            top_cryptos_df: DataFrame with price change columns

        Returns:
            Dictionary with altcoin dispersion metrics
        """
        try:
            # Get price changes
            price_changes = []
            for col in ['price_change_percentage_24h', 'price_change_percentage_7d',
                       'price_change_percentage_30d']:
                if col in top_cryptos_df.columns:
                    price_changes.append(top_cryptos_df[col].dropna())

            if not price_changes:
                return {}

            results = {}

            for i, changes in enumerate(price_changes):
                period = ['24h', '7d', '30d'][i]

                # Filter out BTC and ETH for pure altcoin analysis
                altcoin_changes = changes[~top_cryptos_df['symbol'].str.upper().isin(['BTC', 'ETH'])]

                if len(altcoin_changes) < 5:
                    continue

                # Shannon entropy of return distribution
                shannon = self.entropy_calc.shannon_entropy(altcoin_changes, bins=20)

                # Standard deviation (traditional dispersion)
                std_dev = altcoin_changes.std()

                # Range
                price_range = altcoin_changes.max() - altcoin_changes.min()

                # Coefficient of variation
                mean_change = altcoin_changes.mean()
                cv = (std_dev / abs(mean_change)) if mean_change != 0 else np.inf

                # Classify
                if shannon > 0.7:
                    dispersion = "High Dispersion (Divergent moves)"
                elif shannon > 0.5:
                    dispersion = "Moderate Dispersion"
                else:
                    dispersion = "Low Dispersion (Correlated moves)"

                results[f'{period}_metrics'] = {
                    'shannon_entropy': shannon,
                    'std_deviation': std_dev,
                    'range': price_range,
                    'coefficient_variation': cv,
                    'mean_change': mean_change,
                    'dispersion_level': dispersion
                }

            result = {
                'timestamp': datetime.now(),
                'period_metrics': results,
                'overall_assessment': self._assess_altcoin_opportunity(results)
            }

            self.logger.info("Altcoin dispersion analyzed")
            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze altcoin dispersion: {e}")
            return {}

    def detect_market_regime_from_entropy(
        self,
        market_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """
        Detect market regime using multiple entropy measures.

        Args:
            market_data: Dictionary with 'total_mcap', 'btc_dominance', 'altcoin_mcap' series

        Returns:
            Dictionary with regime detection results
        """
        try:
            regime_signals = []

            # 1. Total market cap entropy (volatility/chaos)
            if 'total_mcap' in market_data:
                mcap_returns = market_data['total_mcap'].pct_change().dropna()
                mcap_entropy = self.entropy_calc.shannon_entropy(mcap_returns)

                if mcap_entropy < 0.4:
                    regime_signals.append("Stable Growth")
                elif mcap_entropy > 0.7:
                    regime_signals.append("High Volatility")

            # 2. Dominance trend
            if 'btc_dominance' in market_data:
                btc_dom = market_data['btc_dominance']
                dom_apen = self.entropy_calc.approximate_entropy(btc_dom)

                recent = btc_dom.tail(30).mean()
                if recent > 50 and dom_apen < 0.5:
                    regime_signals.append("Bitcoin Dominance Era")
                elif recent < 45:
                    regime_signals.append("Altcoin Season")

            # 3. Altcoin market cap entropy
            if 'altcoin_mcap' in market_data:
                alt_returns = market_data['altcoin_mcap'].pct_change().dropna()
                alt_entropy = self.entropy_calc.shannon_entropy(alt_returns)

                if alt_entropy < 0.3:
                    regime_signals.append("Strong Altcoin Trend")

            # 4. Transfer entropy (if BTC and altcoin data available)
            if 'btc_price' in market_data and 'altcoin_mcap' in market_data:
                te = self.entropy_calc.transfer_entropy(
                    market_data['btc_price'],
                    market_data['altcoin_mcap']
                )

                if te > 0.5:
                    regime_signals.append("BTC Leading Altcoins")

            # Combine signals
            regime = self._combine_regime_signals(regime_signals)

            result = {
                'timestamp': datetime.now(),
                'detected_regime': regime,
                'regime_signals': regime_signals,
                'confidence': len(regime_signals) / 4.0  # Max 4 signals
            }

            self.logger.info(f"Market regime detected: {regime}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to detect market regime: {e}")
            return {}

    def calculate_crypto_complexity_index(
        self,
        market_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall crypto market complexity index from entropy metrics.

        Args:
            market_metrics: Dictionary with various market metrics

        Returns:
            Dictionary with complexity index
        """
        try:
            complexity_components = []

            # Component 1: Market cap distribution entropy (0-100)
            if 'distribution_entropy' in market_metrics:
                dist_ent = market_metrics.get('normalized_entropy_pct', 50)
                complexity_components.append(('distribution', dist_ent, 0.25))

            # Component 2: Dominance volatility (normalized)
            if 'dominance_volatility' in market_metrics:
                dom_vol = market_metrics['dominance_volatility']
                dom_vol_norm = min(dom_vol * 10, 100)  # Normalize to 0-100
                complexity_components.append(('dominance_volatility', dom_vol_norm, 0.20))

            # Component 3: Price entropy
            if 'price_entropy' in market_metrics:
                price_ent = market_metrics['price_entropy'] * 100
                complexity_components.append(('price_entropy', price_ent, 0.25))

            # Component 4: Altcoin dispersion
            if 'altcoin_dispersion' in market_metrics:
                disp = market_metrics['altcoin_dispersion']
                complexity_components.append(('altcoin_dispersion', disp, 0.30))

            # Calculate weighted index
            if complexity_components:
                weighted_sum = sum(value * weight for _, value, weight in complexity_components)
                total_weight = sum(weight for _, _, weight in complexity_components)
                complexity_index = weighted_sum / total_weight if total_weight > 0 else 50
            else:
                complexity_index = 50  # Default

            # Classify complexity
            if complexity_index < 30:
                complexity_level = "Low Complexity (Stable/Trending)"
            elif complexity_index < 50:
                complexity_level = "Moderate Complexity"
            elif complexity_index < 70:
                complexity_level = "High Complexity (Volatile)"
            else:
                complexity_level = "Extreme Complexity (Chaotic)"

            result = {
                'timestamp': datetime.now(),
                'complexity_index': complexity_index,
                'complexity_level': complexity_level,
                'components': {name: value for name, value, _ in complexity_components},
                'interpretation': self._interpret_complexity(complexity_index)
            }

            self.logger.info(f"Crypto complexity index: {complexity_index:.1f}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to calculate complexity index: {e}")
            return {}

    # ==================== HELPER METHODS ====================

    def _calculate_gini(self, values: np.ndarray) -> float:
        """Calculate Gini coefficient (inequality measure)."""
        sorted_values = np.sort(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)
        return (2 * np.sum((np.arange(1, n+1)) * sorted_values)) / (n * cumsum[-1]) - (n + 1) / n

    def _classify_market_structure(self, hhi: float, gini: float) -> str:
        """Classify market structure based on HHI and Gini."""
        if hhi > 2500 or gini > 0.7:
            return "Highly Concentrated (Monopolistic)"
        elif hhi > 1500 or gini > 0.5:
            return "Moderately Concentrated (Oligopolistic)"
        else:
            return "Competitive (Distributed)"

    def _classify_diversification(self, norm_entropy: float) -> str:
        """Classify diversification level."""
        if norm_entropy > 80:
            return "Highly Diversified"
        elif norm_entropy > 60:
            return "Moderately Diversified"
        elif norm_entropy > 40:
            return "Somewhat Concentrated"
        else:
            return "Highly Concentrated"

    def _calculate_altcoin_season_from_entropy(
        self,
        shannon: float,
        apen: float,
        current_dom: float
    ) -> float:
        """
        Calculate altcoin season score from entropy metrics.

        Returns: 0-100 score (higher = more altcoin season)
        """
        # Lower BTC dominance = higher altcoin score
        dom_score = max(0, 100 - current_dom * 2)

        # Lower entropy in BTC dom = more stable altcoin season
        entropy_score = max(0, 100 - shannon * 100)

        # Combine
        score = (dom_score * 0.6 + entropy_score * 0.4)

        return np.clip(score, 0, 100)

    def _identify_dominance_phase(self, current_dom: float, entropy: float) -> str:
        """Identify market phase from dominance and entropy."""
        if current_dom > 50 and entropy < 0.5:
            return "Strong Bitcoin Season"
        elif current_dom > 50:
            return "Bitcoin Dominance (Unstable)"
        elif current_dom < 40 and entropy < 0.5:
            return "Strong Altcoin Season"
        elif current_dom < 40:
            return "Altcoin Season (Volatile)"
        else:
            return "Transitional Phase"

    def _assess_altcoin_opportunity(self, period_metrics: Dict) -> str:
        """Assess overall altcoin trading opportunity."""
        if not period_metrics:
            return "Insufficient Data"

        # Check 24h metrics
        if '24h_metrics' in period_metrics:
            metrics = period_metrics['24h_metrics']
            entropy = metrics.get('shannon_entropy', 0.5)

            if entropy > 0.7:
                return "High Opportunity (Divergent moves, select winners carefully)"
            elif entropy > 0.5:
                return "Moderate Opportunity (Mixed performance)"
            else:
                return "Low Opportunity (Correlated moves, market-wide trend)"

        return "Unknown"

    def _combine_regime_signals(self, signals: List[str]) -> str:
        """Combine multiple regime signals into overall assessment."""
        if not signals:
            return "Insufficient Data"

        # Count signal types
        bullish_signals = sum(1 for s in signals if any(x in s for x in
                             ["Growth", "Trend", "Season", "Leading"]))
        bearish_signals = sum(1 for s in signals if any(x in s for x in
                             ["Volatility", "Unstable", "Chaotic"]))

        if "Altcoin Season" in signals:
            return "Altcoin Season (Risk On)"
        elif "Bitcoin Dominance Era" in signals:
            return "Bitcoin Dominance (Risk Off / Accumulation)"
        elif bearish_signals > bullish_signals:
            return "High Uncertainty / Volatility Period"
        elif bullish_signals > bearish_signals:
            return "Growth Phase / Bull Market"
        else:
            return "Mixed / Transitional Market"

    def _interpret_complexity(self, complexity_index: float) -> str:
        """Interpret complexity index for trading."""
        if complexity_index < 30:
            return "✅ Good environment for trend following strategies"
        elif complexity_index < 50:
            return "ℹ️ Moderate complexity - Use adaptive strategies"
        elif complexity_index < 70:
            return "⚠️ High complexity - Reduce position sizes, tighter stops"
        else:
            return "❌ Extreme complexity - Consider staying on sidelines"


# Convenience function
def get_crypto_entropy_analyzer() -> CryptoEntropyAnalyzer:
    """Get CryptoEntropyAnalyzer instance."""
    return CryptoEntropyAnalyzer()
