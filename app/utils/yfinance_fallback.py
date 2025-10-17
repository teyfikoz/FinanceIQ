"""
yfinance Fallback Utility
Provides robust data fetching with automatic fallbacks for empty/failed requests.
"""

import yfinance as yf
import pandas as pd
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Proxy mappings for futures that often fail
FUTURES_PROXIES = {
    "GC=F": "XAUUSD=X",  # Gold
    "SI=F": "XAGUSD=X",  # Silver
    "CL=F": "BZ=F",      # Crude Oil
}


def safe_yf_download(symbol: str, period: str = "1d", interval: str = "1d") -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Safely download yfinance data with automatic fallbacks.

    Fallback chain:
    1. Try original parameters
    2. Try period=5d, interval=1d
    3. Try period=1mo, interval=1d
    4. Try proxy symbol (for futures)

    Args:
        symbol: Ticker symbol
        period: Data period (e.g., "1d", "5d", "1mo")
        interval: Data interval (e.g., "1m", "1d")

    Returns:
        Tuple of (DataFrame, warning_message)
        - DataFrame may be empty if all attempts fail
        - warning_message is None if successful, otherwise contains user-friendly message
    """
    warning = None

    # Attempt 1: Original parameters
    try:
        logger.info(f"Fetching {symbol} with period={period}, interval={interval}")
        df = yf.download(symbol, period=period, interval=interval, progress=False)

        if not df.empty:
            logger.info(f"Successfully fetched {symbol} with original parameters")
            return df, None
        else:
            logger.warning(f"Empty DataFrame for {symbol} with period={period}, interval={interval}")
    except Exception as e:
        logger.warning(f"yfinance download failed for {symbol}: {e}")

    # Attempt 2: Fallback to 5-day period with daily interval
    if period == "1d" and interval == "1m":
        try:
            logger.info(f"Trying fallback: period=5d, interval=1d for {symbol}")
            df = yf.download(symbol, period="5d", interval="1d", progress=False)

            if not df.empty:
                warning = f"ℹ️ Using 5-day data for {symbol} (1-day intraday unavailable)"
                logger.info(f"Fallback successful: 5d data for {symbol}")
                return df, warning
        except Exception as e:
            logger.warning(f"5-day fallback failed for {symbol}: {e}")

    # Attempt 3: Fallback to 1-month period
    try:
        logger.info(f"Trying fallback: period=1mo, interval=1d for {symbol}")
        df = yf.download(symbol, period="1mo", interval="1d", progress=False)

        if not df.empty:
            warning = f"ℹ️ Using 1-month data for {symbol} (shorter periods unavailable)"
            logger.info(f"Fallback successful: 1mo data for {symbol}")
            return df, warning
    except Exception as e:
        logger.warning(f"1-month fallback failed for {symbol}: {e}")

    # Attempt 4: Try proxy symbol for known futures
    if symbol in FUTURES_PROXIES:
        proxy = FUTURES_PROXIES[symbol]
        try:
            logger.info(f"Trying proxy {proxy} for {symbol}")
            df = yf.download(proxy, period=period, interval=interval, progress=False)

            if not df.empty:
                warning = f"ℹ️ Using proxy {proxy} for {symbol}"
                logger.info(f"Proxy successful: {proxy} data for {symbol}")
                return df, warning
        except Exception as e:
            logger.warning(f"Proxy {proxy} failed for {symbol}: {e}")

    # All attempts failed
    warning = f"⚠️ No data available for {symbol}. Please try a different symbol or time period."
    logger.error(f"All fallback attempts failed for {symbol}")
    return pd.DataFrame(), warning
