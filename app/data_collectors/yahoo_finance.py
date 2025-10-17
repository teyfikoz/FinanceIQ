from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

from .base import BaseCollector


class YahooFinanceCollector(BaseCollector):
    """Collector for Yahoo Finance traditional market data."""

    def __init__(self):
        super().__init__("yahoo_finance")
        self.rate_limit_delay = 0.5  # Conservative rate limiting

        # Default symbols to track
        self.default_symbols = {
            # Equity Indices
            "^GSPC": "S&P 500",
            "^IXIC": "NASDAQ Composite",
            "^DJI": "Dow Jones Industrial Average",
            "^RUT": "Russell 2000",
            "^VIX": "CBOE Volatility Index",

            # Currencies
            "DX-Y.NYB": "US Dollar Index",
            "EURUSD=X": "EUR/USD",
            "GBPUSD=X": "GBP/USD",
            "USDJPY=X": "USD/JPY",

            # Commodities
            "GC=F": "Gold Futures",
            "SI=F": "Silver Futures",
            "CL=F": "Crude Oil Futures",

            # Bonds
            "^TNX": "10-Year Treasury Yield",
            "^IRX": "3-Month Treasury Bill",
            "^TYX": "30-Year Treasury Yield",

            # ETFs
            "SPY": "SPDR S&P 500 ETF",
            "QQQ": "Invesco QQQ ETF",
            "GLD": "SPDR Gold Shares",
            "TLT": "iShares 20+ Year Treasury ETF",
            "VTI": "Vanguard Total Stock Market ETF"
        }

    def collect_data(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect current market data for specified symbols."""
        if symbols is None:
            symbols = list(self.default_symbols.keys())

        try:
            # Create comma-separated string for yfinance
            symbols_str = " ".join(symbols)
            tickers = yf.Tickers(symbols_str)

            market_data = []
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    hist = ticker.history(period="2d")  # Get last 2 days for comparison

                    if not hist.empty:
                        latest = hist.iloc[-1]
                        prev = hist.iloc[-2] if len(hist) > 1 else latest

                        # Calculate daily change
                        price_change = latest['Close'] - prev['Close']
                        price_change_pct = (price_change / prev['Close']) * 100 if prev['Close'] != 0 else 0

                        record = {
                            "symbol": symbol,
                            "name": self.default_symbols.get(symbol, symbol),
                            "current_price": latest['Close'],
                            "open": latest['Open'],
                            "high": latest['High'],
                            "low": latest['Low'],
                            "volume": latest['Volume'],
                            "previous_close": prev['Close'],
                            "price_change": price_change,
                            "price_change_percentage": price_change_pct,
                            "market_cap": info.get('marketCap'),
                            "pe_ratio": info.get('trailingPE'),
                            "dividend_yield": info.get('dividendYield'),
                            "timestamp": latest.name.isoformat() if hasattr(latest.name, 'isoformat') else datetime.utcnow().isoformat()
                        }
                        market_data.append(record)

                except Exception as e:
                    self.logger.warning(f"Failed to get data for {symbol}", error=str(e))
                    continue

            result = {
                "market_data": market_data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "yahoo_finance"
            }

            if self.validate_data(result):
                self.log_collection_result(True, len(market_data))
                return result
            else:
                self.log_collection_result(False, error_message="Data validation failed")
                return {}

        except Exception as e:
            self.log_collection_result(False, error_message=str(e))
            return {}

    def get_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: str = "^GSPC",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical data for a specific symbol."""
        try:
            ticker = yf.Ticker(symbol)

            # Download historical data
            hist = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval=interval
            )

            if hist.empty:
                self.logger.warning(f"No historical data for {symbol}")
                return pd.DataFrame()

            # Reset index to get date as column
            df = hist.reset_index()
            df["symbol"] = symbol
            df["timestamp"] = pd.to_datetime(df["Date"])

            # Rename columns to match our schema
            df = df.rename(columns={
                "Open": "open_price",
                "High": "high_price",
                "Low": "low_price",
                "Close": "close_price",
                "Volume": "volume"
            })

            # Select relevant columns
            df = df[["symbol", "timestamp", "open_price", "high_price", "low_price", "close_price", "volume"]]
            df = df.sort_values("timestamp").reset_index(drop=True)

            self.logger.info(f"Collected {len(df)} historical records for {symbol}")
            return df

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}", error=str(e))
            return pd.DataFrame()

    def get_options_data(self, symbol: str) -> Dict[str, Any]:
        """Get options data for a symbol (useful for volatility analysis)."""
        try:
            ticker = yf.Ticker(symbol)

            # Get option expiration dates
            expirations = ticker.options
            if not expirations:
                return {}

            # Get options for the nearest expiration
            nearest_exp = expirations[0]
            opt_chain = ticker.option_chain(nearest_exp)

            calls = opt_chain.calls
            puts = opt_chain.puts

            # Calculate implied volatility statistics
            call_iv_mean = calls['impliedVolatility'].mean() if not calls.empty else 0
            put_iv_mean = puts['impliedVolatility'].mean() if not puts.empty else 0

            return {
                "symbol": symbol,
                "expiration_date": nearest_exp,
                "call_iv_mean": call_iv_mean,
                "put_iv_mean": put_iv_mean,
                "call_volume": calls['volume'].sum() if not calls.empty else 0,
                "put_volume": puts['volume'].sum() if not puts.empty else 0,
                "put_call_ratio": puts['volume'].sum() / calls['volume'].sum() if not calls.empty and calls['volume'].sum() > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get options data for {symbol}", error=str(e))
            return {}

    def get_economic_calendar_events(self) -> List[Dict[str, Any]]:
        """Get upcoming economic events (mock implementation - Yahoo doesn't provide this directly)."""
        # This would typically require a different data source
        # For now, return empty list or integrate with another service
        return []

    def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector performance data."""
        try:
            sector_etfs = {
                "XLK": "Technology",
                "XLF": "Financial",
                "XLV": "Health Care",
                "XLE": "Energy",
                "XLI": "Industrial",
                "XLP": "Consumer Staples",
                "XLY": "Consumer Discretionary",
                "XLU": "Utilities",
                "XLB": "Materials",
                "XLRE": "Real Estate",
                "XLC": "Communication Services"
            }

            sector_data = []
            for etf, sector in sector_etfs.items():
                try:
                    ticker = yf.Ticker(etf)
                    hist = ticker.history(period="5d")

                    if not hist.empty:
                        latest = hist.iloc[-1]
                        first = hist.iloc[0]

                        change_5d = ((latest['Close'] - first['Close']) / first['Close']) * 100

                        sector_data.append({
                            "sector": sector,
                            "etf_symbol": etf,
                            "current_price": latest['Close'],
                            "change_5d": change_5d,
                            "volume": latest['Volume']
                        })

                except Exception as e:
                    self.logger.warning(f"Failed to get data for sector ETF {etf}", error=str(e))
                    continue

            return {
                "sector_performance": sector_data,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error("Failed to get sector performance", error=str(e))
            return {}

    def transform_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Transform Yahoo Finance data to standardized DataFrame."""
        if "market_data" not in data:
            return pd.DataFrame()

        market_data = data["market_data"]

        records = []
        for item in market_data:
            record = {
                "symbol": item["symbol"],
                "timestamp": datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")) if isinstance(item["timestamp"], str) else item["timestamp"],
                "open_price": item.get("open", 0),
                "high_price": item.get("high", 0),
                "low_price": item.get("low", 0),
                "close_price": item.get("current_price", 0),
                "volume": item.get("volume", 0),
                "market_cap": item.get("market_cap"),
                "source": "yahoo_finance"
            }
            records.append(record)

        df = pd.DataFrame(records)
        return df

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate Yahoo Finance data."""
        if not super().validate_data(data):
            return False

        # Check if market_data exists and is not empty
        if "market_data" not in data or not data["market_data"]:
            self.logger.warning("No market data in response")
            return False

        # Check if we have valid price data
        for item in data["market_data"]:
            if not item.get("current_price") or item.get("current_price") <= 0:
                self.logger.warning(f"Invalid price for {item.get('symbol', 'unknown')}")
                return False

        return True