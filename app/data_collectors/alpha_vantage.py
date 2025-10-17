from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import requests
import numpy as np

from .base import BaseCollector
from app.core.config import settings


class AlphaVantageCollector(BaseCollector):
    """Alpha Vantage collector for detailed stock analysis."""

    def __init__(self):
        super().__init__("alpha_vantage")
        self.base_url = "https://www.alphavantage.co/query"
        self.api_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
        self.rate_limit_delay = 12.0  # Alpha Vantage free tier: 5 calls per minute

        # Turkish stocks with .IS suffix for Yahoo Finance compatibility
        self.turkish_stocks = [
            "THYAO.IS",  # Türk Hava Yolları
            "AKBNK.IS",  # Akbank
            "GARAN.IS",  # Garanti BBVA
            "SISE.IS",   # Şişe Cam
            "TCELL.IS",  # Turkcell
            "BIMAS.IS",  # BİM
            "KOZAL.IS",  # Koza Altın
            "KRDMD.IS",  # Kardemir
            "SAHOL.IS",  # Sabancı Holding
            "ISCTR.IS"   # İş Bankası
        ]

    def collect_data(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect stock data using Alpha Vantage API."""
        if not self.api_key:
            self.logger.warning("Alpha Vantage API key not configured")
            return self._get_sample_stock_data()

        if symbols is None:
            # For Turkish stocks, we'll use Yahoo Finance instead
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

        try:
            stock_data = []

            for symbol in symbols[:5]:  # Limit to 5 to stay within rate limits
                try:
                    # Get quote data
                    quote_data = self._get_quote(symbol)
                    if quote_data:
                        stock_data.append(quote_data)

                except Exception as e:
                    self.logger.warning(f"Failed to get data for {symbol}", error=str(e))
                    continue

            result = {
                "stock_data": stock_data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alpha_vantage"
            }

            if self.validate_data(result):
                self.log_collection_result(True, len(stock_data))
                return result
            else:
                return self._get_sample_stock_data()

        except Exception as e:
            self.logger.error("Failed to collect Alpha Vantage data", error=str(e))
            return self._get_sample_stock_data()

    def _get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }

        response = self._make_request(self.base_url, params=params)
        data = response.json()

        if "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "symbol": symbol,
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
                "volume": int(quote.get("06. volume", 0)),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "open": float(quote.get("02. open", 0)),
                "previous_close": float(quote.get("08. previous close", 0))
            }

        return {}

    def get_technical_indicators(self, symbol: str, indicator: str = "RSI") -> Dict[str, Any]:
        """Get technical indicators for a symbol."""
        if not self.api_key:
            return self._get_sample_technical_data(symbol, indicator)

        try:
            params = {
                "function": indicator,
                "symbol": symbol,
                "interval": "daily",
                "time_period": 14,
                "series_type": "close",
                "apikey": self.api_key
            }

            response = self._make_request(self.base_url, params=params)
            data = response.json()

            if f"Technical Analysis: {indicator}" in data:
                technical_data = data[f"Technical Analysis: {indicator}"]

                # Get last 30 days of data
                recent_data = dict(list(technical_data.items())[:30])

                return {
                    "symbol": symbol,
                    "indicator": indicator,
                    "data": recent_data,
                    "current_value": list(recent_data.values())[0] if recent_data else None,
                    "timestamp": datetime.utcnow().isoformat()
                }

            return self._get_sample_technical_data(symbol, indicator)

        except Exception as e:
            self.logger.error(f"Failed to get {indicator} for {symbol}", error=str(e))
            return self._get_sample_technical_data(symbol, indicator)

    def get_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: str = "AAPL",
        interval: str = "daily"
    ) -> pd.DataFrame:
        """Get historical data for a symbol."""
        if not self.api_key:
            return self._generate_sample_historical_data(symbol, start_date, end_date)

        try:
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "full",
                "apikey": self.api_key
            }

            response = self._make_request(self.base_url, params=params)
            data = response.json()

            if "Time Series (Daily)" in data:
                time_series = data["Time Series (Daily)"]

                records = []
                for date_str, values in time_series.items():
                    date = pd.to_datetime(date_str)
                    if start_date <= date <= end_date:
                        records.append({
                            "timestamp": date,
                            "symbol": symbol,
                            "open_price": float(values["1. open"]),
                            "high_price": float(values["2. high"]),
                            "low_price": float(values["3. low"]),
                            "close_price": float(values["4. close"]),
                            "volume": int(values["5. volume"])
                        })

                df = pd.DataFrame(records)
                df = df.sort_values("timestamp").reset_index(drop=True)

                self.logger.info(f"Collected {len(df)} historical records for {symbol}")
                return df

            return self._generate_sample_historical_data(symbol, start_date, end_date)

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}", error=str(e))
            return self._generate_sample_historical_data(symbol, start_date, end_date)

    def _get_sample_stock_data(self) -> Dict[str, Any]:
        """Generate sample stock data when API is not available."""
        sample_stocks = [
            {
                "symbol": "AAPL",
                "price": 175.84,
                "change": 2.15,
                "change_percent": "1.24",
                "volume": 45687231,
                "high": 176.50,
                "low": 173.20,
                "open": 174.10,
                "previous_close": 173.69
            },
            {
                "symbol": "MSFT",
                "price": 378.85,
                "change": -1.23,
                "change_percent": "-0.32",
                "volume": 18234567,
                "high": 380.15,
                "low": 376.80,
                "open": 379.45,
                "previous_close": 380.08
            },
            {
                "symbol": "GOOGL",
                "price": 140.93,
                "change": 0.87,
                "change_percent": "0.62",
                "volume": 23456789,
                "high": 142.10,
                "low": 139.85,
                "open": 140.25,
                "previous_close": 140.06
            },
            {
                "symbol": "TSLA",
                "price": 248.5,
                "change": 8.75,
                "change_percent": "3.65",
                "volume": 67891234,
                "high": 251.20,
                "low": 242.30,
                "open": 243.85,
                "previous_close": 239.75
            }
        ]

        return {
            "stock_data": sample_stocks,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "sample_data",
            "note": "Using sample data - Alpha Vantage API key not configured"
        }

    def _get_sample_technical_data(self, symbol: str, indicator: str) -> Dict[str, Any]:
        """Generate sample technical indicator data."""
        # Generate realistic sample data based on indicator type
        if indicator == "RSI":
            current_value = np.random.uniform(30, 70)
        elif indicator == "MACD":
            current_value = np.random.uniform(-2, 2)
        else:
            current_value = np.random.uniform(0, 100)

        # Generate 30 days of sample data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        sample_data = {}

        for i, date in enumerate(dates):
            # Add some trend and noise
            trend = np.sin(i * 0.2) * 10
            noise = np.random.normal(0, 5)
            value = current_value + trend + noise

            if indicator == "RSI":
                value = max(0, min(100, value))  # RSI bounds

            sample_data[date.strftime("%Y-%m-%d")] = {indicator: str(round(value, 2))}

        return {
            "symbol": symbol,
            "indicator": indicator,
            "data": sample_data,
            "current_value": current_value,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Sample data - Alpha Vantage API key not configured"
        }

    def _generate_sample_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Generate realistic sample historical data."""
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # Start with a base price
        base_price = 100.0
        if symbol == "AAPL":
            base_price = 175.0
        elif symbol == "MSFT":
            base_price = 380.0
        elif symbol == "GOOGL":
            base_price = 140.0
        elif symbol == "TSLA":
            base_price = 250.0

        records = []
        current_price = base_price

        for date in dates:
            # Generate realistic OHLCV data
            daily_change = np.random.normal(0, 0.02)  # 2% daily volatility
            current_price *= (1 + daily_change)

            # Generate intraday range
            daily_range = abs(np.random.normal(0, 0.015)) * current_price
            high = current_price + daily_range / 2
            low = current_price - daily_range / 2

            # Open price (based on previous close with gap)
            gap = np.random.normal(0, 0.005)
            open_price = current_price * (1 + gap)

            # Volume (correlated with price movement)
            base_volume = 25000000
            volume_multiplier = 1 + abs(daily_change) * 5
            volume = int(base_volume * volume_multiplier * np.random.uniform(0.5, 1.5))

            records.append({
                "timestamp": date,
                "symbol": symbol,
                "open_price": round(open_price, 2),
                "high_price": round(high, 2),
                "low_price": round(low, 2),
                "close_price": round(current_price, 2),
                "volume": volume
            })

        df = pd.DataFrame(records)
        return df

    def get_turkish_stocks_data(self) -> Dict[str, Any]:
        """Get Turkish stock data using Yahoo Finance symbols."""
        # This would typically be handled by the Yahoo Finance collector
        # but we provide the symbol mapping here

        turkish_stock_info = {
            "THYAO.IS": {"name": "Türk Hava Yolları", "sector": "Ulaştırma"},
            "AKBNK.IS": {"name": "Akbank", "sector": "Bankacılık"},
            "GARAN.IS": {"name": "Garanti BBVA", "sector": "Bankacılık"},
            "SISE.IS": {"name": "Şişe Cam", "sector": "Cam"},
            "TCELL.IS": {"name": "Turkcell", "sector": "Telekomünikasyon"},
            "BIMAS.IS": {"name": "BİM", "sector": "Perakende"},
            "KOZAL.IS": {"name": "Koza Altın", "sector": "Madencilik"},
            "KRDMD.IS": {"name": "Kardemir", "sector": "Demir-Çelik"},
            "SAHOL.IS": {"name": "Sabancı Holding", "sector": "Holding"},
            "ISCTR.IS": {"name": "İş Bankası", "sector": "Bankacılık"}
        }

        return {
            "turkish_stocks": turkish_stock_info,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Turkish stock symbols for Yahoo Finance integration"
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate Alpha Vantage data."""
        if not super().validate_data(data):
            return False

        if "stock_data" not in data or not data["stock_data"]:
            self.logger.warning("No stock data in response")
            return False

        # Check if we have valid price data
        for stock in data["stock_data"]:
            if not stock.get("price") or stock.get("price") <= 0:
                self.logger.warning(f"Invalid price for {stock.get('symbol', 'unknown')}")
                return False

        return True