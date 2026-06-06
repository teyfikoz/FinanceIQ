from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Dict

from app.core.config import settings
from app.services.cache import cache_get, cache_set
from app.services.kap_site_scraper import KAPSiteScraper
from app.services.snapshot_store import SnapshotStore
from app.utils.logger import get_logger

logger = get_logger(__name__)

CURATED_BIST_DISCLOSURE_SYMBOLS = (
    "ASELS",
    "THYAO",
    "TUPRS",
    "GARAN",
    "BIMAS",
)


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
        if number != number or number in (float("inf"), float("-inf")):
            return None
        return number
    except Exception:
        return None


class StockEnrichmentService:
    def __init__(
        self,
        ttl_seconds: int | None = None,
        snapshot_store: SnapshotStore | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds or settings.PUBLIC_RESEARCH_TTL_SECONDS
        self.snapshot_store = snapshot_store or SnapshotStore()
        self.kap_site_scraper = KAPSiteScraper(
            ttl_seconds=self.ttl_seconds,
            snapshot_store=self.snapshot_store,
        )

    def _cache_key(self, symbol_root: str) -> str:
        return f"public-stock-enrichment:{symbol_root.upper()}"

    def _snapshot_key(self, symbol_root: str) -> str:
        return f"public-stock-enrichment-{symbol_root.upper()}"

    def _normalize_key(self, value: Any) -> str:
        ascii_text = (
            unicodedata.normalize("NFKD", str(value or ""))
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )
        return re.sub(r"[^a-z0-9]", "", ascii_text)

    def _flatten_payload(self, payload: Any, prefix: str = "") -> Dict[str, Any]:
        flattened: Dict[str, Any] = {}
        if isinstance(payload, dict):
            for key, value in payload.items():
                joined = f"{prefix}.{key}" if prefix else str(key)
                flattened[joined] = value
                flattened.update(self._flatten_payload(value, joined))
        elif isinstance(payload, list):
            flattened[prefix] = len(payload)
            for index, value in enumerate(payload):
                joined = f"{prefix}[{index}]"
                flattened[joined] = value
                flattened.update(self._flatten_payload(value, joined))
        return flattened

    def _find_numeric_by_hint(self, flattened: Dict[str, Any], hints: list[str]) -> float | None:
        normalized_hints = [self._normalize_key(hint) for hint in hints]
        for key, value in flattened.items():
            normalized_key = self._normalize_key(key)
            if any(hint in normalized_key for hint in normalized_hints):
                numeric = _safe_float(value)
                if numeric is not None:
                    return numeric
        return None

    def _find_list_count_by_hint(self, payload: Any, hints: list[str], prefix: str = "") -> int | None:
        normalized_hints = [self._normalize_key(hint) for hint in hints]
        if isinstance(payload, dict):
            for key, value in payload.items():
                joined = f"{prefix}.{key}" if prefix else str(key)
                normalized_key = self._normalize_key(joined)
                if isinstance(value, list) and any(hint in normalized_key for hint in normalized_hints):
                    return len(value)
                nested = self._find_list_count_by_hint(value, hints, joined)
                if nested is not None:
                    return nested
        elif isinstance(payload, list):
            for index, value in enumerate(payload):
                nested = self._find_list_count_by_hint(value, hints, f"{prefix}[{index}]")
                if nested is not None:
                    return nested
        return None

    def _find_latest_date_by_hint(self, flattened: Dict[str, Any], hints: list[str]) -> str | None:
        normalized_hints = [self._normalize_key(hint) for hint in hints]
        best: datetime | None = None
        for key, value in flattened.items():
            normalized_key = self._normalize_key(key)
            if not any(hint in normalized_key for hint in normalized_hints):
                continue
            parsed = self._parse_date(value)
            if parsed is None:
                continue
            if best is None or parsed > best:
                best = parsed
        return best.date().isoformat() if best is not None else None

    def _parse_date(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text:
            return None
        iso_candidate = text.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(iso_candidate)
        except Exception:
            pass
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(text[:10], fmt)
            except Exception:
                continue
        return None

    def _empty_snapshot(self, symbol_root: str, source_state: str = "unavailable") -> Dict[str, Any]:
        return {
            "symbol_root": symbol_root.upper(),
            "source_state": source_state,
            "saved_at": None,
            "raw_payload_present": False,
            "field_coverage": 0,
            "paid_in_capital": None,
            "capital_method": None,
            "contract_value_ttm": None,
            "contract_to_sales_ratio_ttm": None,
            "backlog_value": None,
            "disclosures_count": None,
            "disclosures_count_90d": None,
            "material_disclosures_90d": None,
            "contract_mentions_365d": None,
            "disclosure_momentum_score": None,
            "contract_signal_confidence": None,
            "last_disclosure_date": None,
            "coverage_note": "No structured KAP enrichment is available yet.",
        }

    def _has_persistable_signal(self, snapshot: Dict[str, Any]) -> bool:
        return any(
            snapshot.get(field) is not None
            for field in (
                "paid_in_capital",
                "contract_value_ttm",
                "contract_to_sales_ratio_ttm",
                "backlog_value",
                "disclosures_count",
                "material_disclosures_90d",
                "contract_mentions_365d",
                "disclosure_momentum_score",
                "last_disclosure_date",
            )
        )

    def _normalize_snapshot(self, snapshot: Dict[str, Any], symbol_root: str) -> Dict[str, Any]:
        normalized = self._empty_snapshot(symbol_root, snapshot.get("source_state", "persisted"))
        normalized.update(snapshot)
        normalized["symbol_root"] = symbol_root.upper()
        normalized["field_coverage"] = int(snapshot.get("field_coverage") or 0)
        if normalized["field_coverage"] == 0:
            normalized["field_coverage"] = sum(
                1
                for field in (
                    "paid_in_capital",
                    "contract_value_ttm",
                    "contract_to_sales_ratio_ttm",
                    "backlog_value",
                    "disclosures_count",
                    "material_disclosures_90d",
                    "contract_mentions_365d",
                    "disclosure_momentum_score",
                    "last_disclosure_date",
                )
                if normalized.get(field) is not None
            )
        return normalized

    def _fetch_company_payload(self, symbol_root: str) -> Dict[str, Any]:
        try:
            payload = self.kap_site_scraper.get_company_payload(symbol_root)
            if isinstance(payload, dict) and payload:
                return payload
        except Exception as exc:
            logger.warning("KAP public site scrape failed", symbol=symbol_root, error=str(exc))

        try:
            from api.kap_integration import KAPVYKClient

            client = KAPVYKClient()
            payload = client.get_company_info(symbol_root)
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            logger.warning("KAP enrichment fetch failed", symbol=symbol_root, error=str(exc))
            return {}

    def _build_live_snapshot(self, symbol_root: str) -> Dict[str, Any]:
        payload = self._fetch_company_payload(symbol_root)
        flattened = self._flatten_payload(payload)
        paid_in_capital = _safe_float(payload.get("paid_in_capital"))
        if paid_in_capital is None:
            paid_in_capital = self._find_numeric_by_hint(
                flattened,
                ["paid in capital", "odenmis sermaye", "cikarilmis sermaye", "nominal capital", "share capital"],
            )
        contract_value_ttm = _safe_float(payload.get("contract_value_ttm"))
        if contract_value_ttm is None:
            contract_value_ttm = self._find_numeric_by_hint(
                flattened,
                [
                    "new business value",
                    "contract value",
                    "sozlesme tutari",
                    "new contracts value",
                    "siparis tutari",
                    "order value",
                ],
            )
        backlog_value = _safe_float(payload.get("backlog_value"))
        if backlog_value is None:
            backlog_value = self._find_numeric_by_hint(
                flattened,
                ["order backlog", "backlog", "is backlog", "remaining order", "siparis bakiyesi"],
            )
        contract_to_sales_ratio_ttm = _safe_float(payload.get("contract_to_sales_ratio_ttm"))
        disclosures_count = _safe_float(payload.get("disclosures_count"))
        if disclosures_count is None:
            disclosures_count = self._find_numeric_by_hint(
                flattened,
                ["announcement count", "disclosure count", "kap count", "ozel durum aciklama"],
            )
        if disclosures_count is None:
            list_count = self._find_list_count_by_hint(payload, ["announcements", "disclosures", "special disclosures"])
            disclosures_count = float(list_count) if list_count is not None else None
        disclosures_count_90d = _safe_float(payload.get("disclosures_count_90d"))
        material_disclosures_90d = _safe_float(payload.get("material_disclosures_90d"))
        contract_mentions_365d = _safe_float(payload.get("contract_mentions_365d"))
        disclosure_momentum_score = _safe_float(payload.get("disclosure_momentum_score"))
        last_disclosure_date = payload.get("last_disclosure_date")
        if last_disclosure_date is None:
            last_disclosure_date = self._find_latest_date_by_hint(
                flattened,
                ["announcement date", "disclosure date", "kap date", "publish date", "announcementdatetime"],
            )

        field_coverage = sum(
            1
            for field in (
                paid_in_capital,
                contract_value_ttm,
                contract_to_sales_ratio_ttm,
                backlog_value,
                disclosures_count,
                disclosures_count_90d,
                material_disclosures_90d,
                contract_mentions_365d,
                disclosure_momentum_score,
                last_disclosure_date,
            )
            if field is not None
        )
        source_state = "live" if field_coverage > 0 else "partial" if payload else "unavailable"
        coverage_note = (
            "Structured KAP enrichment is live."
            if field_coverage > 0
            else "KAP payload resolved but core capital fields were not structured."
            if payload
            else "KAP enrichment is temporarily unavailable."
        )
        return {
            "symbol_root": symbol_root.upper(),
            "source_state": source_state,
            "saved_at": datetime.utcnow().isoformat() + "Z",
            "raw_payload_present": bool(payload.get("raw_payload_present", bool(payload)))
            if isinstance(payload, dict)
            else bool(payload),
            "field_coverage": field_coverage,
            "paid_in_capital": paid_in_capital,
            "capital_method": str(payload.get("capital_method") or "Exact KAP field via enrichment snapshot")
            if paid_in_capital is not None
            else None,
            "contract_value_ttm": contract_value_ttm,
            "contract_to_sales_ratio_ttm": contract_to_sales_ratio_ttm,
            "backlog_value": backlog_value,
            "disclosures_count": disclosures_count,
            "disclosures_count_90d": disclosures_count_90d,
            "material_disclosures_90d": material_disclosures_90d,
            "contract_mentions_365d": contract_mentions_365d,
            "disclosure_momentum_score": disclosure_momentum_score,
            "contract_signal_confidence": str(payload.get("contract_signal_confidence") or "") or None,
            "last_disclosure_date": last_disclosure_date,
            "coverage_note": str(payload.get("coverage_note") or coverage_note),
        }

    def get_kap_enrichment(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        symbol_root = str(symbol or "").split(".")[0].upper()
        if not symbol_root:
            return self._empty_snapshot("UNKNOWN")

        cache_key = self._cache_key(symbol_root)
        if not force_refresh:
            cached = cache_get(cache_key)
            if isinstance(cached, dict):
                return self._normalize_snapshot(cached, symbol_root)
            persisted = self.snapshot_store.read_json(self._snapshot_key(symbol_root))
            if isinstance(persisted, dict):
                normalized = self._normalize_snapshot(persisted, symbol_root)
                cache_set(cache_key, normalized, ttl=self.ttl_seconds)
                return normalized

        live_snapshot = self._build_live_snapshot(symbol_root)
        if self._has_persistable_signal(live_snapshot):
            cache_set(cache_key, live_snapshot, ttl=self.ttl_seconds)
            self.snapshot_store.write_json(self._snapshot_key(symbol_root), live_snapshot)
            return live_snapshot

        persisted = self.snapshot_store.read_json(self._snapshot_key(symbol_root))
        if isinstance(persisted, dict):
            normalized = self._normalize_snapshot(persisted, symbol_root)
            if self._has_persistable_signal(normalized):
                fallback = dict(normalized)
                fallback["source_state"] = "persisted-fallback"
                fallback["stale_notice"] = (
                    f"Live KAP enrichment failed for {symbol_root}; using the last persisted enrichment snapshot."
                )
                cache_set(cache_key, fallback, ttl=min(self.ttl_seconds, 900))
                return fallback

        ttl = min(self.ttl_seconds, 600)
        cache_set(cache_key, live_snapshot, ttl=ttl)
        return live_snapshot

    def get_health_snapshot(self, symbols: tuple[str, ...] | None = None) -> Dict[str, Any]:
        tracked_symbols = [str(symbol).split(".")[0].upper() for symbol in (symbols or CURATED_BIST_DISCLOSURE_SYMBOLS)]
        rows: list[Dict[str, Any]] = []
        snapshots: list[Dict[str, Any]] = []
        latest_disclosure: datetime | None = None

        for symbol_root in tracked_symbols:
            snapshot = self.get_kap_enrichment(symbol_root, force_refresh=False)
            snapshots.append(snapshot)
            parsed_date = self._parse_date(snapshot.get("last_disclosure_date"))
            if parsed_date is not None and (latest_disclosure is None or parsed_date > latest_disclosure):
                latest_disclosure = parsed_date
            rows.append(
                {
                    "symbol": symbol_root,
                    "source_state": str(snapshot.get("source_state") or "warming"),
                    "field_coverage": int(snapshot.get("field_coverage") or 0),
                    "saved_at": str(snapshot.get("saved_at") or ""),
                    "last_disclosure_date": str(snapshot.get("last_disclosure_date") or "N/A"),
                    "contract_to_sales_ratio_ttm": snapshot.get("contract_to_sales_ratio_ttm"),
                    "disclosure_momentum_score": snapshot.get("disclosure_momentum_score"),
                    "coverage_note": str(snapshot.get("coverage_note") or ""),
                }
            )

        live_count = sum(1 for row in rows if row["source_state"] == "live")
        fallback_count = sum(1 for row in rows if row["source_state"] in {"persisted-fallback", "partial"})
        unavailable_count = sum(1 for row in rows if row["source_state"] == "unavailable")
        average_coverage = round(
            sum(float(row["field_coverage"]) for row in rows) / len(rows),
            1,
        ) if rows else 0.0

        if rows and unavailable_count == 0 and live_count == len(rows):
            state = "healthy"
            state_label = "Healthy"
            detail = f"Structured KAP enrichment is live for all {len(rows)} curated BIST names."
        elif rows and (live_count > 0 or fallback_count > 0):
            state = "degraded"
            state_label = "Fallback Active"
            detail = (
                f"{live_count} live, {fallback_count} fallback, {unavailable_count} unavailable "
                "across curated BIST disclosure leaders."
            )
        else:
            state = "warming"
            state_label = "Refreshing"
            detail = "Curated BIST disclosure enrichment is still warming."

        updated_at = max([str(snapshot.get("saved_at") or "") for snapshot in snapshots] or [""])
        updated_at = updated_at or datetime.utcnow().isoformat() + "Z"

        return {
            "key": "kap-enrichment",
            "label": "BIST disclosures",
            "state": state,
            "state_label": state_label,
            "detail": detail,
            "updated_at": updated_at,
            "summary": {
                "symbols_tracked": len(rows),
                "live_count": live_count,
                "fallback_count": fallback_count,
                "unavailable_count": unavailable_count,
                "average_field_coverage": average_coverage,
                "latest_disclosure_date": latest_disclosure.date().isoformat() if latest_disclosure is not None else "N/A",
            },
            "rows": rows,
        }
