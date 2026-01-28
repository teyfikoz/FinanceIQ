"""Data360 / World Bank indicator helper."""

from datetime import datetime
import time
from typing import Optional, Dict, Any, List

import pandas as pd
import requests

from .secret_utils import get_secret


class Data360API:
    """Lightweight wrapper for country-level macro indicators."""

    def __init__(self, cache_ttl: int = 86400):
        self.base_url = get_secret(
            "DATA360_API_BASE",
            default="https://extdataportal.worldbank.org/api/data360",
        )
        self.worldbank_base = get_secret(
            "WORLDBANK_API_BASE",
            default="https://api.worldbank.org/v2",
        )
        self.token = get_secret("DATA360_API_TOKEN", "DATA360_TOKEN", default="")
        self.filter_template = get_secret("DATA360_FILTER_TEMPLATE", default="")
        self.session = requests.Session()
        self._cache = {}
        self._cache_ttl = cache_ttl
        self._data360_available = None

    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        cached = self._cache.get(key)
        if not cached:
            return None
        ts, data = cached
        if time.time() - ts < self._cache_ttl:
            return data
        self._cache.pop(key, None)
        return None

    def _cache_set(self, key: str, data: Dict[str, Any]) -> None:
        self._cache[key] = (time.time(), data)

    def _parse_date(self, raw: Any) -> Optional[datetime]:
        if raw is None:
            return None
        raw_str = str(raw).strip()
        if not raw_str:
            return None
        if raw_str.isdigit() and len(raw_str) == 4:
            return datetime(int(raw_str), 1, 1)
        try:
            return pd.to_datetime(raw_str, errors="coerce")
        except Exception:
            return None

    def _series_to_df(self, items: List[Dict[str, Any]]) -> pd.DataFrame:
        rows = []
        for item in items:
            date_raw = item.get("date") or item.get("period")
            value_raw = item.get("value") if "value" in item else item.get("Value")
            if value_raw is None or date_raw is None:
                continue
            date_val = self._parse_date(date_raw)
            if date_val is None or pd.isna(date_val):
                continue
            try:
                value_val = float(value_raw)
            except Exception:
                continue
            rows.append({"date": date_val, "value": value_val})

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("date").reset_index(drop=True)
        return df

    def _fetch_data360_indicator(self, indicator: str, country: str) -> Optional[List[Dict[str, Any]]]:
        if self._data360_available is False:
            return None
        if not self.base_url:
            return None
        if "api.worldbank.org" in (self.base_url or ""):
            return None

        url = f"{self.base_url.rstrip('/')}/data/indicator"
        params: Dict[str, Any] = {}
        if self.filter_template:
            params["filter"] = self.filter_template.format(indicator=indicator, country=country)
        else:
            params["indicator"] = indicator
            params["country"] = country

        if self.token:
            params["token"] = self.token

        try:
            resp = self.session.get(url, params=params, timeout=20)
            data = resp.json()
        except Exception:
            self._data360_available = False
            return None

        if not resp.ok:
            self._data360_available = False
            return None

        if isinstance(data, dict):
            if data.get("status") and int(data.get("status")) >= 400:
                self._data360_available = False
                return None
            if data.get("message") and "error" in str(data.get("message")).lower():
                self._data360_available = False
                return None
            if data.get("detail"):
                self._data360_available = False
                return None

            if isinstance(data.get("data"), list):
                self._data360_available = True
                return data["data"]
            if isinstance(data.get("Data"), list):
                self._data360_available = True
                return data["Data"]

        self._data360_available = False
        return None

    def _fetch_worldbank_indicator(self, indicator: str, country: str) -> Optional[List[Dict[str, Any]]]:
        url = f"{self.worldbank_base.rstrip('/')}/country/{country}/indicator/{indicator}"
        params = {"format": "json", "per_page": 20000}

        try:
            resp = self.session.get(url, params=params, timeout=20)
            if not resp.ok:
                return None
            data = resp.json()
        except Exception:
            return None

        if not isinstance(data, list) or len(data) < 2:
            return None

        series = data[1]
        if not isinstance(series, list):
            return None
        return series

    def get_indicator_series(self, indicator: str, country: str) -> Optional[Dict[str, Any]]:
        cache_key = f"series:{indicator}:{country}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        items = self._fetch_data360_indicator(indicator, country)
        if items is None:
            items = self._fetch_worldbank_indicator(indicator, country)
        if not items:
            return None

        df = self._series_to_df(items)
        if df.empty:
            return None

        latest_row = df.iloc[-1]
        result = {
            "series": df,
            "latest_value": latest_row["value"],
            "latest_date": latest_row["date"],
        }
        self._cache_set(cache_key, result)
        return result

    def get_latest_value(self, indicator: str, country: str) -> Optional[Dict[str, Any]]:
        cache_key = f"latest:{indicator}:{country}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        series = self.get_indicator_series(indicator, country)
        if not series:
            return None

        result = {
            "latest_value": series.get("latest_value"),
            "latest_date": series.get("latest_date"),
        }
        self._cache_set(cache_key, result)
        return result
