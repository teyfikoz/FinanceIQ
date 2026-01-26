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

from utils.data_quality import DataQuality

try:
    from utils.tradingview_bridge import TradingViewBridge
    _TV_BRIDGE_AVAILABLE = True
except Exception:
    TradingViewBridge = None  # type: ignore
    _TV_BRIDGE_AVAILABLE = False

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
        self.cache_meta = {}
        self.last_api_call = {}
        self.min_api_interval = 2  # Minimum 2 seconds between API calls
        self.tv_bridge = TradingViewBridge() if _TV_BRIDGE_AVAILABLE else None

    def get_stock_data(self, symbol, period="5d", use_fallback=True, interval=None):
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
        interval_key = interval or "1d"
        cache_key = f"{symbol}_{period}_{interval_key}"
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
            hist = ticker.history(period=period, interval=interval) if interval else ticker.history(period=period)

            if not hist.empty:
                try:
                    info = ticker.info
                except:
                    info = self._get_fallback_info(symbol)

                # Cache the result
                fetched_ts = time.time()
                self.cache[cache_key] = (fetched_ts, (hist, info))
                self.cache_meta[cache_key] = {
                    "provider": "yfinance",
                    "fetched_at": fetched_ts,
                }
                logger.info(f"Successfully fetched real data for {symbol}")
                return hist, info, "yfinance"

        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {str(e)[:100]}")

        # Fallback to synthetic data
        if use_fallback:
            logger.info(f"Using fallback data for {symbol}")
            return self._generate_fallback_data(symbol, period, interval=interval)

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

    def _generate_fallback_data(self, symbol, period, interval=None):
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

        if interval and interval != "1d":
            # Basic intraday expansion for UI continuity (synthetic, not real market data)
            hist = self._expand_to_intraday(hist, interval)

        return hist, info, "fallback"

    def _expand_to_intraday(self, daily_df: pd.DataFrame, interval: str) -> pd.DataFrame:
        """Expand daily bars to synthetic intraday bars for fallback data."""
        freq_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "60m": "60min",
            "90m": "90min",
            "1h": "60min",
            "4h": "4H",
        }
        freq = freq_map.get(interval, "60min")
        expanded = []
        for idx, row in daily_df.iterrows():
            intraday_index = pd.date_range(start=idx, periods=6, freq=freq)
            base = row['Close']
            noise = np.random.normal(0, 0.002, len(intraday_index))
            prices = base * (1 + noise).cumprod()
            day_df = pd.DataFrame({
                'Open': prices,
                'High': prices * (1 + np.random.uniform(0, 0.002, len(prices))),
                'Low': prices * (1 - np.random.uniform(0, 0.002, len(prices))),
                'Close': prices,
                'Volume': np.random.randint(10000, 100000, len(prices))
            }, index=intraday_index)
            expanded.append(day_df)
        return pd.concat(expanded).sort_index()

    def _make_quality(self, status: str, provider: str, fetched_ts: float, cache_age: float = None, note: str = None) -> DataQuality:
        return DataQuality(
            status=status,
            provider=provider,
            fetched_at=datetime.fromtimestamp(fetched_ts),
            cache_age_s=cache_age,
            note=note,
        )

    def get_stock_data_with_meta(self, symbol, period="5d", interval=None, use_fallback=True, source_preference: str = "auto"):
        """
        Get stock data with data-quality metadata (non-breaking helper).

        Returns:
            tuple: (historical_data, info_dict, DataQuality)
        """
        interval_key = interval or "1d"
        cache_key = f"{symbol}_{period}_{interval_key}"

        # Cache check
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                provider = self.cache_meta.get(cache_key, {}).get("provider", "unknown")
                quality = self._make_quality(
                    status="cache",
                    provider=provider,
                    fetched_ts=cached_time,
                    cache_age=time.time() - cached_time,
                    note="served from in-memory cache",
                )
                return cached_data[0], cached_data[1], quality

        # Optional TradingView bridge
        if source_preference in ("auto", "tradingview") and self.tv_bridge and self.tv_bridge.available():
            try:
                tv_df = self.tv_bridge.fetch_ohlc(symbol, timeframe=interval or "D", limit=200)
                if tv_df is not None and not tv_df.empty:
                    info = self._get_fallback_info(symbol)
                    fetched_ts = time.time()
                    self.cache[cache_key] = (fetched_ts, (tv_df, info))
                    self.cache_meta[cache_key] = {
                        "provider": "tradingview",
                        "fetched_at": fetched_ts,
                    }
                    quality = self._make_quality("real", "tradingview", fetched_ts)
                    return tv_df, info, quality
            except Exception as e:
                logger.warning(f"TradingView bridge failed: {str(e)[:120]}")

        # Default yfinance path
        hist, info, source = self.get_stock_data(symbol, period=period, use_fallback=use_fallback, interval=interval)
        fetched_ts = time.time()

        if source == "yfinance":
            quality = self._make_quality("real", "yfinance", fetched_ts)
        elif source == "cache":
            provider = self.cache_meta.get(cache_key, {}).get("provider", "yfinance")
            cache_time = self.cache.get(cache_key, (fetched_ts,))[0] if cache_key in self.cache else fetched_ts
            quality = self._make_quality("cache", provider, cache_time, cache_age=time.time() - cache_time)
        else:
            quality = self._make_quality("fallback", "synthetic", fetched_ts, note="synthetic baseline data")

        return hist, info, quality

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
