from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from .base import BaseCollector
from app.core.config import settings


class EVDSCollector(BaseCollector):
    """Collector for the official TCMB EVDS3 JSON endpoints."""

    def __init__(self) -> None:
        super().__init__("evds")
        self.base_url = settings.TCMB_EVDS_BASE_URL.rstrip("/")
        self.api_key = settings.TCMB_EVDS_API_KEY
        self.rate_limit_delay = 0.15
        self.macro_series: Dict[str, Dict[str, Any]] = {
            "TP.AB.C1": {
                "name": "Gold Reserves",
                "datagroup": None,
                "aggregation": "last",
                "default_frequency": "3",
                "frequency_candidates": ["3"],
                "decimal": "0",
                "currency_code": "USD",
                "unit_scale": 1_000_000,
                "display_kind": "money",
                "display_digits": 0,
                "tone_multiplier": 1,
            },
            "TP.AB.C2": {
                "name": "FX Reserves",
                "datagroup": None,
                "aggregation": "last",
                "default_frequency": "3",
                "frequency_candidates": ["3"],
                "decimal": "0",
                "currency_code": "USD",
                "unit_scale": 1_000_000,
                "display_kind": "money",
                "display_digits": 0,
                "tone_multiplier": 1,
            },
        }
        self._frequency_cache: Dict[str, str] = {}

    def _headers(self, include_json: bool = False) -> Dict[str, str]:
        headers = {"accept": "application/json"}
        if include_json:
            headers["content-type"] = "application/json"
        if self.api_key:
            headers["key"] = self.api_key
        return headers

    def _get_json(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        self._rate_limit()
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(
            url,
            params=params,
            headers=self._headers(),
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def _post_json(self, path: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        self._rate_limit()
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.post(
            url,
            json=payload,
            headers=self._headers(include_json=True),
            timeout=timeout,
        )
        response.raise_for_status()
        parsed = response.json()
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _to_evds_date(value: datetime) -> str:
        return value.strftime("%d-%m-%Y")

    @staticmethod
    def _parse_date(value: Any) -> pd.Timestamp | None:
        if value in (None, ""):
            return None
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed

    @staticmethod
    def _parse_number(value: Any) -> float | None:
        if value in (None, "", "null", "."):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        normalized = text.replace(" ", "")
        if "," in normalized and "." not in normalized:
            left, right = normalized.rsplit(",", 1)
            if right.isdigit() and len(right) == 3:
                normalized = left.replace(",", "") + right
            else:
                normalized = normalized.replace(",", ".")
        try:
            return float(normalized)
        except Exception:
            return None

    @staticmethod
    def _normalize_key(value: Any) -> str:
        return "".join(ch for ch in str(value).upper() if ch.isalnum())

    def _extract_rows(self, payload: Dict[str, Any], series_code: str) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        code_key = self._normalize_key(series_code)

        def _pick_date_and_value(row: Dict[str, Any]) -> tuple[pd.Timestamp | None, float | None]:
            date_value = None
            series_value = None
            for key, value in row.items():
                normalized_key = self._normalize_key(key)
                if date_value is None and ("TARIH" in normalized_key or "DATE" in normalized_key):
                    date_value = self._parse_date(value)
                    continue
                if series_value is None and normalized_key == code_key:
                    series_value = self._parse_number(value)
            if series_value is None:
                for key, value in row.items():
                    normalized_key = self._normalize_key(key)
                    if "TARIH" in normalized_key or "DATE" in normalized_key:
                        continue
                    number = self._parse_number(value)
                    if number is not None:
                        series_value = number
                        break
            return date_value, series_value

        candidate_sets = [
            self._materialize_payload_rows(payload.get("items"), payload.get("columns")),
            self._materialize_payload_rows(payload.get("transposedItems"), payload.get("transposedColumns")),
        ]

        for row_set in candidate_sets:
            for row in row_set:
                date_value, series_value = _pick_date_and_value(row)
                if date_value is None or series_value is None:
                    continue
                rows.append({"date": date_value, "value": series_value})
            if rows:
                break

        rows.sort(key=lambda item: item["date"])
        return rows

    @staticmethod
    def _materialize_payload_rows(raw_rows: Any, columns: Any) -> List[Dict[str, Any]]:
        if not isinstance(raw_rows, list):
            return []
        materialized: List[Dict[str, Any]] = []
        for raw in raw_rows:
            if isinstance(raw, dict):
                materialized.append(raw)
            elif isinstance(raw, list) and isinstance(columns, list) and len(columns) == len(raw):
                materialized.append(dict(zip(columns, raw)))
        return materialized

    def _fetch_reserve_pair_history(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        payload = {
            "type": "json",
            "series": "TP.AB.C1-TP.AB.C2",
            "aggregationTypes": "last-last",
            "formulas": "0-0",
            "startDate": self._to_evds_date(start_date),
            "endDate": self._to_evds_date(end_date),
            "frequency": "3",
            "decimalSeperator": ".",
            "decimal": "0",
            "dateFormat": "0",
            "lang": "tr",
            "ozelFormuller": [
                {
                    "plainFormula": "",
                    "code": "F-1",
                    "description": "MB REZERV",
                    "descriptionEng": "CBRT RESERVE",
                    "name": "Formül 1",
                    "nameEng": "Formula 1",
                    "formula": "$TP_AB_C1$+$TP_AB_C2$",
                    "formulas": ["0", "0"],
                    "aggTypes": ["last", "last"],
                    "series": ["TP.AB.C1", "TP.AB.C2"],
                    "datagroups": "",
                }
            ],
            "groupSeperator": True,
            "isRaporSayfasi": True,
        }
        response = self._post_json("fe", payload)
        rows: List[Dict[str, Any]] = []
        for row in self._materialize_payload_rows(response.get("items"), response.get("columns")):
            date_value = None
            gold_value = None
            fx_value = None
            for key, value in row.items():
                normalized_key = self._normalize_key(key)
                if date_value is None and ("TARIH" in normalized_key or "DATE" in normalized_key):
                    date_value = self._parse_date(value)
                elif normalized_key == self._normalize_key("TP.AB.C1"):
                    gold_value = self._parse_number(value)
                elif normalized_key == self._normalize_key("TP.AB.C2"):
                    fx_value = self._parse_number(value)
            if date_value is None or gold_value is None or fx_value is None:
                continue
            rows.append({"date": date_value, "gold": gold_value, "fx": fx_value})
        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame
        return frame.sort_values("date").reset_index(drop=True)

    def _probe_series_frequency(self, series_code: str, datagroup: Any, frequency: str) -> str | None:
        try:
            response = self._post_json(
                "serieList/baslangicBitis",
                {
                    "frequency": int(frequency),
                    "series": [series_code],
                    "datagroups": [datagroup],
                },
            )
        except Exception:
            return None
        resolved = response.get("frequency")
        return str(resolved or frequency) if response.get("startDate") and response.get("endDate") else None

    def _fetch_series_rows(
        self,
        series_code: str,
        datagroup: Any,
        aggregation: str,
        start_date: datetime,
        end_date: datetime,
        decimal: str,
        requested_frequency: Optional[str],
        frequency_candidates: List[str],
    ) -> List[Dict[str, Any]]:
        candidate_order: List[str] = []
        if requested_frequency:
            candidate_order.append(str(requested_frequency))
        cached_frequency = self._frequency_cache.get(series_code)
        if cached_frequency and cached_frequency not in candidate_order:
            candidate_order.append(cached_frequency)
        for candidate in frequency_candidates:
            if candidate not in candidate_order:
                candidate_order.append(candidate)

        for candidate in candidate_order:
            resolved_frequency = self._probe_series_frequency(series_code, datagroup, candidate)
            if not resolved_frequency:
                continue
            try:
                response = self._post_json(
                    "fe",
                    {
                        "type": "json",
                        "series": series_code,
                        "aggregationTypes": aggregation,
                        "formulas": "0",
                        "startDate": self._to_evds_date(start_date),
                        "endDate": self._to_evds_date(end_date),
                        "frequency": resolved_frequency,
                        "decimalSeperator": ".",
                        "decimal": decimal,
                        "dateFormat": "0",
                        "lang": "tr",
                        "groupSeperator": True,
                        "isRaporSayfasi": True,
                    },
                )
            except Exception:
                continue
            rows = self._extract_rows(response, series_code)
            if rows:
                self._frequency_cache[series_code] = resolved_frequency
                return rows
        return []

    def collect_data(self, series_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.get_macro_indicators(series_codes=series_codes)

    def get_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        series_code: str = "TP.AB.C1",
        frequency: Optional[str] = None,
    ) -> pd.DataFrame:
        if series_code in {"TP.AB.C1", "TP.AB.C2"}:
            reserve_history = self._fetch_reserve_pair_history(start_date, end_date)
            if reserve_history.empty:
                return pd.DataFrame()
            value_column = "gold" if series_code == "TP.AB.C1" else "fx"
            return reserve_history[["date", value_column]].rename(columns={value_column: "value"})

        meta = self.macro_series.get(series_code)
        if not meta:
            self.logger.warning("Unsupported EVDS series requested", series_code=series_code)
            return pd.DataFrame()

        rows = self._fetch_series_rows(
            series_code=series_code,
            datagroup=meta["datagroup"],
            aggregation=meta["aggregation"],
            start_date=start_date,
            end_date=end_date,
            decimal=meta["decimal"],
            requested_frequency=frequency or meta.get("default_frequency"),
            frequency_candidates=list(meta.get("frequency_candidates", [])),
        )
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        if df.empty:
            return df
        return df.sort_values("date").reset_index(drop=True)

    def get_macro_indicators(self, series_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        selected = series_codes or list(self.macro_series.keys())
        indicators: Dict[str, Any] = {}
        end_date = datetime.utcnow()

        reserve_history = self._fetch_reserve_pair_history(
            start_date=end_date - timedelta(days=1_460),
            end_date=end_date,
        )
        if not reserve_history.empty:
            current_row = reserve_history.iloc[-1]
            previous_row = reserve_history.iloc[-2] if len(reserve_history) >= 2 else reserve_history.iloc[-1]
            reserve_specs = {
                "TP.AB.C1": ("gold", "Gold Reserves"),
                "TP.AB.C2": ("fx", "FX Reserves"),
            }
            for series_code, (column, label) in reserve_specs.items():
                if series_code not in selected:
                    continue
                current_value = float(current_row[column])
                previous_value = float(previous_row[column])
                change = ((current_value - previous_value) / previous_value) * 100 if previous_value else 0.0
                indicators[series_code] = {
                    "name": label,
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "display_value": current_value * 1_000_000,
                    "display_previous_value": previous_value * 1_000_000,
                    "change_percent": change,
                    "date": current_row["date"].date().isoformat(),
                    "currency_code": "USD",
                    "unit_scale": 1_000_000,
                    "display_kind": "money",
                    "display_digits": 0,
                    "tone_multiplier": 1,
                    "source_dataset": "TCMB EVDS",
                }

        for series_code in selected:
            if series_code in indicators:
                continue
            meta = self.macro_series.get(series_code)
            if not meta:
                continue
            window_days = 180 if meta["display_kind"] == "price" else 1_460
            start_date = end_date - timedelta(days=window_days)
            history = self.get_historical_data(
                start_date=start_date,
                end_date=end_date,
                series_code=series_code,
                frequency=meta.get("default_frequency"),
            )
            if history.empty:
                continue

            current_row = history.iloc[-1]
            previous_row = history.iloc[-2] if len(history) >= 2 else history.iloc[-1]
            current_value = float(current_row["value"])
            previous_value = float(previous_row["value"])
            change = ((current_value - previous_value) / previous_value) * 100 if previous_value else 0.0
            indicators[series_code] = {
                "name": meta["name"],
                "current_value": current_value,
                "previous_value": previous_value,
                "display_value": current_value * meta["unit_scale"],
                "display_previous_value": previous_value * meta["unit_scale"],
                "change_percent": change,
                "date": current_row["date"].date().isoformat(),
                "currency_code": meta["currency_code"],
                "unit_scale": meta["unit_scale"],
                "display_kind": meta["display_kind"],
                "display_digits": meta["display_digits"],
                "tone_multiplier": meta["tone_multiplier"],
                "source_dataset": "TCMB EVDS",
            }

        gold = indicators.get("TP.AB.C1")
        fx = indicators.get("TP.AB.C2")
        if gold and fx:
            current_total = float(gold["current_value"]) + float(fx["current_value"])
            previous_total = float(gold["previous_value"]) + float(fx["previous_value"])
            change = ((current_total - previous_total) / previous_total) * 100 if previous_total else 0.0
            indicators["TCMB_RESERVES_TOTAL"] = {
                "name": "CBRT Total Reserves",
                "current_value": current_total,
                "previous_value": previous_total,
                "display_value": current_total * 1_000_000,
                "display_previous_value": previous_total * 1_000_000,
                "change_percent": change,
                "date": gold["date"],
                "currency_code": "USD",
                "unit_scale": 1_000_000,
                "display_kind": "money",
                "display_digits": 0,
                "tone_multiplier": 1,
                "source_dataset": "TCMB EVDS",
            }

        return {
            "macro_indicators": indicators,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "evds",
        }
