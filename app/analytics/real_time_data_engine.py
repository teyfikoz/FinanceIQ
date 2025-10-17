import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
import requests
from datetime import datetime, timedelta
import time
import threading
import queue
import warnings
warnings.filterwarnings('ignore')

class RealTimeDataEngine:
    """Real-time data engine for live market data"""

    def __init__(self):
        self.data_cache = {}
        self.last_update = {}
        self.update_intervals = {
            'quotes': 30,  # 30 seconds for quotes
            'options': 300,  # 5 minutes for options
            'fundamentals': 3600,  # 1 hour for fundamentals
            'news': 600  # 10 minutes for news
        }
        self.data_queue = queue.Queue()
        self.is_market_open = self.check_market_hours()

    def check_market_hours(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        # Simple market hours check (9:30 AM - 4:00 PM ET, weekdays)
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= now <= market_close

    def get_real_time_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol"""
        try:
            ticker = yf.Ticker(symbol)

            # Get real-time data
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")

            if not hist.empty:
                latest = hist.iloc[-1]
                prev_close = info.get('previousClose', latest['Close'])

                quote = {
                    'symbol': symbol,
                    'price': latest['Close'],
                    'change': latest['Close'] - prev_close,
                    'change_percent': ((latest['Close'] - prev_close) / prev_close) * 100,
                    'volume': latest['Volume'],
                    'high': hist['High'].max(),
                    'low': hist['Low'].min(),
                    'open': hist['Open'].iloc[0],
                    'previous_close': prev_close,
                    'timestamp': hist.index[-1],
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 0),
                    'dividend_yield': info.get('dividendYield', 0),
                    'volume_avg': info.get('averageVolume', 0),
                    'is_real_time': self.is_market_open
                }

                # Cache the data
                self.data_cache[symbol] = quote
                self.last_update[symbol] = datetime.now()

                return quote
            else:
                return self.get_cached_quote(symbol)

        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            return self.get_cached_quote(symbol)

    def get_cached_quote(self, symbol: str) -> Dict[str, Any]:
        """Get cached quote if real-time fails"""
        if symbol in self.data_cache:
            cached = self.data_cache[symbol].copy()
            cached['is_real_time'] = False
            cached['cache_age'] = (datetime.now() - self.last_update[symbol]).seconds
            return cached
        return {'symbol': symbol, 'error': 'No data available'}

    def get_intraday_data(self, symbol: str, interval: str = "1m") -> pd.DataFrame:
        """Get intraday data for charting"""
        try:
            ticker = yf.Ticker(symbol)

            # Get different periods based on interval
            period_map = {
                "1m": "1d",
                "5m": "5d",
                "15m": "1mo",
                "1h": "3mo"
            }

            period = period_map.get(interval, "1d")
            data = ticker.history(period=period, interval=interval)

            if not data.empty:
                # Add technical indicators
                data = self.add_technical_indicators(data)
                return data
            else:
                return pd.DataFrame()

        except Exception as e:
            print(f"Error fetching intraday data for {symbol}: {e}")
            return pd.DataFrame()

    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical indicators to price data"""
        if len(data) < 20:
            return data

        # Moving averages
        data['MA_20'] = data['Close'].rolling(window=20).mean()
        data['MA_50'] = data['Close'].rolling(window=50).mean()

        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        data['BB_Middle'] = data['Close'].rolling(window=20).mean()
        data['BB_Std'] = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (data['BB_Std'] * 2)
        data['BB_Lower'] = data['BB_Middle'] - (data['BB_Std'] * 2)

        # MACD
        exp1 = data['Close'].ewm(span=12).mean()
        exp2 = data['Close'].ewm(span=26).mean()
        data['MACD'] = exp1 - exp2
        data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']

        return data

    def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview with major indices"""
        indices = {
            'S&P 500': '^GSPC',
            'Dow Jones': '^DJI',
            'NASDAQ': '^IXIC',
            'Russell 2000': '^RUT',
            'VIX': '^VIX'
        }

        overview = {}

        for name, symbol in indices.items():
            quote = self.get_real_time_quote(symbol)
            if 'error' not in quote:
                overview[name] = {
                    'price': quote['price'],
                    'change': quote['change'],
                    'change_percent': quote['change_percent'],
                    'symbol': symbol
                }

        # Add sector performance
        sectors = self.get_sector_performance()
        overview['sectors'] = sectors

        # Add market sentiment indicators
        overview['sentiment'] = self.get_market_sentiment()

        return overview

    def get_sector_performance(self) -> Dict[str, Dict]:
        """Get sector ETF performance"""
        sector_etfs = {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financials': 'XLF',
            'Energy': 'XLE',
            'Consumer Discretionary': 'XLY',
            'Industrials': 'XLI',
            'Materials': 'XLB',
            'Utilities': 'XLU',
            'Consumer Staples': 'XLP',
            'Real Estate': 'XLRE',
            'Communications': 'XLC'
        }

        sector_performance = {}

        for sector, etf in sector_etfs.items():
            quote = self.get_real_time_quote(etf)
            if 'error' not in quote:
                sector_performance[sector] = {
                    'change_percent': quote['change_percent'],
                    'price': quote['price'],
                    'symbol': etf
                }

        return sector_performance

    def get_market_sentiment(self) -> Dict[str, Any]:
        """Calculate market sentiment indicators"""
        try:
            # VIX for fear/greed
            vix_quote = self.get_real_time_quote('^VIX')
            vix_level = vix_quote.get('price', 20)

            # Classify VIX levels
            if vix_level < 15:
                fear_greed = "Greed"
                sentiment_score = 80
            elif vix_level < 20:
                fear_greed = "Neutral"
                sentiment_score = 50
            elif vix_level < 30:
                fear_greed = "Fear"
                sentiment_score = 30
            else:
                fear_greed = "Extreme Fear"
                sentiment_score = 10

            # Market breadth (simplified)
            spy_quote = self.get_real_time_quote('SPY')
            qqq_quote = self.get_real_time_quote('QQQ')
            iwm_quote = self.get_real_time_quote('IWM')

            breadth_score = 50
            if all(q.get('change_percent', 0) > 0 for q in [spy_quote, qqq_quote, iwm_quote]):
                breadth_score = 75
            elif all(q.get('change_percent', 0) < 0 for q in [spy_quote, qqq_quote, iwm_quote]):
                breadth_score = 25

            return {
                'fear_greed_index': fear_greed,
                'sentiment_score': sentiment_score,
                'vix_level': vix_level,
                'market_breadth': breadth_score,
                'overall_sentiment': 'Bullish' if sentiment_score > 60 else 'Bearish' if sentiment_score < 40 else 'Neutral'
            }

        except Exception as e:
            print(f"Error calculating market sentiment: {e}")
            return {
                'fear_greed_index': "Unknown",
                'sentiment_score': 50,
                'vix_level': 0,
                'market_breadth': 50,
                'overall_sentiment': 'Neutral'
            }

    def get_economic_calendar(self) -> List[Dict]:
        """Get upcoming economic events (simplified)"""
        # This would normally connect to an economic calendar API
        # For now, return sample upcoming events
        today = datetime.now()

        sample_events = [
            {
                'date': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '08:30',
                'event': 'GDP Growth Rate',
                'importance': 'High',
                'forecast': '2.1%',
                'previous': '2.0%'
            },
            {
                'date': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
                'time': '14:00',
                'event': 'Federal Funds Rate',
                'importance': 'High',
                'forecast': '5.25%',
                'previous': '5.25%'
            },
            {
                'date': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
                'time': '08:30',
                'event': 'Non-Farm Payrolls',
                'importance': 'High',
                'forecast': '200K',
                'previous': '187K'
            }
        ]

        return sample_events

    def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get news sentiment for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news

            if news:
                # Simple sentiment analysis based on title keywords
                positive_words = ['up', 'gain', 'rise', 'bull', 'strong', 'beat', 'growth', 'positive']
                negative_words = ['down', 'fall', 'bear', 'weak', 'miss', 'decline', 'negative', 'loss']

                sentiment_scores = []
                recent_news = []

                for article in news[:5]:  # Last 5 articles
                    title = article.get('title', '').lower()

                    pos_count = sum(1 for word in positive_words if word in title)
                    neg_count = sum(1 for word in negative_words if word in title)

                    if pos_count > neg_count:
                        sentiment = 'Positive'
                        score = 1
                    elif neg_count > pos_count:
                        sentiment = 'Negative'
                        score = -1
                    else:
                        sentiment = 'Neutral'
                        score = 0

                    sentiment_scores.append(score)
                    recent_news.append({
                        'title': article.get('title', ''),
                        'publisher': article.get('publisher', ''),
                        'link': article.get('link', ''),
                        'publish_time': article.get('providerPublishTime', 0),
                        'sentiment': sentiment
                    })

                avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0

                return {
                    'overall_sentiment': 'Positive' if avg_sentiment > 0.2 else 'Negative' if avg_sentiment < -0.2 else 'Neutral',
                    'sentiment_score': avg_sentiment,
                    'article_count': len(recent_news),
                    'recent_news': recent_news
                }

        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")

        return {
            'overall_sentiment': 'Neutral',
            'sentiment_score': 0,
            'article_count': 0,
            'recent_news': []
        }

    def start_real_time_updates(self, symbols: List[str], callback_func=None):
        """Start real-time data updates for given symbols"""
        def update_loop():
            while True:
                try:
                    for symbol in symbols:
                        if self.should_update(symbol):
                            quote = self.get_real_time_quote(symbol)

                            if callback_func:
                                callback_func(symbol, quote)

                            # Add to queue for processing
                            self.data_queue.put({
                                'type': 'quote_update',
                                'symbol': symbol,
                                'data': quote,
                                'timestamp': datetime.now()
                            })

                    # Update market overview
                    market_data = self.get_market_overview()
                    self.data_queue.put({
                        'type': 'market_update',
                        'data': market_data,
                        'timestamp': datetime.now()
                    })

                    # Sleep based on market hours
                    sleep_time = 30 if self.is_market_open else 300  # 30s during market, 5min after hours
                    time.sleep(sleep_time)

                except Exception as e:
                    print(f"Error in real-time update loop: {e}")
                    time.sleep(60)  # Wait 1 minute on error

        # Start update thread
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

        return update_thread

    def should_update(self, symbol: str) -> bool:
        """Check if symbol should be updated based on last update time"""
        if symbol not in self.last_update:
            return True

        last_update = self.last_update[symbol]
        now = datetime.now()

        # Update more frequently during market hours
        update_interval = 30 if self.is_market_open else 300

        return (now - last_update).seconds >= update_interval

    def get_options_chain(self, symbol: str) -> Dict[str, Any]:
        """Get options chain data"""
        try:
            ticker = yf.Ticker(symbol)
            expiration_dates = ticker.options

            if not expiration_dates:
                return {'error': 'No options data available'}

            # Get nearest expiration
            nearest_exp = expiration_dates[0]
            options_chain = ticker.option_chain(nearest_exp)

            calls = options_chain.calls
            puts = options_chain.puts

            # Calculate implied volatility average
            avg_iv_calls = calls['impliedVolatility'].mean() if not calls.empty else 0
            avg_iv_puts = puts['impliedVolatility'].mean() if not puts.empty else 0

            return {
                'symbol': symbol,
                'expiration_date': nearest_exp,
                'calls_count': len(calls),
                'puts_count': len(puts),
                'avg_iv_calls': avg_iv_calls,
                'avg_iv_puts': avg_iv_puts,
                'avg_iv_overall': (avg_iv_calls + avg_iv_puts) / 2,
                'calls_data': calls.to_dict('records') if not calls.empty else [],
                'puts_data': puts.to_dict('records') if not puts.empty else []
            }

        except Exception as e:
            print(f"Error fetching options chain for {symbol}: {e}")
            return {'error': f'Failed to fetch options data: {str(e)}'}

    def get_analyst_ratings(self, symbol: str) -> Dict[str, Any]:
        """Get analyst ratings and price targets"""
        try:
            ticker = yf.Ticker(symbol)

            # Get recommendations
            recommendations = ticker.recommendations

            if recommendations is not None and not recommendations.empty:
                latest = recommendations.iloc[-1]

                return {
                    'symbol': symbol,
                    'strong_buy': latest.get('strongBuy', 0),
                    'buy': latest.get('buy', 0),
                    'hold': latest.get('hold', 0),
                    'sell': latest.get('sell', 0),
                    'strong_sell': latest.get('strongSell', 0),
                    'consensus': self.calculate_consensus_rating(latest),
                    'last_updated': latest.name if hasattr(latest, 'name') else datetime.now()
                }

        except Exception as e:
            print(f"Error fetching analyst ratings for {symbol}: {e}")

        return {
            'symbol': symbol,
            'strong_buy': 0,
            'buy': 0,
            'hold': 0,
            'sell': 0,
            'strong_sell': 0,
            'consensus': 'No Data',
            'last_updated': datetime.now()
        }

    def calculate_consensus_rating(self, ratings_row) -> str:
        """Calculate consensus rating from individual ratings"""
        total = ratings_row.get('strongBuy', 0) + ratings_row.get('buy', 0) + ratings_row.get('hold', 0) + ratings_row.get('sell', 0) + ratings_row.get('strongSell', 0)

        if total == 0:
            return 'No Rating'

        # Weighted average (5=Strong Buy, 1=Strong Sell)
        weighted_sum = (ratings_row.get('strongBuy', 0) * 5 +
                       ratings_row.get('buy', 0) * 4 +
                       ratings_row.get('hold', 0) * 3 +
                       ratings_row.get('sell', 0) * 2 +
                       ratings_row.get('strongSell', 0) * 1)

        avg_rating = weighted_sum / total

        if avg_rating >= 4.5:
            return 'Strong Buy'
        elif avg_rating >= 3.5:
            return 'Buy'
        elif avg_rating >= 2.5:
            return 'Hold'
        elif avg_rating >= 1.5:
            return 'Sell'
        else:
            return 'Strong Sell'

# Global instance for use across the platform
real_time_engine = RealTimeDataEngine()

if __name__ == "__main__":
    # Test the real-time engine
    engine = RealTimeDataEngine()

    # Test quote
    quote = engine.get_real_time_quote('AAPL')
    print("AAPL Quote:", quote)

    # Test market overview
    market = engine.get_market_overview()
    print("Market Overview:", market)

    # Test intraday data
    intraday = engine.get_intraday_data('AAPL', '5m')
    print("Intraday data shape:", intraday.shape)