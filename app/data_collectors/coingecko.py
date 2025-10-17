from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import time

from .base import BaseCollector
from app.core.config import settings


class CoinGeckoCollector(BaseCollector):
    """Collector for CoinGecko cryptocurrency data."""

    def __init__(self):
        super().__init__("coingecko")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = 1.2  # CoinGecko free tier: 50 calls/min

        # Popular cryptocurrencies to track
        self.default_coins = [
            "bitcoin", "ethereum", "binancecoin", "cardano", "solana",
            "polkadot", "dogecoin", "avalanche-2", "polygon", "chainlink"
        ]

        # Headers for API requests
        self.headers = {}
        if settings.COINGECKO_API_KEY:
            self.headers["x-cg-pro-api-key"] = settings.COINGECKO_API_KEY
            self.rate_limit_delay = 0.1  # Pro tier has higher limits

    def collect_data(self, coins: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect current market data for specified coins."""
        if coins is None:
            coins = self.default_coins

        try:
            # Get current market data
            coins_str = ",".join(coins)
            url = f"{self.base_url}/coins/markets"
            params = {
                "vs_currency": "usd",
                "ids": coins_str,
                "order": "market_cap_desc",
                "per_page": len(coins),
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "1h,24h,7d,30d"
            }

            response = self._make_request(url, params=params, headers=self.headers)
            market_data = response.json()

            # Get global crypto market data
            global_url = f"{self.base_url}/global"
            global_response = self._make_request(global_url, headers=self.headers)
            global_data = global_response.json()

            result = {
                "market_data": market_data,
                "global_data": global_data["data"] if "data" in global_data else {},
                "timestamp": datetime.utcnow().isoformat(),
                "source": "coingecko"
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
        coin_id: str = "bitcoin",
        interval: str = "daily"
    ) -> pd.DataFrame:
        """Get historical price data for a specific coin."""
        try:
            # Convert dates to timestamps
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())

            url = f"{self.base_url}/coins/{coin_id}/market_chart/range"
            params = {
                "vs_currency": "usd",
                "from": start_timestamp,
                "to": end_timestamp
            }

            response = self._make_request(url, params=params, headers=self.headers)
            data = response.json()

            if "prices" not in data:
                self.logger.warning(f"No price data for {coin_id}")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["coin_id"] = coin_id

            # Add volume and market cap if available
            if "market_caps" in data:
                market_caps = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
                market_caps["timestamp"] = pd.to_datetime(market_caps["timestamp"], unit="ms")
                df = df.merge(market_caps, on="timestamp", how="left")

            if "total_volumes" in data:
                volumes = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
                volumes["timestamp"] = pd.to_datetime(volumes["timestamp"], unit="ms")
                df = df.merge(volumes, on="timestamp", how="left")

            df = df.sort_values("timestamp").reset_index(drop=True)

            self.logger.info(f"Collected {len(df)} historical records for {coin_id}")
            return df

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {coin_id}", error=str(e))
            return pd.DataFrame()

    def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get Fear & Greed Index data."""
        try:
            # Note: Fear & Greed Index is from Alternative.me, not CoinGecko
            # This is a placeholder - actual implementation in sentiment.py
            url = "https://api.alternative.me/fng/"

            response = self._make_request(url)
            data = response.json()

            if "data" in data and len(data["data"]) > 0:
                fng_data = data["data"][0]
                return {
                    "value": int(fng_data["value"]),
                    "value_classification": fng_data["value_classification"],
                    "timestamp": fng_data["timestamp"],
                    "time_until_update": fng_data.get("time_until_update")
                }

            return {}

        except Exception as e:
            self.logger.error("Failed to get Fear & Greed Index", error=str(e))
            return {}

    def get_trending_coins(self) -> List[Dict[str, Any]]:
        """Get trending cryptocurrencies."""
        try:
            url = f"{self.base_url}/search/trending"
            response = self._make_request(url, headers=self.headers)
            data = response.json()

            if "coins" in data:
                return [
                    {
                        "id": coin["item"]["id"],
                        "name": coin["item"]["name"],
                        "symbol": coin["item"]["symbol"],
                        "market_cap_rank": coin["item"]["market_cap_rank"],
                        "price_btc": coin["item"]["price_btc"]
                    }
                    for coin in data["coins"]
                ]

            return []

        except Exception as e:
            self.logger.error("Failed to get trending coins", error=str(e))
            return []

    def get_exchange_rates(self) -> Dict[str, float]:
        """Get BTC exchange rates."""
        try:
            url = f"{self.base_url}/exchange_rates"
            response = self._make_request(url, headers=self.headers)
            data = response.json()

            if "rates" in data:
                rates = {}
                for currency, rate_data in data["rates"].items():
                    if currency in ["usd", "eur", "jpy", "gbp", "cad", "aud"]:
                        rates[currency.upper()] = float(rate_data["value"])
                return rates

            return {}

        except Exception as e:
            self.logger.error("Failed to get exchange rates", error=str(e))
            return {}

    def transform_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Transform CoinGecko market data to standardized DataFrame."""
        if "market_data" not in data:
            return pd.DataFrame()

        market_data = data["market_data"]

        records = []
        for coin in market_data:
            record = {
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "timestamp": datetime.utcnow(),
                "open_price": coin.get("current_price", 0),  # CoinGecko doesn't provide OHLC in market endpoint
                "high_price": coin.get("high_24h", coin.get("current_price", 0)),
                "low_price": coin.get("low_24h", coin.get("current_price", 0)),
                "close_price": coin.get("current_price", 0),
                "volume": coin.get("total_volume", 0),
                "market_cap": coin.get("market_cap", 0),
                "price_change_24h": coin.get("price_change_24h", 0),
                "price_change_percentage_24h": coin.get("price_change_percentage_24h", 0),
                "source": "coingecko"
            }
            records.append(record)

        df = pd.DataFrame(records)
        return df

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate CoinGecko data."""
        if not super().validate_data(data):
            return False

        # Check if market_data exists and is not empty
        if "market_data" not in data or not data["market_data"]:
            self.logger.warning("No market data in response")
            return False

        # Check if we have valid price data
        for coin in data["market_data"]:
            if not coin.get("current_price") or coin.get("current_price") <= 0:
                self.logger.warning(f"Invalid price for {coin.get('name', 'unknown')}")
                return False

        return True