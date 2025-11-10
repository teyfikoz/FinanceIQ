"""
Crypto Market Dominance Data Collector
========================================
Collects comprehensive cryptocurrency market metrics including:
- Total market cap
- Market cap excluding BTC, ETH, Top 10
- Bitcoin dominance
- Top 10 individual crypto data
"""

import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
from app.utils.logger import get_logger


class CryptoMarketDominanceCollector:
    """
    Collects crypto market dominance and market cap distribution data.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.logger = get_logger("data_collectors.crypto_dominance")
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.pro_url = "https://pro-api.coingecko.com/api/v3"

        # Use pro API if key provided
        if api_key:
            self.base_url = self.pro_url
            self.headers = {"x-cg-pro-api-key": api_key}
        else:
            self.headers = {}

    def get_global_market_data(self) -> Dict[str, Any]:
        """
        Get global cryptocurrency market data.

        Returns:
            Dictionary containing global market metrics
        """
        try:
            endpoint = f"{self.base_url}/global"
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()['data']

            result = {
                'timestamp': datetime.now(),
                'total_market_cap_usd': data['total_market_cap'].get('usd', 0),
                'total_volume_24h_usd': data['total_volume'].get('usd', 0),
                'bitcoin_dominance': data['market_cap_percentage'].get('btc', 0),
                'ethereum_dominance': data['market_cap_percentage'].get('eth', 0),
                'active_cryptocurrencies': data.get('active_cryptocurrencies', 0),
                'markets': data.get('markets', 0),
                'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd', 0)
            }

            self.logger.info("Global market data retrieved successfully")
            return result

        except Exception as e:
            self.logger.error(f"Failed to get global market data: {e}")
            return {}

    def get_top_cryptos(self, limit: int = 100) -> pd.DataFrame:
        """
        Get top cryptocurrencies by market cap.

        Args:
            limit: Number of cryptocurrencies to retrieve

        Returns:
            DataFrame with crypto data
        """
        try:
            endpoint = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '1h,24h,7d,30d,1y'
            }

            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            df = pd.DataFrame(data)
            df['timestamp'] = datetime.now()

            self.logger.info(f"Retrieved top {len(df)} cryptocurrencies")
            return df

        except Exception as e:
            self.logger.error(f"Failed to get top cryptos: {e}")
            return pd.DataFrame()

    def get_market_cap_segments(self) -> Dict[str, float]:
        """
        Calculate market cap segments (total, excl. BTC, excl. BTC+ETH, excl. Top10).

        Returns:
            Dictionary with market cap segments
        """
        try:
            # Get top 100 to ensure we have top 10 covered
            df = self.get_top_cryptos(limit=100)

            if df.empty:
                return {}

            total_market_cap = df['market_cap'].sum()

            # Get individual market caps
            btc_mcap = df[df['symbol'].str.upper() == 'BTC']['market_cap'].iloc[0] if len(df[df['symbol'].str.upper() == 'BTC']) > 0 else 0
            eth_mcap = df[df['symbol'].str.upper() == 'ETH']['market_cap'].iloc[0] if len(df[df['symbol'].str.upper() == 'ETH']) > 0 else 0

            # Top 10 market cap
            top_10_mcap = df.head(10)['market_cap'].sum()

            result = {
                'timestamp': datetime.now(),
                'total_market_cap': total_market_cap,
                'btc_market_cap': btc_mcap,
                'eth_market_cap': eth_mcap,
                'excl_btc': total_market_cap - btc_mcap,
                'excl_btc_eth': total_market_cap - btc_mcap - eth_mcap,
                'excl_top10': total_market_cap - top_10_mcap,
                'top10_market_cap': top_10_mcap,
                'btc_dominance': (btc_mcap / total_market_cap * 100) if total_market_cap > 0 else 0,
                'eth_dominance': (eth_mcap / total_market_cap * 100) if total_market_cap > 0 else 0,
                'top10_dominance': (top_10_mcap / total_market_cap * 100) if total_market_cap > 0 else 0,
                'altcoin_dominance': ((total_market_cap - btc_mcap) / total_market_cap * 100) if total_market_cap > 0 else 0
            }

            self.logger.info("Market cap segments calculated successfully")
            return result

        except Exception as e:
            self.logger.error(f"Failed to calculate market cap segments: {e}")
            return {}

    def get_historical_market_caps(self, days: int = 365) -> pd.DataFrame:
        """
        Get historical market cap data for Bitcoin and total market.

        Args:
            days: Number of days of historical data

        Returns:
            DataFrame with historical market caps
        """
        try:
            # Get Bitcoin historical data
            btc_endpoint = f"{self.base_url}/coins/bitcoin/market_chart"
            btc_params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }

            response = requests.get(btc_endpoint, headers=self.headers, params=btc_params, timeout=30)
            response.raise_for_status()
            btc_data = response.json()

            # Convert to DataFrame
            btc_df = pd.DataFrame(btc_data['market_caps'], columns=['timestamp', 'btc_market_cap'])
            btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'], unit='ms')

            # Note: CoinGecko free API doesn't have historical total market cap
            # We'll use current ratio to estimate (this is approximate)
            current_data = self.get_market_cap_segments()

            if current_data:
                btc_dominance = current_data['btc_dominance'] / 100
                btc_df['estimated_total_market_cap'] = btc_df['btc_market_cap'] / btc_dominance
                btc_df['estimated_altcoin_market_cap'] = btc_df['estimated_total_market_cap'] - btc_df['btc_market_cap']

            self.logger.info(f"Retrieved {len(btc_df)} days of historical data")
            return btc_df

        except Exception as e:
            self.logger.error(f"Failed to get historical market caps: {e}")
            return pd.DataFrame()

    def get_top10_detailed_data(self) -> pd.DataFrame:
        """
        Get detailed data for top 10 cryptocurrencies.

        Returns:
            DataFrame with detailed top 10 crypto data
        """
        try:
            df = self.get_top_cryptos(limit=10)

            if df.empty:
                return df

            # Select relevant columns
            columns = [
                'id', 'symbol', 'name', 'current_price', 'market_cap', 'market_cap_rank',
                'total_volume', 'high_24h', 'low_24h', 'price_change_24h',
                'price_change_percentage_24h', 'market_cap_change_24h',
                'market_cap_change_percentage_24h', 'circulating_supply',
                'total_supply', 'max_supply', 'ath', 'ath_date',
                'atl', 'atl_date', 'timestamp'
            ]

            # Only keep columns that exist
            available_columns = [col for col in columns if col in df.columns]
            df_detailed = df[available_columns].copy()

            # Calculate additional metrics
            df_detailed['ath_drawdown'] = ((df_detailed['current_price'] / df_detailed['ath']) - 1) * 100
            df_detailed['atl_gain'] = ((df_detailed['current_price'] / df_detailed['atl']) - 1) * 100

            self.logger.info("Top 10 detailed data retrieved successfully")
            return df_detailed

        except Exception as e:
            self.logger.error(f"Failed to get top 10 detailed data: {e}")
            return pd.DataFrame()

    def get_crypto_historical_data(self, crypto_id: str, days: int = 365) -> pd.DataFrame:
        """
        Get historical data for a specific cryptocurrency.

        Args:
            crypto_id: CoinGecko ID (e.g., 'bitcoin', 'ethereum')
            days: Number of days

        Returns:
            DataFrame with historical data
        """
        try:
            endpoint = f"{self.base_url}/coins/{crypto_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }

            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Combine prices, market caps, and volumes
            df = pd.DataFrame({
                'timestamp': [x[0] for x in data['prices']],
                'price': [x[1] for x in data['prices']],
                'market_cap': [x[1] for x in data['market_caps']],
                'volume': [x[1] for x in data['total_volumes']]
            })

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['crypto_id'] = crypto_id

            self.logger.info(f"Retrieved historical data for {crypto_id}")
            return df

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {crypto_id}: {e}")
            return pd.DataFrame()

    def get_altcoin_season_index(self) -> Dict[str, Any]:
        """
        Calculate altcoin season index.

        Altcoin season = when 75%+ of top 50 coins outperform Bitcoin over 90 days.

        Returns:
            Dictionary with altcoin season metrics
        """
        try:
            df = self.get_top_cryptos(limit=50)

            if df.empty or 'price_change_percentage_30d' not in df.columns:
                return {}

            # Get Bitcoin performance
            btc_perf = df[df['symbol'].str.upper() == 'BTC']['price_change_percentage_30d'].iloc[0] if len(df[df['symbol'].str.upper() == 'BTC']) > 0 else 0

            # Count altcoins outperforming BTC (excluding BTC itself)
            altcoins = df[df['symbol'].str.upper() != 'BTC']
            outperforming = (altcoins['price_change_percentage_30d'] > btc_perf).sum()
            total_alts = len(altcoins)

            altcoin_season_score = (outperforming / total_alts * 100) if total_alts > 0 else 0

            result = {
                'timestamp': datetime.now(),
                'altcoin_season_score': altcoin_season_score,
                'outperforming_count': outperforming,
                'total_tracked': total_alts,
                'btc_performance_30d': btc_perf,
                'is_altcoin_season': altcoin_season_score >= 75,
                'season_type': self._classify_season(altcoin_season_score)
            }

            self.logger.info(f"Altcoin season index: {altcoin_season_score:.1f}%")
            return result

        except Exception as e:
            self.logger.error(f"Failed to calculate altcoin season index: {e}")
            return {}

    def _classify_season(self, score: float) -> str:
        """Classify market season based on altcoin season score."""
        if score >= 75:
            return "Strong Altcoin Season"
        elif score >= 60:
            return "Moderate Altcoin Season"
        elif score >= 40:
            return "Neutral / Mixed"
        elif score >= 25:
            return "Bitcoin Season Forming"
        else:
            return "Strong Bitcoin Season"

    def get_market_concentration_metrics(self) -> Dict[str, float]:
        """
        Calculate market concentration metrics (Herfindahl-Hirschman Index, etc.).

        Returns:
            Dictionary with concentration metrics
        """
        try:
            df = self.get_top_cryptos(limit=100)

            if df.empty:
                return {}

            total_mcap = df['market_cap'].sum()
            df['market_share'] = df['market_cap'] / total_mcap

            # Herfindahl-Hirschman Index (HHI)
            hhi = (df['market_share'] ** 2).sum() * 10000

            # Concentration ratios
            cr1 = df.iloc[0]['market_share'] * 100  # Top 1
            cr4 = df.head(4)['market_share'].sum() * 100  # Top 4
            cr10 = df.head(10)['market_share'].sum() * 100  # Top 10

            result = {
                'timestamp': datetime.now(),
                'hhi_index': hhi,
                'concentration_ratio_1': cr1,
                'concentration_ratio_4': cr4,
                'concentration_ratio_10': cr10,
                'concentration_level': self._classify_concentration(hhi),
                'market_share_distribution_entropy': self._calculate_distribution_entropy(df['market_share'].values)
            }

            self.logger.info("Market concentration metrics calculated")
            return result

        except Exception as e:
            self.logger.error(f"Failed to calculate concentration metrics: {e}")
            return {}

    def _classify_concentration(self, hhi: float) -> str:
        """Classify market concentration based on HHI."""
        if hhi > 2500:
            return "Highly Concentrated"
        elif hhi > 1500:
            return "Moderately Concentrated"
        else:
            return "Unconcentrated / Competitive"

    def _calculate_distribution_entropy(self, shares: np.ndarray) -> float:
        """Calculate Shannon entropy of market share distribution."""
        shares = shares[shares > 0]
        entropy = -np.sum(shares * np.log2(shares))
        return entropy

    def get_comprehensive_market_metrics(self) -> Dict[str, Any]:
        """
        Get all market metrics in one call.

        Returns:
            Comprehensive dictionary of all metrics
        """
        try:
            self.logger.info("Collecting comprehensive market metrics...")

            metrics = {
                'timestamp': datetime.now(),
                'global_data': self.get_global_market_data(),
                'market_cap_segments': self.get_market_cap_segments(),
                'altcoin_season': self.get_altcoin_season_index(),
                'concentration': self.get_market_concentration_metrics(),
                'top_10': self.get_top10_detailed_data().to_dict('records') if not self.get_top10_detailed_data().empty else []
            }

            self.logger.info("Comprehensive market metrics collected successfully")
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get comprehensive market metrics: {e}")
            return {}


class CryptoMarketDataCache:
    """
    Cache for crypto market data to avoid excessive API calls.
    """

    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
        self.logger = get_logger("data_collectors.crypto_cache")

    def get(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < self.ttl:
                self.logger.debug(f"Cache hit for {key}")
                return data
            else:
                self.logger.debug(f"Cache expired for {key}")
                del self.cache[key]
        return None

    def set(self, key: str, data: Any):
        """Set cache data with timestamp."""
        self.cache[key] = (data, datetime.now())
        self.logger.debug(f"Cached {key}")

    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        self.logger.info("Cache cleared")


# Convenience function
def get_crypto_market_collector(api_key: Optional[str] = None) -> CryptoMarketDominanceCollector:
    """Get crypto market dominance collector instance."""
    return CryptoMarketDominanceCollector(api_key=api_key)
