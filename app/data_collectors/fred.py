from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import requests

from .base import BaseCollector
from app.core.config import settings


class FredCollector(BaseCollector):
    """Collector for Federal Reserve Economic Data (FRED)."""

    def __init__(self):
        super().__init__("fred")
        self.base_url = "https://api.stlouisfed.org/fred"
        self.api_key = settings.FRED_API_KEY
        self.rate_limit_delay = 0.1  # FRED is generous with rate limits

        # Key economic indicators to track
        self.default_series = {
            # Monetary Policy & Liquidity
            "WALCL": "Fed Total Assets (Balance Sheet)",
            "M2SL": "M2 Money Supply",
            "FEDFUNDS": "Federal Funds Rate",
            "TB3MS": "3-Month Treasury Bill Rate",
            "GS10": "10-Year Treasury Constant Maturity Rate",

            # Economic Activity
            "GDP": "Gross Domestic Product",
            "GDPC1": "Real GDP",
            "UNRATE": "Unemployment Rate",
            "CPIAUCSL": "Consumer Price Index",
            "NAPM": "ISM Manufacturing PMI",

            # Market Indicators
            "VIXCLS": "VIX Volatility Index",
            "DEXUSEU": "US/Euro Exchange Rate",
            "DEXJPUS": "Japan/US Exchange Rate",

            # Credit & Debt
            "TOTALSA": "Total Consumer Credit",
            "GFDEBTN": "Federal Debt Total Public Debt",
            "CPALTT01USM657N": "Core CPI",

            # International
            "ECBASSETSW": "ECB Total Assets",
            "JPNASSETS": "Bank of Japan Total Assets"
        }

    def collect_data(self, series_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect latest data for specified FRED series."""
        if not self.api_key:
            self.logger.error("FRED API key not configured")
            return {}

        if series_ids is None:
            series_ids = list(self.default_series.keys())

        try:
            fred_data = []

            for series_id in series_ids:
                try:
                    # Get series info
                    info = self._get_series_info(series_id)
                    if not info:
                        continue

                    # Get latest observations
                    observations = self._get_series_observations(series_id, limit=1)
                    if not observations:
                        continue

                    latest_obs = observations[0]

                    record = {
                        "series_id": series_id,
                        "title": info.get("title", series_id),
                        "value": float(latest_obs["value"]) if latest_obs["value"] != "." else None,
                        "date": latest_obs["date"],
                        "frequency": info.get("frequency", "Unknown"),
                        "units": info.get("units", "Unknown"),
                        "seasonal_adjustment": info.get("seasonal_adjustment", "Unknown"),
                        "last_updated": info.get("last_updated")
                    }
                    fred_data.append(record)

                except Exception as e:
                    self.logger.warning(f"Failed to get data for series {series_id}", error=str(e))
                    continue

            result = {
                "fred_data": fred_data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "fred"
            }

            if self.validate_data(result):
                self.log_collection_result(True, len(fred_data))
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
        series_id: str = "WALCL",
        frequency: Optional[str] = None
    ) -> pd.DataFrame:
        """Get historical data for a specific FRED series."""
        if not self.api_key:
            self.logger.error("FRED API key not configured")
            return pd.DataFrame()

        try:
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "observation_start": start_date.strftime("%Y-%m-%d"),
                "observation_end": end_date.strftime("%Y-%m-%d")
            }

            if frequency:
                params["frequency"] = frequency

            url = f"{self.base_url}/series/observations"
            response = self._make_request(url, params=params)
            data = response.json()

            if "observations" not in data:
                self.logger.warning(f"No observations for series {series_id}")
                return pd.DataFrame()

            observations = data["observations"]

            # Convert to DataFrame
            records = []
            for obs in observations:
                if obs["value"] != ".":  # FRED uses "." for missing values
                    records.append({
                        "series_id": series_id,
                        "date": pd.to_datetime(obs["date"]),
                        "value": float(obs["value"])
                    })

            if not records:
                self.logger.warning(f"No valid data points for series {series_id}")
                return pd.DataFrame()

            df = pd.DataFrame(records)
            df = df.sort_values("date").reset_index(drop=True)

            self.logger.info(f"Collected {len(df)} historical records for {series_id}")
            return df

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {series_id}", error=str(e))
            return pd.DataFrame()

    def _get_series_info(self, series_id: str) -> Dict[str, Any]:
        """Get metadata for a FRED series."""
        try:
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json"
            }

            url = f"{self.base_url}/series"
            response = self._make_request(url, params=params)
            data = response.json()

            if "seriess" in data and len(data["seriess"]) > 0:
                return data["seriess"][0]

            return {}

        except Exception as e:
            self.logger.error(f"Failed to get series info for {series_id}", error=str(e))
            return {}

    def _get_series_observations(
        self,
        series_id: str,
        limit: int = 1,
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get observations for a FRED series."""
        try:
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": limit,
                "sort_order": sort_order
            }

            url = f"{self.base_url}/series/observations"
            response = self._make_request(url, params=params)
            data = response.json()

            if "observations" in data:
                return data["observations"]

            return []

        except Exception as e:
            self.logger.error(f"Failed to get observations for {series_id}", error=str(e))
            return []

    def get_liquidity_indicators(self) -> Dict[str, Any]:
        """Get key liquidity indicators from FRED."""
        liquidity_series = {
            "WALCL": "Fed Balance Sheet",
            "M2SL": "M2 Money Supply",
            "ECBASSETSW": "ECB Balance Sheet",
            "JPNASSETS": "BoJ Balance Sheet"
        }

        liquidity_data = {}

        for series_id, name in liquidity_series.items():
            try:
                # Get latest value
                observations = self._get_series_observations(series_id, limit=2)
                if len(observations) >= 2:
                    current = observations[0]
                    previous = observations[1]

                    if current["value"] != "." and previous["value"] != ".":
                        current_val = float(current["value"])
                        previous_val = float(previous["value"])
                        change = ((current_val - previous_val) / previous_val) * 100

                        liquidity_data[series_id] = {
                            "name": name,
                            "current_value": current_val,
                            "previous_value": previous_val,
                            "change_percent": change,
                            "date": current["date"]
                        }

            except Exception as e:
                self.logger.warning(f"Failed to get liquidity data for {series_id}", error=str(e))
                continue

        return {
            "liquidity_indicators": liquidity_data,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_inflation_data(self) -> Dict[str, Any]:
        """Get inflation-related indicators."""
        inflation_series = {
            "CPIAUCSL": "Consumer Price Index",
            "CPALTT01USM657N": "Core CPI",
            "DFEDTARL": "Fed Target Rate - Lower Bound",
            "DFEDTARU": "Fed Target Rate - Upper Bound"
        }

        inflation_data = {}

        for series_id, name in inflation_series.items():
            try:
                observations = self._get_series_observations(series_id, limit=12)  # Get 12 months for YoY calculation

                if len(observations) >= 12:
                    current = observations[0]
                    year_ago = observations[11]

                    if current["value"] != "." and year_ago["value"] != ".":
                        current_val = float(current["value"])
                        year_ago_val = float(year_ago["value"])
                        yoy_change = ((current_val - year_ago_val) / year_ago_val) * 100

                        inflation_data[series_id] = {
                            "name": name,
                            "current_value": current_val,
                            "yoy_change": yoy_change,
                            "date": current["date"]
                        }

            except Exception as e:
                self.logger.warning(f"Failed to get inflation data for {series_id}", error=str(e))
                continue

        return {
            "inflation_indicators": inflation_data,
            "timestamp": datetime.utcnow().isoformat()
        }

    def transform_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Transform FRED data to standardized DataFrame."""
        if "fred_data" not in data:
            return pd.DataFrame()

        fred_data = data["fred_data"]

        records = []
        for item in fred_data:
            record = {
                "indicator_code": item["series_id"],
                "indicator_name": item["title"],
                "value": item["value"],
                "timestamp": pd.to_datetime(item["date"]),
                "frequency": item.get("frequency"),
                "unit": item.get("units"),
                "source": "fred"
            }
            records.append(record)

        df = pd.DataFrame(records)
        return df

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate FRED data."""
        if not super().validate_data(data):
            return False

        # Check if fred_data exists and is not empty
        if "fred_data" not in data or not data["fred_data"]:
            self.logger.warning("No FRED data in response")
            return False

        # Check if we have valid values
        valid_count = 0
        for item in data["fred_data"]:
            if item.get("value") is not None:
                valid_count += 1

        if valid_count == 0:
            self.logger.warning("No valid values in FRED data")
            return False

        return True