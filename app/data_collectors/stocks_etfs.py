"""
Global Stocks & ETFs Data Collector
Dünya çapında hisse senetleri ve ETF'ler için veri toplayıcı
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
import time

from .base import BaseCollector
from app.core.config import settings


class StocksETFsCollector(BaseCollector):
    """Global hisse senetleri ve ETF'ler için veri toplayıcı."""

    def __init__(self):
        super().__init__("stocks_etfs")
        self.alpha_vantage_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
        self.rate_limit_delay = 0.5

        # Popüler hisse senetleri ve ETF'ler
        self.popular_stocks = {
            # Tech Giants
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc.",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "META": "Meta Platforms Inc.",
            "NVDA": "NVIDIA Corporation",
            "NFLX": "Netflix Inc.",

            # Major Banks
            "JPM": "JPMorgan Chase & Co.",
            "BAC": "Bank of America Corp.",
            "WFC": "Wells Fargo & Company",

            # Consumer
            "KO": "The Coca-Cola Company",
            "PG": "Procter & Gamble Co.",
            "JNJ": "Johnson & Johnson",
            "WMT": "Walmart Inc.",

            # Energy
            "XOM": "Exxon Mobil Corporation",
            "CVX": "Chevron Corporation"
        }

        self.popular_etfs = {
            # Broad Market ETFs
            "SPY": "SPDR S&P 500 ETF Trust",
            "QQQ": "Invesco QQQ Trust",
            "IWM": "iShares Russell 2000 ETF",
            "VTI": "Vanguard Total Stock Market ETF",
            "VOO": "Vanguard S&P 500 ETF",

            # Sector ETFs
            "XLK": "Technology Select Sector SPDR Fund",
            "XLF": "Financial Select Sector SPDR Fund",
            "XLE": "Energy Select Sector SPDR Fund",
            "XLV": "Health Care Select Sector SPDR Fund",
            "XLI": "Industrial Select Sector SPDR Fund",

            # International
            "EEM": "iShares MSCI Emerging Markets ETF",
            "VEA": "Vanguard FTSE Developed Markets ETF",
            "EFA": "iShares MSCI EAFE ETF",

            # Bonds
            "TLT": "iShares 20+ Year Treasury Bond ETF",
            "AGG": "iShares Core U.S. Aggregate Bond ETF",

            # Commodities
            "GLD": "SPDR Gold Shares",
            "SLV": "iShares Silver Trust",
            "USO": "United States Oil Fund",

            # Growth/Innovation
            "ARKK": "ARK Innovation ETF",
            "ARKQ": "ARK Autonomous Technology & Robotics ETF",
            "VGT": "Vanguard Information Technology ETF"
        }

        # Global indices
        self.global_indices = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones Industrial Average",
            "^IXIC": "NASDAQ Composite",
            "^RUT": "Russell 2000",
            "^VIX": "CBOE Volatility Index",
            "^FTSE": "FTSE 100",
            "^GDAXI": "DAX",
            "^FCHI": "CAC 40",
            "^N225": "Nikkei 225",
            "^HSI": "Hang Seng Index",
            "XU100.IS": "BIST 100"
        }

    def fetch_stock_data_yf(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "1y"
    ) -> Dict[str, Any]:
        """Yahoo Finance'dan hisse senedi verisi çek."""
        try:
            ticker = yf.Ticker(symbol)

            # Tarihlere göre veya periyoda göre veri çek
            if start_date and end_date:
                hist = ticker.history(start=start_date, end=end_date)
            else:
                hist = ticker.history(period=period)

            if hist.empty:
                return {"error": f"No data found for symbol {symbol}"}

            # Ticker bilgilerini al
            info = ticker.info

            # OHLCV verilerini hazırla
            ohlcv_data = []
            for date, row in hist.iterrows():
                ohlcv_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0
                })

            # Temel bilgiler
            current_price = float(hist["Close"].iloc[-1])
            previous_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close) * 100 if previous_close != 0 else 0

            result = {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "current_price": current_price,
                "price_change": price_change,
                "price_change_percent": price_change_pct,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "volume": int(hist["Volume"].iloc[-1]) if not pd.isna(hist["Volume"].iloc[-1]) else 0,
                "avg_volume": info.get("averageVolume"),
                "ohlcv_data": ohlcv_data,
                "data_source": "yahoo_finance",
                "last_updated": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Successfully fetched data for {symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to fetch data for {symbol}", error=str(e))
            return {"error": str(e)}

    def fetch_stock_data_av(
        self,
        symbol: str,
        interval: str = "daily"
    ) -> Dict[str, Any]:
        """Alpha Vantage'dan hisse senedi verisi çek."""
        if not self.alpha_vantage_key:
            return {"error": "Alpha Vantage API key not configured"}

        try:
            # Time series function'ını belirle
            if interval == "daily":
                function = "TIME_SERIES_DAILY"
            elif interval == "weekly":
                function = "TIME_SERIES_WEEKLY"
            elif interval == "monthly":
                function = "TIME_SERIES_MONTHLY"
            else:
                function = "TIME_SERIES_DAILY"

            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
                "outputsize": "compact"
            }

            url = "https://www.alphavantage.co/query"
            response = self._make_request(url, params=params)
            data = response.json()

            # Time series anahtarını bul
            time_series_key = None
            for key in data.keys():
                if "Time Series" in key:
                    time_series_key = key
                    break

            if not time_series_key:
                return {"error": "No time series data found"}

            time_series = data[time_series_key]

            # OHLCV verilerini hazırla
            ohlcv_data = []
            for date_str, values in list(time_series.items())[:100]:  # Son 100 gün
                ohlcv_data.append({
                    "date": date_str,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"])
                })

            # Son fiyat bilgileri
            latest_data = list(time_series.values())[0]
            current_price = float(latest_data["4. close"])

            result = {
                "symbol": symbol,
                "current_price": current_price,
                "ohlcv_data": sorted(ohlcv_data, key=lambda x: x["date"]),
                "data_source": "alpha_vantage",
                "last_updated": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Successfully fetched Alpha Vantage data for {symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to fetch Alpha Vantage data for {symbol}", error=str(e))
            return {"error": str(e)}

    def get_technical_indicators_av(
        self,
        symbol: str,
        indicator: str = "RSI",
        interval: str = "daily",
        time_period: int = 14
    ) -> Dict[str, Any]:
        """Alpha Vantage'dan teknik göstergeler çek."""
        if not self.alpha_vantage_key:
            return {"error": "Alpha Vantage API key not configured"}

        try:
            params = {
                "function": indicator,
                "symbol": symbol,
                "interval": interval,
                "time_period": time_period,
                "series_type": "close",
                "apikey": self.alpha_vantage_key
            }

            url = "https://www.alphavantage.co/query"
            response = self._make_request(url, params=params)
            data = response.json()

            # Technical Analysis anahtarını bul
            tech_key = f"Technical Analysis: {indicator}"
            if tech_key not in data:
                return {"error": f"No {indicator} data found"}

            tech_data = data[tech_key]

            # Son 30 günlük veriyi al
            indicator_data = []
            for date_str, values in list(tech_data.items())[:30]:
                indicator_data.append({
                    "date": date_str,
                    "value": float(list(values.values())[0])
                })

            result = {
                "symbol": symbol,
                "indicator": indicator,
                "current_value": indicator_data[0]["value"] if indicator_data else None,
                "data": sorted(indicator_data, key=lambda x: x["date"]),
                "data_source": "alpha_vantage",
                "last_updated": datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            self.logger.error(f"Failed to fetch {indicator} for {symbol}", error=str(e))
            return {"error": str(e)}

    def get_multiple_stocks_data(
        self,
        symbols: List[str],
        period: str = "6mo"
    ) -> Dict[str, Any]:
        """Birden fazla hisse senedi için veri çek."""
        try:
            stocks_data = {}

            for symbol in symbols:
                data = self.fetch_stock_data_yf(symbol, period=period)
                if "error" not in data:
                    stocks_data[symbol] = data
                else:
                    self.logger.warning(f"Failed to fetch data for {symbol}: {data['error']}")

            result = {
                "stocks_data": stocks_data,
                "total_symbols": len(symbols),
                "successful_symbols": len(stocks_data),
                "last_updated": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Fetched data for {len(stocks_data)}/{len(symbols)} symbols")
            return result

        except Exception as e:
            self.logger.error("Failed to fetch multiple stocks data", error=str(e))
            return {"error": str(e)}

    def search_symbol(self, query: str) -> List[Dict[str, str]]:
        """Sembol arama fonksiyonu."""
        try:
            # Önce popüler listelerden ara
            results = []
            query_upper = query.upper()

            # Popüler hisse senetlerinde ara
            for symbol, name in self.popular_stocks.items():
                if query_upper in symbol or query_upper in name.upper():
                    results.append({
                        "symbol": symbol,
                        "name": name,
                        "type": "Stock"
                    })

            # Popüler ETF'lerde ara
            for symbol, name in self.popular_etfs.items():
                if query_upper in symbol or query_upper in name.upper():
                    results.append({
                        "symbol": symbol,
                        "name": name,
                        "type": "ETF"
                    })

            # Global endekslerde ara
            for symbol, name in self.global_indices.items():
                if query_upper in symbol.replace("^", "") or query_upper in name.upper():
                    results.append({
                        "symbol": symbol,
                        "name": name,
                        "type": "Index"
                    })

            # Eğer sonuç yoksa, Yahoo Finance'dan doğrudan dene
            if not results and len(query) >= 2:
                try:
                    ticker = yf.Ticker(query.upper())
                    info = ticker.info
                    if info and "longName" in info:
                        results.append({
                            "symbol": query.upper(),
                            "name": info["longName"],
                            "type": info.get("quoteType", "Unknown")
                        })
                except:
                    pass

            return results[:10]  # En fazla 10 sonuç

        except Exception as e:
            self.logger.error(f"Failed to search symbol {query}", error=str(e))
            return []

    def get_trending_stocks(self) -> Dict[str, Any]:
        """Trend olan hisse senetlerini getir."""
        try:
            # Yahoo Finance trending tickers (ücretsiz yöntem)
            trending_symbols = [
                "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN",
                "META", "NVDA", "SPY", "QQQ", "BTC-USD"
            ]

            trending_data = {}
            for symbol in trending_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")

                    if not hist.empty:
                        current = hist["Close"].iloc[-1]
                        previous = hist["Close"].iloc[-2] if len(hist) > 1 else current
                        change_pct = ((current - previous) / previous) * 100

                        trending_data[symbol] = {
                            "price": float(current),
                            "change_percent": float(change_pct),
                            "volume": int(hist["Volume"].iloc[-1]) if not pd.isna(hist["Volume"].iloc[-1]) else 0
                        }
                except:
                    continue

            result = {
                "trending_stocks": trending_data,
                "last_updated": datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            self.logger.error("Failed to get trending stocks", error=str(e))
            return {"error": str(e)}

    def collect_data(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Ana veri toplama fonksiyonu."""
        if symbols is None:
            # Default symbols: Top stocks + ETFs
            symbols = list(self.popular_stocks.keys())[:10] + list(self.popular_etfs.keys())[:10]

        return self.get_multiple_stocks_data(symbols)

    def get_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: str = "SPY"
    ) -> pd.DataFrame:
        """Tarihsel veri al."""
        try:
            data = self.fetch_stock_data_yf(symbol, start_date, end_date)

            if "error" not in data and "ohlcv_data" in data:
                df = pd.DataFrame(data["ohlcv_data"])
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}", error=str(e))
            return pd.DataFrame()

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Veri doğrulama."""
        if not super().validate_data(data):
            return False

        # Stocks data kontrolü
        if "stocks_data" in data:
            if not data["stocks_data"]:
                self.logger.warning("No stocks data found")
                return False

            # Her hisse için fiyat kontrolü
            for symbol, stock_data in data["stocks_data"].items():
                if not stock_data.get("current_price") or stock_data.get("current_price") <= 0:
                    self.logger.warning(f"Invalid price for {symbol}")
                    return False

        return True