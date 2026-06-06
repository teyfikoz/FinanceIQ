from typing import Any, Dict, List, Optional
from datetime import datetime

import pandas as pd

from .base import BaseCollector
from app.core.config import settings


class FiscalDataCollector(BaseCollector):
    """Collector for official U.S. Treasury Fiscal Data datasets."""

    def __init__(self):
        super().__init__("fiscaldata")
        self.base_url = settings.TREASURY_FISCALDATA_BASE_URL.rstrip("/")
        self.rate_limit_delay = 0.1

    def collect_data(self, dataset: str = "macro") -> Dict[str, Any]:
        """Collect lightweight official Treasury macro indicators."""
        if dataset == "macro":
            return self.get_fiscal_indicators()
        return {"error": f"Unsupported dataset: {dataset}"}

    def get_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        dataset_path: str = "v2/accounting/od/debt_to_penny",
        value_field: str = "tot_pub_debt_out_amt",
        frequency: Optional[str] = None,
    ) -> pd.DataFrame:
        """Get historical Treasury data for a specific endpoint."""
        try:
            params = {
                "fields": f"record_date,{value_field}",
                "sort": "record_date",
                "page[size]": 1000,
                "filter": (
                    f"record_date:gte:{start_date.strftime('%Y-%m-%d')},"
                    f"record_date:lte:{end_date.strftime('%Y-%m-%d')}"
                ),
            }
            if frequency:
                params["frequency"] = frequency

            response = self._make_request(f"{self.base_url}/{dataset_path}", params=params)
            payload = response.json()
            records = payload.get("data", [])
            if not records:
                return pd.DataFrame()

            rows = []
            for record in records:
                value = record.get(value_field)
                if value in (None, ""):
                    continue
                try:
                    rows.append(
                        {
                            "record_date": pd.to_datetime(record["record_date"]),
                            "value": float(value),
                        }
                    )
                except Exception:
                    continue

            df = pd.DataFrame(rows)
            if df.empty:
                return df
            return df.sort_values("record_date").reset_index(drop=True)
        except Exception as exc:
            self.logger.error("Failed to get Treasury historical data", error=str(exc), dataset_path=dataset_path)
            return pd.DataFrame()

    def _fetch_records(
        self,
        dataset_path: str,
        fields: List[str],
        page_size: int = 2,
        sort: str = "-record_date",
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "fields": ",".join(fields),
            "sort": sort,
            "page[size]": page_size,
        }
        if filter_expr:
            params["filter"] = filter_expr

        response = self._make_request(f"{self.base_url}/{dataset_path}", params=params)
        payload = response.json()
        return payload.get("data", []) if isinstance(payload, dict) else []

    def get_fiscal_indicators(self) -> Dict[str, Any]:
        """Get a compact official macro snapshot from Treasury Fiscal Data."""
        indicators: Dict[str, Any] = {}

        try:
            debt_rows = self._fetch_records(
                dataset_path="v2/accounting/od/debt_to_penny",
                fields=[
                    "record_date",
                    "tot_pub_debt_out_amt",
                    "debt_held_public_amt",
                    "intragov_hold_amt",
                ],
                page_size=2,
            )
        except Exception as exc:
            self.logger.warning("Debt to the Penny fetch failed", error=str(exc))
            debt_rows = []

        if len(debt_rows) >= 2:
            current = debt_rows[0]
            previous = debt_rows[1]
            mappings = (
                ("tot_pub_debt_out_amt", "US Public Debt"),
                ("debt_held_public_amt", "Debt Held by Public"),
                ("intragov_hold_amt", "Intragovernmental Holdings"),
            )
            for field, name in mappings:
                try:
                    current_val = float(current[field])
                    previous_val = float(previous[field])
                except Exception:
                    continue
                change = ((current_val - previous_val) / previous_val) * 100 if previous_val else 0.0
                indicators[field] = {
                    "name": name,
                    "current_value": current_val,
                    "previous_value": previous_val,
                    "display_value": current_val,
                    "display_previous_value": previous_val,
                    "change_percent": change,
                    "date": current.get("record_date"),
                    "currency_code": "USD",
                    "unit_scale": 1,
                    "source_dataset": "Debt to the Penny",
                }

        try:
            cash_rows = self._fetch_records(
                dataset_path="v1/accounting/dts/operating_cash_balance",
                fields=[
                    "record_date",
                    "account_type",
                    "open_today_bal",
                    "close_today_bal",
                ],
                page_size=20,
            )
        except Exception as exc:
            self.logger.warning("Operating cash balance fetch failed", error=str(exc))
            cash_rows = []

        if cash_rows:
            tga_rows = [
                row for row in cash_rows
                if "Treasury General Account" in str(row.get("account_type", ""))
            ]
            ordered_rows = tga_rows or cash_rows
            if len(ordered_rows) >= 2:
                current = ordered_rows[0]
                previous = ordered_rows[1]
                try:
                    current_val = float(current["close_today_bal"])
                    previous_val = float(previous["close_today_bal"])
                except Exception:
                    current_val = previous_val = None
                if current_val is not None and previous_val is not None:
                    change = ((current_val - previous_val) / previous_val) * 100 if previous_val else 0.0
                    indicators["tga_closing_balance"] = {
                        "name": "Treasury General Account",
                        "current_value": current_val,
                        "previous_value": previous_val,
                        "display_value": current_val * 1_000_000,
                        "display_previous_value": previous_val * 1_000_000,
                        "change_percent": change,
                        "date": current.get("record_date"),
                        "currency_code": "USD",
                        "unit_scale": 1_000_000,
                        "source_dataset": "Daily Treasury Statement",
                    }

        return {
            "fiscal_indicators": indicators,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "fiscaldata",
        }
