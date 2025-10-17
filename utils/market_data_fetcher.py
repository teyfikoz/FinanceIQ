#!/usr/bin/env python3
"""
Enhanced market data fetcher with multiple fallback mechanisms
Handles rate limiting and provides cached/static fallback data
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

class MarketDataFetcher:
    """
    Smart market data fetcher with multiple fallback strategies:
    1. Try yfinance (primary)
    2. Use cached data if available
    3. Use static baseline data (for Turkish stocks)
    """

    # Static baseline data for Turkish stocks (updated 2025)
    TURKISH_STOCK_BASELINE = {
        "THYAO.IS": {"price": 285.50, "name": "Turkish Airlines"},
        "AKBNK.IS": {"price": 58.40, "name": "Akbank"},
        "BIMAS.IS": {"price": 525.00, "name": "BIM Stores"},
        "KCHOL.IS": {"price": 189.20, "name": "Koc Holding"},
        "TUPRS.IS": {"price": 168.70, "name": "Tupras"},
        "TCELL.IS": {"price": 95.80, "name": "Turkcell"},
        "MPARK.IS": {"price": 42.50, "name": "MLP Health Services"},
        "ISCTR.IS": {"price": 8.95, "name": "Is Investment"},
        "AKSA.IS": {"price": 15.20, "name": "Aksa Acrylic"},
        "ASTOR.IS": {"price": 25.30, "name": "Astor Energy"},
        "GARAN.IS": {"price": 118.50, "name": "Garanti BBVA"},
        "EREGL.IS": {"price": 52.30, "name": "Eregli Demir Celik"},
        "ASELS.IS": {"price": 78.90, "name": "Aselsan"},
        "PETKM.IS": {"price": 12.40, "name": "Petkim"},
    }

    def __init__(self, cache_duration=300):
        """Initialize with cache duration in seconds (default 5 minutes)"""
        self.cache_duration = cache_duration
        self.cache = {}
        self.last_api_call = {}
        self.min_api_interval = 2  # Minimum 2 seconds between API calls

    def get_stock_data(self, symbol, period="5d", use_fallback=True):
        """
        Get stock data with intelligent fallback

        Args:
            symbol: Stock symbol (e.g., "THYAO.IS")
            period: Time period ("1d", "5d", "1mo", etc.)
            use_fallback: Whether to use fallback data on failure

        Returns:
            tuple: (historical_data, info_dict, data_source)
        """
        # Check cache first
        cache_key = f"{symbol}_{period}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                logger.info(f"Using cached data for {symbol}")
                return cached_data + ("cache",)

        # Rate limiting: wait if needed
        if symbol in self.last_api_call:
            elapsed = time.time() - self.last_api_call[symbol]
            if elapsed < self.min_api_interval:
                time.sleep(self.min_api_interval - elapsed)

        # Try fetching real data
        try:
            self.last_api_call[symbol] = time.time()
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if not hist.empty:
                try:
                    info = ticker.info
                except:
                    info = self._get_fallback_info(symbol)

                # Cache the result
                self.cache[cache_key] = (time.time(), (hist, info))
                logger.info(f"Successfully fetched real data for {symbol}")
                return hist, info, "yfinance"

        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {str(e)[:100]}")

        # Fallback to synthetic data
        if use_fallback:
            logger.info(f"Using fallback data for {symbol}")
            return self._generate_fallback_data(symbol, period)

        return pd.DataFrame(), {}, "none"

    def _get_fallback_info(self, symbol):
        """Get fallback info for a symbol"""
        if symbol in self.TURKISH_STOCK_BASELINE:
            baseline = self.TURKISH_STOCK_BASELINE[symbol]
            return {
                'longName': baseline['name'],
                'symbol': symbol,
                'currency': 'TRY',
                'marketCap': 0,
                'currentPrice': baseline['price']
            }
        return {
            'longName': symbol,
            'symbol': symbol,
            'currency': 'USD',
            'marketCap': 0
        }

    def _generate_fallback_data(self, symbol, period):
        """
        Generate realistic fallback data based on baseline prices
        """
        # Get baseline price
        if symbol in self.TURKISH_STOCK_BASELINE:
            baseline = self.TURKISH_STOCK_BASELINE[symbol]
            base_price = baseline['price']
        else:
            base_price = 100.0

        # Determine number of days
        period_days = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365
        }
        days = period_days.get(period, 30)

        # Generate dates
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=days, freq='D')

        # Generate realistic price movement
        np.random.seed(hash(symbol) % 2**32)
        returns = np.random.normal(0.001, 0.02, days)  # 0.1% daily return, 2% volatility
        prices = base_price * np.cumprod(1 + returns)

        # Create OHLCV data
        hist = pd.DataFrame({
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
            'High': prices * (1 + np.random.uniform(0, 0.02, days)),
            'Low': prices * (1 - np.random.uniform(0, 0.02, days)),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, days)
        }, index=dates)

        info = self._get_fallback_info(symbol)

        return hist, info, "fallback"

    def get_multiple_stocks(self, symbols, period="5d"):
        """
        Get data for multiple stocks efficiently

        Returns:
            dict: {symbol: (hist, info, source)}
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_data(symbol, period)
        return results

    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
        logger.info("Cache cleared")

# Global instance
_fetcher = None

def get_market_fetcher():
    """Get or create global market data fetcher instance"""
    global _fetcher
    if _fetcher is None:
        _fetcher = MarketDataFetcher(cache_duration=300)
    return _fetcher
