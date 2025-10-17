"""Alpha Vantage API integration for news sentiment and market data"""
import os
import requests
import streamlit as st
from typing import Dict, List, Optional


class AlphaVantageAPI:
    """Alpha Vantage API wrapper"""

    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = 'https://www.alphavantage.co/query'

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_news_sentiment(_self, symbol: str, limit: int = 10) -> Optional[Dict]:
        """Get news sentiment for a symbol

        Args:
            symbol: Stock symbol
            limit: Number of news items to return

        Returns:
            Dictionary with sentiment data or None if error
        """
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol,
                'apikey': _self.api_key,
                'limit': limit
            }

            response = requests.get(_self.base_url, params=params, timeout=10)
            data = response.json()

            if 'feed' in data and len(data['feed']) > 0:
                sentiments = []
                news_items = []

                for item in data['feed'][:limit]:
                    # Get ticker sentiment if available
                    ticker_sentiment = next(
                        (ts for ts in item.get('ticker_sentiment', []) if ts['ticker'] == symbol),
                        None
                    )

                    sentiment_score = float(item.get('overall_sentiment_score', 0))
                    sentiments.append(sentiment_score)

                    news_items.append({
                        'headline': item['title'],
                        'summary': item.get('summary', '')[:200] + '...' if len(item.get('summary', '')) > 200 else item.get('summary', ''),
                        'source': item['source'],
                        'url': item.get('url', ''),
                        'time': item['time_published'],
                        'sentiment_label': item.get('overall_sentiment_label', 'Neutral'),
                        'sentiment_score': sentiment_score,
                        'ticker_sentiment_score': float(ticker_sentiment['ticker_sentiment_score']) if ticker_sentiment else sentiment_score,
                        'ticker_sentiment_label': ticker_sentiment['ticker_sentiment_label'] if ticker_sentiment else item.get('overall_sentiment_label', 'Neutral')
                    })

                # Calculate overall sentiment (convert from -1,1 to 0,100)
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                overall_sentiment = (avg_sentiment + 1) * 50  # Convert to 0-100 scale

                return {
                    'overall_sentiment': overall_sentiment,
                    'sentiment_label': _self._get_sentiment_label(overall_sentiment),
                    'news_count': len(news_items),
                    'news_items': news_items
                }

            return None

        except Exception as e:
            print(f"Alpha Vantage API error: {str(e)}")
            return None

    @st.cache_data(ttl=3600)
    def search_symbol(_self, keywords: str) -> List[Dict]:
        """Search for symbols

        Args:
            keywords: Search keywords

        Returns:
            List of matching symbols
        """
        try:
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': keywords,
                'apikey': _self.api_key
            }

            response = requests.get(_self.base_url, params=params, timeout=10)
            data = response.json()

            if 'bestMatches' in data:
                return [
                    {
                        'symbol': match['1. symbol'],
                        'name': match['2. name'],
                        'type': match['3. type'],
                        'region': match['4. region'],
                        'currency': match['8. currency']
                    }
                    for match in data['bestMatches'][:10]
                ]

            return []

        except Exception as e:
            print(f"Alpha Vantage search error: {str(e)}")
            return []

    @staticmethod
    def _get_sentiment_label(score: float) -> str:
        """Convert sentiment score to label"""
        if score >= 60:
            return 'Bullish'
        elif score >= 55:
            return 'Somewhat-Bullish'
        elif score >= 45:
            return 'Neutral'
        elif score >= 40:
            return 'Somewhat-Bearish'
        else:
            return 'Bearish'
