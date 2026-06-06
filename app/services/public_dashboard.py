from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.analytics.entropy_metrics import EntropyCalculator
from app.core.config import settings
from app.data_collectors.coingecko import CoinGeckoCollector
from app.data_collectors.evds import EVDSCollector
from app.data_collectors.fiscaldata import FiscalDataCollector
from app.data_collectors.fred import FredCollector
from app.data_collectors.yahoo_finance import YahooFinanceCollector
from app.services.cache import cache_get, cache_set
from app.services.institutional_pulse import InstitutionalPulseService
from app.services.public_research import PublicResearchService
from app.services.snapshot_store import SnapshotStore
from app.services.stock_enrichment import StockEnrichmentService
from app.services.tr_funds import TRFundsService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _tone_for_change(change_pct: float) -> str:
    if change_pct > 0.1:
        return "positive"
    if change_pct < -0.1:
        return "negative"
    return "neutral"


def _fmt_number(value: float, digits: int = 2) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return "N/A"


def _fmt_pct(value: float, digits: int = 1) -> str:
    try:
        return f"{float(value):+.{digits}f}%"
    except Exception:
        return "N/A"


def _fmt_compact_money(value: float) -> str:
    amount = float(value or 0)
    if abs(amount) >= 1_000_000_000_000:
        return f"${amount / 1_000_000_000_000:.1f}T"
    if abs(amount) >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if abs(amount) >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    return f"${amount:,.0f}"


def _fmt_compact_amount(value: float, currency_code: str = "USD") -> str:
    try:
        amount = float(value or 0)
    except Exception:
        return "N/A"
    prefix = f"{currency_code} "
    if abs(amount) >= 1_000_000_000_000:
        return f"{prefix}{amount / 1_000_000_000_000:.1f}T"
    if abs(amount) >= 1_000_000_000:
        return f"{prefix}{amount / 1_000_000_000:.1f}B"
    if abs(amount) >= 1_000_000:
        return f"{prefix}{amount / 1_000_000:.1f}M"
    return f"{prefix}{amount:,.0f}"


def _affiliate_slot(index: int, defaults: Dict[str, str]) -> Dict[str, str]:
    prefix = f"FUNDPILOT_SLOT_{index}_"
    return {
        "title": os.getenv(f"{prefix}TITLE", defaults["title"]),
        "label": os.getenv(f"{prefix}LABEL", defaults["label"]),
        "href": os.getenv(f"{prefix}HREF", defaults["href"]),
        "description": os.getenv(f"{prefix}DESCRIPTION", defaults["description"]),
        "badge": os.getenv(f"{prefix}BADGE", defaults["badge"]),
    }


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and value != value:
            return None
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return _to_json_safe(value.item())
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except Exception:
        return None
    if np.isnan(number) or np.isinf(number):
        return None
    return number


def _safe_entropy_unit_interval(value: Any) -> float | None:
    number = _safe_float(value)
    if number is None:
        return None
    return max(0.0, min(1.0, number))


def _safe_entropy_score(value: Any, multiplier: float = 100.0) -> float | None:
    number = _safe_float(value)
    if number is None:
        return None
    return max(0.0, min(100.0, number * multiplier))


class PublicDashboardService:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self.public_tr_funds_months = settings.PUBLIC_TR_FUNDS_MONTHS
        self.entropy_window_days = 90
        self.yahoo = YahooFinanceCollector()
        self.coingecko = CoinGeckoCollector()
        self.evds = EVDSCollector()
        self.fred = FredCollector()
        self.fiscaldata = FiscalDataCollector()
        self.snapshot_store = SnapshotStore()
        self.tr_funds = TRFundsService(snapshot_store=self.snapshot_store)
        self.public_research = PublicResearchService(snapshot_store=self.snapshot_store)
        self.institutional = InstitutionalPulseService(snapshot_store=self.snapshot_store)
        self.stock_enrichment = StockEnrichmentService(snapshot_store=self.snapshot_store)
        self.entropy = EntropyCalculator()

    def _snapshot_key(self) -> str:
        return "public-dashboard-snapshot"

    def _influence_snapshot_key(self) -> str:
        return "public-influence-map-snapshot"

    def _entropy_placeholder(self, generated_at: str) -> Dict[str, Any]:
        return {
            "state": "warming",
            "state_label": "Refreshing",
            "regime": "Refreshing",
            "stance": "Entropy snapshot is warming.",
            "predictability_score": None,
            "complexity_score": None,
            "leader_asset": None,
            "leader_symbol": None,
            "window_days": self.entropy_window_days,
            "updated_at": generated_at,
            "asset_rows": [],
            "note": "Entropy tracks how ordered or chaotic return patterns are across major risk assets.",
        }

    def _influence_placeholder(self, generated_at: str) -> Dict[str, Any]:
        return {
            "generated_at": generated_at,
            "headline": {
                "label": "Refreshing",
                "detail": "Influence map is warming.",
            },
            "summary_cards": [
                {"label": "Directed flows", "value": "0", "detail": "No stable lead-lag pairs yet."},
                {"label": "Leading macro source", "value": "Refreshing", "detail": "Awaiting enough history."},
                {"label": "Most influenced target", "value": "Refreshing", "detail": "Awaiting enough history."},
            ],
            "pair_rows": [],
            "source_rows": [],
            "target_rows": [],
            "methodology": [
                "Transfer entropy is directional, unlike simple correlation.",
                "This lane is warming and will repopulate after the next history refresh.",
            ],
        }

    def _default_source_health(self, generated_at: str) -> List[Dict[str, Any]]:
        return [
            {
                "key": "market",
                "label": "Market feed",
                "state": "warming",
                "state_label": "Refreshing",
                "detail": "FundPilot is preparing the latest public snapshot.",
                "updated_at": generated_at,
            },
            {
                "key": "macro",
                "label": "Macro feed",
                "state": "warming",
                "state_label": "Refreshing",
                "detail": "FundPilot is preparing the latest public snapshot.",
                "updated_at": generated_at,
            },
            {
                "key": "crypto",
                "label": "Crypto feed",
                "state": "warming",
                "state_label": "Refreshing",
                "detail": "FundPilot is preparing the latest public snapshot.",
                "updated_at": generated_at,
            },
            {
                "key": "kap-enrichment",
                "label": "BIST disclosures",
                "state": "warming",
                "state_label": "Refreshing",
                "detail": "FundPilot is preparing curated BIST disclosure enrichment.",
                "updated_at": generated_at,
            },
            {
                "key": "institutional",
                "label": "Institutional filings",
                "state": "warming",
                "state_label": "Refreshing",
                "detail": "FundPilot is preparing curated 13F manager coverage.",
                "updated_at": generated_at,
            },
            {
                "key": "tr-funds",
                "label": "TR funds",
                "state": "warming",
                "state_label": "Refreshing",
                "detail": "FundPilot is preparing the latest public snapshot.",
                "updated_at": generated_at,
            },
        ]

    def _market_physics_placeholder(self, generated_at: str) -> Dict[str, Any]:
        return {
            "state": "warming",
            "state_label": "Refreshing",
            "phase_regime": "Refreshing",
            "stance": "Phase alignment is warming.",
            "average_phase_score": None,
            "leader_asset": None,
            "leader_symbol": None,
            "updated_at": generated_at,
            "rows": [],
            "note": (
                "We use phase alignment because trends deserve more trust when short-, medium-, and "
                "intermediate-horizon returns point the same way while entropy stays orderly."
            ),
        }

    def _normalize_snapshot(self, snapshot: Dict[str, Any], generated_at: str | None = None) -> Dict[str, Any]:
        normalized = dict(snapshot)
        effective_generated_at = generated_at or normalized.get("generated_at") or datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        normalized.setdefault("generated_at", effective_generated_at)
        normalized.setdefault("market_cards", [])
        normalized.setdefault("macro_cards", [])
        normalized.setdefault("crypto_cards", [])
        source_health = normalized.get("source_health")
        if not isinstance(source_health, list):
            source_health = []
        source_health_by_key = {
            str(item.get("key")): item
            for item in source_health
            if isinstance(item, dict) and item.get("key")
        }
        for default_item in self._default_source_health(effective_generated_at):
            source_health_by_key.setdefault(default_item["key"], default_item)
        normalized["source_health"] = list(source_health_by_key.values())
        normalized.setdefault("coverage_cards", self._build_coverage_cards())
        normalized.setdefault("bist_catalyst_rows", [])
        normalized.setdefault(
            "bist_catalyst_summary",
            {
                "state": "warming",
                "state_label": "Refreshing",
                "detail": "BIST catalyst lane is warming.",
                "leader": None,
                "active_count": 0,
            },
        )
        normalized.setdefault("influence_rows", [])
        normalized.setdefault(
            "influence_summary",
            {
                "label": "Refreshing",
                "detail": "Influence map is warming.",
            },
        )
        if not isinstance(normalized.get("market_physics"), dict):
            normalized["market_physics"] = self._market_physics_placeholder(effective_generated_at)
        normalized.setdefault("sponsor_slots", self._build_sponsor_slots())
        normalized.setdefault("editorial_cards", self._build_editorial_cards())
        normalized.setdefault(
            "sponsor_disclosure",
            "Some placements on this page may be sponsored or affiliate links. FundPilot does not run personalized ads or third-party tracking scripts.",
        )
        normalized.setdefault(
            "privacy_promise",
            "No account wall, no third-party trackers, no ad-tech cookies, and no client-side portfolio storage in the public build.",
        )
        if not isinstance(normalized.get("entropy_signal"), dict):
            normalized["entropy_signal"] = self._entropy_placeholder(effective_generated_at)
        return normalized

    def build_snapshot(self, force_refresh: bool = False) -> Dict[str, Any]:
        cache_key = "public-dashboard:snapshot"
        cached = cache_get(cache_key)
        if cached is not None and not force_refresh:
            normalized_cached = self._normalize_snapshot(cached)
            cache_set(cache_key, normalized_cached, ttl=self.ttl_seconds)
            return normalized_cached
        if not force_refresh:
            persisted = self.snapshot_store.read_json(self._snapshot_key())
            if isinstance(persisted, dict) and persisted:
                normalized_persisted = self._normalize_snapshot(persisted)
                cache_set(cache_key, normalized_persisted, ttl=self.ttl_seconds)
                return normalized_persisted
            return self._build_placeholder_snapshot()

        generated_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        market_cards, market_status = self._build_market_cards(generated_at)
        entropy_signal = self._build_entropy_signal(generated_at)
        market_physics = self._build_market_physics(entropy_signal, generated_at)
        macro_cards, macro_status = self._build_macro_cards(generated_at)
        crypto_cards, crypto_status = self._build_crypto_cards(generated_at)
        tr_top_pick = self._build_cached_tr_top_pick()
        tr_peer_board = self._build_cached_tr_peer_board()
        tr_status = self._build_tr_status(generated_at, tr_peer_board)
        influence_workspace = self.build_influence_workspace(force_refresh=True)
        kap_status = self.stock_enrichment.get_health_snapshot()
        institutional_status = self.institutional.get_health_snapshot()
        bist_catalyst_rows, bist_catalyst_summary = self._build_bist_catalyst_lane()

        snapshot = {
            "app_name": settings.APP_DISPLAY_NAME,
            "generated_at": generated_at,
            "market_cards": market_cards,
            "entropy_signal": entropy_signal,
            "market_physics": market_physics,
            "macro_cards": macro_cards,
            "crypto_cards": crypto_cards,
            "sentiment": self._build_sentiment(),
            "tr_top_pick": tr_top_pick,
            "tr_peer_board": tr_peer_board,
            "bist_catalyst_rows": bist_catalyst_rows,
            "bist_catalyst_summary": bist_catalyst_summary,
            "influence_rows": influence_workspace.get("pair_rows", [])[:5],
            "influence_summary": influence_workspace.get("headline", {}),
            "source_health": [market_status, macro_status, crypto_status, kap_status, tr_status, institutional_status],
            "coverage_cards": self._build_coverage_cards(),
            "sponsor_slots": self._build_sponsor_slots(),
            "editorial_cards": self._build_editorial_cards(),
            "sponsor_disclosure": (
                "Some placements on this page may be sponsored or affiliate links. "
                "FundPilot does not run personalized ads or third-party tracking scripts."
            ),
            "privacy_promise": (
                "No account wall, no third-party trackers, no ad-tech cookies, "
                "and no client-side portfolio storage in the public build."
            ),
        }
        safe_snapshot = _to_json_safe(self._normalize_snapshot(snapshot, generated_at))
        cache_set(cache_key, safe_snapshot, ttl=self.ttl_seconds)
        self.snapshot_store.write_json(self._snapshot_key(), safe_snapshot)
        return safe_snapshot

    def build_live_source_health(self) -> Dict[str, Any]:
        snapshot = self.build_snapshot()
        generated_at = str(snapshot.get("generated_at") or datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
        source_health_by_key = {
            str(item.get("key")): item
            for item in snapshot.get("source_health", [])
            if isinstance(item, dict) and item.get("key")
        }
        live_items = [
            self._build_macro_cards(generated_at)[1],
            self.stock_enrichment.get_health_snapshot(),
            self._build_tr_status(generated_at, self._build_cached_tr_peer_board()),
            self.institutional.get_health_snapshot(),
        ]
        for item in live_items:
            source_health_by_key[str(item.get("key"))] = item
        return {
            "generated_at": generated_at,
            "source_health": list(source_health_by_key.values()),
        }

    def _build_placeholder_snapshot(self) -> Dict[str, Any]:
        generated_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        return {
            "app_name": settings.APP_DISPLAY_NAME,
            "generated_at": generated_at,
            "market_cards": [],
            "entropy_signal": self._entropy_placeholder(generated_at),
            "market_physics": self._market_physics_placeholder(generated_at),
            "macro_cards": [],
            "crypto_cards": [],
            "sentiment": {
                "score": 0.5,
                "mood": "Refreshing",
                "fear_greed_value": 50,
                "fear_greed_label": "Refreshing",
                "vix_value": 0.0,
                "vix_change": 0.0,
                "vix_label": "N/A",
            },
            "tr_top_pick": None,
            "tr_peer_board": [],
            "bist_catalyst_rows": [],
            "bist_catalyst_summary": {
                "state": "warming",
                "state_label": "Refreshing",
                "detail": "FundPilot is preparing the latest BIST catalyst snapshot.",
                "leader": None,
                "active_count": 0,
            },
            "influence_rows": [],
            "influence_summary": {
                "label": "Refreshing",
                "detail": "Influence map is warming.",
            },
            "source_health": self._default_source_health(generated_at),
            "coverage_cards": self._build_coverage_cards(),
            "sponsor_slots": self._build_sponsor_slots(),
            "editorial_cards": self._build_editorial_cards(),
            "sponsor_disclosure": (
                "Some placements on this page may be sponsored or affiliate links. "
                "FundPilot does not run personalized ads or third-party tracking scripts."
            ),
            "privacy_promise": (
                "No account wall, no third-party trackers, no ad-tech cookies, "
                "and no client-side portfolio storage in the public build."
            ),
        }

    def build_reliability_workspace(self) -> Dict[str, Any]:
        snapshot = self.build_snapshot()
        live_source_health = self.build_live_source_health()
        kap_health = self.stock_enrichment.get_health_snapshot()
        tr_status = self.tr_funds.get_status(months=self.public_tr_funds_months)
        institutional_workspace = self.institutional.get_workspace(settings.PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER)

        return {
            "generated_at": live_source_health.get("generated_at") or snapshot.get("generated_at"),
            "source_health": live_source_health.get("source_health", []),
            "kap_health": kap_health,
            "tr_status": tr_status,
            "institutional_workspace": institutional_workspace,
            "outlook_rows": [
                {
                    "horizon": "6 months",
                    "label": "Operationally stable",
                    "state": "Low risk",
                    "detail": (
                        "Single-worker runtime with persisted snapshots should stay reliable if source cadence "
                        "and prewarm jobs remain disciplined."
                    ),
                },
                {
                    "horizon": "12 months",
                    "label": "Scale pressure begins",
                    "state": "Manageable risk",
                    "detail": (
                        "If traffic climbs, the current in-memory cache model will need Redis or another shared cache "
                        "before adding more workers."
                    ),
                },
                {
                    "horizon": "24 months",
                    "label": "Coverage depth matters",
                    "state": "Medium risk",
                    "detail": (
                        "FundPilot should widen curated BIST, TEFAS, and institutional universes while keeping "
                        "batch enrichment ahead of request-time reads."
                    ),
                },
                {
                    "horizon": "48 months",
                    "label": "Data ownership becomes strategic",
                    "state": "Higher risk",
                    "detail": (
                        "Longer-term durability will benefit from an owned historical warehouse, schema monitoring, "
                        "and less dependence on fragile public surfaces."
                    ),
                },
            ],
            "next_moves": [
                {
                    "title": "Shared cache before multi-worker scale",
                    "detail": "Adopt Redis or an equivalent shared cache before increasing gunicorn worker count.",
                },
                {
                    "title": "Snapshot schema discipline",
                    "detail": "Keep versioned snapshot normalization so older persisted JSON never breaks new templates.",
                },
                {
                    "title": "Curated source expansion",
                    "detail": "Extend BIST disclosure coverage, manager coverage, and TEFAS breadth only through batch enrichment.",
                },
                {
                    "title": "Source contract discipline",
                    "detail": "Prefer first-party or official public sources over third-party mirrors whenever durable alternatives exist.",
                },
            ],
        }

    def build_influence_workspace(self, force_refresh: bool = False) -> Dict[str, Any]:
        cache_key = "public-influence-map:workspace"
        cached = cache_get(cache_key)
        if cached is not None and not force_refresh:
            return cached
        if not force_refresh:
            persisted = self.snapshot_store.read_json(self._influence_snapshot_key())
            if isinstance(persisted, dict) and persisted:
                cache_set(cache_key, persisted, ttl=self.ttl_seconds)
                return persisted
            generated_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            return self._influence_placeholder(generated_at)

        generated_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=170)
        assets = {
            "^VIX": {"label": "VIX", "group": "Volatility"},
            "^TNX": {"label": "US 10Y Yield", "group": "Rates"},
            "UUP": {"label": "US Dollar", "group": "FX"},
            "CL=F": {"label": "Crude Oil", "group": "Commodities"},
            "BTC-USD": {"label": "Bitcoin", "group": "Crypto"},
            "^GSPC": {"label": "S&P 500", "group": "Equities"},
            "^IXIC": {"label": "Nasdaq", "group": "Equities"},
            "XU100.IS": {"label": "BIST 100", "group": "Equities"},
            "GC=F": {"label": "Gold", "group": "Defensive"},
        }
        source_symbols = ["^VIX", "^TNX", "UUP", "CL=F", "BTC-USD"]
        target_symbols = ["^GSPC", "^IXIC", "XU100.IS", "GC=F", "BTC-USD"]

        history: Dict[str, pd.Series] = {}
        for symbol in assets:
            try:
                hist = self.yahoo.get_historical_data(
                    start_date=start_date,
                    end_date=end_date,
                    symbol=symbol,
                    interval="1d",
                )
            except Exception:
                hist = pd.DataFrame()
            if hist.empty or "close_price" not in hist:
                continue
            prices = pd.to_numeric(hist["close_price"], errors="coerce").dropna().reset_index(drop=True)
            if len(prices) < 80:
                continue
            history[symbol] = prices

        pair_rows: List[Dict[str, Any]] = []
        source_stats: Dict[str, Dict[str, Any]] = {}
        target_stats: Dict[str, Dict[str, Any]] = {}
        for source_symbol in source_symbols:
            source_prices = history.get(source_symbol)
            if source_prices is None:
                continue
            source_returns = source_prices.pct_change().dropna().tail(120)
            if len(source_returns) < 60:
                continue
            source_20d = 0.0
            if len(source_prices) > 20:
                start_price = float(source_prices.iloc[-21] or 0)
                end_price = float(source_prices.iloc[-1] or 0)
                if start_price:
                    source_20d = ((end_price / start_price) - 1) * 100
            for target_symbol in target_symbols:
                if source_symbol == target_symbol:
                    continue
                target_prices = history.get(target_symbol)
                if target_prices is None:
                    continue
                target_returns = target_prices.pct_change().dropna().tail(120)
                if len(target_returns) < 60:
                    continue
                aligned = pd.DataFrame(
                    {
                        "source": source_returns.reset_index(drop=True),
                        "target": target_returns.reset_index(drop=True),
                    }
                ).dropna()
                if len(aligned) < 60:
                    continue

                forward = float(
                    self.entropy.transfer_entropy(aligned["source"], aligned["target"], bins=8) or np.nan
                )
                reverse = float(
                    self.entropy.transfer_entropy(aligned["target"], aligned["source"], bins=8) or np.nan
                )
                if not np.isfinite(forward) or not np.isfinite(reverse):
                    continue

                net = round(forward - reverse, 3)
                forward = round(forward, 3)
                reverse = round(reverse, 3)
                magnitude = abs(net)

                if net >= 0.08:
                    state_label = "Source Leading"
                    detail = (
                        f"{assets[source_symbol]['label']} is providing more directional information to "
                        f"{assets[target_symbol]['label']} than it receives back."
                    )
                elif net <= -0.08:
                    state_label = "Target Leading"
                    detail = (
                        f"{assets[target_symbol]['label']} is driving the loop more than "
                        f"{assets[source_symbol]['label']} right now."
                    )
                else:
                    state_label = "Balanced"
                    detail = "Lead-lag is weak enough that correlation matters more than directionality."

                target_20d = 0.0
                if len(target_prices) > 20:
                    start_price = float(target_prices.iloc[-21] or 0)
                    end_price = float(target_prices.iloc[-1] or 0)
                    if start_price:
                        target_20d = ((end_price / start_price) - 1) * 100

                pair_rows.append(
                    {
                        "source_symbol": source_symbol,
                        "source_label": assets[source_symbol]["label"],
                        "source_group": assets[source_symbol]["group"],
                        "target_symbol": target_symbol,
                        "target_label": assets[target_symbol]["label"],
                        "target_group": assets[target_symbol]["group"],
                        "forward_te": _fmt_number(forward, 3),
                        "reverse_te": _fmt_number(reverse, 3),
                        "net_influence": _fmt_number(net, 3),
                        "state_label": state_label,
                        "detail": detail,
                        "source_change_20d": _fmt_pct(source_20d),
                        "target_change_20d": _fmt_pct(target_20d),
                        "magnitude": magnitude,
                    }
                )

                source_bucket = source_stats.setdefault(
                    source_symbol,
                    {"label": assets[source_symbol]["label"], "group": assets[source_symbol]["group"], "leading_count": 0, "net_total": 0.0, "pairs": 0},
                )
                source_bucket["pairs"] += 1
                source_bucket["net_total"] += net
                if net > 0:
                    source_bucket["leading_count"] += 1

                target_bucket = target_stats.setdefault(
                    target_symbol,
                    {"label": assets[target_symbol]["label"], "group": assets[target_symbol]["group"], "incoming_total": 0.0, "pairs": 0},
                )
                target_bucket["pairs"] += 1
                target_bucket["incoming_total"] += max(net, 0.0)

        if not pair_rows:
            placeholder = self._influence_placeholder(generated_at)
            cache_set(cache_key, placeholder, ttl=self.ttl_seconds)
            self.snapshot_store.write_json(self._influence_snapshot_key(), placeholder)
            return placeholder

        pair_rows = sorted(pair_rows, key=lambda item: float(item.get("magnitude") or 0.0), reverse=True)
        source_rows = sorted(
            [
                {
                    "label": bucket["label"],
                    "group": bucket["group"],
                    "leading_count": bucket["leading_count"],
                    "average_net": _fmt_number(bucket["net_total"] / max(bucket["pairs"], 1), 3),
                    "lead_bias": (
                        "Macro leader" if bucket["leading_count"] >= max(1, bucket["pairs"] - 1)
                        else "Selective leader" if bucket["leading_count"] >= 2
                        else "Reactive"
                    ),
                }
                for bucket in source_stats.values()
            ],
            key=lambda item: float(item["average_net"]),
            reverse=True,
        )
        target_rows = sorted(
            [
                {
                    "label": bucket["label"],
                    "group": bucket["group"],
                    "incoming_pressure": _fmt_number(bucket["incoming_total"], 3),
                    "pairs": bucket["pairs"],
                }
                for bucket in target_stats.values()
            ],
            key=lambda item: float(item["incoming_pressure"]),
            reverse=True,
        )
        leader_pair = pair_rows[0]
        top_source = source_rows[0] if source_rows else {"label": "N/A"}
        top_target = target_rows[0] if target_rows else {"label": "N/A"}
        headline_label = f"{leader_pair['source_label']} -> {leader_pair['target_label']}"
        if leader_pair.get("state_label") == "Target Leading":
            headline_label = f"{leader_pair['target_label']} -> {leader_pair['source_label']}"

        workspace = _to_json_safe(
            {
                "generated_at": generated_at,
                "headline": {
                    "label": headline_label,
                    "detail": leader_pair["detail"],
                },
                "summary_cards": [
                    {
                        "label": "Directed flows",
                        "value": str(len(pair_rows)),
                        "detail": "Transfer entropy pairs with enough stable history.",
                    },
                    {
                        "label": "Leading macro source",
                        "value": top_source.get("label", "N/A"),
                        "detail": f"{top_source.get('lead_bias', 'Warming')} across curated targets.",
                    },
                    {
                        "label": "Most influenced target",
                        "value": top_target.get("label", "N/A"),
                        "detail": "Highest incoming transfer-entropy pressure from curated sources.",
                    },
                ],
                "pair_rows": pair_rows[:12],
                "source_rows": source_rows,
                "target_rows": target_rows,
                "methodology": [
                    "Transfer entropy is directional, unlike simple correlation, so it helps identify who is leading and who is reacting.",
                    "Positive net influence means the source adds more information about the target's next move than the reverse loop does.",
                    "Use this as a regime and leadership lens, not as a trading trigger on its own.",
                ],
            }
        )
        cache_set(cache_key, workspace, ttl=self.ttl_seconds)
        self.snapshot_store.write_json(self._influence_snapshot_key(), workspace)
        return workspace

    def _build_bist_catalyst_lane(self) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        try:
            workspace = self.public_research.get_bist_quality_board_workspace(limit=6)
            rows = []
            for item in workspace.get("rows", [])[:5]:
                catalyst_tape = item.get("catalyst_tape") or {}
                rows.append(
                    {
                        "symbol": item.get("symbol"),
                        "name": item.get("name"),
                        "sector": item.get("sector"),
                        "disclosure_momentum_score": item.get("disclosure_momentum_score"),
                        "material_disclosures_90d": item.get("material_disclosures_90d"),
                        "contract_mentions_365d": item.get("contract_mentions_365d"),
                        "contracts_to_sales": item.get("contracts_to_sales"),
                        "capital_profile": item.get("capital_profile"),
                        "fundamental_rating": item.get("fundamental_rating"),
                        "trend_label": item.get("trend_label"),
                        "predictability_score": item.get("predictability_score"),
                        "board_score": item.get("board_score"),
                        "catalyst_clean_score": item.get("catalyst_clean_score"),
                        "catalyst_tape_label": catalyst_tape.get("label", "Watch"),
                        "catalyst_tape_detail": catalyst_tape.get(
                            "detail",
                            "Catalyst pressure and tape quality are still warming.",
                        ),
                        "detail_path": f"/stocks?symbol={item.get('symbol')}",
                    }
                )
            if rows:
                top_row = rows[0]
                return rows, {
                    "state": "healthy",
                    "state_label": str(top_row.get("catalyst_tape_label") or "Catalyst Active"),
                    "detail": (
                        "BIST lane now ranks names where KAP flow, capital efficiency, and clean-tape "
                        "confirmation are aligned instead of just counting raw disclosures."
                    ),
                    "leader": top_row.get("symbol"),
                    "leader_predictability": top_row.get("predictability_score"),
                    "leader_clean_score": top_row.get("catalyst_clean_score"),
                    "active_count": len(rows),
                }
        except Exception as exc:
            logger.warning("BIST catalyst lane build failed", error=str(exc))

        return [], {
            "state": "warming",
            "state_label": "Refreshing",
            "detail": "BIST catalyst lane is warming.",
            "leader": None,
            "active_count": 0,
        }

    def _build_market_physics(
        self,
        entropy_signal: Dict[str, Any],
        generated_at: str,
    ) -> Dict[str, Any]:
        asset_rows = entropy_signal.get("asset_rows") if isinstance(entropy_signal, dict) else []
        if not isinstance(asset_rows, list) or not asset_rows:
            return self._market_physics_placeholder(generated_at)

        rows: List[Dict[str, Any]] = []
        for item in asset_rows:
            if not isinstance(item, dict):
                continue
            change_5d = _safe_float(item.get("change_5d"))
            change_20d = _safe_float(item.get("change_20d"))
            change_60d = _safe_float(item.get("change_60d"))
            predictability = _safe_float(item.get("predictability_score")) or 0.0
            horizon_changes = [value for value in (change_5d, change_20d, change_60d) if value is not None]
            if not horizon_changes:
                continue
            horizon_signs = [1 if value > 0 else -1 if value < 0 else 0 for value in horizon_changes]
            positive_count = sum(1 for sign in horizon_signs if sign > 0)
            negative_count = sum(1 for sign in horizon_signs if sign < 0)
            aligned_count = max(positive_count, negative_count)
            alignment_ratio = aligned_count / max(len(horizon_signs), 1)
            phase_score = round(min(100.0, alignment_ratio * 60.0 + min(predictability, 100.0) * 0.4), 1)

            if positive_count == len(horizon_signs) and predictability >= 60:
                phase_label = "In-Phase Upswing"
                phase_detail = "Short, medium, and intermediate horizons are all leaning the same way with orderly return structure."
            elif negative_count == len(horizon_signs) and predictability >= 60:
                phase_label = "In-Phase Drawdown"
                phase_detail = "All tracked horizons are pointing lower, but the move remains structured rather than random."
            elif positive_count >= 2 and predictability >= 50:
                phase_label = "Constructive Alignment"
                phase_detail = "Most horizons are aligned to the upside and entropy is not fighting the move."
            elif negative_count >= 2 and predictability >= 50:
                phase_label = "Defensive Alignment"
                phase_detail = "Most horizons lean down, so defense deserves more weight than bottom-fishing."
            else:
                phase_label = "Fractured Tape"
                phase_detail = "Direction is not coherent across horizons yet, so extrapolation deserves less trust."

            rows.append(
                {
                    "symbol": item.get("symbol"),
                    "label": item.get("label"),
                    "phase_label": phase_label,
                    "phase_detail": phase_detail,
                    "phase_score": phase_score,
                    "predictability_score": item.get("predictability_score"),
                    "spectral_clarity": item.get("spectral_clarity"),
                    "change_5d_label": item.get("change_5d_label", "N/A"),
                    "change_20d_label": item.get("change_20d_label", "N/A"),
                    "change_60d_label": item.get("change_60d_label", "N/A"),
                }
            )

        if not rows:
            return self._market_physics_placeholder(generated_at)

        rows = sorted(rows, key=lambda item: _safe_float(item.get("phase_score")) or 0.0, reverse=True)
        average_phase_score = round(
            float(np.mean([_safe_float(item.get("phase_score")) or 0.0 for item in rows])),
            1,
        )
        leader = rows[0]

        if average_phase_score >= 75:
            phase_regime = "Coherent Trend"
            stance = "Cross-horizon direction is aligned. Trend signals deserve more respect than usual."
        elif average_phase_score >= 60:
            phase_regime = "Selective Alignment"
            stance = "Some parts of the tape are aligned, but dispersion across horizons still matters."
        elif average_phase_score >= 45:
            phase_regime = "Mixed Phase"
            stance = "Direction is partially aligned, so conviction should stay selective."
        else:
            phase_regime = "Fragmented Tape"
            stance = "Multiple horizons are fighting each other. Price action is noisier than it looks."

        return {
            "state": "healthy" if len(rows) >= 3 else "degraded",
            "state_label": "Healthy" if len(rows) >= 3 else "Degraded",
            "phase_regime": phase_regime,
            "stance": stance,
            "average_phase_score": average_phase_score,
            "leader_asset": leader.get("label"),
            "leader_symbol": leader.get("symbol"),
            "updated_at": generated_at,
            "rows": rows,
            "note": (
                "We use phase alignment because trends deserve more trust when short-, medium-, and "
                "intermediate-horizon returns point the same way while entropy stays orderly."
            ),
        }

    def _build_coverage_cards(self) -> List[Dict[str, str]]:
        return [
            {
                "label": "Sources",
                "value": "Yahoo, CoinGecko, FRED, U.S. Treasury, TCMB EVDS, TEFAS",
                "detail": "Server-side fetch only",
            },
            {
                "label": "Cadence",
                "value": "5 min dashboard cache",
                "detail": "Read-only public surface",
            },
            {
                "label": "Positioning",
                "value": "Signal-first workflow",
                "detail": "No account wall, no user state",
            },
            {
                "label": "Use Case",
                "value": "Orientation, not execution",
                "detail": "Research support, not order routing",
            },
        ]

    def _build_entropy_signal(self, generated_at: str) -> Dict[str, Any]:
        assets = [
            ("^GSPC", "S&P 500"),
            ("^IXIC", "Nasdaq"),
            ("XU100.IS", "BIST 100"),
            ("BTC-USD", "Bitcoin"),
        ]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.entropy_window_days + 20)
        rows: List[Dict[str, Any]] = []

        for symbol, label in assets:
            try:
                hist = self.yahoo.get_historical_data(
                    start_date=start_date,
                    end_date=end_date,
                    symbol=symbol,
                    interval="1d",
                )
            except Exception:
                hist = pd.DataFrame()

            if hist.empty or "close_price" not in hist:
                continue

            prices = pd.to_numeric(hist["close_price"], errors="coerce").dropna().reset_index(drop=True)
            if len(prices) < 35:
                continue

            returns = prices.pct_change().dropna()
            if len(returns) < 30:
                continue

            shannon = _safe_entropy_unit_interval(self.entropy.shannon_entropy(returns))
            permutation = _safe_entropy_unit_interval(self.entropy.permutation_entropy(returns))
            approximate = _safe_float(self.entropy.approximate_entropy(returns))
            spectral = _safe_entropy_unit_interval(self.entropy.spectral_entropy(returns))

            complexity_components = [
                value
                for value in (
                    _safe_entropy_score(shannon),
                    _safe_entropy_score(permutation),
                    max(0.0, min(100.0, float(approximate) * 50.0)) if approximate is not None else np.nan,
                )
                if value is not None and np.isfinite(value)
            ]
            if not complexity_components:
                continue

            complexity_score = round(float(np.mean(complexity_components)), 1)
            predictability_score = round(max(0.0, min(100.0, 100.0 - complexity_score)), 1)
            change_20d = 0.0
            if len(prices) > 20:
                start_price = float(prices.iloc[-21] or 0)
                end_price = float(prices.iloc[-1] or 0)
                if start_price:
                    change_20d = ((end_price / start_price) - 1) * 100
            change_5d = 0.0
            if len(prices) > 5:
                start_price = float(prices.iloc[-6] or 0)
                end_price = float(prices.iloc[-1] or 0)
                if start_price:
                    change_5d = ((end_price / start_price) - 1) * 100
            change_60d = 0.0
            if len(prices) > 60:
                start_price = float(prices.iloc[-61] or 0)
                end_price = float(prices.iloc[-1] or 0)
                if start_price:
                    change_60d = ((end_price / start_price) - 1) * 100

            regime = self.entropy._identify_market_regime(
                {
                    "shannon_entropy": shannon if shannon is not None else 0.5,
                    "approximate_entropy": max(0.0, min(2.0, float(approximate))) if approximate is not None else 1.0,
                }
            )
            risk_level = self.entropy._assess_entropy_risk({"complexity_score": complexity_score})
            if predictability_score >= 65 and change_20d >= 0:
                posture = "Trend Confirming"
            elif predictability_score >= 65 and change_20d < 0:
                posture = "Orderly Risk-Off"
            elif predictability_score >= 50:
                posture = "Selective"
            else:
                posture = "Chaotic"

            rows.append(
                {
                    "symbol": symbol,
                    "label": label,
                    "regime": regime,
                    "risk_level": risk_level,
                    "posture": posture,
                    "predictability_score": predictability_score,
                    "complexity_score": complexity_score,
                    "shannon_entropy": round(float(shannon) * 100, 1) if shannon is not None else None,
                    "permutation_entropy": round(float(permutation) * 100, 1) if permutation is not None else None,
                    "spectral_clarity": round(max(0.0, 100.0 - float(spectral) * 100), 1) if spectral is not None else None,
                    "change_5d": round(change_5d, 1),
                    "change_5d_label": _fmt_pct(change_5d),
                    "change_20d": round(change_20d, 1),
                    "change_20d_label": _fmt_pct(change_20d),
                    "change_60d": round(change_60d, 1),
                    "change_60d_label": _fmt_pct(change_60d),
                    "tone": _tone_for_change(change_20d),
                }
            )

        if not rows:
            return self._entropy_placeholder(generated_at)

        leader = max(rows, key=lambda item: (float(item["predictability_score"]), float(item["change_20d"])))
        avg_predictability = round(float(np.mean([float(item["predictability_score"]) for item in rows])), 1)
        avg_complexity = round(float(np.mean([float(item["complexity_score"]) for item in rows])), 1)
        avg_change = float(np.mean([float(item["change_20d"]) for item in rows]))

        if avg_complexity <= 30:
            regime = "Structured Trend"
        elif avg_complexity <= 45:
            regime = "Constructive Trend"
        elif avg_complexity <= 60:
            regime = "Transitional"
        elif avg_complexity <= 75:
            regime = "Choppy"
        else:
            regime = "Chaotic"

        if avg_predictability >= 65 and avg_change >= 0:
            stance = "Trend-following conditions are cleaner than usual."
        elif avg_predictability >= 65 and avg_change < 0:
            stance = "Orderly downside is dominating. Respect defense."
        elif avg_predictability >= 50:
            stance = "Signals are mixed. Be selective and price-sensitive."
        else:
            stance = "Return patterns are noisy. Capital preservation matters more than conviction."

        return {
            "state": "healthy" if len(rows) >= 3 else "degraded",
            "state_label": "Healthy" if len(rows) >= 3 else "Degraded",
            "regime": regime,
            "stance": stance,
            "predictability_score": avg_predictability,
            "complexity_score": avg_complexity,
            "leader_asset": leader["label"],
            "leader_symbol": leader["symbol"],
            "window_days": self.entropy_window_days,
            "updated_at": generated_at,
            "asset_rows": rows,
            "note": "Entropy here measures how ordered return patterns are, not whether price direction is bullish by itself.",
        }

    def _build_market_cards(self, generated_at: str) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
        symbols = ["^GSPC", "^IXIC", "^DJI", "XU100.IS", "GC=F", "CL=F"]
        fallback_labels = {
            "^GSPC": "S&P 500",
            "^IXIC": "Nasdaq",
            "^DJI": "Dow Jones",
            "XU100.IS": "BIST 100",
            "GC=F": "Gold",
            "CL=F": "Crude Oil",
        }

        data = self.yahoo.collect_data(symbols=symbols).get("market_data", [])
        cards = []
        for item in data:
            cards.append(
                {
                    "symbol": item["symbol"],
                    "label": fallback_labels.get(item["symbol"], item.get("name", item["symbol"])),
                    "price": _fmt_number(item.get("current_price", 0)),
                    "change_pct": float(item.get("price_change_percentage", 0) or 0),
                    "change_label": f"{float(item.get('price_change_percentage', 0) or 0):+.2f}%",
                    "tone": _tone_for_change(float(item.get("price_change_percentage", 0) or 0)),
                    "source": "Yahoo Finance",
                }
            )
        status = {
            "key": "market",
            "label": "Market feed",
            "state": "healthy" if len(cards) >= 4 else "degraded",
            "state_label": "Healthy" if len(cards) >= 4 else "Degraded",
            "detail": f"{len(cards)} market cards rendered from Yahoo Finance.",
            "updated_at": generated_at,
        }
        return cards, status

    def _build_macro_cards(self, generated_at: str) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
        cards: List[Dict[str, Any]] = []
        liquidity = self.fred.get_liquidity_indicators() if settings.FRED_API_KEY else {}
        indicators = liquidity.get("liquidity_indicators", {}) if liquidity else {}
        evds_payload = self.evds.get_macro_indicators() if settings.TCMB_EVDS_API_KEY else {}
        evds_indicators = evds_payload.get("macro_indicators", {}) if evds_payload else {}
        treasury_payload = self.fiscaldata.get_fiscal_indicators()
        treasury_indicators = treasury_payload.get("fiscal_indicators", {}) if treasury_payload else {}
        using_fallback = False
        fred_cards = 0
        evds_cards = 0
        treasury_cards = 0

        if indicators:
            for key, label in (
                ("WALCL", "Fed Balance Sheet"),
                ("M2SL", "US M2"),
                ("ECBASSETSW", "ECB Assets"),
                ("JPNASSETS", "BoJ Assets"),
            ):
                if key not in indicators:
                    continue
                item = indicators[key]
                change = float(item.get("change_percent", 0) or 0)
                cards.append(
                    {
                        "label": label,
                        "value": _fmt_compact_amount(
                            item.get("display_value", item.get("current_value", 0)),
                            item.get("currency_code", "USD"),
                        ),
                        "delta": f"{change:+.2f}%",
                        "tone": _tone_for_change(change),
                        "source": "FRED",
                    }
                )
                fred_cards += 1

        if evds_indicators:
            for key, label in (
                ("TCMB_RESERVES_TOTAL", "CBRT Total Reserves"),
                ("TP.AB.C2", "FX Reserves"),
                ("TP.AB.C1", "Gold Reserves"),
            ):
                if key not in evds_indicators:
                    continue
                item = evds_indicators[key]
                change = float(item.get("change_percent", 0) or 0)
                tone_multiplier = float(item.get("tone_multiplier", 1) or 1)
                if item.get("display_kind") == "price":
                    value_label = _fmt_number(
                        item.get("display_value", item.get("current_value", 0)),
                        digits=int(item.get("display_digits", 2) or 2),
                    )
                else:
                    value_label = _fmt_compact_amount(
                        item.get("display_value", item.get("current_value", 0)),
                        item.get("currency_code", "USD"),
                    )
                cards.append(
                    {
                        "label": label,
                        "value": value_label,
                        "delta": f"{change:+.2f}%",
                        "tone": _tone_for_change(change * tone_multiplier),
                        "source": "TCMB EVDS",
                    }
                )
                evds_cards += 1

        if treasury_indicators:
            for key, label in (
                ("tot_pub_debt_out_amt", "US Public Debt"),
                ("debt_held_public_amt", "Debt Held by Public"),
                ("tga_closing_balance", "Treasury Cash"),
            ):
                if key not in treasury_indicators:
                    continue
                item = treasury_indicators[key]
                change = float(item.get("change_percent", 0) or 0)
                cards.append(
                    {
                        "label": label,
                        "value": _fmt_compact_amount(
                            item.get("display_value", item.get("current_value", 0)),
                            item.get("currency_code", "USD"),
                        ),
                        "delta": f"{change:+.2f}%",
                        "tone": _tone_for_change(change),
                        "source": "U.S. Treasury",
                    }
                )
                treasury_cards += 1

        if not cards:
            cards.extend(
                [
                    {
                        "label": "Fed Balance Sheet",
                        "value": "$8.5T",
                        "delta": "Fallback",
                        "tone": "neutral",
                        "source": "Local fallback",
                    },
                    {
                        "label": "US M2",
                        "value": "$21.7T",
                        "delta": "Fallback",
                        "tone": "neutral",
                        "source": "Local fallback",
                    },
                ]
            )
            using_fallback = True

        source_chunks: List[str] = []
        if fred_cards:
            source_chunks.append(f"{fred_cards} FRED")
        if evds_cards:
            source_chunks.append(f"{evds_cards} TCMB EVDS")
        if treasury_cards:
            source_chunks.append(f"{treasury_cards} U.S. Treasury")
        status = {
            "key": "macro",
            "label": "Macro feed",
            "state": "degraded" if using_fallback or len(cards) < 3 else "healthy",
            "state_label": "Fallback" if using_fallback else ("Degraded" if len(cards) < 3 else "Healthy"),
            "detail": "Using local fallback values because live official macro sources are unavailable."
            if using_fallback
            else f"{len(cards)} macro cards refreshed from {' + '.join(source_chunks)}.",
            "updated_at": generated_at,
        }
        return cards, status

    def _build_crypto_cards(self, generated_at: str) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
        payload = self.coingecko.collect_data(coins=["bitcoin", "ethereum"]).get("market_data", [])
        cards = []
        for item in payload[:2]:
            change = float(item.get("price_change_percentage_24h", 0) or 0)
            cards.append(
                {
                    "symbol": item.get("symbol", "").upper(),
                    "label": item.get("name", "").strip() or item.get("symbol", "").upper(),
                    "price": _fmt_number(item.get("current_price", 0)),
                    "change_pct": change,
                    "change_label": f"{change:+.2f}%",
                    "tone": _tone_for_change(change),
                    "source": "CoinGecko",
                }
            )
        status = {
            "key": "crypto",
            "label": "Crypto feed",
            "state": "healthy" if cards else "warming",
            "state_label": "Healthy" if cards else "Refreshing",
            "detail": f"{len(cards)} crypto cards rendered from CoinGecko."
            if cards
            else "Crypto feed is temporarily empty and will repopulate on the next refresh.",
            "updated_at": generated_at,
        }
        return cards, status

    def _build_sentiment(self) -> Dict[str, Any]:
        fear_greed = self.coingecko.get_fear_greed_index() or {}
        vix_payload = self.yahoo.collect_data(symbols=["^VIX"]).get("market_data", [])
        vix_item = vix_payload[0] if vix_payload else {}

        fng_value = int(fear_greed.get("value", 50) or 50)
        vix_value = float(vix_item.get("current_price", 18.5) or 18.5)
        vix_change = float(vix_item.get("price_change_percentage", 0) or 0)

        normalized_fng = fng_value / 100
        normalized_vix = max(0.0, min(1.0, 1 - (vix_value / 40)))
        score = round((normalized_fng + normalized_vix) / 2, 2)

        if score >= 0.7:
            mood = "Risk-on"
        elif score >= 0.55:
            mood = "Constructive"
        elif score >= 0.4:
            mood = "Neutral"
        else:
            mood = "Defensive"

        return {
            "score": score,
            "mood": mood,
            "fear_greed_value": fng_value,
            "fear_greed_label": fear_greed.get("value_classification", "Neutral"),
            "vix_value": round(vix_value, 2),
            "vix_change": round(vix_change, 2),
            "vix_label": f"{vix_value:.2f}",
        }

    def _build_cached_tr_peer_board(self) -> List[Dict[str, Any]]:
        peer_df = cache_get(f"tr-funds:peer-board:{self.public_tr_funds_months}")
        if not isinstance(peer_df, pd.DataFrame):
            return []
        if peer_df.empty:
            return []
        return peer_df.head(6).to_dict("records")

    def _build_cached_tr_top_pick(self) -> Dict[str, Any] | None:
        peer_df = cache_get(f"tr-funds:peer-board:{self.public_tr_funds_months}")
        if not isinstance(peer_df, pd.DataFrame) or peer_df.empty:
            return None
        return dict(peer_df.iloc[0])

    def _build_tr_status(self, generated_at: str, tr_peer_board: List[Dict[str, Any]]) -> Dict[str, str]:
        status = self.tr_funds.get_status(months=self.public_tr_funds_months)
        state = status.get("status", "warming")
        if tr_peer_board and state == "warming":
            state = "healthy"
        return {
            "key": "tr-funds",
            "label": "TR funds",
            "state": state,
            "state_label": {
                "healthy": "Healthy",
                "degraded": "Degraded",
                "warming": "Warming",
            }.get(state, state.title()),
            "detail": status.get("detail") or "TR funds cache is not ready yet.",
            "updated_at": status.get("last_success_at") or status.get("last_attempt_at") or generated_at,
        }

    def _build_sponsor_slots(self) -> List[Dict[str, str]]:
        defaults = [
            {
                "title": "Sponsor This Slot",
                "label": "Commercial placement",
                "href": f"mailto:{settings.SUPPORT_EMAIL}?subject=FundPilot%20Sponsorship",
                "description": "Weekly sponsor placement for research tools, broker infrastructure, or market data products.",
                "badge": "Sponsored",
            },
            {
                "title": "Partner Tooling",
                "label": "Affiliate-ready slot",
                "href": f"mailto:{settings.SUPPORT_EMAIL}?subject=FundPilot%20Affiliate%20Placement",
                "description": "Reserved for privacy-compatible affiliate tools that do not require invasive ad-tech scripts.",
                "badge": "Affiliate",
            },
            {
                "title": "Research Briefing",
                "label": "Editorial placement",
                "href": settings.PUBLIC_SITE_URL,
                "description": "Use this slot for owned media, premium briefings, or sponsor-supported research notes.",
                "badge": "Editorial",
            },
        ]
        return [_affiliate_slot(index + 1, item) for index, item in enumerate(defaults)]

    def _build_editorial_cards(self) -> List[Dict[str, str]]:
        return [
            {
                "title": "Open Access By Design",
                "body": "The public build favors fast market orientation and readable signal layers over account-gated feature sprawl.",
            },
            {
                "title": "TR Funds First",
                "body": "FundPilot's clearest differentiation is the Turkish funds workflow: TEFAS signal board, allocation drift, and investor momentum.",
            },
            {
                "title": "No Ad-Tech Dependency",
                "body": "Revenue surfaces are sponsor and affiliate placements rendered directly by the app, not by third-party ad exchanges.",
            },
        ]
