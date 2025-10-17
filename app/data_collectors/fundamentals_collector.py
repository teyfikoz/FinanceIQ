"""
Fundamentals Collector Module
Fetches income statement and fundamental data from FMP, Alpha Vantage, and yfinance.
"""

import os
from typing import Dict, List, Optional, Any
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta
import logging
import time

logger = logging.getLogger(__name__)

# Try to import cache service (will be created next)
try:
    from app.services.cache import cache_get, cache_set
except ImportError:
    # Fallback to no caching
    def cache_get(key): return None
    def cache_set(key, value, ttl): pass


class FundamentalsCollector:
    """Collect fundamental financial data from multiple sources."""

    def __init__(self):
        self.fmp_api_key = os.getenv('FMP_API_KEY')
        self.av_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Global-Liquidity-Dashboard/1.0'})

    def get_income_statement(self,
                              ticker: str,
                              period: str = "annual",
                              limit: int = 4) -> pd.DataFrame:
        """
        Get income statement data for a ticker.

        Args:
            ticker: Stock ticker symbol
            period: 'annual' or 'quarterly'
            limit: Number of periods to fetch

        Returns:
            DataFrame with canonical columns
        """
        # Check cache first
        cache_key = f"income:{ticker}:{period}:{limit}"
        cached = cache_get(cache_key)
        if cached is not None:
            logger.info(f"Cache hit for {cache_key}")
            return cached

        # Try FMP first
        df = self._fetch_from_fmp(ticker, period, limit)

        # Fallback to Alpha Vantage
        if df.empty and self.av_api_key:
            logger.info(f"FMP failed, trying Alpha Vantage for {ticker}")
            df = self._fetch_from_alpha_vantage(ticker, period)

        # Final fallback to yfinance
        if df.empty:
            logger.info(f"Alpha Vantage failed, trying yfinance for {ticker}")
            df = self._fetch_from_yfinance(ticker, period)

        # Calculate YoY deltas
        if not df.empty:
            df = self._add_yoy_deltas(df)

        # Cache result (6 hours)
        if not df.empty:
            cache_set(cache_key, df, ttl=6 * 3600)

        return df

    def get_company_name(self, ticker: str) -> str:
        """Get company name for a ticker."""
        cache_key = f"company_name:{ticker}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # Try yfinance first (fastest)
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            name = info.get('longName') or info.get('shortName') or ticker
            cache_set(cache_key, name, ttl=24 * 3600)
            return name
        except Exception as e:
            logger.warning(f"Failed to get company name from yfinance: {e}")

        # Fallback to FMP
        if self.fmp_api_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
                params = {'apikey': self.fmp_api_key}
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        name = data[0].get('companyName', ticker)
                        cache_set(cache_key, name, ttl=24 * 3600)
                        return name
            except Exception as e:
                logger.warning(f"Failed to get company name from FMP: {e}")

        return ticker

    def _fetch_from_fmp(self, ticker: str, period: str, limit: int) -> pd.DataFrame:
        """Fetch from Financial Modeling Prep API."""
        if not self.fmp_api_key:
            return pd.DataFrame()

        try:
            url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}"
            params = {
                'period': period,
                'limit': limit,
                'apikey': self.fmp_api_key
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list):
                    return self._normalize_fmp_data(data)
            else:
                logger.warning(f"FMP API error {response.status_code} for {ticker}")

        except Exception as e:
            logger.error(f"FMP fetch error for {ticker}: {e}")

        return pd.DataFrame()

    def _fetch_from_alpha_vantage(self, ticker: str, period: str) -> pd.DataFrame:
        """Fetch from Alpha Vantage API."""
        if not self.av_api_key:
            return pd.DataFrame()

        try:
            function = "INCOME_STATEMENT"
            url = "https://www.alphavantage.co/query"
            params = {
                'function': function,
                'symbol': ticker,
                'apikey': self.av_api_key
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                reports_key = 'annualReports' if period == 'annual' else 'quarterlyReports'

                if reports_key in data:
                    return self._normalize_av_data(data[reports_key])
            else:
                logger.warning(f"Alpha Vantage API error {response.status_code} for {ticker}")

            # Rate limit protection
            time.sleep(12)  # AV free tier: 5 calls/minute

        except Exception as e:
            logger.error(f"Alpha Vantage fetch error for {ticker}: {e}")

        return pd.DataFrame()

    def _fetch_from_yfinance(self, ticker: str, period: str) -> pd.DataFrame:
        """Fetch from yfinance."""
        try:
            stock = yf.Ticker(ticker)

            if period == 'annual':
                financials = stock.financials  # Annual by default
            else:
                financials = stock.quarterly_financials

            if financials is not None and not financials.empty:
                return self._normalize_yf_data(financials)

        except Exception as e:
            logger.error(f"yfinance fetch error for {ticker}: {e}")

        return pd.DataFrame()

    def _normalize_fmp_data(self, data: List[Dict]) -> pd.DataFrame:
        """Normalize FMP data to canonical format."""
        records = []

        for item in data:
            record = {
                'revenue': item.get('revenue', 0),
                'cost_of_revenue': item.get('costOfRevenue', 0),
                'gross_profit': item.get('grossProfit', 0),
                'operating_income': item.get('operatingIncome', 0),
                'rd_expense': item.get('researchAndDevelopmentExpenses', 0),
                'sga_expense': item.get('sellingGeneralAndAdministrativeExpenses', 0),
                'other_operating_expense': item.get('otherExpenses', 0),
                'tax_expense': item.get('incomeTaxExpense', 0),
                'interest_expense': item.get('interestExpense', 0),
                'net_income': item.get('netIncome', 0),
                'period_end': item.get('date', 'N/A')
            }
            records.append(record)

        return pd.DataFrame(records)

    def _normalize_av_data(self, reports: List[Dict]) -> pd.DataFrame:
        """Normalize Alpha Vantage data to canonical format."""
        records = []

        for report in reports:
            record = {
                'revenue': self._parse_av_value(report.get('totalRevenue', 0)),
                'cost_of_revenue': self._parse_av_value(report.get('costOfRevenue', 0)),
                'gross_profit': self._parse_av_value(report.get('grossProfit', 0)),
                'operating_income': self._parse_av_value(report.get('operatingIncome', 0)),
                'rd_expense': self._parse_av_value(report.get('researchAndDevelopment', 0)),
                'sga_expense': self._parse_av_value(report.get('sellingGeneralAndAdministrative', 0)),
                'other_operating_expense': 0,  # Not directly available
                'tax_expense': self._parse_av_value(report.get('incomeTaxExpense', 0)),
                'interest_expense': self._parse_av_value(report.get('interestExpense', 0)),
                'net_income': self._parse_av_value(report.get('netIncome', 0)),
                'period_end': report.get('fiscalDateEnding', 'N/A')
            }
            records.append(record)

        return pd.DataFrame(records)

    def _normalize_yf_data(self, financials: pd.DataFrame) -> pd.DataFrame:
        """Normalize yfinance data to canonical format."""
        records = []

        # yfinance returns transposed (dates as columns)
        for col in financials.columns:
            data = financials[col]

            record = {
                'revenue': self._safe_get(data, ['Total Revenue', 'TotalRevenue'], 0),
                'cost_of_revenue': self._safe_get(data, ['Cost Of Revenue', 'CostOfRevenue'], 0),
                'gross_profit': self._safe_get(data, ['Gross Profit', 'GrossProfit'], 0),
                'operating_income': self._safe_get(data, ['Operating Income', 'OperatingIncome'], 0),
                'rd_expense': self._safe_get(data, ['Research And Development', 'ResearchAndDevelopment'], 0),
                'sga_expense': self._safe_get(data, ['Selling General And Administration',
                                                       'SellingGeneralAndAdministration'], 0),
                'other_operating_expense': 0,
                'tax_expense': self._safe_get(data, ['Tax Provision', 'TaxProvision'], 0),
                'interest_expense': self._safe_get(data, ['Interest Expense', 'InterestExpense'], 0),
                'net_income': self._safe_get(data, ['Net Income', 'NetIncome'], 0),
                'period_end': col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
            }
            records.append(record)

        return pd.DataFrame(records)

    def _safe_get(self, series: pd.Series, keys: List[str], default: Any) -> Any:
        """Safely get value from series with multiple possible keys."""
        for key in keys:
            if key in series.index:
                val = series[key]
                if pd.notna(val):
                    return float(val)
        return default

    def _parse_av_value(self, value: Any) -> float:
        """Parse Alpha Vantage value (can be string or number)."""
        if value in [None, 'None', '']:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _add_yoy_deltas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Year-over-Year delta columns."""
        if len(df) < 2:
            return df

        for col in ['revenue', 'gross_profit', 'operating_income', 'net_income']:
            if col in df.columns:
                df[f'{col}_yoy'] = df[col].pct_change(periods=-1) * 100  # Reverse order (newest first)

        return df


# Singleton instance
_collector = None


def get_income_statement(ticker: str, period: str = "annual", limit: int = 4) -> pd.DataFrame:
    """Get income statement (module-level function)."""
    global _collector
    if _collector is None:
        _collector = FundamentalsCollector()
    return _collector.get_income_statement(ticker, period, limit)


def get_company_name(ticker: str) -> str:
    """Get company name (module-level function)."""
    global _collector
    if _collector is None:
        _collector = FundamentalsCollector()
    return _collector.get_company_name(ticker)
