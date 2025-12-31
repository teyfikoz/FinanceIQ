"""
yfinance Fallback Utility
Provides robust data fetching with automatic fallbacks for empty/failed requests.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Tuple, Optional, List

import pandas as pd
import yfinance as yf

from app.core.config import settings

try:
    from pandas_datareader import data as pdr
except Exception:
    pdr = None

logger = logging.getLogger(__name__)

# Proxy mappings for futures that often fail
FUTURES_PROXIES = {
    "GC=F": "XAUUSD=X",  # Gold
    "SI=F": "XAGUSD=X",  # Silver
    "CL=F": "BZ=F",      # Crude Oil
}


def _stooq_fallback_enabled() -> bool:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return getattr(settings, "ENABLE_STOOQ_FALLBACK", True)


def _period_to_dates(period: str) -> Tuple[datetime, datetime]:
    end = datetime.utcnow()
    period_map = {
        "1d": 1,
        "5d": 5,
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
        "10y": 3650,
    }

    if period == "ytd":
        start = datetime(end.year, 1, 1)
    elif period == "max":
        start = end - timedelta(days=365 * 20)
    else:
        start = end - timedelta(days=period_map.get(period, 365))

    return start, end


def _stooq_symbol_candidates(symbol: str) -> List[str]:
    if any(ch in symbol for ch in ("^", "=", "/")):
        return []

    base = symbol.replace("-", ".")
    candidates = []

    if "." not in base:
        candidates.append(f"{base}.US")
    candidates.append(base)

    if base != symbol:
        candidates.append(symbol)

    seen = set()
    ordered = []
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.upper()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)

    return ordered


def _stooq_download(symbol: str, period: str) -> Tuple[pd.DataFrame, Optional[str]]:
    if pdr is None:
        return pd.DataFrame(), None
    if not _stooq_fallback_enabled():
        return pd.DataFrame(), None

    start, end = _period_to_dates(period)

    for candidate in _stooq_symbol_candidates(symbol):
        try:
            df = pdr.DataReader(candidate, "stooq", start, end)
        except Exception as e:
            logger.warning(f"Stooq download failed for {candidate}: {e}")
            continue

        if df is None or df.empty:
            continue

        df = df.sort_index()
        if "Adj Close" not in df.columns and "Close" in df.columns:
            df["Adj Close"] = df["Close"]

        warning = f"ℹ️ Using Stooq fallback for {symbol} (daily data)"
        return df, warning

    return pd.DataFrame(), None


def safe_yf_download(symbol: str, period: str = "1d", interval: str = "1d") -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Safely download yfinance data with automatic fallbacks.

    Fallback chain:
    1. Try original parameters
    2. Try period=5d, interval=1d
    3. Try period=1mo, interval=1d
    4. Try proxy symbol (for futures)
    5. Try Stooq (daily only)

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

    # Attempt 5: Stooq fallback for daily data
    if interval == "1d":
        df, stooq_warning = _stooq_download(symbol, period)
        if not df.empty:
            return df, stooq_warning

    # All attempts failed
    warning = f"⚠️ No data available for {symbol}. Please try a different symbol or time period."
    logger.error(f"All fallback attempts failed for {symbol}")
    return pd.DataFrame(), warning
