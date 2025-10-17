"""CoinGecko API integration for crypto market data"""
import requests
import streamlit as st
from typing import Dict, List, Optional


class CoinGeckoAPI:
    """CoinGecko API wrapper"""

    def __init__(self):
        self.base_url = 'https://api.coingecko.com/api/v3'

    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_crypto_prices(_self, ids: List[str] = None) -> Optional[Dict]:
        """Get cryptocurrency prices

        Args:
            ids: List of coin ids (default: bitcoin, ethereum)

        Returns:
            Dictionary with price data
        """
        if ids is None:
            ids = ['bitcoin', 'ethereum', 'tether', 'binancecoin', 'solana']

        try:
            url = f'{_self.base_url}/simple/price'
            params = {
                'ids': ','.join(ids),
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            return data

        except Exception as e:
            print(f"CoinGecko API error: {str(e)}")
            return None

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_global_crypto_data(_self) -> Optional[Dict]:
        """Get global cryptocurrency market data

        Returns:
            Dictionary with global crypto market data
        """
        try:
            url = f'{_self.base_url}/global'
            response = requests.get(url, timeout=10)
            data = response.json()

            if 'data' in data:
                global_data = data['data']
                return {
                    'total_market_cap': global_data.get('total_market_cap', {}).get('usd', 0),
                    'total_volume': global_data.get('total_volume', {}).get('usd', 0),
                    'market_cap_change_24h': global_data.get('market_cap_change_percentage_24h_usd', 0),
                    'btc_dominance': global_data.get('market_cap_percentage', {}).get('btc', 0),
                    'eth_dominance': global_data.get('market_cap_percentage', {}).get('eth', 0),
                    'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                    'markets': global_data.get('markets', 0),
                    'updated_at': global_data.get('updated_at', 0)
                }

            return None

        except Exception as e:
            print(f"CoinGecko global data error: {str(e)}")
            return None

    @st.cache_data(ttl=300)
    def get_top_cryptocurrencies(_self, limit: int = 20) -> Optional[List[Dict]]:
        """Get top cryptocurrencies by market cap

        Args:
            limit: Number of cryptocurrencies to return

        Returns:
            List of top cryptocurrencies
        """
        try:
            url = f'{_self.base_url}/coins/markets'
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h,7d'
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data:
                return [
                    {
                        'id': coin.get('id'),
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name'),
                        'current_price': coin.get('current_price'),
                        'market_cap': coin.get('market_cap'),
                        'market_cap_rank': coin.get('market_cap_rank'),
                        'total_volume': coin.get('total_volume'),
                        'price_change_24h': coin.get('price_change_percentage_24h'),
                        'price_change_7d': coin.get('price_change_percentage_7d_in_currency'),
                        'circulating_supply': coin.get('circulating_supply'),
                        'total_supply': coin.get('total_supply'),
                        'ath': coin.get('ath'),
                        'ath_change_percentage': coin.get('ath_change_percentage')
                    }
                    for coin in data
                ]

            return None

        except Exception as e:
            print(f"CoinGecko top coins error: {str(e)}")
            return None

    @st.cache_data(ttl=3600)
    def get_coin_history(_self, coin_id: str, days: int = 30) -> Optional[Dict]:
        """Get historical data for a cryptocurrency

        Args:
            coin_id: Coin ID (e.g., 'bitcoin')
            days: Number of days of history

        Returns:
            Dictionary with historical data
        """
        try:
            url = f'{_self.base_url}/coins/{coin_id}/market_chart'
            params = {
                'vs_currency': 'usd',
                'days': days
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'prices' in data:
                return {
                    'timestamps': [item[0] for item in data['prices']],
                    'prices': [item[1] for item in data['prices']],
                    'market_caps': [item[1] for item in data.get('market_caps', [])],
                    'volumes': [item[1] for item in data.get('total_volumes', [])]
                }

            return None

        except Exception as e:
            print(f"CoinGecko history error: {str(e)}")
            return None

    @st.cache_data(ttl=3600)
    def get_trending_coins(_self) -> Optional[List[Dict]]:
        """Get trending coins

        Returns:
            List of trending coins
        """
        try:
            url = f'{_self.base_url}/search/trending'
            response = requests.get(url, timeout=10)
            data = response.json()

            if 'coins' in data:
                return [
                    {
                        'id': coin['item'].get('id'),
                        'symbol': coin['item'].get('symbol'),
                        'name': coin['item'].get('name'),
                        'market_cap_rank': coin['item'].get('market_cap_rank'),
                        'price_btc': coin['item'].get('price_btc'),
                        'score': coin['item'].get('score')
                    }
                    for coin in data['coins']
                ]

            return None

        except Exception as e:
            print(f"CoinGecko trending error: {str(e)}")
            return None
