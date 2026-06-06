"""
TEFAS Portfolio Tracker
=======================
Tracks Turkish fund portfolio changes over time using the 2026 TEFAS JSON API.
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta


class TEFASPortfolioTracker:
    """
    Track TEFAS fund size, investor count, and portfolio allocation over time.

    Notes:
    - Historical price/AUM/investor data now comes from `/api/funds/fonGnlBlgSiraliGetir`
    - Portfolio allocation snapshots come from `/api/funds/dagilimSiraliGetirT`
    - Security-level holdings are no longer exposed by the public API, so the
      "holdings" views are derived from allocation buckets instead.
    """

    ASSET_BUCKET_MAP = {
        "hs": "stocks",
        "yhs": "stocks",
        "dt": "bonds",
        "db": "bonds",
        "dot": "bonds",
        "eut": "bonds",
        "ost": "bonds",
        "yba": "bonds",
        "ybkb": "bonds",
        "ybosb": "bonds",
        "osdb": "bonds",
        "hb": "bills",
        "fb": "bills",
        "bb": "bills",
        "r": "repo",
        "tr": "repo",
        "tpp": "repo",
        "bpp": "repo",
        "btaa": "repo",
        "btas": "repo",
        "d": "fx",
        "vmd": "fx",
        "ymk": "fx",
        "kh": "participation",
        "khau": "participation",
        "khd": "participation",
        "khtl": "participation",
        "kks": "participation",
        "kksd": "participation",
        "kkstl": "participation",
        "kksyd": "participation",
        "osks": "participation",
        "oksyd": "participation",
        "km": "precious_metals",
        "gas": "precious_metals",
        "kmbyf": "precious_metals",
        "kmkba": "precious_metals",
        "kmkks": "precious_metals",
        "vmau": "precious_metals",
    }

    BUCKET_LABELS = {
        "stocks": "Stocks",
        "bonds": "Bonds",
        "bills": "Bills",
        "repo": "Repo",
        "fx": "FX",
        "participation": "Participation",
        "precious_metals": "Precious Metals",
        "other": "Other",
    }

    def __init__(self, request_timeout_seconds: int = 6, max_retries: int = 1):
        self.base_url = "https://www.tefas.gov.tr/api/funds"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://www.tefas.gov.tr",
                "Referer": "https://www.tefas.gov.tr/tr/",
            }
        )
        self.max_window_days = 28
        self.request_timeout_seconds = request_timeout_seconds
        self.max_retries = max_retries

    def _post_json(self, endpoint: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/{endpoint}",
                    json=payload,
                    timeout=self.request_timeout_seconds,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("errorMessage"):
                    raise RuntimeError(data["errorMessage"])
                return data.get("resultList") or []
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(0.75 * (attempt + 1))
                    continue
        raise RuntimeError(str(last_error) if last_error else "Unknown TEFAS error")

    def _format_compact_date(self, value: datetime) -> str:
        return value.strftime("%Y%m%d")

    def _chunk_date_range(self, start: datetime, end: datetime) -> List[tuple[datetime, datetime]]:
        chunks: List[tuple[datetime, datetime]] = []
        cursor = start
        while cursor <= end:
            chunk_end = min(cursor + timedelta(days=self.max_window_days - 1), end)
            chunks.append((cursor, chunk_end))
            cursor = chunk_end + timedelta(days=1)
        return chunks

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None or value == "":
                return default
            return float(value)
        except Exception:
            return default

    def _safe_int(self, value: Any, default: int = 0) -> int:
        try:
            if value is None or value == "":
                return default
            return int(float(value))
        except Exception:
            return default

    def _empty_allocation(self) -> Dict[str, float]:
        return {
            "stocks": 0.0,
            "bonds": 0.0,
            "bills": 0.0,
            "repo": 0.0,
            "fx": 0.0,
            "participation": 0.0,
            "precious_metals": 0.0,
            "other": 0.0,
        }

    def _parse_asset_allocation(self, data: Dict[str, Any]) -> Dict[str, float]:
        allocation = self._empty_allocation()
        ignored = {
            "fonKodu",
            "fonUnvan",
            "tarih",
            "bilFiyat",
            "rn",
            "borsaBultenFiyat",
        }

        for key, value in data.items():
            if key in ignored:
                continue
            weight = self._safe_float(value)
            if weight <= 0:
                continue
            bucket = self.ASSET_BUCKET_MAP.get(key.lower(), "other")
            allocation[bucket] += weight

        return {name: round(weight, 2) for name, weight in allocation.items()}

    def get_current_fund_overview(self, fund_code: str) -> Optional[Dict[str, Any]]:
        try:
            rows = self._post_json("fonBilgiGetir", {"fonKodu": fund_code.upper(), "dil": "TR"})
        except Exception as e:
            return None

        if not rows:
            return None

        latest = rows[0]
        return {
            "fund_code": fund_code.upper(),
            "fund_name": latest.get("fonUnvan", ""),
            "current_price": self._safe_float(latest.get("sonFiyat"), math.nan),
            "daily_return": self._safe_float(latest.get("gunlukGetiri"), math.nan),
            "portfolio_value": self._safe_float(latest.get("portBuyukluk")),
            "number_of_investors": self._safe_int(latest.get("yatirimciSayi")),
            "number_of_shares": self._safe_int(latest.get("payAdet")),
            "category": latest.get("fonKategori", ""),
            "category_rank": self._safe_int(latest.get("kategoriDerece")),
            "category_count": self._safe_int(latest.get("kategoriFonSay")),
            "market_share": self._safe_float(latest.get("pazarPayi")),
        }

    def get_fund_daily_snapshots(
        self,
        fund_code: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        error_count = 0
        for chunk_start, chunk_end in self._chunk_date_range(start_date, end_date):
            payload = {
                "fonTipi": "YAT",
                "fonKodu": fund_code.upper(),
                "aramaMetni": None,
                "fonTurKod": None,
                "fonGrubu": None,
                "sfonTurKod": None,
                "basTarih": self._format_compact_date(chunk_start),
                "bitTarih": self._format_compact_date(chunk_end),
                "basSira": 1,
                "bitSira": 200,
                "fonTurAciklama": None,
                "dil": "TR",
                "kurucuKod": None,
            }
            try:
                chunk_rows = self._post_json("fonGnlBlgSiraliGetir", payload)
            except Exception:
                error_count += 1
                continue

            for item in chunk_rows:
                if item.get("fonKodu", "").upper() != fund_code.upper():
                    continue
                rows.append(
                    {
                        "date": item.get("tarih"),
                        "price": self._safe_float(item.get("fiyat"), math.nan),
                        "portfolio_value": self._safe_float(item.get("portfoyBuyukluk")),
                        "num_investors": self._safe_int(item.get("kisiSayisi")),
                        "number_of_shares": self._safe_int(item.get("tedPaySayisi")),
                    }
                )

        df = pd.DataFrame(rows)
        if df.empty and error_count:
            print(f"Daily snapshot data unavailable for {fund_code} across {error_count} TEFAS chunk(s)")
        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).drop_duplicates(subset=["date"]).sort_values("date")
        return df.reset_index(drop=True)

    def get_fund_allocation_history(
        self,
        fund_code: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        error_count = 0
        for chunk_start, chunk_end in self._chunk_date_range(start_date, end_date):
            payload = {
                "fonTipi": "YAT",
                "fonKodu": None,
                "aramaMetni": None,
                "fonTurKod": None,
                "fonGrubu": None,
                "sfonTurKod": None,
                "basTarih": self._format_compact_date(chunk_start),
                "bitTarih": self._format_compact_date(chunk_end),
                "basSira": 1,
                "bitSira": 200,
                "fonTurAciklama": None,
                "dil": "TR",
                "kurucuKod": None,
                "sFonTurKod": "",
                "fonKod": fund_code.upper(),
                "fonGrup": "",
                "fonUnvanTip": "",
            }
            try:
                chunk_rows = self._post_json("dagilimSiraliGetirT", payload)
            except Exception:
                error_count += 1
                continue

            for item in chunk_rows:
                if item.get("fonKodu", "").upper() != fund_code.upper():
                    continue
                rows.append(
                    {
                        "date": item.get("tarih"),
                        "asset_allocation": self._parse_asset_allocation(item),
                    }
                )

        df = pd.DataFrame(rows)
        if df.empty and error_count:
            print(f"Allocation history unavailable for {fund_code} across {error_count} TEFAS chunk(s)")
        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).drop_duplicates(subset=["date"]).sort_values("date")
        return df.reset_index(drop=True)

    def get_fund_portfolio(self, fund_code: str, date: str = None) -> Optional[Dict[str, Any]]:
        if date is None:
            target_date = datetime.now()
        else:
            target_date = datetime.strptime(date, "%Y-%m-%d")

        alloc_df = self.get_fund_allocation_history(fund_code, target_date, target_date)
        if alloc_df.empty:
            return None

        overview = self.get_current_fund_overview(fund_code) or {}
        latest = alloc_df.iloc[-1]
        return {
            "fund_code": fund_code.upper(),
            "date": latest["date"].strftime("%Y-%m-%d"),
            "portfolio_value": overview.get("portfolio_value", 0),
            "number_of_investors": overview.get("number_of_investors", 0),
            "number_of_shares": overview.get("number_of_shares", 0),
            "holdings": [],
            "asset_allocation": latest["asset_allocation"],
        }

    def get_monthly_portfolio_changes(self, fund_code: str, months: int = 12) -> pd.DataFrame:
        try:
            end_date = datetime.now()
            start_date = (end_date - relativedelta(months=months)).replace(day=1)

            snapshots_df = self.get_fund_daily_snapshots(fund_code, start_date, end_date)
            allocation_df = self.get_fund_allocation_history(fund_code, start_date, end_date)

            monthly_rows: Dict[str, Dict[str, Any]] = {}

            if not snapshots_df.empty:
                snapshots_df["month"] = snapshots_df["date"].dt.strftime("%Y-%m")
                for _, row in snapshots_df.groupby("month").tail(1).iterrows():
                    monthly_rows[row["month"]] = {
                        "date": row["date"],
                        "month": row["month"],
                        "portfolio_value": self._safe_float(row.get("portfolio_value")),
                        "num_investors": self._safe_int(row.get("num_investors")),
                        "number_of_shares": self._safe_int(row.get("number_of_shares")),
                        "asset_allocation": self._empty_allocation(),
                        "holdings": [],
                    }

            if not allocation_df.empty:
                allocation_df["month"] = allocation_df["date"].dt.strftime("%Y-%m")
                for _, row in allocation_df.groupby("month").tail(1).iterrows():
                    bucket = monthly_rows.setdefault(
                        row["month"],
                        {
                            "date": row["date"],
                            "month": row["month"],
                            "portfolio_value": 0.0,
                            "num_investors": 0,
                            "number_of_shares": 0,
                            "asset_allocation": self._empty_allocation(),
                            "holdings": [],
                        },
                    )
                    bucket["date"] = max(bucket["date"], row["date"])
                    bucket["asset_allocation"] = row["asset_allocation"]

            if not monthly_rows:
                return pd.DataFrame()

            monthly_data = []
            for month in sorted(monthly_rows):
                row = monthly_rows[month]
                monthly_data.append(
                    {
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "month": month,
                        "portfolio_value": row["portfolio_value"],
                        "num_investors": row["num_investors"],
                        "number_of_shares": row["number_of_shares"],
                        "asset_allocation": row["asset_allocation"],
                        "holdings": row["holdings"],
                    }
                )

            return pd.DataFrame(monthly_data)

        except Exception as e:
            print(f"Error getting monthly changes for {fund_code}: {e}")
            return pd.DataFrame()

    def calculate_allocation_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        try:
            changes = []
            for i in range(1, len(df)):
                prev_month = df.iloc[i - 1]
                curr_month = df.iloc[i]

                prev_alloc = prev_month["asset_allocation"]
                curr_alloc = curr_month["asset_allocation"]
                month_changes = {
                    "month": curr_month["month"],
                    "date": curr_month["date"],
                }

                for asset_class in self._empty_allocation().keys():
                    prev_val = self._safe_float(prev_alloc.get(asset_class, 0))
                    curr_val = self._safe_float(curr_alloc.get(asset_class, 0))
                    change = curr_val - prev_val

                    month_changes[f"{asset_class}_prev"] = prev_val
                    month_changes[f"{asset_class}_curr"] = curr_val
                    month_changes[f"{asset_class}_change"] = round(change, 2)

                changes.append(month_changes)

            return pd.DataFrame(changes)

        except Exception as e:
            print(f"Error calculating allocation changes: {e}")
            return pd.DataFrame()

    def identify_new_and_removed_holdings(self, df: pd.DataFrame) -> Dict[str, List]:
        if df.empty or len(df) < 2:
            return {}

        try:
            changes_by_month = {}
            for i in range(1, len(df)):
                prev_month = df.iloc[i - 1]
                curr_month = df.iloc[i]

                prev_alloc = prev_month["asset_allocation"]
                curr_alloc = curr_month["asset_allocation"]

                prev_active = {k for k, v in prev_alloc.items() if self._safe_float(v) >= 0.5}
                curr_active = {k for k, v in curr_alloc.items() if self._safe_float(v) >= 0.5}

                new_holdings = [
                    {
                        "security_code": code,
                        "security_name": self.BUCKET_LABELS.get(code, code.title()),
                        "weight": self._safe_float(curr_alloc.get(code, 0)),
                    }
                    for code in sorted(curr_active - prev_active)
                ]
                removed_holdings = [
                    {
                        "security_code": code,
                        "security_name": self.BUCKET_LABELS.get(code, code.title()),
                        "weight": self._safe_float(prev_alloc.get(code, 0)),
                    }
                    for code in sorted(prev_active - curr_active)
                ]

                weight_changes = []
                for code in sorted(curr_active & prev_active):
                    prev_weight = self._safe_float(prev_alloc.get(code, 0))
                    curr_weight = self._safe_float(curr_alloc.get(code, 0))
                    change = curr_weight - prev_weight
                    if abs(change) > 1.0:
                        weight_changes.append(
                            {
                                "security_code": code,
                                "security_name": self.BUCKET_LABELS.get(code, code.title()),
                                "prev_weight": prev_weight,
                                "curr_weight": curr_weight,
                                "change": round(change, 2),
                            }
                        )

                changes_by_month[curr_month["month"]] = {
                    "new_holdings": new_holdings,
                    "removed_holdings": removed_holdings,
                    "weight_changes": sorted(
                        weight_changes,
                        key=lambda x: abs(x["change"]),
                        reverse=True,
                    ),
                }

            return changes_by_month

        except Exception as e:
            print(f"Error identifying holdings changes: {e}")
            return {}

    def get_top_holdings_over_time(self, fund_code: str, months: int = 6, top_n: int = 10) -> pd.DataFrame:
        try:
            monthly_df = self.get_monthly_portfolio_changes(fund_code, months)
            if monthly_df.empty:
                return pd.DataFrame()

            top_holdings_data = []
            for _, row in monthly_df.iterrows():
                allocation = row["asset_allocation"]
                sorted_assets = sorted(allocation.items(), key=lambda item: item[1], reverse=True)[:top_n]

                for rank, (asset_code, weight) in enumerate(sorted_assets, 1):
                    if weight <= 0:
                        continue
                    top_holdings_data.append(
                        {
                            "month": row["month"],
                            "rank": rank,
                            "security_name": self.BUCKET_LABELS.get(asset_code, asset_code.title()),
                            "security_code": asset_code,
                            "weight": round(weight, 2),
                            "value": round(self._safe_float(row["portfolio_value"]) * weight / 100, 2),
                        }
                    )

            return pd.DataFrame(top_holdings_data)

        except Exception as e:
            print(f"Error getting top holdings: {e}")
            return pd.DataFrame()

    def generate_portfolio_summary(self, fund_code: str, months: int = 12) -> Dict[str, Any]:
        try:
            overview = self.get_current_fund_overview(fund_code) or {}
            current_alloc = self.get_fund_portfolio(fund_code)
            monthly_df = self.get_monthly_portfolio_changes(fund_code, months)

            if monthly_df.empty and not overview and not current_alloc:
                return {}

            allocation_changes = self.calculate_allocation_changes(monthly_df)
            holdings_changes = self.identify_new_and_removed_holdings(monthly_df)
            top_holdings = self.get_top_holdings_over_time(fund_code, months)

            if not monthly_df.empty:
                latest = monthly_df.iloc[-1]
                oldest = monthly_df.iloc[0]
            else:
                current_alloc = self.get_fund_portfolio(fund_code)
                latest = {
                    "month": datetime.now().strftime("%Y-%m"),
                    "portfolio_value": overview.get("portfolio_value", 0),
                    "num_investors": overview.get("number_of_investors", 0),
                    "asset_allocation": (current_alloc or {}).get("asset_allocation", self._empty_allocation()),
                }
                oldest = latest

            current_allocation = (current_alloc or {}).get(
                "asset_allocation",
                latest.get("asset_allocation", self._empty_allocation()),
            )

            summary = {
                "fund_code": fund_code.upper(),
                "fund_name": overview.get("fund_name", ""),
                "period": f"{oldest['month']} to {latest['month']}",
                "total_months": len(monthly_df) if not monthly_df.empty else 1,
                "latest_portfolio_value": overview.get(
                    "portfolio_value",
                    self._safe_float(latest.get("portfolio_value")),
                ),
                "portfolio_value_change": self._safe_float(latest.get("portfolio_value"))
                - self._safe_float(oldest.get("portfolio_value")),
                "latest_num_investors": overview.get(
                    "number_of_investors",
                    self._safe_int(latest.get("num_investors")),
                ),
                "investor_change": self._safe_int(latest.get("num_investors"))
                - self._safe_int(oldest.get("num_investors")),
                "asset_allocation_current": current_allocation,
                "asset_allocation_initial": oldest.get("asset_allocation", self._empty_allocation()),
                "monthly_allocation_changes": allocation_changes.to_dict("records"),
                "holdings_changes_by_month": holdings_changes,
                "top_holdings_evolution": top_holdings.to_dict("records"),
                "total_new_holdings": sum(len(m["new_holdings"]) for m in holdings_changes.values()),
                "total_removed_holdings": sum(len(m["removed_holdings"]) for m in holdings_changes.values()),
                "current_price": overview.get("current_price"),
                "daily_return": overview.get("daily_return"),
                "category": overview.get("category", ""),
                "category_rank": overview.get("category_rank", 0),
                "category_count": overview.get("category_count", 0),
                "market_share": overview.get("market_share", 0.0),
                "data_source": "tefas_v2",
            }

            return summary

        except Exception as e:
            print(f"Error generating portfolio summary: {e}")
            return {}

    def get_fund_identity(self, fund_code: str) -> Dict[str, Any]:
        """Fetch the current TEFAS identity block for one fund code."""
        overview = self.get_current_fund_overview(fund_code) or {}
        return {
            "fund_code": fund_code.upper(),
            "fund_name": overview.get("fund_name", ""),
            "category": overview.get("category", ""),
            "category_rank": overview.get("category_rank", 0),
            "category_count": overview.get("category_count", 0),
            "market_share": overview.get("market_share", 0.0),
        }
