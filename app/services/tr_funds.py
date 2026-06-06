from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Dict, Optional, Type
import unicodedata

import pandas as pd

from app.data_collectors.tefas_portfolio_tracker import TEFASPortfolioTracker
from app.services.cache import cache_get, cache_set
from app.services.snapshot_store import SnapshotStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


POPULAR_FUNDS: Dict[str, str] = {
    "TCD": "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu",
    "YAT": "Yapi Kredi Portfoy Hisse Senedi Fonu",
    "GAH": "Garanti Portfoy Hisse Senedi Fonu",
    "FBA": "Finans Portfoy Birinci Hisse Senedi Fonu",
    "AKG": "Ak Portfoy Kisa Vadeli Borclanma Araclari Fonu",
    "ZPE": "Ziraat Portfoy Hisse Senedi Fonu",
}

FEATURED_FUND_CODES: tuple[str, ...] = ("TCD", "AFT", "YAT", "GPD")

ASSET_LABELS = {
    "stocks": "Hisse",
    "bonds": "Tahvil",
    "bills": "Bono",
    "repo": "Repo",
    "fx": "Doviz",
    "participation": "Katilim",
    "precious_metals": "Kiymetli Maden",
    "other": "Diger",
}


def _dominant_asset(asset_allocation: Dict[str, float]) -> tuple[str, float]:
    if not asset_allocation:
        return "Belirsiz", 0.0
    key = max(asset_allocation, key=lambda item: asset_allocation.get(item, 0.0))
    return ASSET_LABELS.get(key, key.title()), float(asset_allocation.get(key, 0.0))


def _fund_regime(summary: Dict[str, Any]) -> tuple[str, str]:
    value_delta = float(summary.get("portfolio_value_change", 0) or 0)
    investor_delta = float(summary.get("investor_change", 0) or 0)
    added = int(summary.get("total_new_holdings", 0) or 0)
    removed = int(summary.get("total_removed_holdings", 0) or 0)

    if value_delta > 0 and investor_delta > 0:
        return "Accumulation", "Net deger ve yatirimci ilgisi birlikte artiyor."
    if value_delta < 0 and investor_delta < 0:
        return "Distribution", "Hem varlik tabani hem de yatirimci ilgisi geriliyor."
    if added > removed and investor_delta >= 0:
        return "Rotation", "Portfoy yeniden konumlaniyor; yeni eklemeler daha baskin."
    return "Mixed", "Sinyaller karisik; daha detayli akim analizi gerekli."


def _safe_growth_pct(latest_value: float, delta_value: float) -> float:
    latest = float(latest_value or 0)
    delta = float(delta_value or 0)
    base = latest - delta
    if abs(base) < 1e-9:
        return 0.0
    return (delta / abs(base)) * 100


def _latest_allocation_drift(summary: Dict[str, Any]) -> float:
    monthly_changes = summary.get("monthly_allocation_changes", []) or []
    if not monthly_changes:
        return 0.0

    latest_change = monthly_changes[-1]
    watched_columns = [
        "stocks_change",
        "bonds_change",
        "repo_change",
        "fx_change",
        "participation_change",
        "precious_metals_change",
    ]
    drift = sum(abs(float(latest_change.get(column, 0) or 0)) for column in watched_columns)
    return round(drift, 2)


def _signal_score(summary: Dict[str, Any]) -> float:
    latest_value = float(summary.get("latest_portfolio_value", 0) or 0)
    value_delta = float(summary.get("portfolio_value_change", 0) or 0)
    latest_investors = float(summary.get("latest_num_investors", 0) or 0)
    investor_delta = float(summary.get("investor_change", 0) or 0)
    added = int(summary.get("total_new_holdings", 0) or 0)
    removed = int(summary.get("total_removed_holdings", 0) or 0)

    value_growth_pct = _safe_growth_pct(latest_value, value_delta)
    investor_growth_pct = _safe_growth_pct(latest_investors, investor_delta)
    drift = _latest_allocation_drift(summary)
    regime, _ = _fund_regime(summary)

    regime_bonus = {
        "Accumulation": 22.0,
        "Rotation": 12.0,
        "Mixed": 0.0,
        "Distribution": -20.0,
    }.get(regime, 0.0)

    score = 50.0 + regime_bonus
    score += max(-15.0, min(15.0, value_growth_pct)) * 0.8
    score += max(-15.0, min(15.0, investor_growth_pct)) * 0.9

    if regime in ("Accumulation", "Rotation"):
        score += min(drift, 10.0)
    elif regime == "Distribution":
        score -= min(drift, 10.0) * 0.6
    else:
        score += min(drift, 10.0) * 0.3

    score += min(float(added), 10.0) * 0.7
    score -= min(float(removed), 10.0) * 0.5
    return round(max(0.0, min(100.0, score)), 1)


def _signal_band(score: float) -> str:
    if score >= 75:
        return "Leading"
    if score >= 60:
        return "Constructive"
    if score >= 45:
        return "Neutral"
    return "Under Pressure"


def _short_fund_name(fund_name: str) -> str:
    compact = fund_name.replace(" Portfoy ", " ").replace(" Endeks Hisse Senedi Fonu", "")
    compact = compact.replace(" Hisse Senedi Fonu", "")
    compact = compact.replace(" Kisa Vadeli Borclanma Araclari Fonu", "")
    return compact[:42]


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^A-Z0-9]+", " ", normalized.upper()).strip()
    return normalized


def _fund_family(fund_name: str) -> str:
    normalized = _normalize_text(fund_name)
    family_map = {
        "IS PORTFOY": "Is Portfoy",
        "YAPI KREDI PORTFOY": "Yapi Kredi Portfoy",
        "GARANTI PORTFOY": "Garanti Portfoy",
        "FINANS PORTFOY": "Finans Portfoy",
        "AK PORTFOY": "Ak Portfoy",
        "ZIRAAT PORTFOY": "Ziraat Portfoy",
        "HALK HAYAT VE EMEKLILIK": "Halk Hayat ve Emeklilik",
    }
    for pattern, label in family_map.items():
        if normalized.startswith(pattern):
            return label
    parts = str(fund_name or "").split()
    return " ".join(parts[:2]) if len(parts) >= 2 else str(fund_name or "Unknown")


def _category_percentile(rank: int, count: int) -> float:
    if count <= 1 or rank <= 0:
        return 50.0
    percentile = ((count - rank) / (count - 1)) * 100
    return round(max(0.0, min(100.0, percentile)), 1)


def _quality_tier(category_percentile: float, market_share: float) -> str:
    if category_percentile >= 85 and market_share >= 1.0:
        return "Elite"
    if category_percentile >= 70 or market_share >= 0.75:
        return "Established"
    if category_percentile >= 50:
        return "Emerging"
    return "Niche"


def _category_bucket(summary: Dict[str, Any], fund_name: str) -> str:
    normalized_name = _normalize_text(fund_name)
    normalized_category = _normalize_text(summary.get("category", ""))
    allocation = summary.get("asset_allocation_current", {}) or {}
    stocks = float(allocation.get("stocks", 0) or 0)
    bonds = float(allocation.get("bonds", 0) or 0) + float(allocation.get("bills", 0) or 0)
    repo = float(allocation.get("repo", 0) or 0)
    metals = float(allocation.get("precious_metals", 0) or 0)

    if "ALTIN" in normalized_name or "KIYMETLI MADEN" in normalized_name or metals >= 30:
        return "Gold"
    if "PARA PIYASASI" in normalized_category or repo >= 45:
        return "Liquidity"
    if "BORCLANMA" in normalized_name or "TAHVIL" in normalized_category or bonds >= 35:
        return "Rates"
    if "DEGISKEN" in normalized_category or "MIXED" in normalized_category:
        return "Balanced"
    if "HISSE" in normalized_name or "EQUITY" in normalized_category or stocks >= 45:
        return "Equity"
    return "Mixed"


def _local_factor_lens(summary: Dict[str, Any], fund_name: str) -> str:
    normalized_name = _normalize_text(fund_name)
    bucket = _category_bucket(summary, fund_name)
    allocation = summary.get("asset_allocation_current", {}) or {}
    stocks = float(allocation.get("stocks", 0) or 0)
    repo = float(allocation.get("repo", 0) or 0)
    bonds = float(allocation.get("bonds", 0) or 0) + float(allocation.get("bills", 0) or 0)

    if "BANKA" in normalized_name or "FINANS" in normalized_name:
        return "Banks & Rates"
    if "TEKNOLOJI" in normalized_name:
        return "Tech Growth"
    if "SANAYI" in normalized_name or "IHRACAT" in normalized_name:
        return "Exporters & Industrials"
    if "TEMETTU" in normalized_name:
        return "Defensive Dividend"
    if bucket == "Gold":
        return "Gold Hedge"
    if bucket == "Liquidity":
        return "Liquidity Carry"
    if bucket == "Rates":
        return "Duration Shield" if bonds >= repo else "Liquidity Carry"
    if bucket == "Balanced":
        return "Balanced Allocation"
    if bucket == "Equity":
        return "Broad BIST Beta" if stocks >= 60 else "Selective Equity"
    return "Mixed Exposure"


def _board_score(signal_score: float, category_percentile: float, market_share: float) -> float:
    market_share_component = max(0.0, min(float(market_share or 0), 2.5)) / 2.5 * 10
    score = signal_score * 0.75 + category_percentile * 0.20 + market_share_component * 0.5
    return round(max(0.0, min(100.0, score)), 1)


def _board_band(score: float) -> str:
    if score >= 80:
        return "Institutional Leader"
    if score >= 65:
        return "Watch Closely"
    if score >= 50:
        return "Monitor"
    return "Low Conviction"


def _house_view(avg_board_score: float, avg_signal_score: float) -> str:
    if avg_board_score >= 75 and avg_signal_score >= 65:
        return "House Leader"
    if avg_board_score >= 60:
        return "Selective Strength"
    if avg_board_score >= 45:
        return "Mixed Bench"
    return "Needs Proof"


def _factor_breadth(avg_investor_growth_pct: float, avg_value_growth_pct: float, avg_board_score: float) -> str:
    if avg_investor_growth_pct > 0 and avg_value_growth_pct > 0 and avg_board_score >= 60:
        return "Broadening"
    if avg_investor_growth_pct < 0 and avg_value_growth_pct < 0:
        return "Fading"
    if avg_board_score >= 55:
        return "Selective"
    return "Thin"


def _enrich_peer_board_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    enriched = frame.copy()
    default_columns = {
        "fund_code": "",
        "fund_name": "",
        "fund_name_short": "",
        "signal_score": 0.0,
        "signal_band": "Neutral",
        "investor_growth_pct": 0.0,
        "value_growth_pct": 0.0,
        "allocation_drift": 0.0,
        "dominant_asset": "Belirsiz",
        "dominant_weight": 0.0,
        "regime": "Mixed",
        "market_share": 0.0,
        "category": "",
        "category_rank": 0,
        "category_count": 0,
    }
    for column, default_value in default_columns.items():
        if column not in enriched.columns:
            enriched[column] = default_value

    for index, row in enriched.iterrows():
        fund_name = str(row.get("fund_name") or "")
        summary = {
            "category": row.get("category", ""),
            "category_rank": row.get("category_rank", 0),
            "category_count": row.get("category_count", 0),
            "market_share": row.get("market_share", 0),
            "asset_allocation_current": {
                "stocks": row.get("dominant_weight", 0) if row.get("dominant_asset") == "Hisse" else 0,
                "bonds": row.get("dominant_weight", 0) if row.get("dominant_asset") == "Tahvil" else 0,
                "bills": row.get("dominant_weight", 0) if row.get("dominant_asset") == "Bono" else 0,
                "repo": row.get("dominant_weight", 0) if row.get("dominant_asset") == "Repo" else 0,
                "fx": row.get("dominant_weight", 0) if row.get("dominant_asset") == "Doviz" else 0,
                "participation": row.get("dominant_weight", 0) if row.get("dominant_asset") == "Katilim" else 0,
                "precious_metals": row.get("dominant_weight", 0) if row.get("dominant_asset") == "Kiymetli Maden" else 0,
                "other": row.get("dominant_weight", 0) if row.get("dominant_asset") == "Diger" else 0,
            },
        }
        category_rank = int(row.get("category_rank", 0) or 0)
        category_count = int(row.get("category_count", 0) or 0)
        market_share = float(row.get("market_share", 0) or 0)
        signal_score = float(row.get("signal_score", 0) or 0)
        category_percentile = float(
            row.get("category_percentile", _category_percentile(category_rank, category_count)) or 0
        )
        board_score = float(
            row.get("board_score", _board_score(signal_score, category_percentile, market_share)) or 0
        )

        enriched.at[index, "category_percentile"] = category_percentile
        enriched.at[index, "fund_family"] = row.get("fund_family") or _fund_family(fund_name)
        enriched.at[index, "category_bucket"] = row.get("category_bucket") or _category_bucket(summary, fund_name)
        enriched.at[index, "local_factor"] = row.get("local_factor") or _local_factor_lens(summary, fund_name)
        enriched.at[index, "quality_tier"] = row.get("quality_tier") or _quality_tier(category_percentile, market_share)
        enriched.at[index, "board_score"] = round(board_score, 1)
        enriched.at[index, "board_band"] = row.get("board_band") or _board_band(board_score)

    return enriched


class TRFundsService:
    def __init__(
        self,
        tracker_cls: Type[TEFASPortfolioTracker] = TEFASPortfolioTracker,
        ttl_seconds: int = 600,
        snapshot_store: SnapshotStore | None = None,
    ) -> None:
        self.tracker_cls = tracker_cls
        self.ttl_seconds = ttl_seconds
        self.snapshot_store = snapshot_store or SnapshotStore()

    def _build_tracker(self):
        try:
            return self.tracker_cls(request_timeout_seconds=6, max_retries=1)
        except TypeError:
            return self.tracker_cls()

    def _status_key(self, months: int) -> str:
        return f"tr-funds:status:{months}"

    def _snapshot_key(self, months: int) -> str:
        return f"tr-funds-peer-board-{months}"

    def _summary_snapshot_key(self, fund_code: str, months: int) -> str:
        return f"tr-funds-summary-{fund_code.upper()}-{months}"

    def _canonicalize_summary_identity(self, fund_code: str, summary: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(summary, dict) or not summary:
            return summary

        normalized = dict(summary)
        current_name = str(normalized.get("fund_name", "") or "").strip()
        seed_name = str(POPULAR_FUNDS.get(fund_code.upper(), "") or "").strip()
        needs_identity_refresh = not current_name or current_name == seed_name

        if needs_identity_refresh:
            try:
                tracker = self._build_tracker()
                identity = tracker.get_fund_identity(fund_code)
            except Exception:
                identity = {}

            if identity:
                refreshed_name = str(identity.get("fund_name", "") or "").strip()
                if refreshed_name:
                    normalized["fund_name"] = refreshed_name
                if identity.get("category"):
                    normalized["category"] = identity.get("category")
                if identity.get("category_rank") not in (None, ""):
                    normalized["category_rank"] = identity.get("category_rank")
                if identity.get("category_count") not in (None, ""):
                    normalized["category_count"] = identity.get("category_count")
                if identity.get("market_share") not in (None, ""):
                    normalized["market_share"] = identity.get("market_share")

        return normalized

    def _canonicalize_peer_board_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame

        normalized = frame.copy()
        for index, row in normalized.iterrows():
            fund_code = str(row.get("fund_code", "") or "").strip().upper()
            if not fund_code:
                continue

            identity_seed = {
                "fund_name": row.get("fund_name", ""),
                "category": row.get("category", ""),
                "category_rank": row.get("category_rank", 0),
                "category_count": row.get("category_count", 0),
                "market_share": row.get("market_share", 0),
            }
            identity = self._canonicalize_summary_identity(fund_code, identity_seed)
            resolved_name = str(identity.get("fund_name", "") or row.get("fund_name", "") or fund_code).strip()

            category_rank = int(identity.get("category_rank", row.get("category_rank", 0)) or 0)
            category_count = int(identity.get("category_count", row.get("category_count", 0)) or 0)
            market_share = float(identity.get("market_share", row.get("market_share", 0)) or 0)
            signal_score = float(row.get("signal_score", 0) or 0)
            category_percentile = _category_percentile(category_rank, category_count)
            dominant_asset = str(row.get("dominant_asset", "") or "")
            dominant_weight = float(row.get("dominant_weight", 0) or 0)
            summary = {
                "category": identity.get("category", row.get("category", "")),
                "asset_allocation_current": {
                    "stocks": dominant_weight if dominant_asset == "Hisse" else 0,
                    "bonds": dominant_weight if dominant_asset == "Tahvil" else 0,
                    "bills": dominant_weight if dominant_asset == "Bono" else 0,
                    "repo": dominant_weight if dominant_asset == "Repo" else 0,
                    "fx": dominant_weight if dominant_asset == "Doviz" else 0,
                    "participation": dominant_weight if dominant_asset == "Katilim" else 0,
                    "precious_metals": dominant_weight if dominant_asset == "Kiymetli Maden" else 0,
                    "other": dominant_weight if dominant_asset == "Diger" else 0,
                },
            }
            board_score = _board_score(signal_score, category_percentile, market_share)

            normalized.at[index, "fund_name"] = resolved_name
            normalized.at[index, "fund_name_short"] = _short_fund_name(resolved_name)
            normalized.at[index, "category"] = identity.get("category", row.get("category", ""))
            normalized.at[index, "category_rank"] = category_rank
            normalized.at[index, "category_count"] = category_count
            normalized.at[index, "market_share"] = market_share
            normalized.at[index, "category_percentile"] = category_percentile
            normalized.at[index, "fund_family"] = _fund_family(resolved_name)
            normalized.at[index, "category_bucket"] = _category_bucket(summary, resolved_name)
            normalized.at[index, "local_factor"] = _local_factor_lens(summary, resolved_name)
            normalized.at[index, "quality_tier"] = _quality_tier(category_percentile, market_share)
            normalized.at[index, "board_score"] = round(board_score, 1)
            normalized.at[index, "board_band"] = _board_band(board_score)

        return normalized

    def _now_iso(self) -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    def _load_status(self, months: int) -> Dict[str, Any]:
        cached = cache_get(self._status_key(months))
        if isinstance(cached, dict):
            return cached
        return {
            "status": "warming",
            "detail": "TEFAS cache has not completed a successful refresh yet.",
            "last_attempt_at": None,
            "last_success_at": None,
            "last_failure_at": None,
            "funds_requested": len(POPULAR_FUNDS),
            "funds_loaded": 0,
            "error_count": 0,
            "cache_ttl_seconds": self.ttl_seconds,
        }

    def _save_status(self, months: int, payload: Dict[str, Any]) -> None:
        cache_set(self._status_key(months), payload, ttl=max(self.ttl_seconds * 6, 3600))

    def get_status(self, months: int = 12) -> Dict[str, Any]:
        status = self._load_status(months)
        peer_board = cache_get(f"tr-funds:peer-board:{months}")
        if isinstance(peer_board, pd.DataFrame) and not peer_board.empty and status.get("status") == "warming":
            status["status"] = "healthy"
            status["detail"] = f"Cached peer board available with {len(peer_board)} rows."
            status["funds_loaded"] = len(peer_board)
            return status

        snapshot_payload = self.snapshot_store.read_json(self._snapshot_key(months))
        if snapshot_payload and snapshot_payload.get("rows"):
            status["last_snapshot_at"] = snapshot_payload.get("saved_at")
            if status.get("status") == "warming":
                status["status"] = "healthy"
                status["detail"] = (
                    f"Persisted peer board available with {len(snapshot_payload.get('rows', []))} rows."
                )
                status["funds_loaded"] = len(snapshot_payload.get("rows", []))

        if status.get("status") == "warming" and status.get("last_attempt_at"):
            try:
                attempted_at = datetime.fromisoformat(str(status["last_attempt_at"]).replace("Z", "+00:00"))
                age_seconds = (datetime.utcnow() - attempted_at.replace(tzinfo=None)).total_seconds()
                if age_seconds > 30:
                    status["status"] = "degraded"
                    if snapshot_payload and snapshot_payload.get("rows"):
                        status["detail"] = (
                            "TEFAS refresh is taking longer than expected. "
                            "FundPilot is serving the latest persisted TR funds snapshot."
                        )
                    else:
                        status["detail"] = (
                            "TEFAS refresh is taking longer than expected. "
                            "FundPilot is serving the latest cached TR funds state."
                        )
            except Exception:
                pass
        return status

    def get_cached_peer_signal_board(self, months: int = 12) -> pd.DataFrame:
        cached = cache_get(f"tr-funds:peer-board:{months}")
        if isinstance(cached, pd.DataFrame):
            if not cached.empty:
                canonical_cached = self._canonicalize_peer_board_frame(cached)
                enriched_cached = _enrich_peer_board_frame(canonical_cached)
                cache_set(f"tr-funds:peer-board:{months}", enriched_cached, ttl=self.ttl_seconds)
                return enriched_cached.copy()
        snapshot_payload = self.snapshot_store.read_json(self._snapshot_key(months))
        if snapshot_payload and isinstance(snapshot_payload.get("rows"), list) and snapshot_payload["rows"]:
            frame = self._canonicalize_peer_board_frame(pd.DataFrame(snapshot_payload["rows"]))
            if frame.to_dict("records") != snapshot_payload.get("rows"):
                self.snapshot_store.write_json(
                    self._snapshot_key(months),
                    {
                        "saved_at": self._now_iso(),
                        "months": months,
                        "rows": frame.to_dict("records"),
                    },
                )
            frame = _enrich_peer_board_frame(frame)
            cache_set(f"tr-funds:peer-board:{months}", frame, ttl=self.ttl_seconds)
            return frame.copy()
        return pd.DataFrame()

    def get_cached_top_pick(self, months: int = 12) -> Optional[Dict[str, Any]]:
        peer_df = self.get_cached_peer_signal_board(months)
        if peer_df.empty:
            return None
        return dict(peer_df.iloc[0])

    def get_persisted_fund_summary(self, fund_code: str, months: int = 12) -> Optional[Dict[str, Any]]:
        snapshot = self.snapshot_store.read_json(self._summary_snapshot_key(fund_code.upper(), months))
        if isinstance(snapshot, dict) and isinstance(snapshot.get("summary"), dict) and snapshot.get("summary"):
            return snapshot["summary"]
        return None

    def get_leadership_snapshot(self, months: int = 12) -> Dict[str, list[Dict[str, Any]]]:
        peer_df = self.get_cached_peer_signal_board(months)
        if peer_df.empty:
            return {"family_rows": [], "factor_rows": []}

        sorted_peer_df = peer_df.sort_values(
            ["board_score", "signal_score", "investor_growth_pct"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

        family_df = (
            sorted_peer_df.groupby("fund_family", dropna=False)
            .agg(
                funds_count=("fund_code", "count"),
                avg_board_score=("board_score", "mean"),
                avg_signal_score=("signal_score", "mean"),
                avg_market_share=("market_share", "mean"),
                avg_category_percentile=("category_percentile", "mean"),
                top_fund=("fund_code", "first"),
            )
            .reset_index()
        )
        family_df["avg_board_score"] = family_df["avg_board_score"].round(1)
        family_df["avg_signal_score"] = family_df["avg_signal_score"].round(1)
        family_df["avg_market_share"] = family_df["avg_market_share"].round(2)
        family_df["avg_category_percentile"] = family_df["avg_category_percentile"].round(1)
        family_df["house_view"] = family_df.apply(
            lambda row: _house_view(float(row["avg_board_score"]), float(row["avg_signal_score"])),
            axis=1,
        )
        family_df = family_df.sort_values(
            ["avg_board_score", "avg_signal_score", "funds_count"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

        factor_df = (
            sorted_peer_df.groupby("local_factor", dropna=False)
            .agg(
                funds_count=("fund_code", "count"),
                avg_board_score=("board_score", "mean"),
                avg_signal_score=("signal_score", "mean"),
                avg_investor_growth_pct=("investor_growth_pct", "mean"),
                avg_value_growth_pct=("value_growth_pct", "mean"),
                lead_fund=("fund_code", "first"),
            )
            .reset_index()
        )
        factor_df["avg_board_score"] = factor_df["avg_board_score"].round(1)
        factor_df["avg_signal_score"] = factor_df["avg_signal_score"].round(1)
        factor_df["avg_investor_growth_pct"] = factor_df["avg_investor_growth_pct"].round(1)
        factor_df["avg_value_growth_pct"] = factor_df["avg_value_growth_pct"].round(1)
        factor_df["breadth"] = factor_df.apply(
            lambda row: _factor_breadth(
                float(row["avg_investor_growth_pct"]),
                float(row["avg_value_growth_pct"]),
                float(row["avg_board_score"]),
            ),
            axis=1,
        )
        factor_df = factor_df.sort_values(
            ["avg_board_score", "avg_signal_score", "funds_count"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

        return {
            "family_rows": family_df.head(6).to_dict("records"),
            "factor_rows": factor_df.head(6).to_dict("records"),
        }

    def get_fund_summary(self, fund_code: str, months: int = 12, force_refresh: bool = False) -> Dict[str, Any]:
        fund_code = fund_code.upper()
        cache_key = f"tr-funds:summary:{fund_code}:{months}"
        snapshot_key = self._summary_snapshot_key(fund_code, months)
        cached = cache_get(cache_key)
        if isinstance(cached, dict) and cached and not force_refresh:
            normalized_cached = self._canonicalize_summary_identity(fund_code, cached)
            if normalized_cached != cached:
                cache_set(cache_key, normalized_cached, ttl=self.ttl_seconds)
            return normalized_cached
        persisted_summary = self.get_persisted_fund_summary(fund_code, months)
        if persisted_summary is not None and not force_refresh:
            normalized_persisted = self._canonicalize_summary_identity(fund_code, persisted_summary)
            cache_set(cache_key, normalized_persisted, ttl=self.ttl_seconds)
            if normalized_persisted != persisted_summary:
                self.snapshot_store.write_json(
                    snapshot_key,
                    {
                        "saved_at": self._now_iso(),
                        "fund_code": fund_code,
                        "months": months,
                        "summary": normalized_persisted,
                    },
                )
            return normalized_persisted

        tracker = self._build_tracker()
        summary = tracker.generate_portfolio_summary(fund_code, months) or {}
        summary = self._canonicalize_summary_identity(fund_code, summary)
        if not summary and persisted_summary is not None:
            normalized_persisted = self._canonicalize_summary_identity(fund_code, persisted_summary)
            cache_set(cache_key, normalized_persisted, ttl=self.ttl_seconds)
            return normalized_persisted
        cache_set(cache_key, summary, ttl=self.ttl_seconds)
        if summary:
            self.snapshot_store.write_json(
                snapshot_key,
                {
                    "saved_at": self._now_iso(),
                    "fund_code": fund_code,
                    "months": months,
                    "summary": summary,
                },
            )
        return summary

    def get_peer_signal_board(self, months: int = 12, force_refresh: bool = False) -> pd.DataFrame:
        cache_key = f"tr-funds:peer-board:{months}"
        cached = cache_get(cache_key)
        if isinstance(cached, pd.DataFrame) and not force_refresh:
            canonical_cached = self._canonicalize_peer_board_frame(cached)
            enriched_cached = _enrich_peer_board_frame(canonical_cached)
            cache_set(cache_key, enriched_cached, ttl=self.ttl_seconds)
            return enriched_cached.copy()

        started_at = self._now_iso()
        existing_status = self._load_status(months)
        rows = []
        error_count = 0

        self._save_status(
            months,
            {
                **existing_status,
                "status": "warming",
                "detail": "Refreshing TEFAS peer board.",
                "last_attempt_at": started_at,
                "funds_requested": len(POPULAR_FUNDS),
            },
        )

        rows = []
        for fund_code, fund_name in POPULAR_FUNDS.items():
            try:
                summary = self.get_fund_summary(fund_code, months, force_refresh=force_refresh)
            except Exception as exc:
                logger.warning("Failed to build TR fund summary", fund_code=fund_code, error=str(exc))
                error_count += 1
                continue

            if not summary:
                error_count += 1
                continue

            resolved_fund_name = str(summary.get("fund_name", "") or "").strip() or fund_name or fund_code
            dominant_name, dominant_weight = _dominant_asset(summary.get("asset_allocation_current", {}))
            regime, regime_note = _fund_regime(summary)
            signal_score = _signal_score(summary)
            category_rank = int(summary.get("category_rank", 0) or 0)
            category_count = int(summary.get("category_count", 0) or 0)
            market_share = float(summary.get("market_share", 0) or 0)
            category_percentile = _category_percentile(category_rank, category_count)
            fund_family = _fund_family(resolved_fund_name)
            category_bucket = _category_bucket(summary, resolved_fund_name)
            local_factor = _local_factor_lens(summary, resolved_fund_name)
            board_score = _board_score(signal_score, category_percentile, market_share)
            quality_tier = _quality_tier(category_percentile, market_share)
            latest_value = float(summary.get("latest_portfolio_value", 0) or 0)
            value_delta = float(summary.get("portfolio_value_change", 0) or 0)
            latest_investors = float(summary.get("latest_num_investors", 0) or 0)
            investor_delta = float(summary.get("investor_change", 0) or 0)
            allocation_drift = _latest_allocation_drift(summary)

            rows.append(
                {
                    "fund_code": fund_code,
                    "fund_name": resolved_fund_name,
                    "fund_name_short": _short_fund_name(resolved_fund_name),
                    "latest_portfolio_value": latest_value,
                    "portfolio_value_change": value_delta,
                    "value_growth_pct": _safe_growth_pct(latest_value, value_delta),
                    "latest_num_investors": latest_investors,
                    "investor_change": investor_delta,
                    "investor_growth_pct": _safe_growth_pct(latest_investors, investor_delta),
                    "dominant_asset": dominant_name,
                    "dominant_weight": dominant_weight,
                    "regime": regime,
                    "regime_note": regime_note,
                    "allocation_drift": allocation_drift,
                    "new_holdings": int(summary.get("total_new_holdings", 0) or 0),
                    "removed_holdings": int(summary.get("total_removed_holdings", 0) or 0),
                    "signal_score": signal_score,
                    "signal_band": _signal_band(signal_score),
                    "board_score": board_score,
                    "board_band": _board_band(board_score),
                    "category": summary.get("category", ""),
                    "category_rank": category_rank,
                    "category_count": category_count,
                    "category_percentile": category_percentile,
                    "market_share": market_share,
                    "fund_family": fund_family,
                    "category_bucket": category_bucket,
                    "local_factor": local_factor,
                    "quality_tier": quality_tier,
                }
            )

        peer_df = pd.DataFrame(rows)
        if peer_df.empty:
            self._save_status(
                months,
                {
                    **existing_status,
                    "status": "degraded",
                    "detail": "TEFAS peer board could not be built from current upstream responses.",
                    "last_attempt_at": started_at,
                    "last_failure_at": self._now_iso(),
                    "funds_requested": len(POPULAR_FUNDS),
                    "funds_loaded": 0,
                    "error_count": error_count or len(POPULAR_FUNDS),
                    "cache_ttl_seconds": self.ttl_seconds,
                },
            )
            return peer_df

        peer_df = peer_df.sort_values(
            ["board_score", "signal_score", "investor_growth_pct", "value_growth_pct"],
            ascending=[False, False, False, False],
        ).reset_index(drop=True)
        cache_set(cache_key, peer_df, ttl=self.ttl_seconds)
        self.snapshot_store.write_json(
            self._snapshot_key(months),
            {
                "saved_at": self._now_iso(),
                "months": months,
                "rows": peer_df.to_dict("records"),
            },
        )
        self._save_status(
            months,
            {
                **existing_status,
                "status": "healthy" if error_count == 0 else "degraded",
                "detail": f"Refreshed {len(peer_df)} funds from TEFAS.",
                "last_attempt_at": started_at,
                "last_success_at": self._now_iso(),
                "funds_requested": len(POPULAR_FUNDS),
                "funds_loaded": len(peer_df),
                "error_count": error_count,
                "cache_ttl_seconds": self.ttl_seconds,
            },
        )
        return peer_df.copy()

    def get_top_pick(self, months: int = 12, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        peer_df = self.get_peer_signal_board(months, force_refresh=force_refresh)
        if peer_df.empty:
            return None
        return dict(peer_df.iloc[0])

    def prewarm(self, months: int = 12, force_refresh: bool = True) -> Dict[str, Any]:
        peer_df = self.get_peer_signal_board(months=months, force_refresh=force_refresh)
        status = self.get_status(months=months)
        return {
            "status": status,
            "rows": len(peer_df),
            "top_pick": dict(peer_df.iloc[0]) if not peer_df.empty else None,
        }
