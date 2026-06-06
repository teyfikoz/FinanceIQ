from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
import requests

from app.core.config import settings
from app.services.cache import cache_get, cache_set
from app.services.snapshot_store import SnapshotStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_float(value: Any) -> float:
    try:
        if value in (None, "", "None"):
            return 0.0
        return float(str(value).replace(",", ""))
    except Exception:
        return 0.0


def _fmt_number(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return "N/A"


def _fmt_pct(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value):+,.{digits}f}%"
    except Exception:
        return "N/A"


def _fmt_compact_money(value: Any) -> str:
    amount = _safe_float(value)
    if abs(amount) >= 1_000_000_000_000:
        return f"${amount / 1_000_000_000_000:.1f}T"
    if abs(amount) >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if abs(amount) >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    return f"${amount:,.0f}"


class InstitutionalPulseService:
    MANAGERS: Dict[str, Dict[str, str]] = {
        "berkshire": {
            "label": "Berkshire Hathaway",
            "manager_name": "Warren Buffett",
            "style": "Value + insurance float",
            "cik": "1067983",
        },
        "gates": {
            "label": "Gates Foundation Trust",
            "manager_name": "Bill Gates",
            "style": "Long-horizon compounders",
            "cik": "1166559",
        },
        "bridgewater": {
            "label": "Bridgewater Associates",
            "manager_name": "Ray Dalio",
            "style": "Global macro balanced",
            "cik": "1350694",
        },
        "pershing": {
            "label": "Pershing Square",
            "manager_name": "Bill Ackman",
            "style": "Concentrated activist",
            "cik": "1336528",
        },
        "duquesne": {
            "label": "Duquesne Family Office",
            "manager_name": "Stanley Druckenmiller",
            "style": "Quality growth + macro",
            "cik": "1536411",
        },
    }

    def __init__(
        self,
        ttl_seconds: int | None = None,
        snapshot_store: SnapshotStore | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds or max(settings.PUBLIC_RESEARCH_TTL_SECONDS, 21_600)
        self.snapshot_store = snapshot_store or SnapshotStore()
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": settings.PUBLIC_SEC_USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
            }
        )

    def _cache_key(self, manager_key: str) -> str:
        return f"institutional-pulse:{manager_key}"

    def _snapshot_key(self, manager_key: str) -> str:
        return f"institutional-pulse-{manager_key}"

    def _dataset_cache_key(self, manager_key: str) -> str:
        return f"institutional-pulse-dataset:{manager_key}"

    def _dataset_snapshot_key(self, manager_key: str) -> str:
        return f"institutional-pulse-dataset-{manager_key}"

    def _selected_manager(self, manager_key: str | None) -> str:
        if manager_key in self.MANAGERS:
            return str(manager_key)
        if settings.PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER in self.MANAGERS:
            return settings.PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER
        return next(iter(self.MANAGERS.keys()))

    def _manager_options(self) -> List[Dict[str, str]]:
        return [
            {
                "key": key,
                "label": payload["label"],
                "manager_name": payload["manager_name"],
                "style": payload["style"],
            }
            for key, payload in self.MANAGERS.items()
        ]

    def manager_keys(self) -> List[str]:
        return list(self.MANAGERS.keys())

    def _normalize_issuer_key(self, issuer: str) -> str:
        normalized = re.sub(r"[^A-Z0-9]+", " ", str(issuer or "").upper()).strip()
        suffixes = {
            "INC",
            "INCORPORATED",
            "CORP",
            "CORPORATION",
            "CO",
            "COMPANY",
            "PLC",
            "LTD",
            "LIMITED",
            "HOLDINGS",
            "HLDGS",
            "GROUP",
            "NV",
            "SA",
        }
        parts = normalized.split()
        while parts and parts[-1] in suffixes:
            parts.pop()
        while len(parts) >= 2 and parts[-2] in {"CLASS", "CL"} and parts[-1] in {"A", "B", "C"}:
            parts = parts[:-2]
        return " ".join(parts)

    def _frame_from_rows(self, rows: List[Dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame(rows or [])

    def _fetch_json(self, url: str) -> Dict[str, Any]:
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        return response.json()

    def _fetch_text(self, url: str) -> str:
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        return response.text

    def _submissions_url(self, cik: str) -> str:
        return f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"

    def _filing_base_url(self, cik: str, accession_no_dash: str) -> str:
        return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_dash}"

    def _recent_13f_filings(self, cik: str, limit: int = 2) -> List[Dict[str, str]]:
        payload = self._fetch_json(self._submissions_url(cik))
        recent = payload.get("filings", {}).get("recent", {})
        forms = list(recent.get("form", []))
        accessions = list(recent.get("accessionNumber", []))
        filing_dates = list(recent.get("filingDate", []))
        primary_docs = list(recent.get("primaryDocument", []))

        rows: List[Dict[str, str]] = []
        for form, accession, filing_date, primary_doc in zip(forms, accessions, filing_dates, primary_docs):
            if form not in {"13F-HR", "13F-HR/A"}:
                continue
            rows.append(
                {
                    "form": str(form),
                    "accession": str(accession),
                    "accession_no_dash": str(accession).replace("-", ""),
                    "filing_date": str(filing_date),
                    "primary_document": str(primary_doc),
                }
            )
            if len(rows) >= limit:
                break
        return rows

    def _iter_directory_candidates(self, cik: str, accession_no_dash: str) -> Iterable[str]:
        root_url = self._filing_base_url(cik, accession_no_dash)
        pending = [f"{root_url}/index.json"]
        visited: set[str] = set()

        while pending:
            index_url = pending.pop(0)
            if index_url in visited:
                continue
            visited.add(index_url)
            try:
                payload = self._fetch_json(index_url)
            except Exception:
                continue

            base_url = index_url[: -len("index.json")].rstrip("/")
            items = payload.get("directory", {}).get("item", [])
            for item in items:
                name = str(item.get("name", ""))
                item_type = str(item.get("type", "")).lower()
                if not name:
                    continue
                if item_type == "dir" or ("." not in name and not name.lower().endswith((".xml", ".txt", ".html"))):
                    pending.append(f"{base_url}/{name}/index.json")
                    continue
                yield f"{base_url}/{name}"

    def _find_information_table_url(self, cik: str, accession_no_dash: str, primary_document: str) -> str:
        ranked: List[Tuple[int, str]] = []
        for candidate in self._iter_directory_candidates(cik, accession_no_dash):
            lower = candidate.lower()
            score = 0
            if lower.endswith(".xml"):
                score += 30
            if "info" in lower:
                score += 20
            if "table" in lower:
                score += 20
            if "13f" in lower:
                score += 10
            if "infotable" in lower:
                score += 20
            if score > 0:
                ranked.append((score, candidate))

        if ranked:
            ranked.sort(key=lambda item: item[0], reverse=True)
            return ranked[0][1]

        primary_document = str(primary_document or "")
        if primary_document.lower().endswith(".xml"):
            return f"{self._filing_base_url(cik, accession_no_dash)}/{primary_document}"

        raise RuntimeError("13F information table XML could not be located.")

    def _node_text(self, parent: ET.Element, name: str) -> str:
        for element in parent.iter():
            if element.tag.split("}")[-1] == name:
                return (element.text or "").strip()
        return ""

    def _parse_information_table_xml(self, xml_text: str) -> pd.DataFrame:
        root = ET.fromstring(xml_text)
        rows: List[Dict[str, Any]] = []
        for node in root.iter():
            if node.tag.split("}")[-1] != "infoTable":
                continue
            issuer = self._node_text(node, "nameOfIssuer")
            if not issuer:
                continue
            class_title = self._node_text(node, "titleOfClass") or "N/A"
            cusip = self._node_text(node, "cusip") or "N/A"
            value_thousands = _safe_float(self._node_text(node, "value"))
            rows.append(
                {
                    "issuer": issuer,
                    "issuer_key": self._normalize_issuer_key(issuer),
                    "class_title": class_title,
                    "cusip": cusip,
                    "value_raw": value_thousands,
                    "shares": _safe_float(self._node_text(node, "sshPrnamt")),
                    "put_call": self._node_text(node, "putCall") or "Equity",
                }
            )

        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame

        frame["holding_key"] = frame.apply(
            lambda row: f"{row['cusip']}|{row['issuer_key']}" if row.get("cusip") not in {"", "N/A"} else str(row["issuer_key"]),
            axis=1,
        )
        priced_rows = frame[(frame["shares"] > 0) & (frame["value_raw"] > 0)].copy()
        implied_price = (priced_rows["value_raw"] / priced_rows["shares"]).median() if not priced_rows.empty else 0.0
        scale_factor = 1000.0 if implied_price < 1.0 else 1.0
        frame["value_usd"] = frame["value_raw"] * scale_factor
        frame = (
            frame.groupby(["holding_key", "issuer", "issuer_key", "class_title", "cusip", "put_call"], as_index=False)
            .agg(value_usd=("value_usd", "sum"), shares=("shares", "sum"))
        )
        total_value = float(frame["value_usd"].sum()) or 1.0
        frame["portfolio_weight"] = (frame["value_usd"] / total_value) * 100
        return frame.sort_values("value_usd", ascending=False).reset_index(drop=True)

    def _fetch_holdings_frame(self, cik: str, filing: Dict[str, str]) -> pd.DataFrame:
        info_url = self._find_information_table_url(cik, filing["accession_no_dash"], filing["primary_document"])
        return self._parse_information_table_xml(self._fetch_text(info_url))

    def _compare_holdings_frames(self, current_df: pd.DataFrame, previous_df: pd.DataFrame) -> pd.DataFrame:
        current = current_df.copy() if current_df is not None and not current_df.empty else pd.DataFrame(columns=["holding_key"])
        previous = previous_df.copy() if previous_df is not None and not previous_df.empty else pd.DataFrame(columns=["holding_key"])
        columns = ["holding_key", "issuer", "class_title", "cusip", "value_usd", "shares", "portfolio_weight", "put_call"]

        merged = current[columns].merge(
            previous[columns],
            on="holding_key",
            how="outer",
            suffixes=("_curr", "_prev"),
        ).fillna(0)

        for column in [
            "issuer_curr",
            "class_title_curr",
            "cusip_curr",
            "put_call_curr",
            "issuer_prev",
            "class_title_prev",
            "cusip_prev",
            "put_call_prev",
        ]:
            if column in merged.columns:
                merged[column] = merged[column].replace(0, "")

        merged["issuer"] = merged["issuer_curr"].where(merged["issuer_curr"] != "", merged["issuer_prev"])
        merged["issuer_key"] = merged["issuer"].apply(self._normalize_issuer_key)
        merged["class_title"] = merged["class_title_curr"].where(merged["class_title_curr"] != "", merged["class_title_prev"])
        merged["cusip"] = merged["cusip_curr"].where(merged["cusip_curr"] != "", merged["cusip_prev"])
        merged["put_call"] = merged["put_call_curr"].where(merged["put_call_curr"] != "", merged["put_call_prev"])
        merged["value_change"] = merged["value_usd_curr"] - merged["value_usd_prev"]
        merged["weight_change"] = merged["portfolio_weight_curr"] - merged["portfolio_weight_prev"]

        def _action(row: pd.Series) -> str:
            if row["value_usd_prev"] == 0 and row["value_usd_curr"] > 0:
                return "NEW"
            if row["value_usd_curr"] == 0 and row["value_usd_prev"] > 0:
                return "SOLD"
            if row["value_change"] > 0:
                return "INCREASED"
            if row["value_change"] < 0:
                return "DECREASED"
            return "UNCHANGED"

        merged["action"] = merged.apply(_action, axis=1)
        return merged.reset_index(drop=True)

    def _holdings_rows(self, frame: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
        if frame is None or frame.empty:
            return []
        rows = []
        for _, row in frame.head(limit).iterrows():
            rows.append(
                {
                    "issuer": row.get("issuer", "N/A"),
                    "class_title": row.get("class_title", "N/A"),
                    "put_call": row.get("put_call", "Equity"),
                    "value": _fmt_compact_money(row.get("value_usd")),
                    "portfolio_weight": _fmt_pct(row.get("portfolio_weight")),
                    "shares": _fmt_number(row.get("shares"), 0),
                }
            )
        return rows

    def _serialize_dataset(
        self,
        manager_key: str,
        latest_filing: Dict[str, str],
        previous_filing: Dict[str, str] | None,
        current_df: pd.DataFrame,
        changes_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        manager = self.MANAGERS[manager_key]
        current_total = float(current_df["value_usd"].sum()) if not current_df.empty else 0.0
        top_10_weight = float(current_df.head(10)["portfolio_weight"].sum()) if not current_df.empty else 0.0
        option_value = (
            float(current_df[current_df["put_call"].str.upper() != "EQUITY"]["value_usd"].sum())
            if not current_df.empty
            else 0.0
        )
        largest_position = current_df.iloc[0].to_dict() if not current_df.empty else {}
        try:
            filing_lag_days = (
                datetime.now(timezone.utc).date() - datetime.strptime(latest_filing["filing_date"], "%Y-%m-%d").date()
            ).days
        except Exception:
            filing_lag_days = 0

        return {
            "selected_manager": manager_key,
            "manager": manager,
            "source_state": "live",
            "generated_at": _now_iso(),
            "latest_filing": latest_filing,
            "previous_filing": previous_filing,
            "current_rows": current_df.to_dict("records"),
            "changes_rows": changes_df.to_dict("records"),
            "summary": {
                "portfolio_value": _fmt_compact_money(current_total),
                "holding_count": int(len(current_df)),
                "top_10_weight": _fmt_pct(top_10_weight),
                "option_exposure": _fmt_pct((option_value / current_total) * 100 if current_total else 0),
                "largest_position": largest_position.get("issuer", "N/A"),
                "largest_position_weight": _fmt_pct(largest_position.get("portfolio_weight")),
                "filing_lag_days": filing_lag_days,
                "new_positions": int((changes_df["action"] == "NEW").sum()) if not changes_df.empty else 0,
                "exited_positions": int((changes_df["action"] == "SOLD").sum()) if not changes_df.empty else 0,
            },
        }

    def _build_dataset(self, manager_key: str) -> Dict[str, Any]:
        manager = self.MANAGERS[manager_key]
        filings = self._recent_13f_filings(manager["cik"], limit=2)
        if not filings:
            raise RuntimeError("No recent 13F filings were found for this manager.")

        latest_filing = filings[0]
        current_df = self._fetch_holdings_frame(manager["cik"], latest_filing)
        previous_filing = filings[1] if len(filings) > 1 else None
        previous_df = self._fetch_holdings_frame(manager["cik"], previous_filing) if previous_filing else pd.DataFrame()
        changes_df = self._compare_holdings_frames(current_df, previous_df)
        return self._serialize_dataset(manager_key, latest_filing, previous_filing, current_df, changes_df)

    def _dataset_fallback(self, manager_key: str, exc: Exception) -> Dict[str, Any]:
        snapshot = self.snapshot_store.read_json(self._dataset_snapshot_key(manager_key))
        if snapshot:
            snapshot["source_state"] = "snapshot"
            snapshot["warning"] = "Live SEC refresh failed, so FundPilot is serving the latest persisted manager dataset."
            return snapshot
        manager = self.MANAGERS[manager_key]
        return {
            "selected_manager": manager_key,
            "manager": manager,
            "source_state": "warming",
            "generated_at": _now_iso(),
            "warning": str(exc),
            "latest_filing": None,
            "previous_filing": None,
            "current_rows": [],
            "changes_rows": [],
            "summary": {
                "portfolio_value": "N/A",
                "holding_count": 0,
                "top_10_weight": "N/A",
                "option_exposure": "N/A",
                "largest_position": "N/A",
                "largest_position_weight": "N/A",
                "filing_lag_days": 0,
                "new_positions": 0,
                "exited_positions": 0,
            },
        }

    def get_manager_dataset(self, manager_key: str | None) -> Dict[str, Any]:
        selected_manager = self._selected_manager(manager_key)
        cache_key = self._dataset_cache_key(selected_manager)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        try:
            dataset = self._build_dataset(selected_manager)
        except Exception as exc:
            dataset = self._dataset_fallback(selected_manager, exc)
            cache_set(cache_key, dataset, ttl=900)
            return dataset

        cache_set(cache_key, dataset, ttl=self.ttl_seconds)
        self.snapshot_store.write_json(self._dataset_snapshot_key(selected_manager), dataset)
        return dataset

    def _movement_rows(self, frame: pd.DataFrame, action: str, limit: int = 8) -> List[Dict[str, Any]]:
        if frame is None or frame.empty:
            return []
        subset = frame[frame["action"] == action].copy()
        if subset.empty:
            return []
        primary_column = "value_usd_curr" if action in {"NEW", "INCREASED"} else "value_usd_prev"
        subset = subset.sort_values(primary_column, ascending=False).head(limit)
        rows = []
        for _, row in subset.iterrows():
            rows.append(
                {
                    "issuer": row.get("issuer", "N/A"),
                    "class_title": row.get("class_title", "N/A"),
                    "current_value": _fmt_compact_money(row.get("value_usd_curr")),
                    "previous_value": _fmt_compact_money(row.get("value_usd_prev")),
                    "value_change": _fmt_compact_money(row.get("value_change")),
                    "weight_change": _fmt_pct(row.get("weight_change")),
                }
            )
        return rows

    def _consensus_rows(self, datasets: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        coverage_rows: List[Dict[str, Any]] = []
        success_count = 0
        for manager_key, dataset in datasets.items():
            holdings = self._frame_from_rows(dataset.get("current_rows", []))
            filing = dataset.get("latest_filing")
            if holdings.empty or not filing:
                continue
            success_count += 1
            manager_name = self.MANAGERS[manager_key]["manager_name"]
            for _, row in holdings.head(25).iterrows():
                coverage_rows.append(
                    {
                        "holding_key": row.get("holding_key"),
                        "issuer_key": row.get("issuer_key"),
                        "issuer": row.get("issuer"),
                        "manager": manager_name,
                        "portfolio_weight": float(row.get("portfolio_weight", 0) or 0),
                        "filing_date": filing["filing_date"],
                    }
                )

        if not coverage_rows:
            return [], success_count

        frame = pd.DataFrame(coverage_rows)
        grouped = (
            frame.groupby(["issuer_key"], dropna=False)
            .agg(
                issuer=("issuer", lambda values: sorted(set(values))[0]),
                manager_count=("manager", "nunique"),
                combined_weight=("portfolio_weight", "sum"),
                max_weight=("portfolio_weight", "max"),
                managers=("manager", lambda values: sorted(set(values))),
                latest_filing=("filing_date", "max"),
            )
            .reset_index()
        )
        grouped = grouped[grouped["manager_count"] >= 2].sort_values(
            ["manager_count", "combined_weight", "max_weight"],
            ascending=[False, False, False],
        )

        rows = []
        for _, row in grouped.head(10).iterrows():
            rows.append(
                {
                    "issuer": row.get("issuer", "N/A"),
                    "manager_count": int(row.get("manager_count", 0) or 0),
                    "managers": ", ".join(row.get("managers", [])),
                    "combined_weight": _fmt_pct(row.get("combined_weight")),
                    "max_weight": _fmt_pct(row.get("max_weight")),
                    "latest_filing": row.get("latest_filing", "N/A"),
                }
            )
        return rows, success_count

    def _coverage_rows(self, datasets: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for manager_key in self.manager_keys():
            dataset = datasets.get(manager_key) or self.get_manager_dataset(manager_key)
            manager = self.MANAGERS[manager_key]
            summary = dataset.get("summary", {}) or {}
            latest_filing = dataset.get("latest_filing") or {}
            rows.append(
                {
                    "manager_key": manager_key,
                    "manager_name": manager["manager_name"],
                    "label": manager["label"],
                    "style": manager["style"],
                    "source_state": dataset.get("source_state", "warming"),
                    "latest_filing": latest_filing.get("filing_date", "N/A"),
                    "holding_count": int(summary.get("holding_count", 0) or 0),
                    "portfolio_value": summary.get("portfolio_value", "N/A"),
                    "largest_position": summary.get("largest_position", "N/A"),
                    "top_10_weight": summary.get("top_10_weight", "N/A"),
                    "new_positions": int(summary.get("new_positions", 0) or 0),
                    "exited_positions": int(summary.get("exited_positions", 0) or 0),
                    "filing_lag_days": int(summary.get("filing_lag_days", 0) or 0),
                }
            )

        state_rank = {"live": 0, "snapshot": 1, "warming": 2}
        return sorted(
            rows,
            key=lambda row: (
                state_rank.get(str(row.get("source_state", "warming")), 3),
                -int(row.get("holding_count", 0) or 0),
                str(row.get("label", "")),
            ),
        )

    def get_health_snapshot(self) -> Dict[str, Any]:
        datasets = {manager_key: self.get_manager_dataset(manager_key) for manager_key in self.manager_keys()}
        coverage_rows = self._coverage_rows(datasets)
        live_count = sum(1 for row in coverage_rows if row["source_state"] == "live")
        snapshot_count = sum(1 for row in coverage_rows if row["source_state"] == "snapshot")
        warming_count = sum(1 for row in coverage_rows if row["source_state"] == "warming")
        latest_filing_dates = [str(row["latest_filing"]) for row in coverage_rows if row.get("latest_filing") not in {"", "N/A"}]
        latest_filing = max(latest_filing_dates) if latest_filing_dates else "N/A"

        if live_count == len(coverage_rows) and live_count > 0:
            state = "healthy"
            state_label = "Healthy"
        elif live_count > 0 or snapshot_count > 0:
            state = "degraded"
            state_label = "Degraded"
        else:
            state = "warming"
            state_label = "Refreshing"

        return {
            "key": "institutional",
            "label": "Institutional filings",
            "state": state,
            "state_label": state_label,
            "detail": (
                f"{live_count} live, {snapshot_count} snapshot, {warming_count} warming managers. "
                f"Latest filing {latest_filing}."
            ),
            "updated_at": _now_iso(),
            "summary": {
                "manager_count": len(coverage_rows),
                "live_count": live_count,
                "snapshot_count": snapshot_count,
                "warming_count": warming_count,
                "latest_filing": latest_filing,
            },
        }

    def _workspace_from_dataset(self, dataset: Dict[str, Any], datasets_by_manager: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        selected_manager = dataset["selected_manager"]
        current_df = self._frame_from_rows(dataset.get("current_rows", []))
        changes_df = self._frame_from_rows(dataset.get("changes_rows", []))
        consensus_rows, consensus_coverage = self._consensus_rows(datasets_by_manager)
        coverage_rows = self._coverage_rows(datasets_by_manager)
        coverage_summary = {
            "manager_count": len(coverage_rows),
            "live_count": sum(1 for row in coverage_rows if row["source_state"] == "live"),
            "snapshot_count": sum(1 for row in coverage_rows if row["source_state"] == "snapshot"),
            "warming_count": sum(1 for row in coverage_rows if row["source_state"] == "warming"),
            "latest_filing": max(
                [str(row["latest_filing"]) for row in coverage_rows if row.get("latest_filing") not in {"", "N/A"}],
                default="N/A",
            ),
        }
        return {
            "selected_manager": selected_manager,
            "manager_options": self._manager_options(),
            "manager": dataset["manager"],
            "error": None,
            "warning": dataset.get("warning"),
            "source_state": dataset.get("source_state", "live"),
            "generated_at": dataset.get("generated_at", _now_iso()),
            "source_note": "Official SEC EDGAR 13F filings. Positions can lag quarter-end by up to 45 days.",
            "summary": dataset.get("summary", {}),
            "latest_filing": dataset.get("latest_filing"),
            "previous_filing": dataset.get("previous_filing"),
            "top_holdings": self._holdings_rows(current_df, limit=10),
            "new_positions": self._movement_rows(changes_df, "NEW", limit=8),
            "added_positions": self._movement_rows(changes_df, "INCREASED", limit=8),
            "trimmed_positions": self._movement_rows(changes_df, "DECREASED", limit=8),
            "sold_positions": self._movement_rows(changes_df, "SOLD", limit=8),
            "consensus_rows": consensus_rows,
            "consensus_coverage": consensus_coverage,
            "coverage_rows": coverage_rows,
            "coverage_summary": coverage_summary,
            "methodology": [
                "Latest and previous 13F filings are compared filing-by-filing.",
                "Top holdings use reported market value, not live prices.",
                "Adds, trims, and exits are ranked by reported position size.",
                "Consensus only counts names present in at least two curated manager portfolios.",
            ],
        }

    def _snapshot_fallback(self, manager_key: str, exc: Exception) -> Dict[str, Any]:
        snapshot = self.snapshot_store.read_json(self._snapshot_key(manager_key))
        if snapshot:
            snapshot["source_state"] = "snapshot"
            snapshot["warning"] = "Live SEC refresh failed, so FundPilot is serving the latest persisted 13F snapshot."
            snapshot["error"] = None
            return snapshot

        manager = self.MANAGERS[manager_key]
        return {
            "selected_manager": manager_key,
            "manager_options": self._manager_options(),
            "manager": manager,
            "error": "Institutional Pulse is refreshing and the live SEC dataset is not ready yet.",
            "warning": str(exc),
            "source_state": "warming",
            "generated_at": _now_iso(),
            "source_note": "Official SEC EDGAR 13F filings. Positions can lag quarter-end by up to 45 days.",
            "summary": {
                "portfolio_value": "N/A",
                "holding_count": 0,
                "top_10_weight": "N/A",
                "option_exposure": "N/A",
                "largest_position": "N/A",
                "largest_position_weight": "N/A",
                "filing_lag_days": 0,
                "new_positions": 0,
                "exited_positions": 0,
            },
            "latest_filing": None,
            "previous_filing": None,
            "top_holdings": [],
            "new_positions": [],
            "added_positions": [],
            "trimmed_positions": [],
            "sold_positions": [],
            "consensus_rows": [],
            "consensus_coverage": 0,
            "methodology": [
                "Latest and previous 13F filings are compared filing-by-filing.",
                "Top holdings use reported market value, not live prices.",
            ],
        }

    def get_workspace(self, manager_key: str | None) -> Dict[str, Any]:
        selected_manager = self._selected_manager(manager_key)
        cache_key = self._cache_key(selected_manager)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        dataset = self.get_manager_dataset(selected_manager)
        if dataset.get("source_state") == "warming":
            workspace = self._snapshot_fallback(selected_manager, RuntimeError(dataset.get("warning", "warming")))
            cache_set(cache_key, workspace, ttl=900)
            return workspace

        datasets_by_manager = {selected_manager: dataset}
        for manager_name in self.manager_keys():
            if manager_name == selected_manager:
                continue
            datasets_by_manager[manager_name] = self.get_manager_dataset(manager_name)

        workspace = self._workspace_from_dataset(dataset, datasets_by_manager)

        cache_set(cache_key, workspace, ttl=self.ttl_seconds)
        self.snapshot_store.write_json(self._snapshot_key(selected_manager), workspace)
        return workspace

    def _symbol_signal_for_match(self, current_matches: pd.DataFrame, change_matches: pd.DataFrame) -> str:
        if not current_matches.empty:
            if "NEW" in set(change_matches.get("action", [])):
                return "New"
            if "INCREASED" in set(change_matches.get("action", [])):
                return "Added"
            if "DECREASED" in set(change_matches.get("action", [])):
                return "Trimmed"
            return "Held"
        if not change_matches.empty and "SOLD" in set(change_matches.get("action", [])):
            return "Exited"
        return "No Match"

    def get_symbol_signal(self, symbol: str, issuer_name: str | None = None) -> Dict[str, Any]:
        symbol = str(symbol or "").upper().strip()
        cache_key = f"institutional-pulse-symbol:{symbol}:{self._normalize_issuer_key(issuer_name or symbol)}"
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        if not symbol or "." in symbol:
            result = {
                "available": False,
                "coverage": "13F coverage is strongest for US-listed names; this symbol is outside the curated filing lens.",
                "signal": "Unavailable",
                "supported_market": False,
                "manager_rows": [],
                "exited_rows": [],
                "summary": {
                    "holder_count": 0,
                    "total_weight": "N/A",
                    "top_holder": "N/A",
                    "bullish_managers": 0,
                    "bearish_managers": 0,
                    "fresh_buyers": 0,
                    "exited_managers": 0,
                },
            }
            cache_set(cache_key, result, ttl=1800)
            return result

        candidate_keys = {self._normalize_issuer_key(symbol)}
        if issuer_name:
            candidate_keys.add(self._normalize_issuer_key(issuer_name))
        candidate_keys = {item for item in candidate_keys if item}

        manager_rows: List[Dict[str, Any]] = []
        exited_rows: List[Dict[str, Any]] = []
        for manager_key in self.manager_keys():
            dataset = self.get_manager_dataset(manager_key)
            if dataset.get("source_state") == "warming":
                continue
            current_df = self._frame_from_rows(dataset.get("current_rows", []))
            change_df = self._frame_from_rows(dataset.get("changes_rows", []))
            if current_df.empty and change_df.empty:
                continue

            current_matches = current_df[current_df["issuer_key"].isin(candidate_keys)].copy() if "issuer_key" in current_df.columns else pd.DataFrame()
            change_matches = change_df[change_df["issuer_key"].isin(candidate_keys)].copy() if "issuer_key" in change_df.columns else pd.DataFrame()
            if current_matches.empty and change_matches.empty:
                continue

            signal = self._symbol_signal_for_match(current_matches, change_matches)
            filing = dataset.get("latest_filing") or {}
            manager_entry = {
                "manager": self.MANAGERS[manager_key]["manager_name"],
                "manager_label": self.MANAGERS[manager_key]["label"],
                "style": self.MANAGERS[manager_key]["style"],
                "filing_date": filing.get("filing_date", "N/A"),
                "signal": signal,
                "current_value": _fmt_compact_money(current_matches["value_usd"].sum()) if not current_matches.empty else "$0",
                "portfolio_weight": _fmt_pct(current_matches["portfolio_weight"].sum()) if not current_matches.empty else "0.0%",
                "weight_change": _fmt_pct(change_matches["weight_change"].sum()) if not change_matches.empty else "0.0%",
            }
            if not current_matches.empty:
                manager_rows.append(manager_entry)
            elif signal == "Exited":
                exited_rows.append(manager_entry)

        manager_rows = sorted(
            manager_rows,
            key=lambda row: _safe_float(str(row["portfolio_weight"]).replace("%", "")),
            reverse=True,
        )
        exited_rows = sorted(
            exited_rows,
            key=lambda row: abs(_safe_float(str(row["weight_change"]).replace("%", ""))),
            reverse=True,
        )

        bullish = sum(1 for row in manager_rows if row["signal"] in {"New", "Added"})
        fresh_buyers = bullish
        bearish = len(exited_rows) + sum(1 for row in manager_rows if row["signal"] == "Trimmed")
        total_weight = sum(_safe_float(str(row["portfolio_weight"]).replace("%", "")) for row in manager_rows)
        if len(manager_rows) >= 3 and bullish >= bearish:
            signal_label = "Crowded Long"
        elif bullish > bearish and manager_rows:
            signal_label = "Accumulating"
        elif bearish > bullish and (manager_rows or exited_rows):
            signal_label = "Distribution"
        elif manager_rows:
            signal_label = "Held"
        else:
            signal_label = "Not Present"

        result = {
            "available": bool(manager_rows or exited_rows),
            "coverage": "Curated SEC 13F manager set. This is delayed positioning data, not real-time flow.",
            "signal": signal_label,
            "supported_market": True,
            "manager_rows": manager_rows[:8],
            "exited_rows": exited_rows[:6],
            "summary": {
                "holder_count": len(manager_rows),
                "total_weight": _fmt_pct(total_weight),
                "top_holder": manager_rows[0]["manager"] if manager_rows else "N/A",
                "bullish_managers": bullish,
                "bearish_managers": bearish,
                "fresh_buyers": fresh_buyers,
                "exited_managers": len(exited_rows),
            },
        }
        cache_set(cache_key, result, ttl=3600)
        return result
