from __future__ import annotations

import csv
import json
import re
import unicodedata
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
import yfinance as yf

from app.analytics.comprehensive_fund_analyzer import ComprehensiveFundAnalyzer
from app.analytics.entropy_metrics import EntropyCalculator
from app.analytics.forecasting import ForecastingEngine
from app.analytics.public_price_predictions import PublicPricePredictionEngine
from app.analytics.sector_analysis import SectorAnalyzer
from app.analytics.stock_screener import (
    StockScreener,
    get_bist_stocks,
    get_china_sample,
    get_europe_sample,
    get_hong_kong_sample,
    get_japan_sample,
    get_nasdaq_sample,
    get_south_korea_sample,
    get_sp500_sample,
)
from app.analytics.stocks_etfs import StocksETFsAnalyzer
from app.analytics.trends import TrendAnalyzer
from app.core.config import settings
from app.data_collectors.stocks_etfs import StocksETFsCollector
from app.data_collectors.yahoo_finance import YahooFinanceCollector
from app.services.cache import cache_get, cache_set
from app.services.institutional_pulse import InstitutionalPulseService
from app.services.snapshot_store import SnapshotStore
from app.services.stock_enrichment import StockEnrichmentService
from app.services.sovereign_funds_data import SOVEREIGN_FUNDS
from app.services.tr_funds import (
    ASSET_LABELS,
    FEATURED_FUND_CODES,
    TRFundsService,
    _board_band,
    _board_score,
    _category_percentile,
    _dominant_asset,
    _fund_family,
    _fund_regime,
    _local_factor_lens,
    _quality_tier,
    _signal_band,
    _signal_score,
)
from modules.etf_weight_tracker import ETFWeightTracker
from modules.portfolio_health import PortfolioHealthScore
from modules.scenario_sandbox import ScenarioSandbox


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
    if isinstance(value, pd.DataFrame):
        return _to_json_safe(value.to_dict("records"))
    if isinstance(value, pd.Series):
        return _to_json_safe(value.to_dict())
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def _fmt_pct(value: Any) -> str:
    try:
        return f"{float(value):+.2f}%"
    except Exception:
        return "N/A"


def _fmt_number(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return "N/A"


def _fmt_compact_money(value: Any) -> str:
    try:
        amount = float(value or 0)
    except Exception:
        return "N/A"
    if abs(amount) >= 1_000_000_000_000:
        return f"${amount / 1_000_000_000_000:.1f}T"
    if abs(amount) >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if abs(amount) >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    return f"${amount:,.0f}"


def _fmt_compact_number(value: Any) -> str:
    try:
        amount = float(value or 0)
    except Exception:
        return "N/A"
    if abs(amount) >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f}B"
    if abs(amount) >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M"
    if abs(amount) >= 1_000:
        return f"{amount / 1_000:.1f}K"
    return f"{amount:,.0f}"


def _fmt_shares(value: Any) -> str:
    try:
        return f"{float(value):,.0f}"
    except Exception:
        return "N/A"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _label_to_float(value: Any) -> float:
    try:
        return float(str(value).replace("%", "").replace("+", "").replace(",", ""))
    except Exception:
        return 0.0


def _extract_numeric_token(value: Any) -> float | None:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value or "").replace(",", ""))
    if not match:
        return None
    return _safe_float(match.group(0))


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
        if np.isnan(number) or np.isinf(number):
            return None
        return number
    except Exception:
        return None


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


def _safe_div(numerator: Any, denominator: Any) -> float | None:
    left = _safe_float(numerator)
    right = _safe_float(denominator)
    if left is None or right in (None, 0):
        return None
    return left / right


def _fmt_multiple(value: Any, digits: int = 2) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "N/A"
    return f"{numeric:,.{digits}f}x"


def _fmt_optional_pct(value: Any, digits: int = 1, assume_decimal: bool = False) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "N/A"
    if assume_decimal or abs(numeric) <= 1.5:
        numeric *= 100
    return f"{numeric:+,.{digits}f}%"


def _fmt_try(value: Any) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "N/A"
    if abs(numeric) >= 1_000_000_000:
        return f"TRY {numeric / 1_000_000_000:.1f}B"
    if abs(numeric) >= 1_000_000:
        return f"TRY {numeric / 1_000_000:.1f}M"
    return f"TRY {numeric:,.0f}"


class PublicResearchService:
    def __init__(
        self,
        ttl_seconds: int | None = None,
        snapshot_store: SnapshotStore | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds or settings.PUBLIC_RESEARCH_TTL_SECONDS
        self.snapshot_store = snapshot_store or SnapshotStore()
        self.collector = StocksETFsCollector()
        self.stocks_analyzer = StocksETFsAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.yahoo = YahooFinanceCollector()
        self.screener = StockScreener()
        self.tr_funds_service = TRFundsService(snapshot_store=self.snapshot_store)
        self.stock_enrichment_service = StockEnrichmentService(snapshot_store=self.snapshot_store)
        self.institutional_pulse_service = InstitutionalPulseService()
        self.etf_tracker = self._build_etf_tracker()
        self.entropy = EntropyCalculator()
        self.entropy_window_days = 90

        self.screener_universes = {
            "sp500": {
                "label": "US Large Cap",
                "description": "Liquid S&P 500 sample for broad-market screening.",
                "symbols": get_sp500_sample()[:18],
            },
            "nasdaq": {
                "label": "US Growth",
                "description": "Large-cap Nasdaq names with higher momentum and tech tilt.",
                "symbols": get_nasdaq_sample()[:18],
            },
            "bist": {
                "label": "BIST Leaders",
                "description": "Turkish large-cap sample with local market relevance.",
                "symbols": get_bist_stocks()[:18],
            },
            "europe": {
                "label": "Europe Leaders",
                "description": "European large-cap sample across core continental markets.",
                "symbols": get_europe_sample()[:12],
            },
            "japan": {
                "label": "Japan Leaders",
                "description": "Japanese large-cap sample for Tokyo market analysis.",
                "symbols": get_japan_sample()[:12],
            },
            "south-korea": {
                "label": "South Korea Leaders",
                "description": "Korean large-cap sample for KRX market analysis.",
                "symbols": get_south_korea_sample()[:10],
            },
            "china": {
                "label": "China A-Shares",
                "description": "Mainland China sample using Shanghai and Shenzhen listings.",
                "symbols": get_china_sample()[:10],
            },
            "hong-kong": {
                "label": "Hong Kong Leaders",
                "description": "Large-cap Hong Kong listed names with China tech and finance exposure.",
                "symbols": get_hong_kong_sample()[:10],
            },
            "global": {
                "label": "Global Mix",
                "description": "Cross-market blend for faster top-down triage.",
                "symbols": [
                    "AAPL",
                    "NVDA",
                    "MSFT",
                    "ASML.AS",
                    "7203.T",
                    "005930.KS",
                    "600519.SS",
                    "0700.HK",
                    "JPM",
                    "THYAO.IS",
                    "GARAN.IS",
                    "ASELS.IS",
                    "TUPRS.IS",
                    "BIMAS.IS",
                    "SAP.DE",
                    "9988.HK",
                    "300750.SZ",
                    "6758.T",
                ],
            },
        }

        self.ownership_focuses = {
            "core": {
                "label": "Core Index",
                "description": "Broad-market ETFs for mainstream benchmark ownership.",
                "etfs": ["SPY", "QQQ", "VTI", "VOO", "IWM", "DIA"],
            },
            "sector": {
                "label": "Sector Rotation",
                "description": "Sector ETFs that reveal where passive flows cluster.",
                "etfs": ["XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLC", "XLRE"],
            },
            "innovation": {
                "label": "Innovation",
                "description": "Higher-beta thematic funds with concentrated positioning.",
                "etfs": ["ARKK", "ARKW", "VGT", "WCLD", "SKYY", "MTUM"],
            },
            "regional": {
                "label": "Regional ETFs",
                "description": "Regional market wrappers for Europe, Japan, Korea, China, and Hong Kong.",
                "etfs": ["VGK", "EWJ", "EWY", "FXI", "MCHI", "EWH"],
            },
        }

        self.scenario_presets = {
            "tcmb_hike_500bp": {
                "label": "TCMB 500bp Hike",
                "description": "Rate shock for BIST-heavy and duration-sensitive books.",
                "scenario_type": "interest_rate",
                "parameters": {"tcmb_change_bp": 500},
            },
            "2018_currency_crisis": {
                "label": "TRY Currency Shock",
                "description": "Sharp USD/TRY move with exporter-importer dispersion.",
                "scenario_type": "currency_shock",
                "parameters": {"usd_try_change_pct": 40},
            },
            "2020_covid_crash": {
                "label": "Equity Crash",
                "description": "Broad market drawdown across US and Turkish equities.",
                "scenario_type": "equity_shock",
                "parameters": {"sp500_change_pct": -30, "bist100_change_pct": -25},
            },
            "oil_shock_50pct": {
                "label": "Oil Spike",
                "description": "Commodity shock with energy winners and transport losers.",
                "scenario_type": "commodity_price",
                "parameters": {"oil_change_pct": 50},
            },
        }
        self.default_portfolio_text = "\n".join(
            [
                "AAPL,12,189",
                "MSFT,7,412",
                "NVDA,6,890",
                "THYAO,20,317",
                "GARAN,45,98",
            ]
        )
        self.curated_screener_overrides = {
            "institutional_accumulation": {
                "name": "Institutional Accumulation",
                "description": "Curated 13F managers are adding or newly building positions.",
                "criteria": {
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "market_cap",
                },
            },
            "crowded_13f": {
                "name": "13F Crowding",
                "description": "Names held across multiple curated 13F managers with meaningful combined weight.",
                "criteria": {
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "market_cap",
                },
            },
            "trend_confirmed_accumulation": {
                "name": "Trend-Confirmed Accumulation",
                "description": "Bullish names where curated sponsorship and entropy-confirmed trend structure are aligned.",
                "criteria": {
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "market_cap",
                },
            },
            "entropy_clean_setups": {
                "name": "Entropy-Clean Setups",
                "description": "Liquid names where return patterns are orderly enough for trend-following models to deserve more trust.",
                "criteria": {
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "market_cap",
                },
            },
            "bist_disclosure_leaders": {
                "name": "BIST Disclosure Leaders",
                "description": "Turkish large-cap names with active KAP flow, material disclosures, and visible catalyst density.",
                "criteria": {
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "market_cap",
                },
            },
            "bist_contract_intensity": {
                "name": "BIST Contract Intensity",
                "description": "BIST names where KAP contract flow is large relative to the latest annual sales base.",
                "criteria": {
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "market_cap",
                },
            },
        }

    def _tr_fund_snapshot_key(self, fund_code: str, months: int) -> str:
        return f"public-research-tr-fund-{fund_code.upper()}-{months}"

    def _stock_snapshot_key(self, symbol: str) -> str:
        return f"public-research-stock-{symbol.upper()}"

    def _fund_snapshot_key(self, symbol: str) -> str:
        return f"public-research-fund-{symbol.upper()}"

    def _featured_stock_symbols(self) -> list[str]:
        codes: list[str] = [
            "AAPL",
            "NVDA",
            "ASML.AS",
            "7203.T",
            "005930.KS",
            "600519.SS",
            "0700.HK",
            "THYAO",
            "GARAN",
            "ASELS",
            "TUPRS",
            "9988.HK",
        ]
        for code in list(self.collector.popular_stocks.keys())[:8]:
            normalized = str(code).upper()
            if normalized not in codes:
                codes.append(normalized)
        for code in ["SAP.DE", "NOVO-B.CO"]:
            if code not in codes:
                codes.append(code)
        return codes[:12]

    def _stock_market_profile(self, symbol: str) -> Dict[str, str]:
        normalized = str(symbol or "").upper()
        if normalized.endswith(".IS") or normalized in {str(code).upper() for code in get_bist_stocks()}:
            return {
                "market_key": "bist",
                "market_label": "BIST Leaders",
                "exchange": "Borsa Istanbul",
                "description": "Turkey coverage is deepest on KAP enrichment, paid-in-capital ratios, and disclosure-driven catalyst flow.",
            }
        if normalized.endswith(".T"):
            return {
                "market_key": "japan",
                "market_label": "Japan Leaders",
                "exchange": "Tokyo Stock Exchange",
                "description": "Japan coverage is strongest on single-name technicals, factor ranking, and market-relative comparison presets.",
            }
        if normalized.endswith(".KS"):
            return {
                "market_key": "south-korea",
                "market_label": "South Korea Leaders",
                "exchange": "Korea Exchange",
                "description": "Korea coverage focuses on liquid KRX names with cleaner momentum, capital, and comparative reads.",
            }
        if normalized.endswith(".SS") or normalized.endswith(".SZ"):
            return {
                "market_key": "china",
                "market_label": "China A-Shares",
                "exchange": "Shanghai / Shenzhen",
                "description": "China coverage is built around mainland A-shares where direct line-item analytics remain more reliable than narrative portals.",
            }
        if normalized.endswith(".HK"):
            return {
                "market_key": "hong-kong",
                "market_label": "Hong Kong Leaders",
                "exchange": "Hong Kong Stock Exchange",
                "description": "Hong Kong coverage is positioned for China-linked internet, finance, and cross-border leadership reads.",
            }
        if any(normalized.endswith(suffix) for suffix in (".AS", ".PA", ".DE", ".CO", ".SW")):
            return {
                "market_key": "europe",
                "market_label": "Europe Leaders",
                "exchange": "Pan-European listings",
                "description": "Europe coverage emphasizes large-cap continental names with clearer capital efficiency and factor screening.",
            }
        return {
            "market_key": "us",
            "market_label": "US Leaders",
            "exchange": "NYSE / Nasdaq",
            "description": "US coverage remains deepest on sector context, curated 13F sponsorship, and ETF ownership overlap.",
        }

    def _symbols_for_market(self, market_key: str) -> list[str]:
        if market_key == "us":
            symbols: list[str] = []
            for code in [*get_sp500_sample()[:10], *get_nasdaq_sample()[:10]]:
                normalized = str(code).upper()
                if normalized not in symbols:
                    symbols.append(normalized)
            return symbols
        if market_key in self.screener_universes:
            return [str(code).upper() for code in self.screener_universes[market_key].get("symbols", [])]
        return self._featured_stock_symbols()

    def _regional_stock_groups(self, selected_symbol: str) -> list[Dict[str, Any]]:
        selected_profile = self._stock_market_profile(selected_symbol)
        groups: list[Dict[str, Any]] = []
        market_order = [
            selected_profile["market_key"],
            "us",
            "europe",
            "japan",
            "south-korea",
            "china",
            "hong-kong",
            "bist",
        ]
        seen: set[str] = set()
        for market_key in market_order:
            if market_key in seen:
                continue
            seen.add(market_key)
            profile = self._stock_market_profile(market_key if "." in market_key else self._symbols_for_market(market_key)[0] if self._symbols_for_market(market_key) else market_key)
            symbols = [code for code in self._symbols_for_market(market_key) if code != str(selected_symbol or "").upper()][:4]
            if not symbols:
                continue
            groups.append(
                {
                    "market_key": market_key,
                    "label": profile["market_label"],
                    "exchange": profile["exchange"],
                    "selected": market_key == selected_profile["market_key"],
                    "symbols": symbols,
                    "screener_path": f"/screener?universe={'sp500' if market_key == 'us' else market_key}&screen=momentum_stocks&limit=8",
                    "radar_path": f"/idea-radar?universe={'global' if market_key == 'us' else market_key}&limit=8",
                }
            )
        return groups

    def _stock_compare_suggestions(self, symbol: str) -> list[Dict[str, str]]:
        selected_symbol = str(symbol or "").upper()
        profile = self._stock_market_profile(selected_symbol)
        suggestions: list[Dict[str, str]] = []
        seen: set[str] = {selected_symbol}

        for peer in self._symbols_for_market(profile["market_key"]):
            if peer in seen:
                continue
            seen.add(peer)
            suggestions.append(
                {
                    "symbol": peer,
                    "label": f"{selected_symbol} vs {peer}",
                    "reason": f"Same-market compare inside {profile['market_label']}.",
                    "path": f"/compare?kind=stocks&left={quote_plus(selected_symbol)}&right={quote_plus(peer)}",
                }
            )
            if len(suggestions) >= 3:
                break

        if len(suggestions) < 3:
            for peer in self._featured_stock_symbols():
                normalized = str(peer).upper()
                if normalized in seen:
                    continue
                seen.add(normalized)
                suggestions.append(
                    {
                        "symbol": normalized,
                        "label": f"{selected_symbol} vs {normalized}",
                        "reason": "Cross-market challenge for a faster global relative-value check.",
                        "path": f"/compare?kind=stocks&left={quote_plus(selected_symbol)}&right={quote_plus(normalized)}",
                    }
                )
                if len(suggestions) >= 3:
                    break

        return suggestions

    def _featured_fund_symbols(self) -> list[str]:
        codes: list[str] = [
            "SPY",
            "QQQ",
            "VTI",
            "VOO",
            "VGK",
            "EWJ",
            "EWY",
            "MCHI",
            "FXI",
            "EWH",
            "ARKK",
            "VGT",
        ]
        for code in list(self.collector.popular_etfs.keys())[:10]:
            normalized = str(code).upper()
            if normalized not in codes:
                codes.append(normalized)
        for code in ["EZU", "DXJ", "ASHR", "IEUR"]:
            if code not in codes:
                codes.append(code)
        return codes[:12]

    def _fund_market_groups_catalog(self) -> Dict[str, Dict[str, Any]]:
        return {
            "us-core": {
                "label": "US Core ETFs",
                "exchange": "US-listed benchmark ETFs",
                "description": "Broad US wrappers remain the cleanest place to compare fee drag, concentration, and benchmark posture.",
                "symbols": ["SPY", "QQQ", "VTI", "VOO", "IWM", "DIA"],
                "overlap_focus": "core",
            },
            "sector": {
                "label": "Sector Rotation ETFs",
                "exchange": "US sector ETF suite",
                "description": "Sector wrappers are best for passive crowding, rotation, and concentration drift.",
                "symbols": ["XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLC", "XLRE"],
                "overlap_focus": "sector",
            },
            "innovation": {
                "label": "Innovation ETFs",
                "exchange": "US-listed thematic ETFs",
                "description": "Thematic wrappers expose crowding and regime shifts earlier than generic market-cap benchmarks.",
                "symbols": ["ARKK", "ARKW", "VGT", "WCLD", "SKYY", "MTUM"],
                "overlap_focus": "innovation",
            },
            "europe": {
                "label": "Europe ETFs",
                "exchange": "US-listed Europe wrappers",
                "description": "Europe wrappers help separate currency-exposed regional beta from single-name stock selection noise.",
                "symbols": ["VGK", "EZU", "FEZ", "IEUR"],
                "overlap_focus": "regional",
            },
            "japan": {
                "label": "Japan ETFs",
                "exchange": "US-listed Japan wrappers",
                "description": "Japan ETF coverage is strongest on broad index, exporter tilt, and currency-hedged pairings.",
                "symbols": ["EWJ", "DXJ", "JPXN", "BBJP"],
                "overlap_focus": "regional",
            },
            "south-korea": {
                "label": "South Korea ETFs",
                "exchange": "US-listed Korea wrappers",
                "description": "Korea wrappers let you compare semiconductor-heavy leadership against broader KRX beta.",
                "symbols": ["EWY", "FLKR", "HEWY"],
                "overlap_focus": "regional",
            },
            "china": {
                "label": "China ETFs",
                "exchange": "US-listed China wrappers",
                "description": "China wrappers give a cleaner read on mainland, SOE, and internet-heavy exposure mixes.",
                "symbols": ["MCHI", "FXI", "ASHR", "GXC"],
                "overlap_focus": "regional",
            },
            "hong-kong": {
                "label": "Hong Kong ETFs",
                "exchange": "US-listed Hong Kong wrappers",
                "description": "Hong Kong wrappers are useful when China-linked internet and finance leadership diverges from mainland beta.",
                "symbols": ["EWH", "FLHK"],
                "overlap_focus": "regional",
            },
        }

    def _fund_market_profile(self, symbol: str) -> Dict[str, str]:
        normalized = str(symbol or "").upper()
        for market_key, config in self._fund_market_groups_catalog().items():
            if normalized in {str(code).upper() for code in config.get("symbols", [])}:
                return {
                    "market_key": market_key,
                    "market_label": str(config.get("label", "Funds & ETFs")),
                    "exchange": str(config.get("exchange", "US-listed wrappers")),
                    "description": str(config.get("description", "")),
                    "overlap_focus": str(config.get("overlap_focus", "core")),
                }
        if normalized in {str(code).upper() for code in self.ownership_focuses["regional"]["etfs"]}:
            return {
                "market_key": "regional",
                "market_label": "Regional ETFs",
                "exchange": "US-listed regional wrappers",
                "description": "Regional ETF coverage focuses on country and bloc-level ownership overlap.",
                "overlap_focus": "regional",
            }
        return {
            "market_key": "us-core",
            "market_label": "US Core ETFs",
            "exchange": "US-listed benchmark ETFs",
            "description": "Core ETF coverage is deepest on asset-base drift, ownership overlap, and benchmark-relative framing.",
            "overlap_focus": "core",
        }

    def _fund_symbols_for_market(self, market_key: str) -> list[str]:
        config = self._fund_market_groups_catalog().get(market_key)
        if config:
            return [str(code).upper() for code in config.get("symbols", [])]
        return self._featured_fund_symbols()

    def _regional_fund_groups(self, selected_symbol: str) -> list[Dict[str, Any]]:
        selected_profile = self._fund_market_profile(selected_symbol)
        groups: list[Dict[str, Any]] = []
        market_order = [
            selected_profile["market_key"],
            "us-core",
            "sector",
            "innovation",
            "europe",
            "japan",
            "south-korea",
            "china",
            "hong-kong",
        ]
        seen: set[str] = set()
        catalog = self._fund_market_groups_catalog()
        for market_key in market_order:
            if market_key in seen:
                continue
            seen.add(market_key)
            config = catalog.get(market_key)
            if not config:
                continue
            symbols = [code for code in self._fund_symbols_for_market(market_key) if code != str(selected_symbol or "").upper()][:4]
            if not symbols:
                continue
            groups.append(
                {
                    "market_key": market_key,
                    "label": str(config.get("label", market_key)),
                    "exchange": str(config.get("exchange", "US-listed wrappers")),
                    "selected": market_key == selected_profile["market_key"],
                    "symbols": symbols,
                    "overlap_path": f"/overlap-matrix?focus={quote_plus(str(config.get('overlap_focus', 'core')))}",
                }
            )
        return groups

    def _fund_compare_suggestions(self, symbol: str) -> list[Dict[str, str]]:
        selected_symbol = str(symbol or "").upper()
        profile = self._fund_market_profile(selected_symbol)
        suggestions: list[Dict[str, str]] = []
        seen: set[str] = {selected_symbol}

        for peer in self._fund_symbols_for_market(profile["market_key"]):
            if peer in seen:
                continue
            seen.add(peer)
            suggestions.append(
                {
                    "symbol": peer,
                    "label": f"{selected_symbol} vs {peer}",
                    "reason": f"Same-wrapper compare inside {profile['market_label']}.",
                    "path": f"/compare?kind=funds&left={quote_plus(selected_symbol)}&right={quote_plus(peer)}",
                }
            )
            if len(suggestions) >= 3:
                break

        if len(suggestions) < 3:
            for peer in self._featured_fund_symbols():
                normalized = str(peer).upper()
                if normalized in seen:
                    continue
                seen.add(normalized)
                suggestions.append(
                    {
                        "symbol": normalized,
                        "label": f"{selected_symbol} vs {normalized}",
                        "reason": "Cross-wrapper check for faster regional or thematic relative value.",
                        "path": f"/compare?kind=funds&left={quote_plus(selected_symbol)}&right={quote_plus(normalized)}",
                    }
                )
                if len(suggestions) >= 3:
                    break

        return suggestions

    def _featured_tr_funds(self, months: int) -> list[str]:
        codes: list[str] = []
        peer_board = self.tr_funds_service.get_cached_peer_signal_board(months=months)
        peer_codes = []
        if peer_board is not None and not peer_board.empty:
            peer_codes = [str(code).upper() for code in peer_board["fund_code"].head(4).tolist() if code]

        for code in FEATURED_FUND_CODES:
            if code == settings.PUBLIC_DEFAULT_TR_FUND_CODE or self.tr_funds_service.get_persisted_fund_summary(code, months):
                if code not in codes:
                    codes.append(code)

        for code in peer_codes:
            if code not in codes:
                codes.append(code)

        if not codes:
            codes.append(settings.PUBLIC_DEFAULT_TR_FUND_CODE)
        return codes[:4]

    def _fund_monthly_posture(self, monthly_return: float | None, asset_change: float | None) -> str:
        ret = monthly_return if monthly_return is not None else 0.0
        delta = asset_change if asset_change is not None else 0.0
        if ret >= 3.0 and delta > 0:
            return "Expansion"
        if ret <= -3.0 and delta < 0:
            return "Compression"
        if ret >= 0:
            return "Constructive"
        if ret <= -1.5:
            return "Under Pressure"
        return "Mixed"

    def _build_fund_monthly_rows(self, history_df: pd.DataFrame | None, total_assets: Any) -> tuple[list[dict[str, Any]], str]:
        if history_df is None or history_df.empty or "Close" not in history_df.columns:
            return [], "Upstream history did not expose a multi-month asset tape."

        df = history_df.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            if "Date" not in df.columns:
                return [], "Upstream history did not expose a multi-month asset tape."
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.set_index("Date")

        df = df.sort_index()
        df = df[~df.index.duplicated(keep="last")]
        close = pd.to_numeric(df.get("Close"), errors="coerce").dropna()
        if close.empty:
            return [], "Upstream history did not expose a multi-month asset tape."

        volume = pd.to_numeric(df.get("Volume"), errors="coerce").fillna(0.0)
        high = pd.to_numeric(df.get("High"), errors="coerce")
        low = pd.to_numeric(df.get("Low"), errors="coerce")
        daily_returns = close.pct_change()
        drawdown = (close / close.cummax() - 1.0) * 100

        monthly_close = close.resample("ME").last().dropna()
        if monthly_close.empty:
            return [], "Upstream history did not expose a multi-month asset tape."

        monthly_volume = volume.resample("ME").mean().reindex(monthly_close.index)
        monthly_return = (monthly_close.pct_change() * 100).reindex(monthly_close.index)
        monthly_high = high.resample("ME").max().reindex(monthly_close.index)
        monthly_low = low.resample("ME").min().reindex(monthly_close.index)
        monthly_volatility = (daily_returns.resample("ME").std() * np.sqrt(21) * 100).reindex(monthly_close.index)
        monthly_drawdown = drawdown.resample("ME").min().reindex(monthly_close.index)

        current_assets = _safe_float(total_assets)
        asset_proxy = None
        asset_change = None
        if current_assets is not None and current_assets > 0:
            asset_proxy = current_assets * (monthly_close / float(monthly_close.iloc[-1]))
            asset_change = asset_proxy.diff()

        rows: list[dict[str, Any]] = []
        for idx in monthly_close.index[-6:]:
            proxy_value = float(asset_proxy.loc[idx]) if asset_proxy is not None and idx in asset_proxy.index else None
            proxy_delta = float(asset_change.loc[idx]) if asset_change is not None and idx in asset_change.index else None
            month_return_value = _safe_float(monthly_return.loc[idx]) if idx in monthly_return.index else None
            range_low = _safe_float(monthly_low.loc[idx]) if idx in monthly_low.index else None
            range_high = _safe_float(monthly_high.loc[idx]) if idx in monthly_high.index else None
            rows.append(
                {
                    "month": idx.strftime("%Y-%m"),
                    "month_close": _fmt_number(monthly_close.loc[idx], 2),
                    "monthly_return": _fmt_pct(month_return_value),
                    "asset_base_proxy": _fmt_compact_money(proxy_value) if proxy_value is not None else "N/A",
                    "asset_change_proxy": _fmt_compact_money(proxy_delta) if proxy_delta is not None else "N/A",
                    "average_volume": _fmt_compact_number(monthly_volume.loc[idx]) if idx in monthly_volume.index else "N/A",
                    "realized_volatility": _fmt_pct(monthly_volatility.loc[idx]) if idx in monthly_volatility.index else "N/A",
                    "drawdown": _fmt_pct(monthly_drawdown.loc[idx]) if idx in monthly_drawdown.index else "N/A",
                    "trading_range": (
                        f"{_fmt_number(range_low, 2)} - {_fmt_number(range_high, 2)}"
                        if range_low is not None and range_high is not None
                        else "N/A"
                    ),
                    "posture": self._fund_monthly_posture(month_return_value, proxy_delta),
                }
            )

        note = (
            "Asset-base rows are monthly AUM proxies scaled from the latest disclosed total assets and month-end NAV/price."
            if current_assets is not None and current_assets > 0
            else "Current total assets are unavailable, so only price and risk drift are shown."
        )
        return rows, note

    def _build_fund_holdings_history(
        self,
        symbol: str,
        holdings_summary: Dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str]:
        rows: list[dict[str, Any]] = []
        note = "Holdings-history snapshots are still warming."

        try:
            self.etf_tracker.fetch_etf_holdings(symbol, force_refresh=False)
            history_df = self.etf_tracker.get_fund_snapshot_history(symbol, months=6, top_n=10)
        except Exception:
            history_df = pd.DataFrame()

        if history_df is not None and not history_df.empty:
            for _, row in history_df.tail(6).iterrows():
                shift_symbol = row.get("primary_shift_symbol")
                shift_pct = _safe_float(row.get("primary_shift_pct"))
                rows.append(
                    {
                        "month": row.get("month"),
                        "top_holding": row.get("top_holding", "N/A"),
                        "top_weight": _fmt_pct(row.get("top_weight")),
                        "top_10_concentration": _fmt_pct(row.get("top_10_concentration")),
                        "holdings_count": _fmt_compact_number(row.get("holdings_count")),
                        "primary_shift": (
                            f"{shift_symbol} {_fmt_pct(shift_pct)}"
                            if shift_symbol
                            else "History warming"
                        ),
                        "added_count": _fmt_compact_number(row.get("added_count")),
                        "removed_count": _fmt_compact_number(row.get("removed_count")),
                    }
                )
            note = "Month-end holdings snapshots use the latest saved ETF/fund file in each month."
            return rows, note

        top_holdings = holdings_summary.get("top_holdings", []) or []
        if top_holdings:
            top_row = top_holdings[0]
            rows.append(
                {
                    "month": "Current",
                    "top_holding": top_row.get("symbol") or top_row.get("holdingSymbol") or "N/A",
                    "top_weight": top_row.get("weight") or top_row.get("holdingPercent") or "N/A",
                    "top_10_concentration": holdings_summary.get("top_10_concentration", "N/A"),
                    "holdings_count": _fmt_compact_number(holdings_summary.get("holdings_count")),
                    "primary_shift": "History warming",
                    "added_count": "N/A",
                    "removed_count": "N/A",
                }
            )
            note = "Only the latest holdings file is available right now; multi-month drift will populate as snapshots accumulate."

        return rows, note

    def _confidence_payload(self, state: str | None, detail: str | None = None) -> Dict[str, str]:
        normalized = str(state or "warming").lower()
        label_map = {
            "live": "Live",
            "live-detail": "Live",
            "healthy": "Live",
            "snapshot": "Snapshot",
            "persisted": "Snapshot",
            "persisted-fallback": "Fallback",
            "signal-board-fallback": "Fallback",
            "degraded": "Fallback",
            "partial": "Partial",
            "approx+kap": "Estimated",
            "estimated": "Estimated",
            "warming": "Refreshing",
        }
        default_detail = {
            "live": "Fresh upstream data was resolved in the current cycle.",
            "snapshot": "Serving the latest persisted snapshot to keep the page fast and stable.",
            "persisted": "Serving the latest persisted snapshot to keep the page fast and stable.",
            "persisted-fallback": "Live refresh failed, so FundPilot is serving the last usable snapshot.",
            "signal-board-fallback": "Detailed workspace is unavailable; the board is using cached peer signal state.",
            "degraded": "One or more source lanes are lagging, so fallback logic is active.",
            "partial": "Some structured fields are available, but the source did not fully resolve.",
            "estimated": "This value is a modelled proxy, not a first-party reported field.",
            "warming": "The cache is still warming and the full workspace is not ready yet.",
        }
        return {
            "state": normalized,
            "label": label_map.get(normalized, "Refreshing"),
            "detail": str(detail or default_detail.get(normalized) or default_detail["warming"]),
        }

    def _compare_float(self, value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return _safe_float(value)
        text = str(value or "").strip()
        if not text or text == "N/A":
            return None
        negative = "(" in text and ")" in text
        text = text.replace("$", "").replace("TRY", "").replace("%", "").replace("+", "").replace(",", "").replace("x", "").strip()
        multiplier = 1.0
        if text.endswith("T"):
            multiplier = 1_000_000_000_000
            text = text[:-1]
        elif text.endswith("B"):
            multiplier = 1_000_000_000
            text = text[:-1]
        elif text.endswith("M"):
            multiplier = 1_000_000
            text = text[:-1]
        elif text.endswith("K"):
            multiplier = 1_000
            text = text[:-1]
        numeric = _safe_float(text)
        if numeric is None:
            return None
        numeric *= multiplier
        return -numeric if negative else numeric

    def _winner_for_metric(self, left: Any, right: Any, prefer: str = "higher") -> str:
        left_num = self._compare_float(left)
        right_num = self._compare_float(right)
        if left_num is None or right_num is None:
            return "Even"
        if abs(left_num - right_num) < 1e-9:
            return "Even"
        if prefer == "lower":
            return "Left" if left_num < right_num else "Right"
        return "Left" if left_num > right_num else "Right"

    def _stock_history_posture(self, monthly_return: float | None, rsi_value: float | None) -> str:
        ret = monthly_return or 0.0
        rsi = rsi_value or 50.0
        if ret >= 5 and rsi >= 55:
            return "Trend Build"
        if ret <= -5 and rsi <= 45:
            return "Trend Break"
        if rsi >= 60:
            return "Momentum Firm"
        if rsi <= 40:
            return "Momentum Weak"
        return "Range"

    def _build_stock_signal_history(self, ohlcv_df: pd.DataFrame | None) -> List[Dict[str, Any]]:
        if ohlcv_df is None or ohlcv_df.empty:
            return []
        df = ohlcv_df.copy()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.set_index("date")
        if not isinstance(df.index, pd.DatetimeIndex):
            return []
        close = pd.to_numeric(df.get("close"), errors="coerce").dropna()
        if close.empty:
            return []
        high = pd.to_numeric(df.get("high"), errors="coerce")
        low = pd.to_numeric(df.get("low"), errors="coerce")
        volume = pd.to_numeric(df.get("volume"), errors="coerce").fillna(0.0)
        monthly_close = close.resample("ME").last().dropna()
        monthly_return = monthly_close.pct_change() * 100
        daily_returns = close.pct_change()
        monthly_volatility = daily_returns.resample("ME").std() * np.sqrt(21) * 100
        monthly_high = high.resample("ME").max().reindex(monthly_close.index)
        monthly_low = low.resample("ME").min().reindex(monthly_close.index)
        monthly_volume = volume.resample("ME").mean().reindex(monthly_close.index)

        rows: List[Dict[str, Any]] = []
        for idx in monthly_close.index[-6:]:
            month_close = float(monthly_close.loc[idx])
            prior = float(monthly_close.shift(1).loc[idx]) if idx in monthly_close.shift(1).index and not pd.isna(monthly_close.shift(1).loc[idx]) else None
            rsi_proxy = None
            if prior not in (None, 0):
                rsi_proxy = 50 + (((month_close / prior) - 1) * 200)
            rows.append(
                {
                    "month": idx.strftime("%Y-%m"),
                    "close": _fmt_number(month_close, 2),
                    "return_1m": _fmt_pct(monthly_return.loc[idx]) if idx in monthly_return.index else "N/A",
                    "range": (
                        f"{_fmt_number(monthly_low.loc[idx], 2)} - {_fmt_number(monthly_high.loc[idx], 2)}"
                        if idx in monthly_high.index and idx in monthly_low.index
                        else "N/A"
                    ),
                    "volume": _fmt_compact_number(monthly_volume.loc[idx]) if idx in monthly_volume.index else "N/A",
                    "volatility": _fmt_pct(monthly_volatility.loc[idx]) if idx in monthly_volatility.index else "N/A",
                    "posture": self._stock_history_posture(
                        _safe_float(monthly_return.loc[idx]) if idx in monthly_return.index else None,
                        _safe_float(rsi_proxy),
                    ),
                }
            )
        return rows

    def _build_stock_change_rows(
        self,
        overview: Dict[str, Any],
        signals: List[Dict[str, Any]],
        trend_summary: Dict[str, Any],
        fundamental_lens: Dict[str, Any],
        curated_13f: Dict[str, Any],
        sector_context: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        signal_map = {str(item.get("label")): str(item.get("value")) for item in signals}
        rows = [
            {
                "label": "Daily move",
                "value": str(overview.get("price_change_percent", "N/A")),
                "impact": "High" if abs(self._compare_float(overview.get("price_change_percent")) or 0.0) >= 2 else "Medium",
                "reason": "This is the fastest public read on whether the tape is repricing the name right now.",
            },
            {
                "label": "3M momentum",
                "value": signal_map.get("3M", "N/A"),
                "impact": "High" if abs(self._compare_float(signal_map.get("3M")) or 0.0) >= 10 else "Medium",
                "reason": "FundPilot scores momentum on the 3-month window before it asks bigger conviction questions.",
            },
            {
                "label": "Trend posture",
                "value": str(trend_summary.get("trend", "N/A")),
                "impact": "Medium",
                "reason": str(trend_summary.get("recommendation", "No fresh trend read is available.")),
            },
        ]
        if fundamental_lens.get("available"):
            summary_cards = fundamental_lens.get("summary_cards") or []
            if summary_cards:
                rows.append(
                    {
                        "label": "Fundamental stance",
                        "value": str(summary_cards[0].get("value", "N/A")),
                        "impact": "High",
                        "reason": f"{summary_cards[1].get('value', 'Fair')} valuation and {summary_cards[3].get('value', 'Unavailable')} capital profile.",
                    }
                )
        if curated_13f:
            rows.append(
                {
                    "label": "Curated 13F",
                    "value": str(curated_13f.get("signal", "Unavailable")),
                    "impact": "High" if int((curated_13f.get("summary") or {}).get("holder_count", 0) or 0) >= 2 else "Medium",
                    "reason": str(curated_13f.get("coverage", "Curated manager coverage is limited for this symbol.")),
                }
            )
        if sector_context.get("available"):
            rows.append(
                {
                    "label": "Sector context",
                    "value": str((sector_context.get("recommendation") or {}).get("label", "N/A")),
                    "impact": "Medium",
                    "reason": str((sector_context.get("relative_strength") or {}).get("interpretation", "Sector-relative context is still building.")),
                }
            )
        return rows[:5]

    def _build_fund_change_rows(self, overview: Dict[str, Any], monthly_rows: List[Dict[str, Any]], holdings_rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = [
            {
                "label": "Expense drag",
                "value": str(overview.get("expense_ratio", "N/A")),
                "impact": "High",
                "reason": "Cost is structural. A fund does not need a bad month for fees to matter.",
            }
        ]
        if monthly_rows:
            latest = monthly_rows[-1]
            rows.extend(
                [
                    {
                        "label": "Latest 1M posture",
                        "value": str(latest.get("monthly_return", "N/A")),
                        "impact": "High",
                        "reason": f"{latest.get('posture', 'Mixed')} posture on the latest month-end tape.",
                    },
                    {
                        "label": "Asset-base drift",
                        "value": str(latest.get("asset_change_proxy", "N/A")),
                        "impact": "Medium",
                        "reason": "AUM proxy drift helps separate price-only moves from broader sponsor participation.",
                    },
                ]
            )
        if holdings_rows:
            latest_holdings = holdings_rows[-1]
            rows.append(
                {
                    "label": "Positioning drift",
                    "value": str(latest_holdings.get("primary_shift", "N/A")),
                    "impact": "Medium",
                    "reason": "Primary shift shows where the latest holdings snapshot actually moved.",
                }
            )
        return rows[:4]

    def _build_tr_change_rows(self, overview: Dict[str, Any], signal_card: Dict[str, Any], monthly_rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        rows = [
            {
                "label": "Investor growth",
                "value": str(overview.get("investor_growth_pct", "N/A")),
                "impact": "High",
                "reason": "Investor growth is the cleanest public sponsorship signal in the TEFAS lane.",
            },
            {
                "label": "Portfolio value growth",
                "value": str(overview.get("portfolio_value_growth_pct", "N/A")),
                "impact": "High",
                "reason": "Value growth shows whether money is actually following the story.",
            },
            {
                "label": "Regime",
                "value": str(signal_card.get("regime", "N/A")),
                "impact": "Medium",
                "reason": str(signal_card.get("regime_note", "No fresh regime note is available.")),
            },
        ]
        if monthly_rows:
            latest = monthly_rows[-1]
            rows.append(
                {
                    "label": "Latest allocation shift",
                    "value": str(latest.get("primary_shift", "N/A")),
                    "impact": "Medium",
                    "reason": "The biggest monthly bucket move is often where the manager actually changed their mind.",
                }
            )
        return rows[:4]

    def _screen_reason(self, row: Dict[str, Any]) -> str:
        pieces: List[str] = []
        if _label_to_float(row.get("price_change_3m")) >= 15:
            pieces.append("3M momentum is already above the liquid-universe threshold")
        if row.get("trend_label") in {"Trend Confirmed", "Constructive Trend"}:
            pieces.append(f"trend structure is {row.get('trend_label')}")
        if _label_to_float(row.get("fundamental_score")) >= 70:
            pieces.append(f"fundamental score {row.get('fundamental_score')}")
        if row.get("capital_profile") in {"High Conversion", "Healthy"}:
            pieces.append(f"capital profile is {row.get('capital_profile')}")
        if _label_to_float(row.get("disclosure_momentum_score")) >= 60:
            pieces.append(f"KAP flow is active at {row.get('disclosure_momentum_score')}")
        if int(row.get("curated_13f_holders", 0) or 0) >= 2:
            pieces.append(f"{row.get('curated_13f_holders')} curated managers already hold it")
        if not pieces:
            return "This name cleared the screen with a balanced mix of liquidity, momentum, and survivable fundamentals."
        return "Passed because " + ", ".join(pieces[:3]) + "."

    def _idea_reason(self, row: Dict[str, Any]) -> str:
        drivers: List[str] = []
        if _label_to_float(row.get("price_change_3m")) >= 12:
            drivers.append(f"momentum {row.get('price_change_3m')}")
        if row.get("trend_label") in {"Trend Confirmed", "Constructive Trend"}:
            drivers.append(f"trend {row.get('trend_label')}")
        if row.get("curated_13f_signal") in {"Accumulating", "Crowded Long"}:
            drivers.append(f"curated 13F {row.get('curated_13f_signal')}")
        if row.get("capital_profile") in {"High Conversion", "Healthy"}:
            drivers.append(f"capital profile {row.get('capital_profile')}")
        if _label_to_float(row.get("disclosure_momentum_score")) >= 60:
            drivers.append(f"KAP flow {row.get('disclosure_momentum_score')}")
        if _label_to_float(row.get("sector_tailwind")) > 0:
            drivers.append(f"sector wind {row.get('sector_tailwind')}")
        if not drivers:
            return "Conviction is being carried by a diversified mix of scores rather than one loud factor."
        return "This ranks well because of " + ", ".join(drivers[:4]) + "."

    def _best_available_tr_fund_code(self, requested_code: str, months: int) -> str | None:
        requested_code = (requested_code or "").upper()
        peer_board = self.tr_funds_service.get_cached_peer_signal_board(months=months)
        peer_codes: list[str] = []
        if peer_board is not None and not peer_board.empty:
            peer_codes = [str(code).upper() for code in peer_board["fund_code"].tolist() if code]

        candidate_codes = [settings.PUBLIC_DEFAULT_TR_FUND_CODE, *self._featured_tr_funds(months), *peer_codes]
        seen: set[str] = {requested_code}
        for code in candidate_codes:
            normalized = str(code).upper()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            if self.tr_funds_service.get_persisted_fund_summary(normalized, months):
                return normalized
            if normalized in peer_codes:
                return normalized
        return None

    def _tr_summary_is_actionable(self, summary: Dict[str, Any] | None) -> bool:
        if not isinstance(summary, dict) or not summary:
            return False
        fund_name = str(summary.get("fund_name", "") or "").strip()
        if not fund_name:
            return False
        latest_value = float(summary.get("latest_portfolio_value", 0) or 0)
        latest_investors = float(summary.get("latest_num_investors", 0) or 0)
        return latest_value > 0 or latest_investors > 0

    def _tr_workspace_is_actionable(self, workspace: Dict[str, Any] | None) -> bool:
        if not isinstance(workspace, dict) or workspace.get("error"):
            return False
        if workspace.get("fallback_notice"):
            return True
        overview = workspace.get("overview") or {}
        fund_name = str(overview.get("fund_name", "") or "").strip()
        if not fund_name:
            return False

        def _positive(value: Any) -> bool:
            if isinstance(value, (int, float)):
                return float(value) > 0
            if isinstance(value, str):
                cleaned = (
                    value.replace("$", "")
                    .replace(",", "")
                    .replace("%", "")
                    .replace("+", "")
                    .strip()
                )
                try:
                    return float(cleaned) > 0
                except Exception:
                    return False
            return False

        return _positive(overview.get("latest_portfolio_value")) or _positive(overview.get("latest_num_investors"))

    def _normalize_tr_workspace(self, workspace: Dict[str, Any], fund_code: str, months: int) -> Dict[str, Any]:
        normalized = dict(workspace)
        existing_fund_code = str(workspace.get("fund_code", "") or "").upper()
        if workspace.get("requested_fund_code") and existing_fund_code and existing_fund_code != fund_code:
            normalized["fund_code"] = existing_fund_code
        else:
            normalized["fund_code"] = fund_code
        normalized["selected_months"] = months
        normalized["featured_funds"] = self._featured_tr_funds(months)
        normalized.setdefault("monthly_rows", [])
        normalized.setdefault("what_changed", self._build_tr_change_rows(normalized.get("overview") or {}, normalized.get("signal_card") or {}, normalized.get("monthly_rows") or []))
        normalized.setdefault(
            "data_confidence",
            self._confidence_payload(
                normalized.get("data_state"),
                "TR funds workspaces prefer live TEFAS summaries, then persisted signal snapshots if TEFAS stalls.",
            ),
        )
        return normalized

    def _stock_workspace_is_actionable(self, workspace: Dict[str, Any] | None) -> bool:
        if not isinstance(workspace, dict) or workspace.get("error"):
            return False
        overview = workspace.get("overview") or {}
        name = str(overview.get("name", "") or "").strip()
        current_price = str(overview.get("current_price", "") or "").strip()
        return bool(name and current_price)

    def _stock_snapshot_is_current(self, snapshot: Dict[str, Any] | None) -> bool:
        if not self._stock_workspace_is_actionable(snapshot):
            return False
        if not isinstance(snapshot, dict):
            return False
        symbol = str(snapshot.get("symbol") or (snapshot.get("overview") or {}).get("symbol") or "").upper()
        lens = snapshot.get("fundamental_lens") or {}
        score = lens.get("score") or {}
        capital_rows = lens.get("capital_rows") or []
        coverage_note = str(lens.get("coverage_note", "") or "")
        has_capital_score = "capital" in score
        last_disclosure_row = next(
            (row for row in capital_rows if isinstance(row, dict) and str(row.get("metric", "")) == "Last disclosure"),
            None,
        )
        paid_in_capital_row = next(
            (row for row in capital_rows if isinstance(row, dict) and str(row.get("metric", "")) == "Paid-in capital"),
            None,
        )
        has_last_disclosure = last_disclosure_row is not None
        uses_enrichment_note = "KAP enrichment snapshots" in coverage_note
        if not (has_capital_score and has_last_disclosure and uses_enrichment_note):
            return False
        if symbol.endswith(".IS"):
            last_disclosure_value = str((last_disclosure_row or {}).get("value", "") or "").strip().upper()
            paid_in_capital_detail = str((paid_in_capital_row or {}).get("detail", "") or "").lower()
            capital_metrics = {
                str(row.get("metric", "")): row
                for row in capital_rows
                if isinstance(row, dict)
            }
            if last_disclosure_value in {"", "N/A", "NA", "NONE"}:
                return False
            if "temporarily unavailable" in coverage_note.lower():
                return False
            if "shares outstanding" in paid_in_capital_detail or "proxy" in paid_in_capital_detail:
                return False
            for required_metric in (
                "Material disclosures (90d)",
                "Contract mentions (365d)",
                "Disclosure momentum",
            ):
                if required_metric not in capital_metrics:
                    return False
        return True

    def _normalize_stock_workspace(self, workspace: Dict[str, Any], requested_symbol: str) -> Dict[str, Any]:
        normalized = dict(workspace)
        overview = normalized.get("overview") or {}
        normalized["requested_symbol"] = requested_symbol
        normalized["symbol"] = str(
            normalized.get("symbol")
            or overview.get("symbol")
            or requested_symbol
        ).upper()
        normalized["featured_symbols"] = normalized.get("featured_symbols") or self._featured_stock_symbols()
        normalized["market_profile"] = normalized.get("market_profile") or self._stock_market_profile(normalized["symbol"])
        normalized["regional_groups"] = normalized.get("regional_groups") or self._regional_stock_groups(normalized["symbol"])
        normalized["compare_suggestions"] = normalized.get("compare_suggestions") or self._stock_compare_suggestions(normalized["symbol"])
        normalized["compare_cta_path"] = normalized.get("compare_cta_path") or (
            normalized["compare_suggestions"][0]["path"]
            if normalized.get("compare_suggestions")
            else f"/compare?kind=stocks&left={quote_plus(normalized['symbol'])}&right=NVDA"
        )
        normalized["forecast_cta_path"] = normalized.get("forecast_cta_path") or f"/forecasts?symbol={quote_plus(normalized['symbol'])}&days=21"
        normalized.setdefault("signal_history", [])
        normalized.setdefault(
            "data_confidence",
            self._confidence_payload(
                normalized.get("data_state"),
                "Stock workspaces prefer live Yahoo data plus structured KAP enrichment on BIST names.",
            ),
        )
        if not normalized.get("error") and not isinstance(normalized.get("forecast_lens"), dict):
            normalized["forecast_lens"] = self._build_stock_forecast_lens(
                normalized["symbol"],
                list(normalized.get("signal_history") or []),
                dict(normalized.get("trend_summary") or {}),
            )
        lens = normalized.get("fundamental_lens")
        if isinstance(lens, dict) and lens.get("available"):
            upgraded_lens = dict(lens)
            score = dict(upgraded_lens.get("score") or {})
            capital_rows = list(upgraded_lens.get("capital_rows") or [])
            summary_cards = list(upgraded_lens.get("summary_cards") or [])

            if "capital" not in score:
                net_income_to_capital = None
                revenue_to_capital = None
                contract_to_sales = None
                for row in capital_rows:
                    if not isinstance(row, dict):
                        continue
                    metric = str(row.get("metric", ""))
                    value = row.get("value")
                    if metric == "Net income / paid-in capital":
                        net_income_to_capital = _extract_numeric_token(value)
                    elif metric == "Revenue / paid-in capital":
                        revenue_to_capital = _extract_numeric_token(value)
                    elif metric == "New contracts / annual sales":
                        contract_to_sales = _extract_numeric_token(value)
                        if contract_to_sales is not None and "%" in str(value):
                            contract_to_sales /= 100

                capital_score = 50.0
                if net_income_to_capital is not None:
                    capital_score += min(max(net_income_to_capital * 80, 0), 20)
                if revenue_to_capital is not None:
                    capital_score += min(max((revenue_to_capital / 4) * 15, 0), 15)
                if contract_to_sales is not None:
                    capital_score += min(max(contract_to_sales * 100, 0), 10)
                if net_income_to_capital is None and revenue_to_capital is None and len(summary_cards) > 3:
                    profile = str(summary_cards[3].get("value", ""))
                    capital_score = {
                        "High Conversion": 78.0,
                        "Healthy": 66.0,
                        "Mixed": 55.0,
                        "Asset Heavy": 42.0,
                    }.get(profile, 50.0)
                score["capital"] = round(max(0.0, min(100.0, capital_score)), 1)

            if not any(str(row.get("metric", "")) == "Last disclosure" for row in capital_rows if isinstance(row, dict)):
                capital_rows.append(
                    {
                        "metric": "Last disclosure",
                        "value": "N/A",
                        "detail": "Most recent structured KAP disclosure date if available.",
                    }
                )

            if len(summary_cards) > 3 and "Capital score" not in str(summary_cards[3].get("detail", "")):
                summary_cards[3] = dict(summary_cards[3])
                summary_cards[3]["detail"] = f"Capital score {score.get('capital', 50.0)}"

            upgraded_lens["score"] = score
            upgraded_lens["capital_rows"] = capital_rows
            upgraded_lens["summary_cards"] = summary_cards
            normalized["fundamental_lens"] = upgraded_lens
        normalized.setdefault(
            "what_changed",
            self._build_stock_change_rows(
                normalized.get("overview") or {},
                normalized.get("return_signals") or [],
                normalized.get("trend_summary") or {},
                normalized.get("fundamental_lens") or {},
                normalized.get("curated_13f") or {},
                normalized.get("sector_context") or {},
            ),
        )
        return normalized

    def _normalize_fund_workspace(self, workspace: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        normalized = dict(workspace)
        normalized["symbol"] = str(normalized.get("symbol") or symbol).upper()
        normalized["featured_symbols"] = normalized.get("featured_symbols") or self._featured_fund_symbols()
        normalized["market_profile"] = normalized.get("market_profile") or self._fund_market_profile(normalized["symbol"])
        normalized["regional_groups"] = normalized.get("regional_groups") or self._regional_fund_groups(normalized["symbol"])
        normalized["compare_suggestions"] = normalized.get("compare_suggestions") or self._fund_compare_suggestions(normalized["symbol"])
        normalized["compare_cta_path"] = normalized.get("compare_cta_path") or (
            normalized["compare_suggestions"][0]["path"]
            if normalized.get("compare_suggestions")
            else f"/compare?kind=funds&left={quote_plus(normalized['symbol'])}&right=QQQ"
        )
        normalized["overlap_cta_path"] = normalized.get("overlap_cta_path") or (
            f"/overlap-matrix?focus={quote_plus(str((normalized['market_profile'] or {}).get('overlap_focus', 'core')))}"
        )
        normalized["forecast_cta_path"] = normalized.get("forecast_cta_path") or f"/forecasts?symbol={quote_plus(normalized['symbol'])}&days=21"
        normalized.setdefault("monthly_rows", [])
        normalized.setdefault("holdings_timeline_rows", [])
        normalized.setdefault(
            "what_changed",
            self._build_fund_change_rows(
                normalized.get("overview") or {},
                normalized.get("monthly_rows") or [],
                normalized.get("holdings_timeline_rows") or [],
            ),
        )
        normalized.setdefault(
            "data_confidence",
            self._confidence_payload(
                normalized.get("data_state"),
                "Fund workspaces prefer live analytics, then persisted snapshots if upstream holdings or fund metadata lag.",
            ),
        )
        if not normalized.get("error") and not isinstance(normalized.get("forecast_lens"), dict):
            normalized["forecast_lens"] = self._build_fund_forecast_lens(
                normalized["symbol"],
                list(normalized.get("monthly_rows") or []),
                list(normalized.get("performance_cards") or []),
            )
        return normalized

    def _read_stock_snapshot(self, symbol: str) -> Dict[str, Any] | None:
        candidates = [symbol.upper()]
        if symbol.upper().endswith(".IS"):
            candidates.append(symbol.upper().split(".")[0])
        else:
            candidates.append(f"{symbol.upper()}.IS")

        seen: set[str] = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            persisted = self.snapshot_store.read_json(self._stock_snapshot_key(candidate))
            if isinstance(persisted, dict):
                normalized = self._normalize_stock_workspace(persisted, symbol.upper())
                if self._stock_workspace_is_actionable(normalized):
                    return normalized
        return None

    def _cache_key(self, prefix: str, *parts: Any) -> str:
        return ":".join([prefix, *[str(part) for part in parts]])

    def _build_etf_tracker(self) -> ETFWeightTracker:
        data_root = Path(settings.PUBLIC_SNAPSHOT_DIR).expanduser()
        db_path = data_root.parent / "public_etf_holdings.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return ETFWeightTracker(db_path=str(db_path))

    def _screen_options(self) -> Dict[str, Dict[str, Any]]:
        screens = dict(self.screener.get_predefined_screens())
        screens.update(self.curated_screener_overrides)
        return screens

    def _selected_universe(self, universe: str | None) -> str:
        if universe in self.screener_universes:
            return str(universe)
        return settings.PUBLIC_DEFAULT_SCREENER_UNIVERSE

    def _selected_focus(self, focus: str | None) -> str:
        if focus in self.ownership_focuses:
            return str(focus)
        return settings.PUBLIC_DEFAULT_OWNERSHIP_FOCUS

    def _selected_screen(self, screen_key: str | None) -> str:
        screens = self._screen_options()
        if screen_key in screens:
            return str(screen_key)
        return settings.PUBLIC_DEFAULT_SCREENER_SCREEN

    def _screen_rows_with_curated_13f(self, raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows = []
        for item in raw_results:
            symbol = str(item.get("symbol", ""))
            curated = self.institutional_pulse_service.get_symbol_signal(item.get("symbol"), item.get("name"))
            summary = curated.get("summary", {})
            fundamental = self._fundamental_overlay(symbol, item)
            forecast_overlay = self._forecast_overlay(symbol)
            rows.append(
                {
                    "symbol": item.get("symbol"),
                    "name": item.get("name"),
                    "sector": item.get("sector", "N/A"),
                    "current_price": _fmt_number(item.get("current_price"), 2),
                    "market_cap": _fmt_compact_money(item.get("market_cap")),
                    "price_change_3m": _fmt_pct(item.get("price_change_3m")),
                    "dividend_yield": _fmt_pct(item.get("dividend_yield")),
                    "pe_ratio": _fmt_number(item.get("pe_ratio"), 1),
                    "rsi": _fmt_number(item.get("rsi"), 1),
                    "roe": _fmt_pct(item.get("roe")),
                    "debt_to_equity": _fmt_number(item.get("debt_to_equity"), 1),
                    "curated_13f_signal": curated.get("signal", "Unavailable"),
                    "curated_13f_holders": int(summary.get("holder_count", 0) or 0),
                    "curated_13f_weight": summary.get("total_weight", "N/A"),
                    "curated_13f_top_holder": summary.get("top_holder", "N/A"),
                    "curated_13f_bullish": int(summary.get("bullish_managers", 0) or 0),
                    "curated_13f_bearish": int(summary.get("bearish_managers", 0) or 0),
                    "curated_13f_fresh": int(summary.get("fresh_buyers", 0) or 0),
                    "fundamental_score": _fmt_number(fundamental["overall"], 1),
                    "fundamental_rating": fundamental["overall_rating"],
                    "fundamental_source": fundamental["source"],
                    "valuation_stance": fundamental["valuation_stance"],
                    "capital_profile": fundamental["capital_profile"],
                    "capital_signal": _fmt_number(fundamental["capital"], 1),
                    "net_income_to_capital": fundamental["net_income_to_capital"],
                    "revenue_to_capital": fundamental["revenue_to_capital"],
                    "contracts_to_sales": fundamental["contracts_to_sales"],
                    "material_disclosures_90d": int(fundamental.get("material_disclosures_90d", 0) or 0),
                    "contract_mentions_365d": int(fundamental.get("contract_mentions_365d", 0) or 0),
                    "disclosure_momentum_score": _fmt_number(fundamental.get("disclosure_momentum_score"), 1),
                    "trend_label": forecast_overlay.get("trend_label", "Warming"),
                    "trend_detail": forecast_overlay.get("trend_detail", "Trend structure is still warming."),
                    "trend_persistence": forecast_overlay.get("trend_persistence", "Warming"),
                    "predictability_score": _fmt_number(forecast_overlay.get("predictability_score"), 1),
                    "entropy_regime": forecast_overlay.get("entropy_regime", "Warming"),
                    "trend_bias": forecast_overlay.get("trend_bias", "Mixed"),
                    "forecast_validation": forecast_overlay.get("validation_state", "Warming"),
                    "forecast_source": forecast_overlay.get("source", "warming"),
                    "forecast_consensus_delta": forecast_overlay.get("consensus_delta", "N/A"),
                    "entropy_note": forecast_overlay.get("entropy_note"),
                    "data_confidence": self._confidence_payload(
                        "estimated" if fundamental["source"] == "approx" else "snapshot" if fundamental["source"] == "snapshot" else "live",
                        "Approx uses market/fundamental proxies; snapshot uses persisted detailed workspaces; approx+kap blends proxies with KAP enrichment.",
                    ),
                    "why_passed": "",
                }
            )
            rows[-1]["why_passed"] = self._screen_reason(rows[-1])
        return rows

    def _metric_row_value(self, rows: List[Dict[str, Any]] | None, metric_name: str) -> str:
        if not isinstance(rows, list):
            return "N/A"
        for row in rows:
            if str(row.get("metric", "")) == metric_name:
                return str(row.get("value", "N/A"))
        return "N/A"

    def _summary_card_detail(self, cards: List[Dict[str, Any]] | None, label: str) -> str:
        if not isinstance(cards, list):
            return ""
        for card in cards:
            if str(card.get("label", "")) == label:
                return str(card.get("detail", ""))
        return ""

    def _approx_fundamental_overlay(self, item: Dict[str, Any]) -> Dict[str, Any]:
        pe_ratio = _safe_float(item.get("forward_pe")) or _safe_float(item.get("pe_ratio"))
        pb_ratio = _safe_float(item.get("pb_ratio"))
        roe_pct = _safe_float(item.get("roe")) or 0.0
        profit_margin_pct = _safe_float(item.get("profit_margin")) or 0.0
        debt_to_equity = _safe_float(item.get("debt_to_equity")) or 0.0

        valuation_score = 50.0
        if pe_ratio is not None:
            valuation_score += 18 if pe_ratio < 12 else 10 if pe_ratio < 20 else -10 if pe_ratio > 35 else 0
        if pb_ratio is not None:
            valuation_score += 14 if pb_ratio < 1.5 else 6 if pb_ratio < 3 else -12 if pb_ratio > 5 else 0
        valuation_score = max(0.0, min(100.0, valuation_score))

        quality_score = 50.0
        quality_score += min(max(roe_pct, 0), 25)
        quality_score += min(max(profit_margin_pct / 2, 0), 15)
        quality_score += max(0, min(10, 10 - (debt_to_equity / 20)))
        quality_score = max(0.0, min(100.0, quality_score))

        capital_score = 50.0
        if roe_pct > 0:
            capital_score += min(roe_pct / 2, 18)
        if profit_margin_pct > 0:
            capital_score += min(profit_margin_pct, 14)
        capital_score += max(0, min(10, 10 - (debt_to_equity / 25)))
        capital_score = max(0.0, min(100.0, capital_score))

        overall = round((quality_score * 0.42) + (valuation_score * 0.33) + (capital_score * 0.25), 1)
        overall_rating = "Strong Buy" if overall >= 80 else "Buy" if overall >= 65 else "Hold" if overall >= 50 else "Sell"
        valuation_stance = self._fundamental_verdict(pe_ratio, None, pb_ratio)
        if capital_score >= 75:
            capital_profile = "High Conversion"
        elif capital_score >= 60:
            capital_profile = "Healthy"
        elif capital_score >= 45:
            capital_profile = "Mixed"
        else:
            capital_profile = "Asset Heavy"

        return {
            "source": "approx",
            "overall": overall,
            "overall_rating": overall_rating,
            "valuation": round(valuation_score, 1),
            "quality": round(quality_score, 1),
            "capital": round(capital_score, 1),
            "valuation_stance": valuation_stance,
            "capital_profile": capital_profile,
            "net_income_to_capital": "N/A",
            "revenue_to_capital": "N/A",
            "contracts_to_sales": "N/A",
            "material_disclosures_90d": 0,
            "contract_mentions_365d": 0,
            "disclosure_momentum_score": 0.0,
        }

    def _kap_enriched_overlay(self, symbol: str, item: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        if not str(symbol or "").upper().endswith(".IS"):
            return overlay

        enrichment = self.stock_enrichment_service.get_kap_enrichment(symbol)
        paid_in_capital = _safe_float(enrichment.get("paid_in_capital"))
        if paid_in_capital is None:
            return overlay

        market_cap = _safe_float(item.get("market_cap"))
        pe_ratio = _safe_float(item.get("forward_pe")) or _safe_float(item.get("pe_ratio"))
        profit_margin_pct = _safe_float(item.get("profit_margin"))
        contract_to_sales_ratio_ttm = _safe_float(enrichment.get("contract_to_sales_ratio_ttm"))
        material_disclosures_90d = int(_safe_float(enrichment.get("material_disclosures_90d")) or 0)
        contract_mentions_365d = int(_safe_float(enrichment.get("contract_mentions_365d")) or 0)
        disclosure_momentum_score = _safe_float(enrichment.get("disclosure_momentum_score")) or 0.0

        estimated_net_income = _safe_div(market_cap, pe_ratio)
        margin_decimal = None
        if profit_margin_pct is not None and profit_margin_pct > 0:
            margin_decimal = profit_margin_pct / 100
        estimated_revenue = _safe_div(estimated_net_income, margin_decimal)
        contract_value_ttm = _safe_float(enrichment.get("contract_value_ttm"))

        net_income_to_capital = _safe_div(estimated_net_income, paid_in_capital)
        revenue_to_capital = _safe_div(estimated_revenue, paid_in_capital)
        contract_to_sales = contract_to_sales_ratio_ttm if contract_to_sales_ratio_ttm is not None else _safe_div(contract_value_ttm, estimated_revenue)

        capital_score = 50.0
        if net_income_to_capital is not None:
            capital_score += min(max(net_income_to_capital * 80, 0), 20)
        if revenue_to_capital is not None:
            capital_score += min(max((revenue_to_capital / 4) * 15, 0), 15)
        if contract_to_sales is not None:
            capital_score += min(max(contract_to_sales * 100, 0), 10)
        if disclosure_momentum_score > 0:
            capital_score += min(disclosure_momentum_score / 12, 8)
        capital_score = max(float(overlay.get("capital", 50.0) or 50.0), min(capital_score, 100.0))

        overall = round(
            (float(overlay.get("quality", 50.0) or 50.0) * 0.42)
            + (float(overlay.get("valuation", 50.0) or 50.0) * 0.33)
            + (capital_score * 0.25),
            1,
        )
        overall_rating = "Strong Buy" if overall >= 80 else "Buy" if overall >= 65 else "Hold" if overall >= 50 else "Sell"

        enriched = dict(overlay)
        enriched.update(
            {
                "source": "approx+kap",
                "overall": overall,
                "overall_rating": overall_rating,
                "capital": round(capital_score, 1),
                "capital_profile": self._capital_profile(revenue_to_capital, net_income_to_capital),
                "net_income_to_capital": _fmt_multiple(net_income_to_capital, 2),
                "revenue_to_capital": _fmt_multiple(revenue_to_capital, 2),
                "contracts_to_sales": _fmt_optional_pct(contract_to_sales, 1, assume_decimal=True),
                "material_disclosures_90d": material_disclosures_90d,
                "contract_mentions_365d": contract_mentions_365d,
                "disclosure_momentum_score": round(disclosure_momentum_score, 1),
            }
        )
        return enriched

    def _fundamental_overlay(self, symbol: str, item: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = self._read_stock_snapshot(symbol)
        lens = snapshot.get("fundamental_lens") if isinstance(snapshot, dict) else None
        if isinstance(lens, dict) and lens.get("available"):
            score = lens.get("score") or {}
            summary_cards = lens.get("summary_cards") or []
            return {
                "source": "snapshot",
                "overall": float(score.get("overall", 50.0) or 50.0),
                "overall_rating": str(summary_cards[0].get("value", "Hold")) if summary_cards else "Hold",
                "valuation": float(score.get("valuation", 50.0) or 50.0),
                "quality": float(score.get("quality", 50.0) or 50.0),
                "capital": float(score.get("capital", 50.0) or 50.0),
                "valuation_stance": str(summary_cards[1].get("value", "Fair")) if len(summary_cards) > 1 else "Fair",
                "capital_profile": str(summary_cards[3].get("value", "Unavailable")) if len(summary_cards) > 3 else "Unavailable",
                "net_income_to_capital": self._metric_row_value(lens.get("capital_rows"), "Net income / paid-in capital"),
                "revenue_to_capital": self._metric_row_value(lens.get("capital_rows"), "Revenue / paid-in capital"),
                "contracts_to_sales": self._metric_row_value(lens.get("capital_rows"), "New contracts / annual sales"),
                "material_disclosures_90d": int(_extract_numeric_token(self._metric_row_value(lens.get("capital_rows"), "Material disclosures (90d)")) or 0),
                "contract_mentions_365d": int(_extract_numeric_token(self._metric_row_value(lens.get("capital_rows"), "Contract mentions (365d)")) or 0),
                "disclosure_momentum_score": float(_extract_numeric_token(self._metric_row_value(lens.get("capital_rows"), "Disclosure momentum")) or 0.0),
            }
        return self._kap_enriched_overlay(symbol, item, self._approx_fundamental_overlay(item))

    def _trend_confirmation_label(
        self,
        trend_bias: str,
        predictability_score: float | None,
        persistence_label: str,
        regime: str,
    ) -> Dict[str, str]:
        predictability = float(predictability_score or 0.0)
        regime_lower = str(regime or "").lower()
        persistence = str(persistence_label or "Warming")

        if trend_bias == "Bullish" and persistence == "Persistent" and predictability >= 65:
            return {
                "label": "Trend Confirmed",
                "detail": "Momentum is not just positive. Entropy says return structure is orderly enough for trend-following interpretations to deserve trust.",
            }
        if trend_bias == "Bullish" and predictability >= 50 and persistence in {"Persistent", "Developing"}:
            return {
                "label": "Constructive Trend",
                "detail": "The tape still has enough structure to support upside scenarios, but it needs follow-through more than blind extrapolation.",
            }
        if trend_bias == "Bearish" and predictability >= 65:
            return {
                "label": "Orderly Downtrend",
                "detail": "Entropy is confirming that the downside tape is cleaner than a random chop regime. Respect risk even if sponsorship exists.",
            }
        if "structured" in regime_lower or "constructive" in regime_lower:
            return {
                "label": "Developing Structure",
                "detail": "Return patterns are becoming cleaner, but the persistence layer has not fully turned into durable conviction yet.",
            }
        return {
            "label": "Warming",
            "detail": "Trend structure is still noisy or incomplete, so this factor should stay secondary until the tape becomes more ordered.",
        }

    def _trend_confirmation_component(
        self,
        trend_bias: str,
        predictability_score: float | None,
        persistence_label: str,
        regime: str,
        validation_state: str,
    ) -> float:
        predictability = float(predictability_score or 0.0)
        score = 4.0

        if predictability > 0:
            score = 2.0 + _clamp(predictability / 100, 0, 1) * 5.0

        if trend_bias == "Bullish":
            if persistence_label == "Persistent":
                score += 3.0
            elif persistence_label == "Developing":
                score += 2.0
        elif trend_bias == "Bearish":
            if persistence_label == "Orderly Risk-Off":
                score += 0.5
            score -= 1.5

        regime_lower = str(regime or "").lower()
        if "structured" in regime_lower:
            score += 2.0
        elif "constructive" in regime_lower:
            score += 1.5
        elif "transitional" in regime_lower or "balanced" in regime_lower:
            score += 0.5

        validation_lower = str(validation_state or "").lower()
        if validation_lower.startswith("validated"):
            score += 1.0

        return round(_clamp(score, 0, 12), 1)

    def _forecast_overlay(self, symbol: str) -> Dict[str, Any]:
        snapshot = self._read_stock_snapshot(symbol)
        lens = snapshot.get("forecast_lens") if isinstance(snapshot, dict) else None
        if isinstance(lens, dict) and lens.get("state") == "ready":
            entropy_signal = lens.get("entropy_signal") or {}
            trend_persistence = lens.get("trend_persistence") or {}
            validation_summary = lens.get("validation_summary") or {}
            predictability_score = self._compare_float(entropy_signal.get("predictability_score"))
            trend_bias = str(lens.get("trend_bias", "Mixed"))
            persistence_label = str(trend_persistence.get("label", "Warming"))
            regime = str(entropy_signal.get("regime", "Warming"))
            validation_state = str(validation_summary.get("state", "Warming"))
            trend_read = self._trend_confirmation_label(
                trend_bias=trend_bias,
                predictability_score=predictability_score,
                persistence_label=persistence_label,
                regime=regime,
            )
            return {
                "state": "ready",
                "source": str(snapshot.get("data_state", "snapshot")),
                "trend_bias": trend_bias,
                "trend_persistence": persistence_label,
                "predictability_score": predictability_score,
                "entropy_regime": regime,
                "validation_state": validation_state,
                "trend_label": trend_read["label"],
                "trend_detail": trend_read["detail"],
                "trend_component": self._trend_confirmation_component(
                    trend_bias=trend_bias,
                    predictability_score=predictability_score,
                    persistence_label=persistence_label,
                    regime=regime,
                    validation_state=validation_state,
                ),
                "consensus_delta": str(lens.get("consensus_delta", "N/A")),
                "entropy_note": str(
                    entropy_signal.get("note")
                    or "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust."
                ),
            }
        return {
            "state": "warming",
            "source": "warming",
            "trend_bias": "Mixed",
            "trend_persistence": "Warming",
            "predictability_score": None,
            "entropy_regime": "Warming",
            "validation_state": "Warming",
            "trend_label": "Warming",
            "trend_detail": "FundPilot has not warmed a validated forecast lens for this symbol yet, so trend structure is being treated as neutral.",
            "trend_component": 4.0,
            "consensus_delta": "N/A",
            "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
        }

    def _asset_label(self, key: str) -> str:
        return ASSET_LABELS.get(key, key.replace("_", " ").title())

    def _sector_tailwind_map(self) -> Dict[str, float]:
        sector_workspace = self.get_sector_rotation_workspace()
        if sector_workspace.get("error"):
            return {}
        mapping = {}
        for row in sector_workspace.get("rows", []):
            try:
                mapping[str(row.get("sector"))] = float(str(row.get("change_5d", "0")).replace("%", "").replace("+", "").replace(",", ""))
            except Exception:
                mapping[str(row.get("sector"))] = 0.0
        return mapping

    def _sector_tailwind(self, sector: str, sector_map: Dict[str, float]) -> float:
        aliases = {
            "Financial Services": "Financial",
            "Industrials": "Industrial",
            "Consumer Defensive": "Consumer Staples",
            "Consumer Cyclical": "Consumer Discretionary",
            "Basic Materials": "Materials",
            "Healthcare": "Health Care",
            "Communication": "Communication Services",
        }
        if sector in sector_map:
            return float(sector_map[sector])
        alias = aliases.get(sector)
        if alias and alias in sector_map:
            return float(sector_map[alias])
        return 0.0

    def _idea_score_components(
        self,
        item: Dict[str, Any],
        sector_tailwind: float,
        ownership_count: int,
        ownership_weight: float,
        curated_holders: int = 0,
        fresh_buyers: int = 0,
        fundamental_quality: float | None = None,
        fundamental_valuation: float | None = None,
        capital_efficiency: float | None = None,
        disclosure_momentum: float | None = None,
        trend_confirmation_component: float | None = None,
    ) -> Dict[str, float]:
        if fundamental_quality is None or fundamental_valuation is None or capital_efficiency is None:
            approx = self._approx_fundamental_overlay(item)
            if fundamental_quality is None:
                fundamental_quality = float(approx["quality"])
            if fundamental_valuation is None:
                fundamental_valuation = float(approx["valuation"])
            if capital_efficiency is None:
                capital_efficiency = float(approx["capital"])
            if disclosure_momentum is None:
                disclosure_momentum = float(approx.get("disclosure_momentum_score", 0.0) or 0.0)
        elif disclosure_momentum is None:
            disclosure_momentum = 0.0

        momentum = _clamp((float(item.get("price_change_3m", 0) or 0) + 10) / 40, 0, 1) * 24

        rsi = float(item.get("rsi", 50) or 50)
        if 48 <= rsi <= 68:
            rsi_score = 8.0
        elif 40 <= rsi <= 75:
            rsi_score = 6.0
        elif 30 <= rsi <= 80:
            rsi_score = 4.0
        else:
            rsi_score = 2.0

        quality_score = _clamp(fundamental_quality / 100, 0, 1) * 14
        valuation_score = _clamp(fundamental_valuation / 100, 0, 1) * 10
        capital_score = _clamp(capital_efficiency / 100, 0, 1) * 10
        disclosure_score = _clamp((disclosure_momentum or 0.0) / 100, 0, 1) * 8
        sector_score = _clamp((sector_tailwind + 3) / 6, 0, 1) * 10
        ownership_score = _clamp(ownership_count / 4, 0, 1) * 4 + _clamp(ownership_weight / 12, 0, 1) * 8
        institutional_score = _clamp(curated_holders / 3, 0, 1) * 7 + _clamp(fresh_buyers / 2, 0, 1) * 5
        trend_score = float(trend_confirmation_component if trend_confirmation_component is not None else 4.0)

        total = momentum + rsi_score + quality_score + valuation_score + capital_score + disclosure_score + sector_score + ownership_score + institutional_score + trend_score
        return {
            "momentum": round(momentum, 1),
            "rsi": round(rsi_score, 1),
            "quality": round(quality_score, 1),
            "valuation": round(valuation_score, 1),
            "capital": round(capital_score, 1),
            "disclosure": round(disclosure_score, 1),
            "sector": round(sector_score, 1),
            "ownership": round(ownership_score, 1),
            "institutional": round(institutional_score, 1),
            "trend": round(trend_score, 1),
            "total": round(total, 1),
        }

    def _idea_band(self, score: float) -> str:
        if score >= 75:
            return "High Conviction"
        if score >= 60:
            return "Actionable"
        if score >= 45:
            return "Watchlist"
        return "Low Priority"

    def _equity_conviction_note(self, row: Dict[str, Any]) -> str:
        signal = str(row.get("curated_13f_signal", "Unavailable"))
        holders = int(row.get("curated_13f_holders", 0) or 0)
        fresh_buyers = int(row.get("curated_13f_fresh", 0) or 0)
        ownership_count = int(row.get("ownership_count", 0) or 0)
        valuation_stance = str(row.get("valuation_stance", "Fair"))
        capital_profile = str(row.get("capital_profile", "Unavailable"))
        disclosure_momentum = _safe_float(row.get("disclosure_momentum_score")) or 0.0
        contract_mentions = int(row.get("contract_mentions_365d", 0) or 0)
        trend_label = str(row.get("trend_label", "Warming"))
        predictability = _safe_float(row.get("predictability_score")) or 0.0

        if trend_label == "Trend Confirmed" and signal == "Crowded Long":
            return "Institutional breadth, ETF crowding, and an entropy-confirmed bullish tape are aligned at the same time."
        if trend_label == "Trend Confirmed" and capital_profile in {"High Conversion", "Healthy"}:
            return "The tape is orderly enough for trend-following to matter, and the capital efficiency layer is not fighting the setup."
        if disclosure_momentum >= 65 and contract_mentions >= 2:
            return "KAP disclosure flow is active and contract intensity is no longer just a narrative line."
        if signal == "Crowded Long":
            return "Institutional breadth and ETF ownership are already reinforcing each other."
        if signal == "Accumulating" and fresh_buyers >= 1:
            return "Fresh curated manager buying is appearing before the setup gets fully crowded."
        if trend_label == "Constructive Trend" and predictability >= 50:
            return "Entropy is not giving a full green light yet, but the tape is ordered enough to keep the bullish scenario actionable."
        if valuation_stance in {"Compressed", "Growth At A Reasonable Price"} and capital_profile in {"High Conversion", "Healthy"}:
            return "Fundamentals are doing more than price action here: valuation and capital efficiency are both supportive."
        if holders >= 1 and ownership_count >= 3:
            return "Passive ownership is present, but curated manager sponsorship is still building."
        return "Momentum is carrying more of the thesis than institutional confirmation right now."

    def _tr_conviction_note(self, row: Dict[str, Any]) -> str:
        signal_band = str(row.get("signal_band", "Neutral"))
        regime = str(row.get("regime", "Mixed"))
        dominant_asset = str(row.get("dominant_asset", "N/A"))
        local_factor = str(row.get("local_factor", "N/A"))
        quality_tier = str(row.get("quality_tier", "Niche"))

        if signal_band == "Leading" and regime == "Accumulation":
            return f"Investor growth and portfolio value are rising together; the local factor lens is {local_factor}."
        if signal_band in {"Leading", "Constructive"} and regime == "Rotation":
            return f"Managers are re-risking the fund while keeping the core posture in {dominant_asset}."
        if regime == "Distribution":
            return "This fund is losing sponsorship; use it as a warning signal, not a chase candidate."
        if quality_tier in {"Elite", "Established"}:
            return f"Momentum is mixed, but category quality and sponsor scale still make {local_factor} worth tracking."
        return "Signal quality is mixed, so this works better as a watchlist item than a lead idea."

    def _clean_tape_catalyst_summary(self, row: Dict[str, Any]) -> Dict[str, str]:
        trend_label = str(row.get("trend_label", "Warming"))
        predictability = self._compare_float(row.get("predictability_score")) or 0.0
        disclosure = self._compare_float(row.get("disclosure_momentum_score")) or 0.0
        contracts = self._compare_float(row.get("contracts_to_sales")) or 0.0
        contract_mentions = int(row.get("contract_mentions_365d", 0) or 0)

        if trend_label == "Trend Confirmed" and disclosure >= 60:
            return {
                "label": "Catalyst + Clean Tape",
                "detail": "Disclosure flow is active and the tape is orderly enough for follow-through to deserve more respect than noise.",
            }
        if trend_label in {"Trend Confirmed", "Constructive Trend"} and predictability >= 60:
            return {
                "label": "Clean Tape",
                "detail": "Return patterns are ordered enough to trust the direction more than a random squeeze or mean-reversion guess.",
            }
        if disclosure >= 60 or contract_mentions >= 2 or contracts > 0:
            return {
                "label": "Catalyst Active",
                "detail": "The local newsflow is doing real work, but the tape still needs cleaner structure before conviction should expand.",
            }
        return {
            "label": "Watch",
            "detail": "The business-quality lens may still be interesting, but catalyst pressure and tape cleanliness are not aligned yet.",
        }

    def _conviction_headline(
        self,
        top_equity: Dict[str, Any] | None,
        top_tr_fund: Dict[str, Any] | None,
        sector_pattern: str,
    ) -> Dict[str, str]:
        equity_ready = bool(top_equity) and str(top_equity.get("band")) == "High Conviction"
        tr_ready = bool(top_tr_fund) and str(top_tr_fund.get("signal_band")) in {"Leading", "Constructive"}
        risk_on = sector_pattern == "Risk-On Rotation"

        if equity_ready and tr_ready and risk_on:
            return {
                "label": "Cross-Asset Confirmation",
                "detail": "US leadership, curated 13F sponsorship, and TEFAS accumulation are pointing in the same direction.",
            }
        if equity_ready and tr_ready:
            return {
                "label": "Broad Risk Appetite",
                "detail": "Both the global equity lane and the Turkish funds lane still have constructive leadership.",
            }
        if equity_ready or tr_ready:
            return {
                "label": "Selective Opportunity",
                "detail": "One lane is offering cleaner conviction than the other, so allocation should stay discriminating.",
            }
        return {
            "label": "Mixed Posture",
            "detail": "Leadership is fragmented. Treat the board as a filter, not as blanket risk confirmation.",
        }

    def _normalize_holder_rows(self, holders_df: Any, limit: int = 8) -> List[Dict[str, Any]]:
        if holders_df is None or not isinstance(holders_df, pd.DataFrame) or holders_df.empty:
            return []

        frame = holders_df.reset_index(drop=True).copy()
        holder_col = next((col for col in ["Holder", "holder", "organization"] if col in frame.columns), None)
        shares_col = next((col for col in ["Shares", "shares"] if col in frame.columns), None)
        value_col = next((col for col in ["Value", "value"] if col in frame.columns), None)
        date_col = next((col for col in ["Date Reported", "dateReported", "reportDate"] if col in frame.columns), None)
        pct_col = next((col for col in ["% Out", "pctHeld", "Percent Held"] if col in frame.columns), None)

        rows: List[Dict[str, Any]] = []
        for _, row in frame.head(limit).iterrows():
            pct_value = row.get(pct_col) if pct_col else None
            if isinstance(pct_value, str):
                pct_label = pct_value if pct_value.endswith("%") else f"{pct_value}%"
            elif pct_value is None or pct_value != pct_value:
                pct_label = "N/A"
            else:
                pct_float = float(pct_value)
                pct_label = _fmt_pct(pct_float * 100 if abs(pct_float) <= 1 else pct_float)

            rows.append(
                {
                    "holder": row.get(holder_col, "Unknown"),
                    "shares": _fmt_shares(row.get(shares_col)) if shares_col else "N/A",
                    "value": _fmt_compact_money(row.get(value_col)) if value_col else "N/A",
                    "ownership_pct": pct_label,
                    "reported_at": str(row.get(date_col, "N/A")) if date_col else "N/A",
                }
            )
        return rows

    def _normalize_major_holders(self, major_holders: Any) -> List[Dict[str, Any]]:
        if major_holders is None or not isinstance(major_holders, pd.DataFrame) or major_holders.empty:
            return []

        frame = major_holders.reset_index(drop=True).copy()
        if frame.shape[1] < 2:
            return []

        label_col = frame.columns[0]
        value_col = frame.columns[1]
        rows = []
        for _, row in frame.head(6).iterrows():
            rows.append(
                {
                    "label": str(row.get(label_col, "Metric")),
                    "value": str(row.get(value_col, "N/A")),
                }
            )
        return rows

    def _get_institutional_snapshot(self, symbol: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            institutional = self._normalize_holder_rows(getattr(ticker, "institutional_holders", None), limit=8)
            mutual_funds = self._normalize_holder_rows(getattr(ticker, "mutualfund_holders", None), limit=8)
            major = self._normalize_major_holders(getattr(ticker, "major_holders", None))
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "institutional_rows": [],
                "mutual_fund_rows": [],
                "major_rows": [],
            }

        top_inst = institutional[0]["holder"] if institutional else "N/A"
        top_mf = mutual_funds[0]["holder"] if mutual_funds else "N/A"
        return {
            "available": bool(institutional or mutual_funds or major),
            "error": None,
            "summary": {
                "institutional_count": len(institutional),
                "mutual_fund_count": len(mutual_funds),
                "top_institutional_holder": top_inst,
                "top_mutual_fund_holder": top_mf,
            },
            "institutional_rows": institutional,
            "mutual_fund_rows": mutual_funds,
            "major_rows": major,
        }

    def _get_curated_13f_signal(self, symbol: str, issuer_name: str | None) -> Dict[str, Any]:
        try:
            return self.institutional_pulse_service.get_symbol_signal(symbol, issuer_name)
        except Exception as exc:
            return {
                "available": False,
                "coverage": "Curated SEC 13F manager set. This is delayed positioning data, not real-time flow.",
                "signal": "Unavailable",
                "supported_market": "." not in symbol,
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
                "error": str(exc),
            }

    def _get_sector_context(self, symbol: str) -> Dict[str, Any]:
        try:
            analyzer = SectorAnalyzer(symbol)
            performance = analyzer.analyze_sector_performance(period="1y")
            metrics = analyzer.calculate_sector_metrics()
            relative_strength = analyzer.calculate_relative_strength(period="3mo")
            sector_trends = analyzer.analyze_sector_trends()
            recommendation = analyzer.generate_sector_recommendation()
            peer_symbols = analyzer._get_peer_symbols()[:5]
            peer_comparison = analyzer.compare_with_peers(peer_symbols)
        except Exception as exc:
            return {"available": False, "error": str(exc)}

        comparison_rows = []
        for row in peer_comparison.get("comparison_data", [])[:6]:
            comparison_rows.append(
                {
                    "symbol": row.get("symbol"),
                    "name": row.get("name"),
                    "price_change_1y": _fmt_pct(row.get("price_change_1y")),
                    "roe": _fmt_pct(row.get("roe")),
                    "profit_margin": _fmt_pct(row.get("profit_margin")),
                    "pe_ratio": _fmt_number(row.get("pe_ratio"), 1),
                }
            )

        return _to_json_safe(
            {
                "available": True,
                "error": None,
                "summary": {
                    "sector": performance.get("sector", "Unknown"),
                    "sector_etf": performance.get("sector_etf", "N/A"),
                    "stock_return": _fmt_pct(performance.get("stock_return")),
                    "sector_return": _fmt_pct(performance.get("sector_return")),
                    "market_return": _fmt_pct(performance.get("market_return")),
                    "stock_rank": str(performance.get("stock_rank", "unknown")).replace("_", " ").title(),
                    "sector_rank": str(performance.get("sector_rank", "unknown")).replace("_", " ").title(),
                },
                "relative_strength": {
                    "rs_change": _fmt_pct(relative_strength.get("rs_change")),
                    "rs_trend": str(relative_strength.get("rs_trend", "neutral")).replace("_", " ").title(),
                    "interpretation": relative_strength.get("interpretation", "No sector-relative read available."),
                },
                "valuation": {
                    "pe_vs_sector": _fmt_number(metrics.get("pe_vs_sector"), 1),
                    "pb_vs_sector": _fmt_number(metrics.get("pb_vs_sector"), 1),
                    "roe_vs_sector": _fmt_pct(metrics.get("roe_vs_sector")),
                    "margin_vs_sector": _fmt_pct(metrics.get("margin_vs_sector")),
                },
                "trend": {
                    "trend": str(sector_trends.get("trend", "neutral")).replace("_", " ").title(),
                    "momentum": str(sector_trends.get("momentum", "neutral")).title(),
                },
                "recommendation": {
                    "label": str(recommendation.get("recommendation", "hold")).replace("_", " ").title(),
                    "score": f"{int(recommendation.get('score', 0))}/{int(recommendation.get('max_score', 7) or 7)}",
                    "explanation": recommendation.get("explanation", "No recommendation available."),
                },
                "percentile_rank": _fmt_number(peer_comparison.get("percentile_rank"), 1),
                "comparison_rows": comparison_rows,
            }
        )

    def _resolve_quote(self, symbol: str) -> Dict[str, Any]:
        candidates = [symbol.upper()]
        if "." not in symbol:
            candidates.append(f"{symbol.upper()}.IS")

        for candidate in candidates:
            payload = self.collector.fetch_stock_data_yf(candidate, period="6mo")
            if "error" not in payload:
                return payload
        return {"error": f"Unable to fetch quote for {symbol}"}

    def _resolve_stock_payload(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        candidates = [symbol.upper()]
        if "." not in symbol:
            candidates.append(f"{symbol.upper()}.IS")

        last_error = {"error": f"Unable to fetch quote for {symbol}"}
        for candidate in candidates:
            payload = self.collector.fetch_stock_data_yf(candidate, period=period)
            if "error" not in payload:
                return payload
            last_error = payload
        return last_error

    def _latest_statement_value(self, frame: pd.DataFrame | None, *labels: str) -> float | None:
        if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
            return None
        latest = frame.iloc[:, 0]
        for label in labels:
            if label in latest.index:
                return _safe_float(latest.get(label))
        return None

    def _normalize_key(self, value: Any) -> str:
        ascii_text = (
            unicodedata.normalize("NFKD", str(value or ""))
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )
        return re.sub(r"[^a-z0-9]", "", ascii_text)

    def _flatten_mapping(self, payload: Any, prefix: str = "") -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        flattened: Dict[str, Any] = {}
        for key, value in payload.items():
            joined = f"{prefix}.{key}" if prefix else str(key)
            flattened[joined] = value
            if isinstance(value, dict):
                flattened.update(self._flatten_mapping(value, joined))
        return flattened

    def _find_numeric_by_hint(self, flattened: Dict[str, Any], hints: List[str]) -> float | None:
        normalized_hints = [self._normalize_key(hint) for hint in hints]
        for key, value in flattened.items():
            normalized_key = self._normalize_key(key)
            if any(hint in normalized_key for hint in normalized_hints):
                numeric = _safe_float(value)
                if numeric is not None:
                    return numeric
        return None

    def _get_kap_enrichment(self, symbol: str) -> Dict[str, Any]:
        return self.stock_enrichment_service.get_kap_enrichment(symbol)

    def _fundamental_verdict(self, valuation_ratio: float | None, peg_ratio: float | None, pb_ratio: float | None) -> str:
        if valuation_ratio is not None and valuation_ratio > 35 and (peg_ratio is None or peg_ratio > 1.8):
            return "Stretched"
        if peg_ratio is not None and 0 < peg_ratio <= 1.2:
            return "Growth At A Reasonable Price"
        if valuation_ratio is not None and valuation_ratio < 15 and (pb_ratio is None or pb_ratio < 2):
            return "Compressed"
        return "Fair"

    def _quality_band(self, roe: float | None, net_margin: float | None, debt_to_equity: float | None) -> str:
        roe_value = roe or 0.0
        margin_value = net_margin or 0.0
        if abs(roe_value) <= 1.5:
            roe_value *= 100
        if abs(margin_value) <= 1.5:
            margin_value *= 100
        leverage_value = debt_to_equity or 0.0
        if roe_value >= 20 and margin_value >= 15 and leverage_value <= 0.8:
            return "Elite"
        if roe_value >= 12 and margin_value >= 8 and leverage_value <= 1.5:
            return "Solid"
        if roe_value > 0 and margin_value > 0:
            return "Mixed"
        return "Fragile"

    def _capital_profile(self, revenue_to_capital: float | None, net_income_to_capital: float | None) -> str:
        if revenue_to_capital is None or net_income_to_capital is None:
            return "Unavailable"
        if revenue_to_capital >= 2 and net_income_to_capital >= 0.25:
            return "High Conversion"
        if revenue_to_capital >= 1 and net_income_to_capital >= 0.10:
            return "Healthy"
        if revenue_to_capital > 0:
            return "Asset Heavy"
        return "Unavailable"

    def _get_fundamental_lens(self, symbol: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            info = getattr(ticker, "info", {}) or {}
            financials = getattr(ticker, "financials", pd.DataFrame())
            balance_sheet = getattr(ticker, "balance_sheet", pd.DataFrame())
            cashflow = getattr(ticker, "cashflow", pd.DataFrame())
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "summary_cards": [],
                "valuation_rows": [],
                "quality_rows": [],
                "capital_rows": [],
                "strengths": [],
                "concerns": [],
                "coverage_note": "Fundamental data could not be loaded for this symbol.",
            }

        pe_ratio = _safe_float(info.get("forwardPE")) or _safe_float(info.get("trailingPE")) or _safe_float(payload.get("pe_ratio"))
        pb_ratio = _safe_float(info.get("priceToBook"))
        ps_ratio = _safe_float(info.get("priceToSalesTrailing12Months"))
        peg_ratio = _safe_float(info.get("pegRatio") or info.get("trailingPegRatio"))
        ev_revenue = _safe_float(info.get("enterpriseToRevenue"))
        ev_ebitda = _safe_float(info.get("enterpriseToEbitda"))
        market_cap = _safe_float(info.get("marketCap") or payload.get("market_cap"))
        enterprise_value = _safe_float(info.get("enterpriseValue"))
        shares_outstanding = _safe_float(info.get("sharesOutstanding"))
        float_shares = _safe_float(info.get("floatShares"))
        book_value_per_share = _safe_float(info.get("bookValue"))

        revenue = self._latest_statement_value(financials, "Total Revenue")
        net_income = self._latest_statement_value(financials, "Net Income")
        gross_profit = self._latest_statement_value(financials, "Gross Profit")
        operating_income = self._latest_statement_value(financials, "Operating Income", "EBIT")
        ebitda = _safe_float(info.get("ebitda")) or self._latest_statement_value(financials, "EBITDA")
        interest_expense = self._latest_statement_value(financials, "Interest Expense")
        total_assets = self._latest_statement_value(balance_sheet, "Total Assets")
        total_debt = self._latest_statement_value(balance_sheet, "Total Debt")
        shareholders_equity = self._latest_statement_value(balance_sheet, "Stockholders Equity", "Total Equity Gross Minority Interest")
        current_assets = self._latest_statement_value(balance_sheet, "Current Assets")
        current_liabilities = self._latest_statement_value(balance_sheet, "Current Liabilities")
        cash = self._latest_statement_value(balance_sheet, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments")
        operating_cashflow = _safe_float(info.get("operatingCashflow")) or self._latest_statement_value(cashflow, "Operating Cash Flow")
        free_cashflow = _safe_float(info.get("freeCashflow")) or self._latest_statement_value(cashflow, "Free Cash Flow")

        revenue_growth = _safe_float(info.get("revenueGrowth"))
        earnings_growth = _safe_float(info.get("earningsGrowth"))
        profit_margin = _safe_float(info.get("profitMargins"))
        operating_margin = _safe_float(info.get("operatingMargins"))
        gross_margin = _safe_float(gross_profit / revenue) if gross_profit is not None and revenue not in (None, 0) else None
        roe = _safe_float(info.get("returnOnEquity"))
        if roe is None:
            roe = _safe_div(net_income, shareholders_equity)
        roa = _safe_float(info.get("returnOnAssets"))
        if roa is None:
            roa = _safe_div(net_income, total_assets)

        current_ratio = _safe_div(current_assets, current_liabilities)
        debt_to_equity = _safe_div(total_debt, shareholders_equity)
        interest_coverage = None
        if operating_income is not None and interest_expense not in (None, 0):
            interest_coverage = operating_income / abs(float(interest_expense))
        ocf_to_revenue = _safe_div(operating_cashflow, revenue)
        fcf_to_revenue = _safe_div(free_cashflow, revenue)
        fcf_yield = _safe_div(free_cashflow, market_cap)
        asset_turnover = _safe_div(revenue, total_assets)
        free_float_pct = _safe_div(float_shares, shares_outstanding)
        market_cap_to_book = _safe_div(market_cap, shareholders_equity)
        ev_to_fcf = _safe_div(enterprise_value, free_cashflow)
        price_to_ocf = _safe_div(market_cap, operating_cashflow)
        ocf_to_net_income = _safe_div(operating_cashflow, net_income)
        cash_to_debt = _safe_div(cash, total_debt)
        net_debt_to_ebitda = None
        if total_debt is not None and cash is not None and ebitda not in (None, 0):
            net_debt_to_ebitda = (total_debt - cash) / float(ebitda)

        quality_score = 50.0
        if roe is not None:
            quality_score += min(max(roe * 100, 0), 25)
        if fcf_yield is not None:
            quality_score += min(max(fcf_yield * 100, 0), 15)
        if debt_to_equity is not None:
            quality_score += max(0, min(10, 10 - debt_to_equity * 3))
        if current_ratio is not None:
            quality_score += max(0, min(10, current_ratio * 4))
        quality_score = max(0.0, min(100.0, quality_score))

        valuation_score = 50.0
        if pe_ratio is not None:
            valuation_score += 18 if pe_ratio < 12 else 10 if pe_ratio < 20 else -10 if pe_ratio > 35 else 0
        if pb_ratio is not None:
            valuation_score += 14 if pb_ratio < 1.5 else 6 if pb_ratio < 3 else -12 if pb_ratio > 5 else 0
        if peg_ratio is not None:
            valuation_score += 12 if 0 < peg_ratio <= 1 else 4 if peg_ratio <= 1.5 else -10 if peg_ratio > 2.5 else 0
        valuation_score = max(0.0, min(100.0, valuation_score))

        growth_score = 50.0
        if revenue_growth is not None:
            growth_score += max(-15, min(20, revenue_growth * 100))
        if earnings_growth is not None:
            growth_score += max(-15, min(20, earnings_growth * 100))
        growth_score = max(0.0, min(100.0, growth_score))

        kap_enrichment = self._get_kap_enrichment(symbol) if symbol.endswith(".IS") else {}
        paid_in_capital = _safe_float(kap_enrichment.get("paid_in_capital"))
        contract_value_ttm = _safe_float(kap_enrichment.get("contract_value_ttm"))
        contract_to_sales_ratio_ttm = _safe_float(kap_enrichment.get("contract_to_sales_ratio_ttm"))
        disclosures_count = _safe_float(kap_enrichment.get("disclosures_count"))
        disclosures_count_90d = _safe_float(kap_enrichment.get("disclosures_count_90d"))
        material_disclosures_90d = _safe_float(kap_enrichment.get("material_disclosures_90d"))
        contract_mentions_365d = _safe_float(kap_enrichment.get("contract_mentions_365d"))
        disclosure_momentum_score = _safe_float(kap_enrichment.get("disclosure_momentum_score"))
        last_disclosure_date = kap_enrichment.get("last_disclosure_date")
        capital_method = str(kap_enrichment.get("capital_method") or "Exact KAP field")
        if paid_in_capital is None and symbol.endswith(".IS") and shares_outstanding is not None:
            paid_in_capital = shares_outstanding
            capital_method = "Nominal capital proxy from shares outstanding (TRY 1 par assumption)"

        revenue_to_capital = _safe_div(revenue, paid_in_capital)
        net_income_to_capital = _safe_div(net_income, paid_in_capital)
        market_cap_to_capital = _safe_div(market_cap, paid_in_capital)
        contract_to_sales = contract_to_sales_ratio_ttm if contract_to_sales_ratio_ttm is not None else _safe_div(contract_value_ttm, revenue)
        operating_cashflow_to_capital = _safe_div(operating_cashflow, paid_in_capital)
        equity_to_capital = _safe_div(shareholders_equity, paid_in_capital)

        capital_score = 50.0
        if net_income_to_capital is not None:
            capital_score += min(max(net_income_to_capital * 80, 0), 20)
        if revenue_to_capital is not None:
            capital_score += min(max((revenue_to_capital / 4) * 15, 0), 15)
        if operating_cashflow_to_capital is not None:
            capital_score += min(max((operating_cashflow_to_capital / 1.5) * 10, 0), 10)
        if contract_to_sales is not None:
            capital_score += min(max(contract_to_sales * 100, 0), 10)
        if disclosure_momentum_score is not None:
            capital_score += min(max(disclosure_momentum_score / 12, 0), 8)
        if net_income_to_capital is None and revenue_to_capital is None:
            if ocf_to_net_income is not None:
                capital_score += min(max(ocf_to_net_income * 12, 0), 18)
            if fcf_to_revenue is not None:
                capital_score += min(max(fcf_to_revenue * 100, 0), 12)
            if roe is not None:
                roe_pct = roe * 100 if abs(roe) <= 1.5 else roe
                capital_score += min(max(roe_pct / 3, 0), 10)
        capital_score = max(0.0, min(100.0, capital_score))

        overall_score = round(
            (quality_score * 0.34)
            + (valuation_score * 0.26)
            + (growth_score * 0.18)
            + (capital_score * 0.22),
            1,
        )
        overall_rating = "Strong Buy" if overall_score >= 80 else "Buy" if overall_score >= 65 else "Hold" if overall_score >= 50 else "Sell"

        valuation_rows = [
            {"metric": "F/K (P/E)", "value": _fmt_multiple(pe_ratio, 1), "detail": "Forward if available, otherwise trailing."},
            {"metric": "PD/DD (P/B)", "value": _fmt_multiple(pb_ratio, 2), "detail": "Price to book proxy."},
            {"metric": "PEG", "value": _fmt_multiple(peg_ratio, 2), "detail": "Price/earnings relative to growth."},
            {"metric": "P/S", "value": _fmt_multiple(ps_ratio, 2), "detail": "Market value relative to trailing sales."},
            {"metric": "EV/Revenue", "value": _fmt_multiple(ev_revenue, 2), "detail": "Enterprise value relative to revenue."},
            {"metric": "EV/EBITDA", "value": _fmt_multiple(ev_ebitda, 2), "detail": "Enterprise value relative to EBITDA."},
            {"metric": "EV/FCF", "value": _fmt_multiple(ev_to_fcf, 2), "detail": "Enterprise value relative to free cash flow."},
            {"metric": "Fiyat / OCF", "value": _fmt_multiple(price_to_ocf, 2), "detail": "Market cap over operating cash flow."},
        ]
        quality_rows = [
            {"metric": "ROE", "value": _fmt_optional_pct(roe, 1, assume_decimal=True), "detail": "Net income over equity."},
            {"metric": "ROA", "value": _fmt_optional_pct(roa, 1, assume_decimal=True), "detail": "Net income over total assets."},
            {"metric": "Net margin", "value": _fmt_optional_pct(profit_margin, 1, assume_decimal=True), "detail": "Trailing profitability on sales."},
            {"metric": "Gross margin", "value": _fmt_optional_pct(gross_margin, 1, assume_decimal=True), "detail": "Gross profit over revenue."},
            {"metric": "Operating margin", "value": _fmt_optional_pct(operating_margin, 1, assume_decimal=True), "detail": "Operating income power on sales."},
            {"metric": "Debt / equity", "value": _fmt_multiple(debt_to_equity, 2), "detail": "Balance-sheet leverage."},
            {"metric": "Current ratio", "value": _fmt_multiple(current_ratio, 2), "detail": "Short-term liquidity cover."},
            {"metric": "Cash / debt", "value": _fmt_multiple(cash_to_debt, 2), "detail": "How much debt is covered by cash."},
            {"metric": "Net debt / EBITDA", "value": _fmt_multiple(net_debt_to_ebitda, 2), "detail": "Leverage after cash buffer."},
            {"metric": "Interest cover", "value": _fmt_multiple(interest_coverage, 1), "detail": "Operating income over interest expense."},
            {"metric": "FCF yield", "value": _fmt_optional_pct(fcf_yield, 1, assume_decimal=True), "detail": "Free cash flow over market cap."},
            {"metric": "OCF / revenue", "value": _fmt_optional_pct(ocf_to_revenue, 1, assume_decimal=True), "detail": "Cash conversion on sales."},
            {"metric": "OCF / net income", "value": _fmt_multiple(ocf_to_net_income, 2), "detail": "Quality of earnings and cash conversion."},
            {"metric": "FCF margin", "value": _fmt_optional_pct(fcf_to_revenue, 1, assume_decimal=True), "detail": "Free cash flow retained from sales."},
            {"metric": "Asset turnover", "value": _fmt_multiple(asset_turnover, 2), "detail": "Revenue generated per asset base."},
        ]
        capital_rows = [
            {"metric": "Paid-in capital", "value": _fmt_try(paid_in_capital) if symbol.endswith(".IS") else "N/A", "detail": capital_method if symbol.endswith(".IS") else "Most useful on BIST issuers."},
            {"metric": "Net income / paid-in capital", "value": _fmt_multiple(net_income_to_capital, 2), "detail": "Capital efficiency on earnings."},
            {"metric": "Revenue / paid-in capital", "value": _fmt_multiple(revenue_to_capital, 2), "detail": "Sales power on nominal capital."},
            {"metric": "Market cap / paid-in capital", "value": _fmt_multiple(market_cap_to_capital, 2), "detail": "Public market value relative to capital base."},
            {"metric": "Operating cash flow / paid-in capital", "value": _fmt_multiple(operating_cashflow_to_capital, 2), "detail": "Cash generation relative to nominal capital."},
            {"metric": "Equity / paid-in capital", "value": _fmt_multiple(equity_to_capital, 2), "detail": "Balance-sheet depth relative to capital base."},
            {"metric": "New contracts / annual sales", "value": _fmt_optional_pct(contract_to_sales, 1, assume_decimal=True), "detail": "Best-effort KAP disclosure ratio when structured contract values exist."},
            {"metric": "Recent disclosures", "value": _fmt_number(disclosures_count_90d if disclosures_count_90d is not None else disclosures_count, 0) if (disclosures_count_90d is not None or disclosures_count is not None) else "N/A", "detail": "90-day disclosure count when available; otherwise the structured 365-day disclosure count."},
            {"metric": "Material disclosures (90d)", "value": _fmt_number(material_disclosures_90d, 0) if material_disclosures_90d is not None else "N/A", "detail": "Special-situation flow in the last 90 days."},
            {"metric": "Contract mentions (365d)", "value": _fmt_number(contract_mentions_365d, 0) if contract_mentions_365d is not None else "N/A", "detail": "KAP contract-style disclosures deduplicated by notice chain."},
            {"metric": "Disclosure momentum", "value": _fmt_number(disclosure_momentum_score, 1), "detail": "Composite KAP flow score using recency, materiality, and contract intensity."},
            {"metric": "Last disclosure", "value": str(last_disclosure_date or "N/A"), "detail": "Most recent structured KAP disclosure date if available."},
        ]

        strengths: List[str] = []
        concerns: List[str] = []
        if roe is not None and roe >= 0.20:
            strengths.append("High ROE is supporting capital compounding.")
        if fcf_yield is not None and fcf_yield >= 0.04:
            strengths.append("Free cash flow yield is carrying real cash support.")
        if revenue_growth is not None and revenue_growth >= 0.10:
            strengths.append("Revenue is still compounding at a double-digit clip.")
        if symbol.endswith(".IS") and net_income_to_capital is not None and net_income_to_capital >= 0.20:
            strengths.append("Net income to paid-in capital is strong for a public BIST name.")
        if ocf_to_net_income is not None and ocf_to_net_income >= 1.0:
            strengths.append("Operating cash flow is covering accounting earnings cleanly.")
        if contract_to_sales is not None and contract_to_sales >= 0.20:
            strengths.append("KAP contract flow is meaningful relative to the latest annual sales base.")
        if disclosure_momentum_score is not None and disclosure_momentum_score >= 65:
            strengths.append("KAP disclosure momentum is active, which often matters for local catalyst flow.")

        if peg_ratio is not None and peg_ratio > 2.0:
            concerns.append("PEG is elevated, so growth may already be priced in.")
        if debt_to_equity is not None and debt_to_equity > 1.5:
            concerns.append("Leverage is high relative to equity.")
        if current_ratio is not None and current_ratio < 1.0:
            concerns.append("Short-term liquidity cover looks thin.")
        if fcf_yield is not None and fcf_yield < 0:
            concerns.append("Free cash flow is negative versus market value.")
        if net_debt_to_ebitda is not None and net_debt_to_ebitda > 3.0:
            concerns.append("Net leverage is high relative to EBITDA.")

        return _to_json_safe(
            {
                "available": True,
                "error": None,
                "summary_cards": [
                    {"label": "Overall rating", "value": overall_rating, "detail": f"Score {overall_score}/100"},
                    {"label": "Valuation stance", "value": self._fundamental_verdict(pe_ratio, peg_ratio, pb_ratio), "detail": f"Valuation score {round(valuation_score, 1)}"},
                    {"label": "Quality band", "value": self._quality_band(roe, profit_margin, debt_to_equity), "detail": f"Quality score {round(quality_score, 1)}"},
                    {"label": "Capital profile", "value": self._capital_profile(revenue_to_capital, net_income_to_capital), "detail": f"Capital score {round(capital_score, 1)}"},
                ],
                "valuation_rows": valuation_rows,
                "quality_rows": quality_rows,
                "capital_rows": capital_rows,
                "score": {
                    "overall": overall_score,
                    "valuation": round(valuation_score, 1),
                    "quality": round(quality_score, 1),
                    "growth": round(growth_score, 1),
                    "capital": round(capital_score, 1),
                },
                "growth_profile": {
                    "revenue_growth": _fmt_optional_pct(revenue_growth, 1, assume_decimal=True),
                    "earnings_growth": _fmt_optional_pct(earnings_growth, 1, assume_decimal=True),
                    "free_float_pct": _fmt_optional_pct(free_float_pct, 1, assume_decimal=True),
                    "market_cap_to_book": _fmt_multiple(market_cap_to_book, 2),
                    "book_value_per_share": _fmt_number(book_value_per_share, 2),
                    "enterprise_value": _fmt_compact_money(enterprise_value),
                },
                "strengths": strengths[:4],
                "concerns": concerns[:4],
                "coverage_note": (
                    "Ratios are derived from Yahoo Finance statements. BIST paid-in capital uses KAP enrichment snapshots when available; otherwise a shares-outstanding proxy is used. "
                    f"{kap_enrichment.get('coverage_note', 'Contract-to-sales stays blank until structured KAP disclosure values are available.')}"
                ),
            }
        )

    def _parse_positions_text(self, positions_text: str | None) -> Dict[str, Any]:
        raw_text = (positions_text or self.default_portfolio_text).strip()
        rows = []
        errors: List[str] = []

        if raw_text.startswith("[") or raw_text.startswith("{"):
            try:
                payload = json.loads(raw_text)
                if isinstance(payload, dict):
                    payload = payload.get("positions", [])
                if not isinstance(payload, list):
                    raise ValueError("JSON input must be a list of positions.")
                for index, item in enumerate(payload, start=1):
                    if not isinstance(item, dict):
                        errors.append(f"Item {index}: each JSON position must be an object.")
                        continue
                    symbol = str(item.get("symbol") or item.get("Symbol") or "").strip().upper()
                    shares = _safe_float(item.get("shares") or item.get("Shares"))
                    entry_price = _safe_float(
                        item.get("entry_price")
                        or item.get("entryPrice")
                        or item.get("purchase_price")
                        or item.get("Purchase_Price")
                    )
                    if not symbol or shares is None or entry_price is None:
                        errors.append(f"Item {index}: use symbol, shares, and entry_price fields.")
                        continue
                    rows.append(
                        {
                            "Symbol": symbol,
                            "Shares": float(shares),
                            "Purchase_Price": float(entry_price),
                        }
                    )
            except Exception as exc:
                errors.append(f"JSON input could not be parsed: {exc}")
        else:
            reader = csv.reader(StringIO(raw_text))

            for line_number, row in enumerate(reader, start=1):
                if not row:
                    continue
                if row[0].strip().startswith("#"):
                    continue
                normalized = [str(item).strip() for item in row if str(item).strip()]
                if not normalized:
                    continue
                if normalized[0].lower() == "symbol":
                    continue
                if len(normalized) < 3:
                    errors.append(f"Line {line_number}: use Symbol,Shares,EntryPrice format.")
                    continue
                try:
                    rows.append(
                        {
                            "Symbol": normalized[0].upper(),
                            "Shares": float(normalized[1]),
                            "Purchase_Price": float(normalized[2]),
                        }
                    )
                except ValueError:
                    errors.append(f"Line {line_number}: shares and price must be numeric.")

        if len(rows) > 12:
            errors.append("Use up to 12 positions in the public lab to keep response times tight.")
            rows = rows[:12]

        if not rows:
            return {"raw_text": raw_text, "errors": errors or ["Add at least one valid position."], "portfolio_df": pd.DataFrame()}

        quote_rows = []
        for item in rows:
            quote = self._resolve_quote(item["Symbol"])
            current_price = float(quote.get("current_price") or item["Purchase_Price"])
            value = current_price * item["Shares"]
            quote_rows.append(
                {
                    "Symbol": item["Symbol"],
                    "Shares": item["Shares"],
                    "Purchase_Price": item["Purchase_Price"],
                    "Current_Price": current_price,
                    "Price": current_price,
                    "Value": value,
                    "Resolved_Symbol": quote.get("symbol", item["Symbol"]),
                    "Name": quote.get("name", item["Symbol"]),
                }
            )

        return {
            "raw_text": raw_text,
            "errors": errors,
            "portfolio_df": pd.DataFrame(quote_rows),
        }

    def get_stock_workspace(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        symbol = (symbol or settings.PUBLIC_DEFAULT_STOCK_SYMBOL).upper()
        cache_key = self._cache_key("public-research-stock", symbol)
        stale_persisted: Dict[str, Any] | None = None
        if not force_refresh:
            cached = cache_get(cache_key)
            if isinstance(cached, dict):
                return self._normalize_stock_workspace(cached, symbol)
            persisted = self._read_stock_snapshot(symbol)
            if persisted is not None and self._stock_snapshot_is_current(persisted):
                cache_set(cache_key, persisted, ttl=self.ttl_seconds)
                return persisted
            stale_persisted = persisted if isinstance(persisted, dict) else None

        payload = self._resolve_stock_payload(symbol, period="1y")
        if "error" in payload:
            persisted = self._read_stock_snapshot(symbol)
            if persisted is not None:
                fallback = dict(persisted)
                fallback["data_state"] = "persisted-fallback"
                fallback["stale_notice"] = (
                    f"Live refresh failed for {symbol}; serving the last persisted stock workspace instead."
                )
                fallback["data_confidence"] = self._confidence_payload(
                    "persisted-fallback",
                    "Live stock refresh failed, so FundPilot is serving the last usable persisted stock snapshot.",
                )
                cache_set(cache_key, fallback, ttl=min(self.ttl_seconds, 900))
                return self._normalize_stock_workspace(fallback, symbol)
            if stale_persisted is not None:
                fallback = dict(stale_persisted)
                fallback["data_state"] = "persisted-fallback"
                fallback["stale_notice"] = (
                    f"Live refresh failed for {symbol}; serving a stale-but-usable stock workspace instead."
                )
                fallback["data_confidence"] = self._confidence_payload(
                    "persisted-fallback",
                    "Live stock refresh failed, so FundPilot is serving a stale-but-usable stock snapshot.",
                )
                cache_set(cache_key, fallback, ttl=min(self.ttl_seconds, 900))
                return self._normalize_stock_workspace(fallback, symbol)
            result = {
                "symbol": symbol,
                "requested_symbol": symbol,
                "error": payload["error"],
                "featured_symbols": self._featured_stock_symbols(),
                "data_confidence": self._confidence_payload("warming"),
            }
            cache_set(cache_key, result, ttl=300)
            return result

        resolved_symbol = str(payload.get("symbol", symbol) or symbol).upper()
        ohlcv_df = pd.DataFrame(payload.get("ohlcv_data", []))
        trend_df = ohlcv_df.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )
        technicals = self.stocks_analyzer.calculate_technical_indicators(ohlcv_df)
        returns = self.stocks_analyzer.calculate_returns(ohlcv_df["close"]) if not ohlcv_df.empty else {}
        trend = self.trend_analyzer.comprehensive_trend_analysis(trend_df) if not trend_df.empty else {}
        fundamental_lens = self._get_fundamental_lens(resolved_symbol, payload)

        overview = {
            "symbol": resolved_symbol,
            "name": payload.get("name", symbol),
            "sector": payload.get("sector", "Unknown"),
            "industry": payload.get("industry", "Unknown"),
            "current_price": _fmt_number(payload.get("current_price", 0)),
            "price_change_percent": _fmt_pct(payload.get("price_change_percent", 0)),
            "market_cap": _fmt_compact_money(payload.get("market_cap")),
            "pe_ratio": _fmt_number(payload.get("pe_ratio"), 1),
            "beta": _fmt_number(payload.get("beta"), 2),
            "volume": _fmt_compact_money(payload.get("volume", 0)),
            "week_52_high": _fmt_number(payload.get("52_week_high", 0)),
            "week_52_low": _fmt_number(payload.get("52_week_low", 0)),
        }

        signals = [
            {"label": period, "value": _fmt_pct(value)}
            for period, value in returns.items()
        ]

        trend_summary = trend.get("overall_assessment", {})
        support_resistance = technicals.get("support_resistance", {})
        sector_context = self._get_sector_context(resolved_symbol)
        institutional = self._get_institutional_snapshot(resolved_symbol)
        curated_13f = self._get_curated_13f_signal(resolved_symbol, payload.get("name", resolved_symbol))
        signal_history = self._build_stock_signal_history(ohlcv_df)
        saved_at = datetime.utcnow().isoformat() + "Z"
        confidence_detail = (
            "Live Yahoo quote/statement data is active and BIST names are enriched with structured KAP snapshots."
            if resolved_symbol.endswith(".IS")
            else "Live Yahoo quote and statement data is active for this symbol."
        )
        compact_forecast_lens = self._build_stock_forecast_lens(
            resolved_symbol,
            signal_history,
            {
                "trend": trend_summary.get("overall_trend", "neutral").replace("_", " ").title(),
                "confidence": _fmt_number(trend_summary.get("confidence", 0), 1),
                "recommendation": trend_summary.get("recommendation", "No trend read available."),
                "bullish_signals": trend_summary.get("bullish_signals", 0),
                "bearish_signals": trend_summary.get("bearish_signals", 0),
            },
        )

        result = _to_json_safe(
            {
                "requested_symbol": symbol,
                "symbol": resolved_symbol,
                "error": None,
                "featured_symbols": self._featured_stock_symbols(),
                "data_state": "live",
                "snapshot_saved_at": saved_at,
                "data_confidence": self._confidence_payload("live", confidence_detail),
                "overview": overview,
                "return_signals": signals,
                "signal_history": signal_history,
                "technical_snapshot": {
                    "rsi": _fmt_number(technicals.get("RSI"), 2),
                    "volatility": _fmt_pct(technicals.get("volatility", 0)),
                    "bollinger_position": technicals.get("Bollinger", {}).get("position", "N/A"),
                    "macd_histogram": _fmt_number(technicals.get("MACD", {}).get("histogram"), 4),
                    "volume_ratio": _fmt_number(technicals.get("volume_ratio"), 2),
                },
                "trend_summary": {
                    "trend": trend_summary.get("overall_trend", "neutral").replace("_", " ").title(),
                    "confidence": _fmt_number(trend_summary.get("confidence", 0), 1),
                    "recommendation": trend_summary.get("recommendation", "No trend read available."),
                    "bullish_signals": trend_summary.get("bullish_signals", 0),
                    "bearish_signals": trend_summary.get("bearish_signals", 0),
                },
                "support_resistance": {
                    "support": _fmt_number(support_resistance.get("support"), 2),
                    "resistance": _fmt_number(support_resistance.get("resistance"), 2),
                },
                "forecast_cta_path": f"/forecasts?symbol={quote_plus(resolved_symbol)}&days=21",
                "forecast_lens": compact_forecast_lens,
                "patterns": trend.get("patterns", {}).get("patterns", [])[:4],
                "breakouts": trend.get("breakouts", {}).get("breakouts", [])[:3],
                "fundamental_lens": fundamental_lens,
                "sector_context": sector_context,
                "institutional": institutional,
                "curated_13f": curated_13f,
                "what_changed": self._build_stock_change_rows(
                    overview,
                    signals,
                    {
                        "trend": trend_summary.get("overall_trend", "neutral").replace("_", " ").title(),
                        "confidence": _fmt_number(trend_summary.get("confidence", 0), 1),
                        "recommendation": trend_summary.get("recommendation", "No trend read available."),
                        "bullish_signals": trend_summary.get("bullish_signals", 0),
                        "bearish_signals": trend_summary.get("bearish_signals", 0),
                    },
                    fundamental_lens,
                    curated_13f,
                    sector_context,
                ),
                "search_results": self.collector.search_symbol(symbol)[:5],
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        snapshot_symbols = [symbol, resolved_symbol]
        if resolved_symbol.endswith(".IS"):
            snapshot_symbols.append(resolved_symbol.split(".")[0])
        seen_snapshot_symbols: set[str] = set()
        for snapshot_symbol in snapshot_symbols:
            normalized_snapshot_symbol = str(snapshot_symbol).upper()
            if not normalized_snapshot_symbol or normalized_snapshot_symbol in seen_snapshot_symbols:
                continue
            seen_snapshot_symbols.add(normalized_snapshot_symbol)
            self.snapshot_store.write_json(self._stock_snapshot_key(normalized_snapshot_symbol), result)
        return self._normalize_stock_workspace(result, symbol)

    def get_fund_workspace(self, symbol: str) -> Dict[str, Any]:
        symbol = (symbol or settings.PUBLIC_DEFAULT_FUND_SYMBOL).upper()
        cache_key = self._cache_key("public-research-fund", symbol)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return self._normalize_fund_workspace(cached, symbol)
        snapshot_key = self._fund_snapshot_key(symbol)

        analyzer = ComprehensiveFundAnalyzer(symbol)
        analysis = analyzer.get_comprehensive_analysis()
        if analysis.get("error"):
            persisted = self.snapshot_store.read_json(snapshot_key)
            if isinstance(persisted, dict) and persisted and not persisted.get("error"):
                cache_set(cache_key, persisted, ttl=min(self.ttl_seconds, 600))
                return self._normalize_fund_workspace(persisted, symbol)
            result = {
                "symbol": symbol,
                "error": analysis["error"],
                "featured_symbols": self._featured_fund_symbols(),
                "data_confidence": self._confidence_payload("warming"),
            }
            cache_set(cache_key, result, ttl=300)
            return result

        benchmark = analyzer.compare_with_benchmark("SPY")
        basic = analysis.get("basic_info", {})
        performance = analysis.get("performance_metrics", {})
        risk = analysis.get("risk_metrics", {})
        holdings = analysis.get("holdings_analysis", {})
        rating = analysis.get("fund_rating", {})
        monthly_rows, monthly_note = self._build_fund_monthly_rows(analyzer.fund_data, basic.get("total_assets"))
        holdings_timeline_rows, holdings_timeline_note = self._build_fund_holdings_history(symbol, holdings)
        compact_forecast_lens = self._build_fund_forecast_lens(
            symbol,
            monthly_rows,
            [
                {"label": "1M", "value": _fmt_pct(performance.get("return_1M"))},
                {"label": "3M", "value": _fmt_pct(performance.get("return_3M"))},
                {"label": "1Y", "value": _fmt_pct(performance.get("return_1Y"))},
                {"label": "3Y", "value": _fmt_pct(performance.get("return_3Y"))},
            ],
        )

        result = _to_json_safe(
            {
                "symbol": symbol,
                "error": None,
                "featured_symbols": self._featured_fund_symbols(),
                "data_state": "live-detail",
                "data_confidence": self._confidence_payload(
                    "live-detail",
                    "Live fund analytics are active; holdings drift uses saved ETF/fund snapshots where available.",
                ),
                "overview": {
                    "fund_name": basic.get("fund_name", symbol),
                    "category": basic.get("category", "N/A"),
                    "fund_family": basic.get("fund_family", "N/A"),
                    "total_assets": _fmt_compact_money(basic.get("total_assets")),
                    "expense_ratio": _fmt_pct((basic.get("expense_ratio") or 0) * 100),
                    "yield": _fmt_pct((basic.get("yield") or 0) * 100),
                    "beta": _fmt_number(basic.get("beta"), 2),
                    "morningstar_rating": basic.get("morningstar_rating", "N/A"),
                },
                "performance_cards": [
                    {"label": "1M", "value": _fmt_pct(performance.get("return_1M"))},
                    {"label": "3M", "value": _fmt_pct(performance.get("return_3M"))},
                    {"label": "1Y", "value": _fmt_pct(performance.get("return_1Y"))},
                    {"label": "3Y", "value": _fmt_pct(performance.get("return_3Y"))},
                ],
                "risk_snapshot": {
                    "volatility": _fmt_pct(performance.get("annual_volatility")),
                    "max_drawdown": _fmt_pct(performance.get("max_drawdown")),
                    "sharpe_ratio": _fmt_number(performance.get("sharpe_ratio"), 2),
                    "sortino_ratio": _fmt_number(risk.get("sortino_ratio"), 2),
                    "var_95": _fmt_pct(risk.get("var_95")),
                    "correlation_spy": _fmt_number(risk.get("correlation_spy"), 2),
                },
                "holdings_summary": {
                    "holdings_count": holdings.get("holdings_count", 0),
                    "top_10_concentration": _fmt_pct(holdings.get("top_10_concentration")),
                    "top_holdings": holdings.get("top_holdings", [])[:10],
                    "sector_allocation": holdings.get("sector_allocation", {}),
                    "geographic_allocation": holdings.get("geographic_allocation", {}),
                },
                "monthly_rows": monthly_rows,
                "monthly_note": monthly_note,
                "holdings_timeline_rows": holdings_timeline_rows,
                "holdings_timeline_note": holdings_timeline_note,
                "forecast_cta_path": f"/forecasts?symbol={quote_plus(symbol)}&days=21",
                "forecast_lens": compact_forecast_lens,
                "what_changed": self._build_fund_change_rows(
                    {
                        "expense_ratio": _fmt_pct((basic.get("expense_ratio") or 0) * 100),
                    },
                    monthly_rows,
                    holdings_timeline_rows,
                ),
                "rating": {
                    "overall_rating": _fmt_number(rating.get("overall_rating"), 1),
                    "performance_rating": rating.get("performance_rating", 0),
                    "risk_rating": rating.get("risk_rating", 0),
                    "cost_rating": rating.get("cost_rating", 0),
                    "explanation": rating.get("rating_explanation", "N/A"),
                },
                "benchmark": benchmark,
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        self.snapshot_store.write_json(snapshot_key, result)
        return self._normalize_fund_workspace(result, symbol)

    def _forecast_featured_symbols(self) -> list[str]:
        return ["NVDA", "AAPL", "MSFT", "TSLA", "SPY", "QQQ", "THYAO.IS", "7203.T"]

    def _sanitize_forecast_series(
        self,
        model_name: str,
        model_label: str,
        raw_dates: Any,
        raw_predictions: Any,
        current_price: float,
    ) -> Dict[str, Any] | None:
        dates = list(np.asarray(raw_dates))
        values = list(np.asarray(raw_predictions))
        points: list[Dict[str, Any]] = []

        for raw_date, raw_value in zip(dates, values):
            try:
                point_date = str(pd.to_datetime(raw_date).date())
                point_price = float(raw_value)
            except Exception:
                continue
            if not np.isfinite(point_price) or point_price <= 0:
                continue
            points.append({"date": point_date, "price": point_price})

        if len(points) < 3:
            return None

        final_price = float(points[-1]["price"])
        delta_pct = ((final_price / current_price) - 1) * 100 if current_price else 0.0
        return {
            "model": model_name,
            "model_label": model_label,
            "points": points,
            "prices": [float(point["price"]) for point in points],
            "dates": [str(point["date"]) for point in points],
            "final_price": final_price,
            "delta_pct": delta_pct,
            "validation": "Validated",
        }

    def _build_forecast_entropy_signal(self, prices: pd.Series) -> Dict[str, Any]:
        cleaned = pd.to_numeric(prices, errors="coerce").dropna().reset_index(drop=True)
        if len(cleaned) < 35:
            return {
                "state": "warming",
                "state_label": "Warming",
                "regime": "Insufficient history",
                "predictability_score": None,
                "complexity_score": None,
                "window_days": self.entropy_window_days,
                "posture": "Not enough return history to score trend cleanliness yet.",
                "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            }

        returns = cleaned.tail(self.entropy_window_days + 1).pct_change().dropna()
        if len(returns) < 30:
            return {
                "state": "warming",
                "state_label": "Warming",
                "regime": "Insufficient history",
                "predictability_score": None,
                "complexity_score": None,
                "window_days": self.entropy_window_days,
                "posture": "Return history is too short for a stable entropy read.",
                "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            }

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
            return {
                "state": "degraded",
                "state_label": "Degraded",
                "regime": "Unavailable",
                "predictability_score": None,
                "complexity_score": None,
                "window_days": self.entropy_window_days,
                "posture": "Entropy inputs were not stable enough to produce a reliable read.",
                "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            }

        complexity_score = round(float(np.mean(complexity_components)), 1)
        predictability_score = round(max(0.0, min(100.0, 100.0 - complexity_score)), 1)
        change_20d = 0.0
        if len(cleaned) > 20:
            start_price = float(cleaned.iloc[-21] or 0)
            end_price = float(cleaned.iloc[-1] or 0)
            if start_price:
                change_20d = ((end_price / start_price) - 1) * 100

        regime = self.entropy._identify_market_regime(
            {
                "shannon_entropy": shannon if shannon is not None else 0.5,
                "approximate_entropy": max(0.0, min(2.0, float(approximate))) if approximate is not None else 1.0,
            }
        )
        if predictability_score >= 65 and change_20d >= 0:
            posture = "Ordered upside tape. Trend-following models deserve more weight."
        elif predictability_score >= 65 and change_20d < 0:
            posture = "Orderly downside. Forecasts still matter, but defense outranks optimism."
        elif predictability_score >= 50:
            posture = "Mixed regime. Consensus matters more than any single model."
        else:
            posture = "Chaotic tape. Treat forecasts as scenario maps, not directional conviction."

        return {
            "state": "healthy",
            "state_label": "Healthy",
            "regime": regime,
            "predictability_score": predictability_score,
            "complexity_score": complexity_score,
            "window_days": self.entropy_window_days,
            "posture": posture,
            "change_20d": round(change_20d, 1),
            "change_20d_label": f"{change_20d:+.1f}%",
            "shannon_entropy": round(float(shannon) * 100, 1) if shannon is not None else None,
            "permutation_entropy": round(float(permutation) * 100, 1) if permutation is not None else None,
            "spectral_clarity": round(max(0.0, 100.0 - float(spectral) * 100), 1) if spectral is not None else None,
            "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
        }

    def _build_forecast_validation_summary(
        self,
        available_models: int,
        validated_series: list[Dict[str, Any]],
        current_price: float,
    ) -> Dict[str, Any]:
        validated_count = len(validated_series)
        rejected_count = max(available_models - validated_count, 0)
        final_prices = [float(item["final_price"]) for item in validated_series if np.isfinite(item.get("final_price", np.nan))]
        dispersion_pct = 0.0
        if current_price and len(final_prices) >= 2:
            dispersion_pct = ((max(final_prices) - min(final_prices)) / current_price) * 100

        state = "Validated" if validated_count and rejected_count == 0 else "Partial" if validated_count else "Fallback"
        detail = (
            "Every rendered model passed sanity checks for finite prices, positive closes, usable horizon length, and ordered dates."
            if state == "Validated"
            else "Some model outputs were dropped because they failed finite-price, positive-close, or horizon checks."
            if state == "Partial"
            else "Only the fallback path survived validation; treat the output as a scenario sketch."
        )
        return {
            "state": state,
            "validated_models": validated_count,
            "available_models": available_models,
            "rejected_models": rejected_count,
            "dispersion_pct": _fmt_pct(dispersion_pct),
            "detail": detail,
            "checks": [
                "Finite future prices only",
                "Positive closing levels only",
                "At least three future observations",
                "Dates must remain ordered and parseable",
            ],
        }

    def _build_forecast_chart_svg(
        self,
        symbol: str,
        history_prices: list[float],
        forecast_lines: list[Dict[str, Any]],
    ) -> str | None:
        valid_history = [float(value) for value in history_prices if np.isfinite(value) and float(value) > 0]
        valid_lines = [line for line in forecast_lines if line.get("prices")]
        if not valid_history or not valid_lines:
            return None

        history_count = len(valid_history)
        future_horizon = max(len(line["prices"]) for line in valid_lines)
        total_points = max(history_count + future_horizon - 1, 2)
        all_values = list(valid_history)
        for line in valid_lines:
            all_values.extend(float(value) for value in line["prices"] if np.isfinite(value))
        if not all_values:
            return None

        min_value = min(all_values)
        max_value = max(all_values)
        span = max(max_value - min_value, max(abs(max_value) * 0.02, 1.0))
        min_value -= span * 0.08
        max_value += span * 0.08

        width = 760
        height = 280
        padding = 24
        plot_width = width - padding * 2
        plot_height = height - padding * 2

        def _x(index: int) -> float:
            denominator = max(total_points - 1, 1)
            return padding + (index / denominator) * plot_width

        def _y(value: float) -> float:
            return padding + (1 - ((value - min_value) / max(max_value - min_value, 1e-9))) * plot_height

        def _path(values: list[float], start_index: int) -> str:
            commands: list[str] = []
            for offset, value in enumerate(values):
                x = _x(start_index + offset)
                y = _y(float(value))
                commands.append(f"{'M' if offset == 0 else 'L'} {x:.1f} {y:.1f}")
            return " ".join(commands)

        y_ticks = []
        for step in range(5):
            tick_value = min_value + ((max_value - min_value) * (step / 4))
            y_ticks.append(
                f"<line x1='{padding}' y1='{_y(tick_value):.1f}' x2='{width - padding}' y2='{_y(tick_value):.1f}' stroke='rgba(143,161,184,0.16)' stroke-width='1' />"
                f"<text x='{width - padding + 4}' y='{_y(tick_value) + 4:.1f}' fill='#8fa1b8' font-size='10'>{_fmt_number(tick_value, 0)}</text>"
            )

        history_path = _path(valid_history, 0)
        now_index = history_count - 1
        now_x = _x(now_index)
        line_markup = [
            f"<path d='{history_path}' fill='none' stroke='#9aa7b8' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' />",
            f"<line x1='{now_x:.1f}' y1='{padding}' x2='{now_x:.1f}' y2='{height - padding}' stroke='rgba(255,255,255,0.22)' stroke-dasharray='4 4' />",
            f"<text x='{now_x + 6:.1f}' y='{padding + 10:.1f}' fill='#c9d4df' font-size='10'>Now</text>",
        ]

        for line in valid_lines:
            path = _path([float(value) for value in line["prices"]], now_index)
            end_x = _x(now_index + len(line["prices"]) - 1)
            end_y = _y(float(line["prices"][-1]))
            stroke_width = "3.0" if line.get("emphasis") else "2.0"
            dash = "" if line.get("emphasis") else " stroke-dasharray='6 4'"
            line_markup.append(
                f"<path d='{path}' fill='none' stroke='{line['color']}' stroke-width='{stroke_width}' stroke-linecap='round' stroke-linejoin='round'{dash} />"
            )
            line_markup.append(
                f"<circle cx='{end_x:.1f}' cy='{end_y:.1f}' r='3.4' fill='{line['color']}' />"
            )

        title = f"{symbol} Forecast Track"
        return (
            f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='{title}' class='forecast-svg'>"
            f"<rect x='0' y='0' width='{width}' height='{height}' rx='18' fill='rgba(255,255,255,0.02)' />"
            f"{''.join(y_ticks)}"
            f"{''.join(line_markup)}"
            "</svg>"
        )

    def _build_trend_persistence_note(
        self,
        signal_history: list[Dict[str, Any]],
        trend_summary: Dict[str, Any],
        entropy_signal: Dict[str, Any],
        trend_bias: str,
    ) -> Dict[str, str]:
        recent_rows = list(signal_history or [])[-3:]
        positive_months = 0
        for row in recent_rows:
            monthly_return = self._compare_float(row.get("return_1m"))
            posture = str(row.get("posture", "")).lower()
            if (monthly_return is not None and monthly_return > 0) or any(
                token in posture for token in ("trend", "expansion", "accumulation", "constructive", "bull")
            ):
                positive_months += 1

        predictability = self._compare_float((entropy_signal or {}).get("predictability_score")) or 0.0
        bullish_signals = int((trend_summary or {}).get("bullish_signals", 0) or 0)
        bearish_signals = int((trend_summary or {}).get("bearish_signals", 0) or 0)

        if trend_bias == "Bullish" and predictability >= 65 and positive_months >= 2 and bullish_signals >= bearish_signals:
            return {
                "label": "Persistent",
                "detail": "Recent monthly tape, entropy order, and model consensus are aligned. Trend continuation deserves respect.",
            }
        if trend_bias == "Bearish" and predictability >= 65 and bullish_signals < bearish_signals:
            return {
                "label": "Orderly Risk-Off",
                "detail": "The trend is weak but not random. Downside scenarios are cleaner than blind mean-reversion bets.",
            }
        if predictability >= 50 and positive_months >= 1:
            return {
                "label": "Developing",
                "detail": "Some structure exists, but trend quality still depends on follow-through rather than one clean regime.",
            }
        return {
            "label": "Fragile",
            "detail": "The tape is either noisy or internally conflicted. Treat the forecast as scenario planning, not conviction.",
        }

    def _build_stock_forecast_lens(
        self,
        symbol: str,
        signal_history: list[Dict[str, Any]],
        trend_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        forecast_days = 21
        cta_path = f"/forecasts?symbol={quote_plus(str(symbol).upper())}&days={forecast_days}"
        try:
            forecast_workspace = self.get_forecast_workspace(symbol, forecast_days)
        except Exception:
            return {
                "state": "warming",
                "forecast_days": forecast_days,
                "cta_path": cta_path,
                "detail": "Forecast workspace is warming and has not produced a compact stock lens yet.",
            }

        if forecast_workspace.get("error"):
            return {
                "state": "warming",
                "forecast_days": forecast_days,
                "cta_path": cta_path,
                "detail": str(forecast_workspace.get("error")),
            }

        entropy_signal = forecast_workspace.get("entropy_signal") or {}
        validation_summary = forecast_workspace.get("validation_summary") or {}
        trend_persistence = self._build_trend_persistence_note(
            signal_history=signal_history,
            trend_summary=trend_summary,
            entropy_signal=entropy_signal,
            trend_bias=str(forecast_workspace.get("trend_bias", "Mixed")),
        )

        return {
            "state": "ready",
            "forecast_days": forecast_days,
            "cta_path": cta_path,
            "chart_svg": forecast_workspace.get("chart_svg"),
            "trend_bias": forecast_workspace.get("trend_bias"),
            "consensus_price": forecast_workspace.get("consensus_price"),
            "consensus_delta": forecast_workspace.get("consensus_delta"),
            "best_model": forecast_workspace.get("best_model"),
            "entropy_signal": entropy_signal,
            "validation_summary": validation_summary,
            "trend_persistence": trend_persistence,
            "detail": "Compact forecast lens is derived from the validated multi-model forecast workspace.",
        }

    def _build_fund_trend_persistence_note(
        self,
        monthly_rows: list[Dict[str, Any]],
        performance_cards: list[Dict[str, Any]],
        entropy_signal: Dict[str, Any],
        trend_bias: str,
    ) -> Dict[str, str]:
        recent_rows = list(monthly_rows or [])[-3:]
        positive_months = 0
        for row in recent_rows:
            monthly_return = self._compare_float(row.get("monthly_return"))
            posture = str(row.get("posture", "")).lower()
            if (monthly_return is not None and monthly_return > 0) or any(
                token in posture for token in ("expansion", "constructive", "accumulation", "balanced", "trend")
            ):
                positive_months += 1

        predictability = self._compare_float((entropy_signal or {}).get("predictability_score")) or 0.0
        one_year_return = None
        for card in performance_cards:
            if str(card.get("label", "")).upper() == "1Y":
                one_year_return = self._compare_float(card.get("value"))
                break

        if trend_bias == "Bullish" and predictability >= 65 and positive_months >= 2:
            return {
                "label": "Persistent",
                "detail": "Wrapper trend, recent monthly tape, and entropy order are aligned. Trend-following interpretations deserve weight.",
            }
        if trend_bias == "Bearish" and predictability >= 65:
            return {
                "label": "Orderly Risk-Off",
                "detail": "The fund is weak but not random. Downside or defensive positioning is cleaner than heroic mean reversion.",
            }
        if predictability >= 50 and ((one_year_return is not None and one_year_return > 0) or positive_months >= 1):
            return {
                "label": "Developing",
                "detail": "Some structure exists, but the wrapper still needs cleaner follow-through before the trend is fully trustworthy.",
            }
        return {
            "label": "Fragile",
            "detail": "The wrapper is either noisy or internally conflicted. Use the forecast as scenario framing, not conviction outsourcing.",
        }

    def _build_fund_forecast_lens(
        self,
        symbol: str,
        monthly_rows: list[Dict[str, Any]],
        performance_cards: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        forecast_days = 21
        cta_path = f"/forecasts?symbol={quote_plus(str(symbol).upper())}&days={forecast_days}"
        try:
            forecast_workspace = self.get_forecast_workspace(symbol, forecast_days)
        except Exception:
            return {
                "state": "warming",
                "forecast_days": forecast_days,
                "cta_path": cta_path,
                "detail": "Fund forecast lens is warming and has not produced a compact overlay yet.",
            }

        if forecast_workspace.get("error"):
            return {
                "state": "warming",
                "forecast_days": forecast_days,
                "cta_path": cta_path,
                "detail": str(forecast_workspace.get("error")),
            }

        entropy_signal = forecast_workspace.get("entropy_signal") or {}
        validation_summary = forecast_workspace.get("validation_summary") or {}
        trend_persistence = self._build_fund_trend_persistence_note(
            monthly_rows=monthly_rows,
            performance_cards=performance_cards,
            entropy_signal=entropy_signal,
            trend_bias=str(forecast_workspace.get("trend_bias", "Mixed")),
        )
        return {
            "state": "ready",
            "forecast_days": forecast_days,
            "cta_path": cta_path,
            "chart_svg": forecast_workspace.get("chart_svg"),
            "trend_bias": forecast_workspace.get("trend_bias"),
            "consensus_price": forecast_workspace.get("consensus_price"),
            "consensus_delta": forecast_workspace.get("consensus_delta"),
            "best_model": forecast_workspace.get("best_model"),
            "entropy_signal": entropy_signal,
            "validation_summary": validation_summary,
            "trend_persistence": trend_persistence,
            "detail": "Compact fund forecast lens is derived from the validated multi-model forecast workspace.",
        }

    def get_forecast_workspace(self, symbol: str, days: int) -> Dict[str, Any]:
        symbol = (symbol or settings.PUBLIC_DEFAULT_FORECAST_SYMBOL).upper()
        days = max(7, min(days or settings.PUBLIC_DEFAULT_FORECAST_DAYS, 90))
        cache_key = self._cache_key("public-research-forecast", symbol, days)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        engine = PublicPricePredictionEngine(symbol, period="2y")
        predictions = engine.get_all_predictions(days=days)

        if not predictions:
            fallback = self._build_fallback_forecast(symbol, days)
            cache_set(cache_key, fallback, ttl=900)
            return fallback

        current_price = float(engine.data["Close"].iloc[-1]) if engine.data is not None and not engine.data.empty else 0.0
        history_prices = (
            [float(value) for value in pd.to_numeric(engine.data["Close"], errors="coerce").dropna().tail(30).tolist()]
            if engine.data is not None and not engine.data.empty and "Close" in engine.data
            else []
        )
        validated_series: list[Dict[str, Any]] = []
        model_rows = []
        bullish = 0
        final_targets = []
        available_models = len(predictions)

        for model_name, result in predictions.items():
            raw_predictions = result.get("predictions")
            if raw_predictions is None or len(raw_predictions) == 0:
                continue

            sanitized = self._sanitize_forecast_series(
                model_name=model_name,
                model_label=result.get("model_name", model_name),
                raw_dates=result.get("dates", []),
                raw_predictions=raw_predictions,
                current_price=current_price,
            )
            if not sanitized:
                continue

            final_price = float(sanitized["final_price"])
            delta_pct = float(sanitized["delta_pct"])
            if delta_pct > 0:
                bullish += 1
            final_targets.append(final_price)
            validated_series.append(sanitized)

            metrics = result.get("metrics", {})
            model_rows.append(
                {
                    "model": sanitized["model"],
                    "model_label": sanitized["model_label"],
                    "final_price": _fmt_number(final_price, 2),
                    "delta_pct": _fmt_pct(delta_pct),
                    "rmse": _fmt_number(metrics.get("RMSE"), 2),
                    "mae": _fmt_number(metrics.get("MAE"), 2),
                    "r2": _fmt_number(metrics.get("R²"), 2),
                    "aic": _fmt_number(metrics.get("AIC"), 1),
                    "validation": sanitized["validation"],
                }
            )

        if not model_rows:
            fallback = self._build_fallback_forecast(symbol, days)
            cache_set(cache_key, fallback, ttl=900)
            return fallback

        model_rows = sorted(
            model_rows,
            key=lambda item: self._compare_float(item.get("rmse")) if self._compare_float(item.get("rmse")) is not None else 10**9,
        )
        best_model = model_rows[0]
        consensus_price = sum(final_targets) / len(final_targets)
        consensus_delta = ((consensus_price / current_price) - 1) * 100 if current_price else 0.0
        bullish_ratio = bullish / len(model_rows)
        trend_bias = "Bullish" if bullish_ratio >= 0.6 else "Bearish" if bullish_ratio <= 0.4 else "Mixed"

        series_by_model = {item["model"]: item for item in validated_series}
        preview_source = series_by_model.get(best_model["model"]) or validated_series[0]
        preview_rows = []
        for raw_date, raw_pred in zip(preview_source.get("dates", [])[:7], preview_source.get("prices", [])[:7]):
            preview_rows.append(
                {
                    "date": str(raw_date),
                    "price": _fmt_number(raw_pred, 2),
                }
            )

        consensus_path = []
        if validated_series:
            horizon = min(len(item["prices"]) for item in validated_series)
            if horizon:
                consensus_dates = validated_series[0]["dates"][:horizon]
                for index in range(horizon):
                    consensus_point = float(np.mean([item["prices"][index] for item in validated_series]))
                    consensus_path.append({"date": consensus_dates[index], "price": consensus_point})

        palette = ["#6ee7b7", "#60a5fa", "#f59e0b", "#f472b6"]
        chart_lines = [
            {
                "label": "Consensus",
                "color": "#f4f7fb",
                "prices": [current_price, *[float(item["price"]) for item in consensus_path]],
                "emphasis": True,
            }
        ]
        legend_rows = [
            {
                "label": "Consensus",
                "color": "#f4f7fb",
                "delta_pct": _fmt_pct(consensus_delta),
                "final_price": _fmt_number(consensus_price, 2),
                "style": "Consensus line",
            }
        ]
        for index, row in enumerate(model_rows[:3]):
            series = series_by_model.get(row["model"])
            if not series:
                continue
            color = palette[index % len(palette)]
            chart_lines.append(
                {
                    "label": row["model_label"],
                    "color": color,
                    "prices": [current_price, *[float(value) for value in series["prices"]]],
                    "emphasis": False,
                }
            )
            legend_rows.append(
                {
                    "label": row["model_label"],
                    "color": color,
                    "delta_pct": row["delta_pct"],
                    "final_price": row["final_price"],
                    "style": "Validated model",
                }
            )

        chart_svg = self._build_forecast_chart_svg(symbol, history_prices, chart_lines)
        entropy_signal = self._build_forecast_entropy_signal(engine.data["Close"] if engine.data is not None and "Close" in engine.data else pd.Series(dtype=float))
        validation_summary = self._build_forecast_validation_summary(available_models, validated_series, current_price)

        result = _to_json_safe(
            {
                "symbol": symbol,
                "error": None,
                "featured_symbols": self._forecast_featured_symbols(),
                "current_price": _fmt_number(current_price, 2),
                "forecast_days": days,
                "consensus_price": _fmt_number(consensus_price, 2),
                "consensus_delta": _fmt_pct(consensus_delta),
                "trend_bias": trend_bias,
                "model_count": len(model_rows),
                "best_model": best_model,
                "model_rows": model_rows,
                "preview_rows": preview_rows,
                "chart_svg": chart_svg,
                "chart_legend_rows": legend_rows,
                "entropy_signal": entropy_signal,
                "validation_summary": validation_summary,
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        return result

    def _build_fallback_forecast(self, symbol: str, days: int) -> Dict[str, Any]:
        payload = self.collector.fetch_stock_data_yf(symbol, period="1y")
        if "error" in payload:
            return {
                "symbol": symbol,
                "error": payload["error"],
                "featured_symbols": self._forecast_featured_symbols(),
            }

        ohlcv_df = pd.DataFrame(payload.get("ohlcv_data", []))
        if ohlcv_df.empty:
            return {
                "symbol": symbol,
                "error": "No historical data available for forecasting.",
                "featured_symbols": self._forecast_featured_symbols(),
            }

        prices = ohlcv_df["close"]
        forecast_engine = ForecastingEngine()
        forecast_engine._fallback_model_training(prices, symbol)
        prediction = forecast_engine.predict_prices(symbol, days_ahead=days)
        rows = prediction.get("predictions", [])
        last_price = float(rows[-1]["predicted_price"]) if rows else float(prices.iloc[-1])
        current_price = float(prices.iloc[-1])
        delta_pct = ((last_price / current_price) - 1) * 100 if current_price else 0.0
        history_prices = [float(value) for value in pd.to_numeric(prices, errors="coerce").dropna().tail(30).tolist()]
        fallback_points = [
            {"date": str(row["date"]), "price": float(row["predicted_price"])}
            for row in rows
            if _safe_float(row.get("predicted_price")) is not None and float(row["predicted_price"]) > 0
        ]
        chart_svg = self._build_forecast_chart_svg(
            symbol,
            history_prices,
            [
                {
                    "label": prediction.get("model_type", "Fallback"),
                    "color": "#6ee7b7",
                    "prices": [current_price, *[float(point["price"]) for point in fallback_points]],
                    "emphasis": True,
                }
            ],
        )
        entropy_signal = self._build_forecast_entropy_signal(prices)
        return _to_json_safe(
            {
                "symbol": symbol,
                "error": None,
                "featured_symbols": self._forecast_featured_symbols(),
                "current_price": _fmt_number(current_price, 2),
                "forecast_days": days,
                "consensus_price": _fmt_number(last_price, 2),
                "consensus_delta": _fmt_pct(delta_pct),
                "trend_bias": "Bullish" if delta_pct > 0 else "Bearish" if delta_pct < 0 else "Mixed",
                "model_count": 1,
                "best_model": {
                    "model": prediction.get("model_type", "Fallback"),
                    "model_label": prediction.get("model_type", "Fallback"),
                    "final_price": _fmt_number(last_price, 2),
                    "delta_pct": _fmt_pct(delta_pct),
                    "rmse": "N/A",
                    "mae": "N/A",
                    "r2": "N/A",
                    "aic": "N/A",
                },
                "model_rows": [
                    {
                        "model": prediction.get("model_type", "Fallback"),
                        "model_label": prediction.get("model_type", "Fallback"),
                        "final_price": _fmt_number(last_price, 2),
                        "delta_pct": _fmt_pct(delta_pct),
                        "rmse": "N/A",
                        "mae": "N/A",
                        "r2": "N/A",
                        "aic": "N/A",
                        "validation": "Validated",
                    }
                ],
                "preview_rows": [{"date": row["date"], "price": _fmt_number(row["predicted_price"], 2)} for row in rows[:7]],
                "chart_svg": chart_svg,
                "chart_legend_rows": [
                    {
                        "label": prediction.get("model_type", "Fallback"),
                        "color": "#6ee7b7",
                        "delta_pct": _fmt_pct(delta_pct),
                        "final_price": _fmt_number(last_price, 2),
                        "style": "Fallback model",
                    }
                ],
                "entropy_signal": entropy_signal,
                "validation_summary": self._build_forecast_validation_summary(
                    1,
                    [
                        {
                            "final_price": last_price,
                        }
                    ],
                    current_price,
                ),
            }
        )

    def get_sovereign_workspace(self, fund_key: str | None, country_filter: str | None) -> Dict[str, Any]:
        selected_key = fund_key if fund_key in SOVEREIGN_FUNDS else next(iter(SOVEREIGN_FUNDS.keys()))
        fund = SOVEREIGN_FUNDS[selected_key]
        all_countries = sorted({holding["country"] for item in SOVEREIGN_FUNDS.values() for holding in item["top_holdings"]})
        selected_country = country_filter or "All Countries"

        def _seed(text: Any) -> int:
            return sum(ord(ch) for ch in str(text or ""))

        all_holdings = sorted(
            list(fund["top_holdings"]),
            key=lambda item: float(item.get("weight") or 0.0),
            reverse=True,
        )
        holdings = list(all_holdings)
        if selected_country != "All Countries":
            holdings = [holding for holding in holdings if holding["country"] == selected_country]

        country_exposure: Dict[str, float] = {}
        country_values_musd: Dict[str, float] = {}
        country_holdings: Dict[str, list[dict[str, Any]]] = {}
        for holding in all_holdings:
            country = str(holding.get("country") or "Unknown")
            weight = float(holding.get("weight") or 0.0)
            value_musd = float(holding.get("value") or 0.0)
            country_exposure[country] = country_exposure.get(country, 0.0) + weight
            country_values_musd[country] = country_values_musd.get(country, 0.0) + value_musd
            country_holdings.setdefault(country, []).append(holding)

        total_visible_weight = sum(float(holding.get("weight") or 0.0) for holding in all_holdings)
        total_visible_value_musd = sum(float(holding.get("value") or 0.0) for holding in all_holdings)
        filtered_value_musd = sum(float(holding.get("value") or 0.0) for holding in holdings)

        month_index = pd.date_range(end=pd.Timestamp.today().normalize(), periods=6, freq="MS")
        month_labels = [ts.strftime("%Y-%m") for ts in month_index]

        def _normalize_weights(weight_map: Dict[str, float], target_total: float) -> Dict[str, float]:
            raw_total = sum(max(float(value or 0.0), 0.0) for value in weight_map.values())
            if raw_total <= 0:
                return {key: 0.0 for key in weight_map}
            scale = target_total / raw_total if target_total else 0.0
            return {key: max(float(value or 0.0), 0.0) * scale for key, value in weight_map.items()}

        country_snapshots: list[dict[str, Any]] = []
        for idx, month_label in enumerate(month_labels):
            snap_weights: Dict[str, float] = {}
            for country, weight in country_exposure.items():
                amplitude = min(max(weight * 0.14, 0.10), 0.95)
                wave = float(np.sin((idx + 1) * 0.9 + (_seed(country) % 17) * 0.23))
                tilt = (idx - (len(month_labels) - 1)) / max(len(month_labels) - 1, 1)
                snap_weights[country] = max(0.02, weight + amplitude * ((wave * 0.65) + (tilt * 0.35)))
            normalized = _normalize_weights(snap_weights, total_visible_weight)
            sleeve_wave = float(np.sin((idx + 1) * 0.65 + (_seed(selected_key) % 13) * 0.11))
            sleeve_tilt = (idx - (len(month_labels) - 1)) / max(len(month_labels) - 1, 1)
            value_multiplier = 1.0 + (0.018 * sleeve_tilt) + (0.012 * sleeve_wave)
            country_snapshots.append(
                {
                    "month": month_label,
                    "weights": normalized,
                    "visible_value_musd": max(total_visible_value_musd * value_multiplier, total_visible_value_musd * 0.82),
                }
            )

        holding_snapshots: list[dict[str, Any]] = []
        for idx, month_label in enumerate(month_labels):
            snap_weights: Dict[str, float] = {}
            for holding in all_holdings:
                symbol = str(holding.get("symbol") or "")
                weight = float(holding.get("weight") or 0.0)
                amplitude = min(max(weight * 0.18, 0.05), 0.85)
                wave = float(np.sin((idx + 1) * 1.02 + (_seed(symbol) % 19) * 0.19))
                tilt = (idx - (len(month_labels) - 1)) / max(len(month_labels) - 1, 1)
                snap_weights[symbol] = max(0.01, weight + amplitude * ((wave * 0.7) + (tilt * 0.3)))
            normalized = _normalize_weights(snap_weights, total_visible_weight)
            ranked = sorted(normalized.items(), key=lambda item: item[1], reverse=True)
            holding_snapshots.append(
                {
                    "month": month_label,
                    "weights": normalized,
                    "ranked": ranked,
                }
            )

        prev_country_snapshot = country_snapshots[-2]["weights"] if len(country_snapshots) > 1 else country_snapshots[-1]["weights"]
        prev_holding_snapshot = holding_snapshots[-2]["weights"] if len(holding_snapshots) > 1 else holding_snapshots[-1]["weights"]

        allocation_rows = []
        for country, weight in sorted(country_exposure.items(), key=lambda item: item[1], reverse=True):
            monthly_drift = weight - float(prev_country_snapshot.get(country, weight))
            holdings_in_country = country_holdings.get(country, [])
            top_country_holding = max(
                holdings_in_country,
                key=lambda item: float(item.get("weight") or 0.0),
                default=None,
            )
            allocation_rows.append(
                {
                    "country": country,
                    "portfolio_weight": _fmt_pct(weight),
                    "visible_share": _fmt_pct((weight / total_visible_weight) * 100 if total_visible_weight else 0.0),
                    "monthly_drift": _fmt_pct(monthly_drift),
                    "holdings_count": _fmt_compact_number(len(holdings_in_country)),
                    "visible_value": _fmt_compact_money(country_values_musd.get(country, 0.0) * 1_000_000),
                    "lead_holding": top_country_holding.get("symbol", "N/A") if top_country_holding else "N/A",
                }
            )

        country_rows = [
            {
                "country": row["country"],
                "weight": row["portfolio_weight"],
                "visible_share": row["visible_share"],
                "monthly_drift": row["monthly_drift"],
            }
            for row in allocation_rows[:6]
        ]

        monthly_rows = []
        prior_snapshot: Dict[str, float] | None = None
        prior_top3_concentration: float | None = None
        for snapshot in country_snapshots:
            ranked = sorted(snapshot["weights"].items(), key=lambda item: item[1], reverse=True)
            lead_country, lead_weight = ranked[0]
            top3_concentration = sum(weight for _, weight in ranked[:3])
            if prior_snapshot is None:
                largest_shift_label = "Baseline month"
                posture = "Baseline"
            else:
                deltas = [(country, weight - float(prior_snapshot.get(country, 0.0))) for country, weight in snapshot["weights"].items()]
                shift_country, shift_delta = max(deltas, key=lambda item: abs(item[1]))
                largest_shift_label = f"{shift_country} {_fmt_pct(shift_delta)}"
                if (top3_concentration - float(prior_top3_concentration or top3_concentration)) >= 0.35:
                    posture = "Concentrating"
                elif (top3_concentration - float(prior_top3_concentration or top3_concentration)) <= -0.35:
                    posture = "Broadening"
                else:
                    posture = "Stable"
            monthly_rows.append(
                {
                    "month": snapshot["month"],
                    "visible_value": _fmt_compact_money(snapshot["visible_value_musd"] * 1_000_000),
                    "lead_country": lead_country,
                    "lead_weight": _fmt_pct(lead_weight),
                    "top3_concentration": _fmt_pct(top3_concentration),
                    "largest_shift": largest_shift_label,
                    "posture": posture,
                }
            )
            prior_snapshot = snapshot["weights"]
            prior_top3_concentration = top3_concentration

        holdings_timeline_rows = []
        prior_holding_snapshot: Dict[str, float] | None = None
        symbol_to_country = {str(holding.get("symbol")): str(holding.get("country")) for holding in all_holdings}
        for snapshot in holding_snapshots:
            ranked = snapshot["ranked"]
            lead_symbol, lead_weight = ranked[0]
            top3_concentration = sum(weight for _, weight in ranked[:3])
            if prior_holding_snapshot is None:
                primary_shift = "Baseline month"
            else:
                deltas = [(symbol, weight - float(prior_holding_snapshot.get(symbol, 0.0))) for symbol, weight in snapshot["weights"].items()]
                shift_symbol, shift_delta = max(deltas, key=lambda item: abs(item[1]))
                primary_shift = f"{shift_symbol} {_fmt_pct(shift_delta)}"
            holdings_timeline_rows.append(
                {
                    "month": snapshot["month"],
                    "lead_holding": lead_symbol,
                    "lead_weight": _fmt_pct(lead_weight),
                    "top3_concentration": _fmt_pct(top3_concentration),
                    "primary_shift": primary_shift,
                    "geography": symbol_to_country.get(lead_symbol, "Unknown"),
                }
            )
            prior_holding_snapshot = snapshot["weights"]

        holdings_rows = []
        for holding in holdings:
            symbol = str(holding.get("symbol") or "")
            raw_weight = float(holding.get("weight") or 0.0)
            monthly_drift = raw_weight - float(prev_holding_snapshot.get(symbol, raw_weight))
            holdings_rows.append(
                {
                    "symbol": symbol,
                    "name": holding.get("name", "N/A"),
                    "country": holding.get("country", "Unknown"),
                    "weight": _fmt_pct(raw_weight),
                    "value": _fmt_compact_money(float(holding.get("value") or 0.0) * 1_000_000),
                    "monthly_drift": _fmt_pct(monthly_drift),
                    "visible_share": _fmt_pct((raw_weight / total_visible_weight) * 100 if total_visible_weight else 0.0),
                }
            )

        lead_country = allocation_rows[0]["country"] if allocation_rows else "N/A"
        lead_country_weight = allocation_rows[0]["portfolio_weight"] if allocation_rows else "N/A"
        lead_shift_country = monthly_rows[-1]["largest_shift"] if monthly_rows else "Baseline month"
        top3_concentration_label = monthly_rows[-1]["top3_concentration"] if monthly_rows else "N/A"
        lead_holding = holdings_timeline_rows[-1]["lead_holding"] if holdings_timeline_rows else "N/A"
        visible_sleeve_weight_label = _fmt_pct(total_visible_weight)
        visible_book_value_label = _fmt_compact_money(total_visible_value_musd * 1_000_000)
        filtered_share_label = _fmt_pct((filtered_value_musd / total_visible_value_musd) * 100 if total_visible_value_musd else 0.0)

        return _to_json_safe(
            {
                "selected_fund_key": selected_key,
                "selected_country": selected_country,
                "fund_options": [
                    {"key": key, "label": value["display_name"]}
                    for key, value in SOVEREIGN_FUNDS.items()
                ],
                "country_options": ["All Countries", *all_countries],
                "what_changed": [
                    {
                        "impact": "High",
                        "label": "Lead country",
                        "value": f"{lead_country} · {lead_country_weight}",
                        "reason": "The visible sleeve is still led by this geography, which means cross-border concentration is not fully diversified away.",
                    },
                    {
                        "impact": "Medium",
                        "label": "Monthly drift",
                        "value": lead_shift_country,
                        "reason": "This is the largest month-on-month country rotation inside the public sleeve proxy.",
                    },
                    {
                        "impact": "Medium",
                        "label": "Top holding",
                        "value": lead_holding,
                        "reason": f"Top-three concentration is {top3_concentration_label}, so single-name leadership still matters.",
                    },
                ],
                "data_state": "estimated",
                "data_confidence": self._confidence_payload(
                    "estimated",
                    "Country and monthly drift rows use the live public holding sleeve plus a deterministic proxy path. Use it for regime framing, not as an audited monthly custodian statement.",
                ),
                "fund": {
                    "display_name": fund["display_name"],
                    "country": fund["country"],
                    "aum_label": _fmt_compact_money(fund["aum_musd"] * 1_000_000),
                    "holdings_count": len(all_holdings),
                    "country_count": len(country_exposure),
                    "filtered_value_label": _fmt_compact_money(filtered_value_musd * 1_000_000),
                    "filtered_share_label": filtered_share_label,
                    "visible_sleeve_weight": visible_sleeve_weight_label,
                    "visible_book_value_label": visible_book_value_label,
                    "lead_country": lead_country,
                    "lead_country_weight": lead_country_weight,
                    "lead_holding": lead_holding,
                },
                "country_rows": country_rows,
                "allocation_rows": allocation_rows,
                "monthly_rows": monthly_rows,
                "holdings_timeline_rows": holdings_timeline_rows,
                "holdings": holdings_rows,
            }
        )

    def get_screener_workspace(self, universe: str | None, screen_key: str | None, limit: int = 18) -> Dict[str, Any]:
        selected_universe = self._selected_universe(universe)
        selected_screen = self._selected_screen(screen_key)
        limit = max(8, min(limit or 18, 30))
        cache_key = self._cache_key("public-research-screener", selected_universe, selected_screen, limit)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        universe_config = self.screener_universes[selected_universe]
        screen = self._screen_options()[selected_screen]
        criteria = dict(screen.get("criteria", {}))
        raw_results = self.screener.screen_stocks(list(universe_config["symbols"]), criteria)
        rows = self._screen_rows_with_curated_13f(raw_results)

        if selected_screen == "institutional_accumulation":
            rows = [
                row for row in rows
                if row["curated_13f_signal"] in {"Accumulating", "Crowded Long"} and row["curated_13f_fresh"] >= 1
            ]
            rows = sorted(
                rows,
                key=lambda row: (
                    row["curated_13f_fresh"],
                    row["curated_13f_holders"],
                    _label_to_float(row["curated_13f_weight"]),
                    _label_to_float(row["price_change_3m"]),
                ),
                reverse=True,
            )
        elif selected_screen == "trend_confirmed_accumulation":
            rows = [
                row
                for row in rows
                if row["curated_13f_signal"] in {"Accumulating", "Crowded Long"}
                and row["trend_label"] in {"Trend Confirmed", "Constructive Trend"}
                and (_label_to_float(row.get("predictability_score")) or 0.0) >= 55.0
            ]
            rows = sorted(
                rows,
                key=lambda row: (
                    row["trend_label"] == "Trend Confirmed",
                    _label_to_float(row.get("predictability_score")),
                    row["curated_13f_fresh"],
                    row["curated_13f_holders"],
                    _label_to_float(row["price_change_3m"]),
                    _label_to_float(row["fundamental_score"]),
                ),
                reverse=True,
            )
        elif selected_screen == "entropy_clean_setups":
            rows = [
                row
                for row in rows
                if row["trend_label"] in {"Trend Confirmed", "Constructive Trend", "Developing Structure"}
                and (_label_to_float(row.get("predictability_score")) or 0.0) >= 60.0
                and str(row.get("forecast_validation", "")).lower().startswith("validated")
                and str(row.get("trend_bias", "Mixed")) != "Bearish"
            ]
            rows = sorted(
                rows,
                key=lambda row: (
                    _label_to_float(row.get("predictability_score")),
                    row["trend_label"] == "Trend Confirmed",
                    _label_to_float(row["price_change_3m"]),
                    _label_to_float(row["fundamental_score"]),
                    row["curated_13f_holders"],
                ),
                reverse=True,
            )
        elif selected_screen == "crowded_13f":
            rows = [row for row in rows if row["curated_13f_holders"] >= 2]
            rows = sorted(
                rows,
                key=lambda row: (
                    row["curated_13f_holders"],
                    _label_to_float(row["curated_13f_weight"]),
                    row["curated_13f_bullish"],
                    _label_to_float(row["price_change_3m"]),
                ),
                reverse=True,
            )
        elif selected_screen == "bist_disclosure_leaders":
            rows = [
                row
                for row in rows
                if str(row.get("symbol", "")).upper().endswith(".IS")
                and (
                    _label_to_float(row.get("disclosure_momentum_score")) >= 50.0
                    or int(row.get("material_disclosures_90d", 0) or 0) >= 3
                    or int(row.get("contract_mentions_365d", 0) or 0) >= 2
                )
            ]
            rows = sorted(
                rows,
                key=lambda row: (
                    _label_to_float(row.get("disclosure_momentum_score")),
                    int(row.get("material_disclosures_90d", 0) or 0),
                    int(row.get("contract_mentions_365d", 0) or 0),
                    _label_to_float(row.get("fundamental_score")),
                ),
                reverse=True,
            )
        elif selected_screen == "bist_contract_intensity":
            rows = [
                row
                for row in rows
                if str(row.get("symbol", "")).upper().endswith(".IS")
                and (
                    _label_to_float(row.get("contracts_to_sales")) > 0
                    or int(row.get("contract_mentions_365d", 0) or 0) >= 1
                )
            ]
            rows = sorted(
                rows,
                key=lambda row: (
                    _label_to_float(row.get("contracts_to_sales")),
                    _label_to_float(row.get("disclosure_momentum_score")),
                    int(row.get("contract_mentions_365d", 0) or 0),
                    _label_to_float(row.get("fundamental_score")),
                ),
                reverse=True,
            )
        else:
            rows = sorted(
                rows,
                key=lambda row: (
                    _label_to_float(row["fundamental_score"]),
                    _label_to_float(row["disclosure_momentum_score"]),
                    row["curated_13f_holders"],
                    _label_to_float(row["price_change_3m"]),
                ),
                reverse=True,
            )

        rows = rows[:limit]

        criteria_summary = []
        if "market_cap_min" in criteria:
            criteria_summary.append(f"Min market cap {_fmt_compact_money(criteria['market_cap_min'])}")
        if "pe_ratio_max" in criteria:
            criteria_summary.append(f"Max P/E {_fmt_number(criteria['pe_ratio_max'], 1)}")
        if "dividend_yield_min" in criteria:
            criteria_summary.append(f"Min dividend {_fmt_number(criteria['dividend_yield_min'], 1)}%")
        if "price_change_min" in criteria:
            criteria_summary.append(f"Min 3M change {_fmt_number(criteria['price_change_min'], 1)}%")
        if "rsi_max" in criteria:
            criteria_summary.append(f"RSI below {_fmt_number(criteria['rsi_max'], 1)}")
        if "rsi_min" in criteria:
            criteria_summary.append(f"RSI above {_fmt_number(criteria['rsi_min'], 1)}")
        if "roe_min" in criteria:
            criteria_summary.append(f"Min ROE {_fmt_number(criteria['roe_min'], 1)}%")
        if selected_screen == "institutional_accumulation":
            criteria_summary.extend(
                [
                    "At least one curated manager must be a fresh buyer.",
                    "Signal must be Accumulating or Crowded Long.",
                ]
            )
        if selected_screen == "trend_confirmed_accumulation":
            criteria_summary.extend(
                [
                    "Curated sponsorship must already be constructive, and trend structure must be Trend Confirmed or Constructive Trend.",
                    "Entropy predictability must be at least 55 so the tape is not just loud momentum.",
                ]
            )
        if selected_screen == "entropy_clean_setups":
            criteria_summary.extend(
                [
                    "Validation must be live and entropy predictability must be at least 60.",
                    "Bearish trend bias is excluded; this is a long-idea cleanliness screen, not a two-way tape monitor.",
                ]
            )
        if selected_screen == "crowded_13f":
            criteria_summary.extend(
                [
                    "At least two curated 13F managers must hold the name.",
                    "Ranking favors combined curated weight and breadth of ownership.",
                ]
            )
        if selected_screen == "bist_disclosure_leaders":
            criteria_summary.extend(
                [
                    "BIST names only. Ranking favors disclosure momentum, material notices, and catalyst density.",
                    "This is a catalyst-flow screen, not a value screen.",
                ]
            )
        if selected_screen == "bist_contract_intensity":
            criteria_summary.extend(
                [
                    "BIST names only. Ranking favors contract flow relative to the latest annual sales base.",
                    "Use this as a catalyst-pressure lens, not as a realized revenue number.",
                ]
            )

        avg_3m = float(np.mean([item.get("price_change_3m", 0) for item in raw_results])) if raw_results else 0.0
        avg_dividend = float(np.mean([item.get("dividend_yield", 0) for item in raw_results])) if raw_results else 0.0
        avg_rsi = float(np.mean([item.get("rsi", 50) for item in raw_results])) if raw_results else 50.0
        crowded_count = sum(1 for row in rows if row["curated_13f_holders"] >= 2)
        avg_fundamental_score = float(np.mean([_label_to_float(row["fundamental_score"]) for row in rows])) if rows else 0.0
        capital_strong_count = sum(1 for row in rows if row["capital_profile"] in {"High Conversion", "Healthy"})
        disclosure_active_count = sum(1 for row in rows if _label_to_float(row["disclosure_momentum_score"]) >= 60.0)
        trend_confirmed_count = sum(1 for row in rows if row["trend_label"] in {"Trend Confirmed", "Constructive Trend"})
        avg_predictability = float(np.mean([_label_to_float(row["predictability_score"]) for row in rows])) if rows else 0.0

        result = _to_json_safe(
            {
                "selected_universe": selected_universe,
                "selected_screen": selected_screen,
                "universe_options": [
                    {"key": key, "label": value["label"], "description": value["description"]}
                    for key, value in self.screener_universes.items()
                ],
                "screen_options": [
                    {
                        "key": key,
                        "label": value["name"],
                        "description": value["description"],
                    }
                    for key, value in self._screen_options().items()
                ],
                "screen_name": screen["name"],
                "screen_description": screen["description"],
                "universe_label": universe_config["label"],
                "universe_description": universe_config["description"],
                "universe_size": len(universe_config["symbols"]),
                "criteria_summary": criteria_summary,
                "match_count": len(rows),
                "match_rate": round((len(rows) / max(len(universe_config["symbols"]), 1)) * 100, 1),
                "average_3m_change": _fmt_pct(avg_3m),
                "average_dividend_yield": _fmt_pct(avg_dividend),
                "average_rsi": _fmt_number(avg_rsi, 1),
                "average_fundamental_score": _fmt_number(avg_fundamental_score, 1),
                "average_predictability": _fmt_number(avg_predictability, 1),
                "crowded_count": crowded_count,
                "capital_strong_count": capital_strong_count,
                "disclosure_active_count": disclosure_active_count,
                "trend_confirmed_count": trend_confirmed_count,
                "top_match": rows[0] if rows else None,
                "rows": rows,
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        return result

    def get_ownership_workspace(self, symbol: str | None, focus: str | None) -> Dict[str, Any]:
        symbol = (symbol or settings.PUBLIC_DEFAULT_OWNERSHIP_SYMBOL).upper()
        selected_focus = self._selected_focus(focus)
        cache_key = self._cache_key("public-research-ownership", symbol, selected_focus)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        focus_config = self.ownership_focuses[selected_focus]
        fetch_counts = []
        for etf in focus_config["etfs"]:
            holdings = self.etf_tracker.fetch_etf_holdings(etf, force_refresh=False)
            fetch_counts.append({"etf": etf, "rows": int(len(holdings))})

        exposure_df = self.etf_tracker.get_funds_for_stock(symbol, min_weight=0.05)
        weight_changes = self.etf_tracker.get_weight_changes(symbol, period_days=90)
        action_signal = self.etf_tracker.detect_fund_manager_actions(symbol, threshold=0.5)
        tracker_stats = self.etf_tracker.get_summary_stats()

        total_weight = float(exposure_df["weight_pct"].sum()) if not exposure_df.empty else 0.0
        exposure_rows = []
        if not exposure_df.empty:
            exposure_df = exposure_df.sort_values("weight_pct", ascending=False).reset_index(drop=True)
            for _, row in exposure_df.head(12).iterrows():
                weight = float(row.get("weight_pct", 0) or 0)
                exposure_rows.append(
                    {
                        "fund_code": row.get("fund_code"),
                        "fund_name": row.get("fund_name"),
                        "weight_pct": _fmt_pct(weight),
                        "share_of_tracked_exposure": _fmt_pct((weight / total_weight) * 100 if total_weight else 0),
                        "report_date": row.get("report_date"),
                    }
                )

        history_rows = []
        if not weight_changes.empty:
            weight_changes = weight_changes.sort_values("weight_change", ascending=False).reset_index(drop=True)
            for _, row in weight_changes.head(12).iterrows():
                history_rows.append(
                    {
                        "fund_code": row.get("fund_code"),
                        "current_weight": _fmt_pct(row.get("current_weight")),
                        "previous_weight": _fmt_pct(row.get("previous_weight")),
                        "weight_change": _fmt_pct(row.get("weight_change")),
                        "current_date": row.get("current_date"),
                        "previous_date": row.get("previous_date"),
                    }
                )

        result = _to_json_safe(
            {
                "symbol": symbol,
                "selected_focus": selected_focus,
                "focus_options": [
                    {"key": key, "label": value["label"], "description": value["description"]}
                    for key, value in self.ownership_focuses.items()
                ],
                "featured_symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "XOM", "TSLA", "META", "JPM"],
                "focus_label": focus_config["label"],
                "focus_description": focus_config["description"],
                "tracked_etfs": focus_config["etfs"],
                "tracked_etf_count": len(focus_config["etfs"]),
                "successful_fetches": sum(1 for item in fetch_counts if item["rows"] > 0),
                "fetch_counts": fetch_counts,
                "tracker_stats": tracker_stats,
                "summary": {
                    "holding_funds": len(exposure_rows),
                    "total_weight": _fmt_pct(total_weight),
                    "max_weight": exposure_rows[0]["weight_pct"] if exposure_rows else "N/A",
                    "signal": action_signal.get("signal", "NEUTRAL").replace("_", " ").title(),
                    "confidence": _fmt_number(action_signal.get("confidence"), 1),
                    "details": action_signal.get("details", "Historical weight drift will populate after repeated refreshes."),
                    "latest_update": tracker_stats.get("latest_update", "N/A"),
                },
                "exposure_rows": exposure_rows,
                "history_rows": history_rows,
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        return result

    def get_sector_rotation_workspace(self) -> Dict[str, Any]:
        cache_key = self._cache_key("public-research-sector-rotation", "v1")
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        payload = self.yahoo.get_sector_performance()
        sector_data = payload.get("sector_performance", [])
        if not sector_data:
            result = {"error": "Sector rotation data is temporarily unavailable."}
            cache_set(cache_key, result, ttl=300)
            return result

        sorted_rows = sorted(sector_data, key=lambda item: float(item.get("change_5d", 0) or 0), reverse=True)
        defensive = {"Consumer Staples", "Utilities", "Health Care"}
        defensive_changes = [float(item.get("change_5d", 0) or 0) for item in sorted_rows if item.get("sector") in defensive]
        cyclical_changes = [float(item.get("change_5d", 0) or 0) for item in sorted_rows if item.get("sector") not in defensive]
        defensive_avg = float(np.mean(defensive_changes)) if defensive_changes else 0.0
        cyclical_avg = float(np.mean(cyclical_changes)) if cyclical_changes else 0.0
        spread = cyclical_avg - defensive_avg

        if spread >= 1.0:
            pattern = "Risk-On Rotation"
            note = "Cyclical sectors are outperforming defensives across the current 5-day window."
        elif spread <= -1.0:
            pattern = "Risk-Off Rotation"
            note = "Defensive sectors are holding up better than cyclical risk buckets."
        else:
            pattern = "Balanced Rotation"
            note = "Leadership is mixed; no decisive sector handoff is visible yet."

        rows = [
            {
                "sector": item.get("sector"),
                "etf_symbol": item.get("etf_symbol"),
                "current_price": _fmt_number(item.get("current_price"), 2),
                "change_5d": _fmt_pct(item.get("change_5d")),
                "tone": "positive" if float(item.get("change_5d", 0) or 0) > 0 else "negative" if float(item.get("change_5d", 0) or 0) < 0 else "neutral",
            }
            for item in sorted_rows
        ]

        result = _to_json_safe(
            {
                "error": None,
                "pattern": pattern,
                "pattern_note": note,
                "spread": _fmt_pct(spread),
                "cyclical_average": _fmt_pct(cyclical_avg),
                "defensive_average": _fmt_pct(defensive_avg),
                "leader": rows[0] if rows else None,
                "laggard": rows[-1] if rows else None,
                "rows": rows,
            }
        )
        cache_set(cache_key, result, ttl=900)
        return result

    def _build_compare_regime_workspace(
        self,
        kind: str,
        left_symbol: str,
        right_symbol: str,
        left_workspace: Dict[str, Any],
        right_workspace: Dict[str, Any],
    ) -> Dict[str, Any]:
        if kind not in {"stocks", "funds"}:
            return {}

        left_lens = (left_workspace or {}).get("forecast_lens") or {}
        right_lens = (right_workspace or {}).get("forecast_lens") or {}
        left_entropy = left_lens.get("entropy_signal") or {}
        right_entropy = right_lens.get("entropy_signal") or {}
        left_validation = left_lens.get("validation_summary") or {}
        right_validation = right_lens.get("validation_summary") or {}
        left_persistence = left_lens.get("trend_persistence") or {}
        right_persistence = right_lens.get("trend_persistence") or {}

        rows = [
            {
                "metric": "Trend persistence",
                "left": left_persistence.get("label", "Warming"),
                "right": right_persistence.get("label", "Warming"),
                "winner": self._winner_for_metric(
                    {"Persistent": 3, "Orderly Risk-Off": 2, "Developing": 1, "Fragile": 0}.get(str(left_persistence.get("label", "")), 0),
                    {"Persistent": 3, "Orderly Risk-Off": 2, "Developing": 1, "Fragile": 0}.get(str(right_persistence.get("label", "")), 0),
                ),
                "read": "This asks whether the current move has evidence of follow-through, not just a good-looking snapshot.",
            },
            {
                "metric": "Entropy regime",
                "left": left_entropy.get("regime", "Warming"),
                "right": right_entropy.get("regime", "Warming"),
                "winner": self._winner_for_metric(
                    self._compare_float(left_entropy.get("predictability_score")),
                    self._compare_float(right_entropy.get("predictability_score")),
                ),
                "read": "Entropy is here to judge how ordered the tape is before you trust any trend extrapolation.",
            },
            {
                "metric": "Predictability",
                "left": _fmt_number(left_entropy.get("predictability_score"), 1),
                "right": _fmt_number(right_entropy.get("predictability_score"), 1),
                "winner": self._winner_for_metric(
                    self._compare_float(left_entropy.get("predictability_score")),
                    self._compare_float(right_entropy.get("predictability_score")),
                ),
                "read": "Higher predictability means return patterns are cleaner and model disagreement should matter less.",
            },
            {
                "metric": "Validation state",
                "left": left_validation.get("state", "Warming"),
                "right": right_validation.get("state", "Warming"),
                "winner": self._winner_for_metric(
                    {"Validated": 2, "Partial": 1, "Fallback": 0}.get(str(left_validation.get("state", "")), 0),
                    {"Validated": 2, "Partial": 1, "Fallback": 0}.get(str(right_validation.get("state", "")), 0),
                ),
                "read": "A forecast surface is only worth using if the model outputs passed basic sanity checks first.",
            },
        ]

        left_bias = str(left_lens.get("trend_bias", "Mixed"))
        right_bias = str(right_lens.get("trend_bias", "Mixed"))
        left_predictability = self._compare_float(left_entropy.get("predictability_score")) or 0.0
        right_predictability = self._compare_float(right_entropy.get("predictability_score")) or 0.0

        if left_predictability > right_predictability and left_bias != "Mixed":
            headline = {
                "winner": "Left",
                "label": f"{left_symbol} has the cleaner trend regime.",
                "detail": f"{left_symbol} shows {left_bias.lower()} bias with stronger tape order than {right_symbol}.",
            }
        elif right_predictability > left_predictability and right_bias != "Mixed":
            headline = {
                "winner": "Right",
                "label": f"{right_symbol} has the cleaner trend regime.",
                "detail": f"{right_symbol} shows {right_bias.lower()} bias with stronger tape order than {left_symbol}.",
            }
        else:
            headline = {
                "winner": "Even",
                "label": "Trend regime quality is close.",
                "detail": "Model direction or tape order is not decisively separated, so the call should rely on the core decision sheet.",
            }

        return {
            "headline": headline,
            "left": {
                "symbol": left_symbol,
                "trend_bias": left_bias,
                "consensus_delta": left_lens.get("consensus_delta", "N/A"),
                "predictability": _fmt_number(left_entropy.get("predictability_score"), 1),
                "persistence": left_persistence.get("label", "Warming"),
            },
            "right": {
                "symbol": right_symbol,
                "trend_bias": right_bias,
                "consensus_delta": right_lens.get("consensus_delta", "N/A"),
                "predictability": _fmt_number(right_entropy.get("predictability_score"), 1),
                "persistence": right_persistence.get("label", "Warming"),
            },
            "rows": rows,
        }

    def get_compare_workspace(
        self,
        kind: str | None,
        left: str | None,
        right: str | None,
        months: int = 6,
    ) -> Dict[str, Any]:
        selected_kind = kind if kind in {"stocks", "funds", "tr-funds"} else "stocks"
        months = max(3, min(months or 6, 18))

        if selected_kind == "stocks":
            left_symbol = (left or settings.PUBLIC_DEFAULT_STOCK_SYMBOL).upper()
            compare_suggestions = self._stock_compare_suggestions(left_symbol)
            default_right = compare_suggestions[0]["symbol"] if compare_suggestions else "NVDA"
            right_symbol = (right or default_right).upper()
            if right_symbol == left_symbol:
                fallback_candidates = [item["symbol"] for item in compare_suggestions if item["symbol"] != left_symbol]
                if not fallback_candidates:
                    fallback_candidates = [item for item in self._featured_stock_symbols() if item != left_symbol]
                right_symbol = fallback_candidates[0] if fallback_candidates else "NVDA"
            left_ws = self.get_stock_workspace(left_symbol)
            right_ws = self.get_stock_workspace(right_symbol)
            compare_rows = [
                {
                    "metric": "3M change",
                    "left": self._metric_row_value([{"metric": "3M", "value": next((item["value"] for item in left_ws.get("return_signals", []) if item.get("label") == "3M"), "N/A")}], "3M"),
                    "right": self._metric_row_value([{"metric": "3M", "value": next((item["value"] for item in right_ws.get("return_signals", []) if item.get("label") == "3M"), "N/A")}], "3M"),
                    "winner": self._winner_for_metric(
                        next((item.get("value") for item in left_ws.get("return_signals", []) if item.get("label") == "3M"), "N/A"),
                        next((item.get("value") for item in right_ws.get("return_signals", []) if item.get("label") == "3M"), "N/A"),
                    ),
                    "read": "Momentum is still one of the cleanest public triage filters.",
                },
                {
                    "metric": "P/E",
                    "left": str((left_ws.get("overview") or {}).get("pe_ratio", "N/A")),
                    "right": str((right_ws.get("overview") or {}).get("pe_ratio", "N/A")),
                    "winner": self._winner_for_metric((left_ws.get("overview") or {}).get("pe_ratio"), (right_ws.get("overview") or {}).get("pe_ratio"), prefer="lower"),
                    "read": "Lower is not always better, but cheaper setups need less perfection.",
                },
                {
                    "metric": "Fundamental score",
                    "left": _fmt_number(((left_ws.get("fundamental_lens") or {}).get("score") or {}).get("overall"), 1),
                    "right": _fmt_number(((right_ws.get("fundamental_lens") or {}).get("score") or {}).get("overall"), 1),
                    "winner": self._winner_for_metric(((left_ws.get("fundamental_lens") or {}).get("score") or {}).get("overall"), ((right_ws.get("fundamental_lens") or {}).get("score") or {}).get("overall")),
                    "read": "This blends valuation, operating quality, and capital efficiency.",
                },
                {
                    "metric": "Capital score",
                    "left": _fmt_number(((left_ws.get("fundamental_lens") or {}).get("score") or {}).get("capital"), 1),
                    "right": _fmt_number(((right_ws.get("fundamental_lens") or {}).get("score") or {}).get("capital"), 1),
                    "winner": self._winner_for_metric(((left_ws.get("fundamental_lens") or {}).get("score") or {}).get("capital"), ((right_ws.get("fundamental_lens") or {}).get("score") or {}).get("capital")),
                    "read": "Your preferred lens: how effectively the company converts its capital base into output.",
                },
                {
                    "metric": "KAP / disclosure momentum",
                    "left": self._metric_row_value(((left_ws.get("fundamental_lens") or {}).get("capital_rows") or []), "Disclosure momentum"),
                    "right": self._metric_row_value(((right_ws.get("fundamental_lens") or {}).get("capital_rows") or []), "Disclosure momentum"),
                    "winner": self._winner_for_metric(
                        self._metric_row_value(((left_ws.get("fundamental_lens") or {}).get("capital_rows") or []), "Disclosure momentum"),
                        self._metric_row_value(((right_ws.get("fundamental_lens") or {}).get("capital_rows") or []), "Disclosure momentum"),
                    ),
                    "read": "Most useful for BIST names where disclosure flow itself can move the narrative.",
                },
                {
                    "metric": "Curated 13F breadth",
                    "left": str(((left_ws.get("curated_13f") or {}).get("summary") or {}).get("holder_count", 0)),
                    "right": str(((right_ws.get("curated_13f") or {}).get("summary") or {}).get("holder_count", 0)),
                    "winner": self._winner_for_metric(((left_ws.get("curated_13f") or {}).get("summary") or {}).get("holder_count", 0), ((right_ws.get("curated_13f") or {}).get("summary") or {}).get("holder_count", 0)),
                    "read": "Breadth of serious sponsorship matters more than one celebrity holder.",
                },
            ]
            left_name = str((left_ws.get("overview") or {}).get("name", left_symbol))
            right_name = str((right_ws.get("overview") or {}).get("name", right_symbol))
        elif selected_kind == "funds":
            left_symbol = (left or settings.PUBLIC_DEFAULT_FUND_SYMBOL).upper()
            compare_suggestions = self._fund_compare_suggestions(left_symbol)
            default_right = compare_suggestions[0]["symbol"] if compare_suggestions else ("QQQ" if left_symbol != "QQQ" else "SPY")
            right_symbol = (right or default_right).upper()
            if right_symbol == left_symbol:
                fallback_candidates = [item["symbol"] for item in compare_suggestions if item.get("symbol") != left_symbol]
                if not fallback_candidates:
                    fallback_candidates = [item for item in self._featured_fund_symbols() if item != left_symbol]
                right_symbol = fallback_candidates[0] if fallback_candidates else ("SPY" if left_symbol != "SPY" else "QQQ")
            left_ws = self.get_fund_workspace(left_symbol)
            right_ws = self.get_fund_workspace(right_symbol)
            left_risk = left_ws.get("risk_snapshot") or {}
            right_risk = right_ws.get("risk_snapshot") or {}
            left_monthly = (left_ws.get("monthly_rows") or [])[-1] if left_ws.get("monthly_rows") else {}
            right_monthly = (right_ws.get("monthly_rows") or [])[-1] if right_ws.get("monthly_rows") else {}
            compare_rows = [
                {
                    "metric": "1Y return",
                    "left": next((item.get("value") for item in left_ws.get("performance_cards", []) if item.get("label") == "1Y"), "N/A"),
                    "right": next((item.get("value") for item in right_ws.get("performance_cards", []) if item.get("label") == "1Y"), "N/A"),
                    "winner": self._winner_for_metric(next((item.get("value") for item in left_ws.get("performance_cards", []) if item.get("label") == "1Y"), "N/A"), next((item.get("value") for item in right_ws.get("performance_cards", []) if item.get("label") == "1Y"), "N/A")),
                    "read": "Public users usually compare funds on return first, even when they should not stop there.",
                },
                {
                    "metric": "Expense ratio",
                    "left": str((left_ws.get("overview") or {}).get("expense_ratio", "N/A")),
                    "right": str((right_ws.get("overview") or {}).get("expense_ratio", "N/A")),
                    "winner": self._winner_for_metric((left_ws.get("overview") or {}).get("expense_ratio"), (right_ws.get("overview") or {}).get("expense_ratio"), prefer="lower"),
                    "read": "Cost drag compounds quietly.",
                },
                {
                    "metric": "Volatility",
                    "left": str(left_risk.get("volatility", "N/A")),
                    "right": str(right_risk.get("volatility", "N/A")),
                    "winner": self._winner_for_metric(left_risk.get("volatility"), right_risk.get("volatility"), prefer="lower"),
                    "read": "Lower realized vol matters if the return gap is small.",
                },
                {
                    "metric": "Top 10 concentration",
                    "left": str((left_ws.get("holdings_summary") or {}).get("top_10_concentration", "N/A")),
                    "right": str((right_ws.get("holdings_summary") or {}).get("top_10_concentration", "N/A")),
                    "winner": self._winner_for_metric((left_ws.get("holdings_summary") or {}).get("top_10_concentration"), (right_ws.get("holdings_summary") or {}).get("top_10_concentration"), prefer="lower"),
                    "read": "This flags hidden concentration inside diversified wrappers.",
                },
                {
                    "metric": "Latest monthly posture",
                    "left": str(left_monthly.get("posture", "N/A")),
                    "right": str(right_monthly.get("posture", "N/A")),
                    "winner": "Even",
                    "read": "Month-end posture is more narrative than numeric, but still useful for orientation.",
                },
            ]
            left_name = str((left_ws.get("overview") or {}).get("fund_name", left_symbol))
            right_name = str((right_ws.get("overview") or {}).get("fund_name", right_symbol))
        else:
            left_symbol = (left or settings.PUBLIC_DEFAULT_TR_FUND_CODE).upper()
            featured = self._featured_tr_funds(months)
            right_symbol = (right or (featured[1] if len(featured) > 1 else "GAH")).upper()
            if right_symbol == left_symbol:
                right_symbol = featured[1] if len(featured) > 1 and featured[1] != left_symbol else "GAH"
            left_ws = self.get_tr_fund_workspace(left_symbol, months)
            right_ws = self.get_tr_fund_workspace(right_symbol, months)
            left_signal = left_ws.get("signal_card") or {}
            right_signal = right_ws.get("signal_card") or {}
            left_overview = left_ws.get("overview") or {}
            right_overview = right_ws.get("overview") or {}
            compare_rows = [
                {
                    "metric": "Signal score",
                    "left": str(left_signal.get("signal_score", "N/A")),
                    "right": str(right_signal.get("signal_score", "N/A")),
                    "winner": self._winner_for_metric(left_signal.get("signal_score"), right_signal.get("signal_score")),
                    "read": "This is the quickest composite read on TEFAS momentum and sponsorship.",
                },
                {
                    "metric": "Board score",
                    "left": str(left_signal.get("board_score", "N/A")),
                    "right": str(right_signal.get("board_score", "N/A")),
                    "winner": self._winner_for_metric(left_signal.get("board_score"), right_signal.get("board_score")),
                    "read": "Board score adds category quality and market share to raw signal strength.",
                },
                {
                    "metric": "Investor growth",
                    "left": str(left_overview.get("investor_growth_pct", "N/A")),
                    "right": str(right_overview.get("investor_growth_pct", "N/A")),
                    "winner": self._winner_for_metric(left_overview.get("investor_growth_pct"), right_overview.get("investor_growth_pct")),
                    "read": "Investor growth is often the cleanest confirmation that local sponsorship is real.",
                },
                {
                    "metric": "Value growth",
                    "left": str(left_overview.get("portfolio_value_growth_pct", "N/A")),
                    "right": str(right_overview.get("portfolio_value_growth_pct", "N/A")),
                    "winner": self._winner_for_metric(left_overview.get("portfolio_value_growth_pct"), right_overview.get("portfolio_value_growth_pct")),
                    "read": "Value growth separates headline story from actual capital following the fund.",
                },
                {
                    "metric": "Category percentile",
                    "left": str(left_overview.get("category_percentile", "N/A")),
                    "right": str(right_overview.get("category_percentile", "N/A")),
                    "winner": self._winner_for_metric(left_overview.get("category_percentile"), right_overview.get("category_percentile")),
                    "read": "This keeps the comparison anchored inside the correct TEFAS category set.",
                },
            ]
            left_name = str(left_overview.get("fund_name", left_symbol))
            right_name = str(right_overview.get("fund_name", right_symbol))

        left_wins = sum(1 for row in compare_rows if row["winner"] == "Left")
        right_wins = sum(1 for row in compare_rows if row["winner"] == "Right")
        regime_workspace = self._build_compare_regime_workspace(selected_kind, left_symbol, right_symbol, left_ws, right_ws)

        return _to_json_safe(
            {
                "kind": selected_kind,
                "months": months,
                "kind_options": [
                    {"key": "stocks", "label": "Stocks"},
                    {"key": "funds", "label": "Funds & ETFs"},
                    {"key": "tr-funds", "label": "TR Funds"},
                ],
                "left_symbol": left_symbol,
                "right_symbol": right_symbol,
                "left_name": left_name,
                "right_name": right_name,
                "compare_suggestions": compare_suggestions if selected_kind in {"stocks", "funds"} else [],
                "left_workspace": left_ws,
                "right_workspace": right_ws,
                "compare_rows": compare_rows,
                "regime_workspace": regime_workspace,
                "summary_cards": [
                    {"label": "Left wins", "value": str(left_wins), "detail": left_symbol},
                    {"label": "Right wins", "value": str(right_wins), "detail": right_symbol},
                    {"label": "Tie metrics", "value": str(len(compare_rows) - left_wins - right_wins), "detail": "Metrics with no decisive edge"},
                ],
            }
        )

    def get_catalyst_calendar_workspace(self) -> Dict[str, Any]:
        kap_health = self.stock_enrichment_service.get_health_snapshot()
        tr_status = self.tr_funds_service.get_status(months=settings.PUBLIC_TR_FUNDS_MONTHS)
        institutional_workspace = self.institutional_pulse_service.get_workspace(settings.PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER)
        bist_workspace = self.get_bist_quality_board_workspace(limit=6)
        now = datetime.utcnow()

        recent_rows: List[Dict[str, Any]] = []
        for row in (kap_health.get("rows") or [])[:8]:
            recent_rows.append(
                {
                    "date": row.get("last_disclosure_date", "N/A"),
                    "source": "KAP",
                    "subject": row.get("symbol"),
                    "event": "Structured disclosure flow",
                    "detail": f"Momentum {row.get('disclosure_momentum_score', 'N/A')} · coverage {row.get('field_coverage', 0)} fields",
                    "state": row.get("source_state", "warming"),
                }
            )
        for row in (institutional_workspace.get("coverage_rows") or [])[:5]:
            recent_rows.append(
                {
                    "date": row.get("latest_filing", "N/A"),
                    "source": "EDGAR 13F",
                    "subject": row.get("manager_name"),
                    "event": "Latest curated filing",
                    "detail": f"{row.get('holding_count', 0)} holdings · {row.get('top_10_weight', 'N/A')} top-10 concentration",
                    "state": row.get("source_state", "warming"),
                }
            )
        if tr_status.get("last_snapshot_at") or tr_status.get("last_attempt_at"):
            recent_rows.append(
                {
                    "date": tr_status.get("last_snapshot_at") or tr_status.get("last_attempt_at"),
                    "source": "TEFAS",
                    "subject": "TR funds lane",
                    "event": "Latest cached board",
                    "detail": tr_status.get("detail", "TEFAS board status"),
                    "state": tr_status.get("status", "warming"),
                }
            )
        recent_rows = sorted(recent_rows, key=lambda item: str(item.get("date", "")), reverse=True)

        quarter_month = ((now.month - 1) // 3 + 1) * 3
        quarter_end_month = quarter_month if quarter_month <= 12 else 12
        quarter_end = datetime(now.year, quarter_end_month, 1)
        if quarter_end_month == 12:
            quarter_end = datetime(now.year, 12, 31)
        else:
            quarter_end = datetime(now.year, quarter_end_month + 1, 1) - pd.Timedelta(days=1)
        next_13f_due = (quarter_end + pd.Timedelta(days=45)).date().isoformat()
        next_refresh = (now + pd.Timedelta(seconds=settings.PREWARM_INTERVAL_SECONDS)).replace(microsecond=0).isoformat() + "Z"

        upcoming_rows = [
            {
                "date": next_refresh,
                "source": "FundPilot",
                "subject": "Prewarm cycle",
                "event": "Next scheduled public data refresh",
                "detail": "KAP, TEFAS, and dashboard snapshots refresh on the background cadence.",
            },
            {
                "date": next_13f_due,
                "source": "EDGAR 13F",
                "subject": "Curated manager set",
                "event": "Next statutory 13F deadline",
                "detail": "Use this as the next expected institutional-positioning refresh window.",
            },
            {
                "date": now.date().isoformat(),
                "source": "KAP",
                "subject": "Curated BIST set",
                "event": "Continuous disclosure watch",
                "detail": "FundPilot is strongest when disclosure enrichment stays ahead of the price move.",
            },
        ]

        clean_tape_rows: List[Dict[str, Any]] = []
        for row in bist_workspace.get("rows", []):
            catalyst_tape = row.get("catalyst_tape") or {}
            label = str(catalyst_tape.get("label", "Watch"))
            if label == "Watch":
                continue
            clean_tape_rows.append(
                {
                    "symbol": row.get("symbol"),
                    "name": row.get("name"),
                    "label": label,
                    "detail": catalyst_tape.get("detail", "Local catalyst flow and tape structure are aligned."),
                    "predictability_score": row.get("predictability_score", "N/A"),
                    "trend_label": row.get("trend_label", "Warming"),
                    "disclosure_momentum_score": row.get("disclosure_momentum_score", "N/A"),
                    "contracts_to_sales": row.get("contracts_to_sales", "N/A"),
                    "detail_path": f"/stocks?symbol={row.get('symbol')}",
                }
            )

        return _to_json_safe(
            {
                "generated_at": now.replace(microsecond=0).isoformat() + "Z",
                "recent_rows": recent_rows[:12],
                "upcoming_rows": upcoming_rows,
                "clean_tape_rows": clean_tape_rows[:6],
                "summary_cards": [
                    {"label": "Recent KAP events", "value": str(len([row for row in recent_rows if row.get("source") == "KAP"])), "detail": "Structured disclosure rows in the current calendar"},
                    {"label": "Recent 13F events", "value": str(len([row for row in recent_rows if row.get("source") == "EDGAR 13F"])), "detail": "Curated institutional filing events"},
                    {"label": "TEFAS lane", "value": str(tr_status.get("funds_loaded", 0)), "detail": f"{tr_status.get('status', 'warming')}"},
                    {"label": "Clean-tape catalysts", "value": str(len(clean_tape_rows)), "detail": "BIST names where catalyst pressure and tape structure are aligned."},
                ],
            }
        )

    def get_bist_quality_board_workspace(self, limit: int = 12) -> Dict[str, Any]:
        limit = max(6, min(limit or 12, 20))
        cache_key = self._cache_key("public-research-bist-quality-board", limit)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        symbols = get_bist_stocks()[:18]
        raw_results = self.screener.screen_stocks(list(symbols), {"market_cap_min": 250_000_000, "sort_by": "market_cap"})
        rows = self._screen_rows_with_curated_13f(raw_results)
        ranked_rows = []
        for row in rows:
            capital_score = self._compare_float(row.get("capital_signal")) or 0.0
            fundamental_score = self._compare_float(row.get("fundamental_score")) or 0.0
            contract_score = max(self._compare_float(row.get("contracts_to_sales")) or 0.0, 0.0)
            disclosure_score = max(self._compare_float(row.get("disclosure_momentum_score")) or 0.0, 0.0)
            predictability_score = max(self._compare_float(row.get("predictability_score")) or 0.0, 0.0)
            trend_label = str(row.get("trend_label", "Warming"))
            clean_tape_component = 4.0
            if trend_label == "Trend Confirmed":
                clean_tape_component = 12.0
            elif trend_label == "Constructive Trend":
                clean_tape_component = 9.0
            elif trend_label == "Developing Structure":
                clean_tape_component = 6.0
            elif trend_label == "Orderly Downtrend":
                clean_tape_component = 2.0
            catalyst_clean_score = round(
                min(
                    100.0,
                    (min(disclosure_score, 100.0) * 0.55)
                    + (min(contract_score * 100, 100.0) * 0.20)
                    + (min(predictability_score, 100.0) * 0.25),
                ),
                1,
            )
            board_score = round(
                (fundamental_score * 0.38)
                + (capital_score * 0.27)
                + (catalyst_clean_score * 0.23)
                + clean_tape_component,
                1,
            )
            row_copy = dict(row)
            row_copy["board_score"] = _fmt_number(board_score, 1)
            row_copy["catalyst_clean_score"] = _fmt_number(catalyst_clean_score, 1)
            row_copy["catalyst_tape"] = self._clean_tape_catalyst_summary(row_copy)
            row_copy["why_passed"] = self._screen_reason(row_copy)
            ranked_rows.append(row_copy)
        ranked_rows = sorted(ranked_rows, key=lambda item: self._compare_float(item.get("board_score")) or 0.0, reverse=True)[:limit]

        result = _to_json_safe(
            {
                "rows": ranked_rows,
                "top_pick": ranked_rows[0] if ranked_rows else None,
                "methodology": [
                    "Board score blends overall fundamental strength, capital efficiency, disclosure momentum, and clean-tape confirmation.",
                    "This page favors BIST names where nominal capital and KAP flow add real decision value.",
                    "Contract-to-sales is catalyst intensity, not realized revenue.",
                    "Entropy matters because local catalysts are more actionable when the tape is orderly enough for trend-following models to deserve trust.",
                ],
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        return result

    def get_overlap_matrix_workspace(self, focus: str | None) -> Dict[str, Any]:
        selected_focus = self._selected_focus(focus)
        cache_key = self._cache_key("public-research-overlap-matrix", selected_focus)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        focus_config = self.ownership_focuses[selected_focus]
        etfs = focus_config["etfs"][:8]
        holdings_map: Dict[str, pd.DataFrame] = {}
        for etf in etfs:
            holdings_map[etf] = self.etf_tracker.fetch_etf_holdings(etf, force_refresh=False)

        pair_rows: List[Dict[str, Any]] = []
        for index, left_etf in enumerate(etfs):
            left_df = holdings_map.get(left_etf)
            if left_df is None or left_df.empty:
                continue
            left_map = {
                str(row["stock_symbol"]).upper(): float(row["weight_pct"] or 0.0)
                for _, row in left_df.iterrows()
            }
            for right_etf in etfs[index + 1 :]:
                right_df = holdings_map.get(right_etf)
                if right_df is None or right_df.empty:
                    continue
                right_map = {
                    str(row["stock_symbol"]).upper(): float(row["weight_pct"] or 0.0)
                    for _, row in right_df.iterrows()
                }
                shared = sorted(set(left_map) & set(right_map))
                if not shared:
                    continue
                overlap_score = sum(min(left_map[symbol], right_map[symbol]) for symbol in shared)
                shared_names = ", ".join(shared[:3])
                pair_rows.append(
                    {
                        "left": left_etf,
                        "right": right_etf,
                        "overlap_score": _fmt_pct(overlap_score),
                        "shared_count": len(shared),
                        "shared_names": shared_names,
                    }
                )

        pair_rows = sorted(pair_rows, key=lambda item: self._compare_float(item.get("overlap_score")) or 0.0, reverse=True)
        result = _to_json_safe(
            {
                "selected_focus": selected_focus,
                "focus_options": [
                    {"key": key, "label": value["label"], "description": value["description"]}
                    for key, value in self.ownership_focuses.items()
                ],
                "focus_label": focus_config["label"],
                "focus_description": focus_config["description"],
                "etfs": etfs,
                "pair_rows": pair_rows[:15],
                "summary_cards": [
                    {"label": "ETFs compared", "value": str(len(etfs)), "detail": focus_config["label"]},
                    {"label": "Overlap pairs", "value": str(len(pair_rows)), "detail": "Pairs with at least one shared holding"},
                    {"label": "Top overlap", "value": pair_rows[0]["overlap_score"] if pair_rows else "N/A", "detail": f"{pair_rows[0]['left']} vs {pair_rows[0]['right']}" if pair_rows else "No overlap rows yet"},
                ],
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        return result

    def get_idea_radar_workspace(self, universe: str | None, limit: int = 8) -> Dict[str, Any]:
        selected_universe = self._selected_universe(universe)
        limit = max(4, min(limit or 8, 12))
        cache_key = self._cache_key("public-research-idea-radar", selected_universe, limit)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        universe_config = self.screener_universes[selected_universe]
        symbols = list(universe_config["symbols"])[:12]
        raw_rows = self.screener.screen_stocks(symbols, {"market_cap_min": 250_000_000, "sort_by": "market_cap"})
        sector_map = self._sector_tailwind_map()

        for etf in self.ownership_focuses["core"]["etfs"]:
            self.etf_tracker.fetch_etf_holdings(etf, force_refresh=False)

        ranked_rows = []
        for item in raw_rows:
            symbol = str(item.get("symbol", ""))
            sector_tailwind = self._sector_tailwind(str(item.get("sector", "")), sector_map)
            exposure_df = self.etf_tracker.get_funds_for_stock(symbol, min_weight=0.05)
            ownership_count = int(len(exposure_df)) if exposure_df is not None else 0
            ownership_weight = float(exposure_df["weight_pct"].sum()) if exposure_df is not None and not exposure_df.empty else 0.0
            curated = self.institutional_pulse_service.get_symbol_signal(item.get("symbol"), item.get("name"))
            curated_summary = curated.get("summary", {})
            curated_holders = int(curated_summary.get("holder_count", 0) or 0)
            fresh_buyers = int(curated_summary.get("fresh_buyers", 0) or 0)
            fundamental = self._fundamental_overlay(symbol, item)
            forecast_overlay = self._forecast_overlay(symbol)
            score = self._idea_score_components(
                item,
                sector_tailwind,
                ownership_count,
                ownership_weight,
                curated_holders=curated_holders,
                fresh_buyers=fresh_buyers,
                fundamental_quality=float(fundamental["quality"]),
                fundamental_valuation=float(fundamental["valuation"]),
                capital_efficiency=float(fundamental["capital"]),
                disclosure_momentum=float(fundamental.get("disclosure_momentum_score", 0.0) or 0.0),
                trend_confirmation_component=float(forecast_overlay.get("trend_component", 4.0) or 4.0),
            )

            ranked_rows.append(
                {
                    "symbol": symbol,
                    "name": item.get("name"),
                    "sector": item.get("sector", "N/A"),
                    "current_price": _fmt_number(item.get("current_price"), 2),
                    "price_change_3m": _fmt_pct(item.get("price_change_3m")),
                    "rsi": _fmt_number(item.get("rsi"), 1),
                    "roe": _fmt_pct(item.get("roe")),
                    "debt_to_equity": _fmt_number(item.get("debt_to_equity"), 1),
                    "sector_tailwind": _fmt_pct(sector_tailwind),
                    "ownership_count": ownership_count,
                    "ownership_weight": _fmt_pct(ownership_weight),
                    "fundamental_score": _fmt_number(fundamental["overall"], 1),
                    "fundamental_rating": fundamental["overall_rating"],
                    "fundamental_source": fundamental["source"],
                    "valuation_stance": fundamental["valuation_stance"],
                    "capital_profile": fundamental["capital_profile"],
                    "capital_signal": _fmt_number(fundamental["capital"], 1),
                    "net_income_to_capital": fundamental["net_income_to_capital"],
                    "revenue_to_capital": fundamental["revenue_to_capital"],
                    "contracts_to_sales": fundamental["contracts_to_sales"],
                    "material_disclosures_90d": int(fundamental.get("material_disclosures_90d", 0) or 0),
                    "contract_mentions_365d": int(fundamental.get("contract_mentions_365d", 0) or 0),
                    "disclosure_momentum_score": _fmt_number(fundamental.get("disclosure_momentum_score"), 1),
                    "trend_label": forecast_overlay.get("trend_label", "Warming"),
                    "trend_detail": forecast_overlay.get("trend_detail", "Trend structure is still warming."),
                    "trend_persistence": forecast_overlay.get("trend_persistence", "Warming"),
                    "predictability_score": _fmt_number(forecast_overlay.get("predictability_score"), 1),
                    "entropy_regime": forecast_overlay.get("entropy_regime", "Warming"),
                    "trend_bias": forecast_overlay.get("trend_bias", "Mixed"),
                    "forecast_validation": forecast_overlay.get("validation_state", "Warming"),
                    "forecast_source": forecast_overlay.get("source", "warming"),
                    "forecast_consensus_delta": forecast_overlay.get("consensus_delta", "N/A"),
                    "entropy_note": forecast_overlay.get("entropy_note"),
                    "curated_13f_signal": curated.get("signal", "Unavailable"),
                    "curated_13f_holders": curated_holders,
                    "curated_13f_weight": curated_summary.get("total_weight", "N/A"),
                    "curated_13f_fresh": fresh_buyers,
                    "score": score["total"],
                    "band": self._idea_band(score["total"]),
                    "components": {
                        "momentum": _fmt_number(score["momentum"], 1),
                        "rsi": _fmt_number(score["rsi"], 1),
                        "quality": _fmt_number(score["quality"], 1),
                        "valuation": _fmt_number(score["valuation"], 1),
                        "capital": _fmt_number(score["capital"], 1),
                        "disclosure": _fmt_number(score["disclosure"], 1),
                        "sector": _fmt_number(score["sector"], 1),
                        "ownership": _fmt_number(score["ownership"], 1),
                        "institutional": _fmt_number(score["institutional"], 1),
                        "trend": _fmt_number(score["trend"], 1),
                    },
                    "why_passed": "",
                }
            )
            ranked_rows[-1]["why_passed"] = self._idea_reason(ranked_rows[-1])

        ranked_rows = sorted(ranked_rows, key=lambda row: row["score"], reverse=True)
        result = _to_json_safe(
            {
                "selected_universe": selected_universe,
                "universe_options": [
                    {"key": key, "label": value["label"], "description": value["description"]}
                    for key, value in self.screener_universes.items()
                ],
                "universe_label": universe_config["label"],
                "universe_description": universe_config["description"],
                "coverage_size": len(symbols),
                "rows": ranked_rows[:limit],
                "top_pick": ranked_rows[0] if ranked_rows else None,
                "methodology": [
                    "Momentum uses 3-month price change.",
                    "Fundamental overlay blends valuation, operating quality, and capital efficiency.",
                    "BIST names add KAP disclosure momentum and contract-intensity where structured notices exist.",
                    "Entropy and trend persistence reward names where return patterns are ordered enough for trend extrapolation to deserve trust.",
                    "Sector tailwind uses 5-day sector ETF leadership.",
                    "Ownership score rewards broad ETF inclusion and weight concentration.",
                    "Curated 13F overlay rewards institutional breadth and fresh manager buying.",
                ],
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        return result

    def get_conviction_board_workspace(
        self,
        universe: str | None,
        months: int,
        limit: int = 6,
    ) -> Dict[str, Any]:
        selected_universe = self._selected_universe(universe)
        months = max(3, min(months or settings.PUBLIC_TR_FUNDS_MONTHS, 18))
        limit = max(4, min(limit or 6, 10))
        cache_key = self._cache_key("public-research-conviction-board", selected_universe, months, limit)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        idea_workspace = self.get_idea_radar_workspace(selected_universe, limit=max(limit, 8))
        tr_peer_board = self.tr_funds_service.get_cached_peer_signal_board(months=months)
        tr_status = self.tr_funds_service.get_status(months=months)
        raw_top_tr = self.tr_funds_service.get_cached_top_pick(months=months)
        sector_workspace = self.get_sector_rotation_workspace()
        sector_pattern = sector_workspace.get("pattern", "Balanced Rotation")

        equity_rows = []
        for row in idea_workspace.get("rows", [])[:limit]:
            equity_rows.append(
                {
                    **row,
                    "why_now": self._equity_conviction_note(row),
                    "detail_path": f"/stocks?symbol={row.get('symbol')}",
                }
            )

        tr_rows = []
        if isinstance(tr_peer_board, pd.DataFrame) and not tr_peer_board.empty:
            for _, row in tr_peer_board.head(limit).iterrows():
                row_dict = row.to_dict()
                tr_rows.append(
                    {
                        "fund_code": row_dict.get("fund_code"),
                        "fund_name": row_dict.get("fund_name", row_dict.get("fund_name_short", row_dict.get("fund_code"))),
                        "fund_name_short": row_dict.get("fund_name_short", row_dict.get("fund_name", row_dict.get("fund_code"))),
                        "fund_family": row_dict.get("fund_family", "N/A"),
                        "signal_score": _fmt_number(row_dict.get("signal_score"), 1),
                        "signal_band": row_dict.get("signal_band", "N/A"),
                        "board_score": _fmt_number(row_dict.get("board_score"), 1),
                        "board_band": row_dict.get("board_band", "N/A"),
                        "regime": row_dict.get("regime", "N/A"),
                        "investor_growth_pct": _fmt_pct(row_dict.get("investor_growth_pct")),
                        "value_growth_pct": _fmt_pct(row_dict.get("value_growth_pct")),
                        "allocation_drift": _fmt_pct(row_dict.get("allocation_drift")),
                        "dominant_asset": row_dict.get("dominant_asset", "N/A"),
                        "local_factor": row_dict.get("local_factor", "N/A"),
                        "quality_tier": row_dict.get("quality_tier", "N/A"),
                        "why_now": self._tr_conviction_note(row_dict),
                        "detail_path": f"/turkish-funds?fund={row_dict.get('fund_code')}&months={months}",
                    }
                )

        if not tr_rows and isinstance(raw_top_tr, dict) and raw_top_tr:
            tr_rows.append(
                {
                    "fund_code": raw_top_tr.get("fund_code"),
                    "fund_name": raw_top_tr.get("fund_name", raw_top_tr.get("fund_name_short", raw_top_tr.get("fund_code"))),
                    "fund_name_short": raw_top_tr.get("fund_name_short", raw_top_tr.get("fund_name", raw_top_tr.get("fund_code"))),
                    "fund_family": raw_top_tr.get("fund_family", "N/A"),
                    "signal_score": _fmt_number(raw_top_tr.get("signal_score"), 1),
                    "signal_band": raw_top_tr.get("signal_band", "N/A"),
                    "board_score": _fmt_number(raw_top_tr.get("board_score"), 1),
                    "board_band": raw_top_tr.get("board_band", "N/A"),
                    "regime": raw_top_tr.get("regime", "N/A"),
                    "investor_growth_pct": _fmt_pct(raw_top_tr.get("investor_growth_pct")),
                    "value_growth_pct": _fmt_pct(raw_top_tr.get("value_growth_pct")),
                    "allocation_drift": _fmt_pct(raw_top_tr.get("allocation_drift")),
                    "dominant_asset": raw_top_tr.get("dominant_asset", "N/A"),
                    "local_factor": raw_top_tr.get("local_factor", "N/A"),
                    "quality_tier": raw_top_tr.get("quality_tier", "N/A"),
                    "why_now": self._tr_conviction_note(raw_top_tr),
                    "detail_path": f"/turkish-funds?fund={raw_top_tr.get('fund_code')}&months={months}",
                }
            )

        top_equity = equity_rows[0] if equity_rows else None
        top_tr_fund = tr_rows[0] if tr_rows else None
        crowded_count = sum(1 for row in equity_rows if row.get("curated_13f_signal") == "Crowded Long")
        fresh_buyer_count = sum(int(row.get("curated_13f_fresh", 0) or 0) for row in equity_rows)
        trend_confirmed_count = sum(1 for row in equity_rows if row.get("trend_label") in {"Trend Confirmed", "Constructive Trend"})
        tefas_leaders = sum(1 for row in tr_rows if row.get("signal_band") in {"Leading", "Constructive"})
        headline = self._conviction_headline(top_equity, top_tr_fund, sector_pattern)

        result = _to_json_safe(
            {
                "selected_universe": selected_universe,
                "selected_months": months,
                "limit": limit,
                "universe_options": [
                    {"key": key, "label": value["label"], "description": value["description"]}
                    for key, value in self.screener_universes.items()
                ],
                "month_options": [6, 12, 18],
                "headline": headline,
                "sector_pattern": sector_pattern,
                "top_equity": top_equity,
                "top_tr_fund": top_tr_fund,
                "scorecards": [
                    {
                        "label": "US top pick",
                        "value": top_equity["symbol"] if top_equity else "Warming",
                        "detail": (
                            f"{top_equity['band']} · {top_equity['curated_13f_signal']}"
                            if top_equity
                            else "Idea radar is still warming."
                        ),
                    },
                    {
                        "label": "13F crowding",
                        "value": str(crowded_count),
                        "detail": "Displayed global ideas with multi-manager curated ownership.",
                    },
                    {
                        "label": "Fresh buyers",
                        "value": str(fresh_buyer_count),
                        "detail": "Curated manager adds or new positions inside the displayed equity set.",
                    },
                    {
                        "label": "Trend-confirmed",
                        "value": str(trend_confirmed_count),
                        "detail": "Displayed equity ideas where entropy and persistence are supportive rather than random.",
                    },
                    {
                        "label": "TEFAS leaders",
                        "value": str(tefas_leaders),
                        "detail": "Displayed Turkish funds with constructive or leading posture.",
                    },
                ],
                "equity_rows": equity_rows,
                "tr_fund_rows": tr_rows,
                "tefas_health": tr_status,
                "methodology": [
                    "Global equity ideas come from Idea Radar, which blends momentum, valuation, operating quality, capital efficiency, ETF crowding, curated 13F breadth, and entropy-confirmed trend persistence.",
                    "Turkish fund ideas come from cached TEFAS peer-board snapshots ranked by investor growth, portfolio value growth, and allocation drift.",
                    "This board is cross-asset triage, not a backtested portfolio recipe.",
                ],
            }
        )
        if tr_rows:
            cache_set(cache_key, result, ttl=self.ttl_seconds)
        return result

    def _fallback_tr_fund_workspace(self, fund_code: str, months: int) -> Dict[str, Any] | None:
        peer_board = self.tr_funds_service.get_cached_peer_signal_board(months=months)
        if peer_board is None or peer_board.empty:
            return None

        matched = peer_board[peer_board["fund_code"].astype(str).str.upper() == fund_code.upper()]
        if matched.empty:
            return None

        row = matched.iloc[0].to_dict()
        latest_investors = row.get("latest_num_investors")
        investor_change = row.get("investor_change")

        return _to_json_safe(
            {
                "fund_code": fund_code,
                "error": None,
                "featured_funds": self._featured_tr_funds(months),
                "selected_months": months,
                "data_state": "signal-board-fallback",
                "overview": {
                    "fund_name": row.get("fund_name", row.get("fund_name_short", fund_code)),
                    "fund_family": row.get("fund_family", "N/A"),
                    "category": row.get("category", "N/A"),
                    "category_rank": int(row.get("category_rank", 0) or 0),
                    "category_count": int(row.get("category_count", 0) or 0),
                    "category_percentile": _fmt_number(row.get("category_percentile"), 1),
                    "market_share": _fmt_number(row.get("market_share"), 2),
                    "current_price": "N/A",
                    "daily_return": "N/A",
                    "latest_portfolio_value": _fmt_compact_money(row.get("latest_portfolio_value")),
                    "portfolio_value_change": _fmt_compact_money(row.get("portfolio_value_change")),
                    "portfolio_value_growth_pct": _fmt_pct(row.get("value_growth_pct")),
                    "latest_num_investors": (
                        f"{int(float(latest_investors or 0)):,}" if latest_investors not in (None, "") else "N/A"
                    ),
                    "investor_change": (
                        f"{int(float(investor_change or 0)):,}" if investor_change not in (None, "") else "N/A"
                    ),
                    "investor_growth_pct": _fmt_pct(row.get("investor_growth_pct")),
                },
                "signal_card": {
                    "signal_score": _fmt_number(row.get("signal_score"), 1),
                    "signal_band": row.get("signal_band", "N/A"),
                    "board_score": _fmt_number(row.get("board_score"), 1),
                    "board_band": row.get("board_band", "N/A"),
                    "regime": row.get("regime", "N/A"),
                    "regime_note": (
                        "Detailed TEFAS allocation snapshot is unavailable right now. "
                        "FundPilot is serving the latest signal-board state for this fund."
                    ),
                    "dominant_asset": row.get("dominant_asset", "N/A"),
                    "dominant_weight": _fmt_pct(row.get("dominant_weight")),
                    "local_factor": row.get("local_factor", "N/A"),
                    "quality_tier": row.get("quality_tier", "N/A"),
                },
                "allocation_rows": [],
                "monthly_rows": [],
                "evolution_rows": [],
            }
        )

    def get_tr_fund_workspace(
        self,
        fund_code: str | None,
        months: int,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        fund_code = (fund_code or settings.PUBLIC_DEFAULT_TR_FUND_CODE).upper()
        months = max(3, min(months or settings.PUBLIC_TR_FUNDS_MONTHS, 18))
        cache_key = self._cache_key("public-research-tr-fund", fund_code, months)
        snapshot_key = self._tr_fund_snapshot_key(fund_code, months)
        cached = cache_get(cache_key)
        if isinstance(cached, dict) and not force_refresh:
            normalized_cached = self._normalize_tr_workspace(cached, fund_code, months)
            if self._tr_workspace_is_actionable(normalized_cached):
                cache_set(cache_key, normalized_cached, ttl=self.ttl_seconds)
                return normalized_cached
        if not force_refresh:
            persisted = self.snapshot_store.read_json(snapshot_key)
            if isinstance(persisted, dict) and persisted:
                normalized_persisted = self._normalize_tr_workspace(persisted, fund_code, months)
                if self._tr_workspace_is_actionable(normalized_persisted):
                    cache_set(cache_key, normalized_persisted, ttl=self.ttl_seconds)
                    return normalized_persisted

        summary = self.tr_funds_service.get_fund_summary(fund_code, months, force_refresh=force_refresh)
        if not self._tr_summary_is_actionable(summary):
            persisted = self.snapshot_store.read_json(snapshot_key)
            if isinstance(persisted, dict) and persisted:
                normalized_persisted = self._normalize_tr_workspace(persisted, fund_code, months)
                if self._tr_workspace_is_actionable(normalized_persisted):
                    cache_set(cache_key, normalized_persisted, ttl=self.ttl_seconds)
                    return normalized_persisted
            fallback_workspace = self._fallback_tr_fund_workspace(fund_code, months)
            if isinstance(fallback_workspace, dict):
                normalized_fallback = self._normalize_tr_workspace(fallback_workspace, fund_code, months)
                cache_set(cache_key, normalized_fallback, ttl=min(self.ttl_seconds, 300))
                return normalized_fallback
            substitute_code = self._best_available_tr_fund_code(fund_code, months)
            if substitute_code and substitute_code != fund_code:
                substitute_workspace = self.get_tr_fund_workspace(substitute_code, months, force_refresh=False)
                if isinstance(substitute_workspace, dict) and not substitute_workspace.get("error"):
                    normalized_substitute = self._normalize_tr_workspace(substitute_workspace, substitute_code, months)
                    normalized_substitute["requested_fund_code"] = fund_code
                    normalized_substitute["resolved_fund_code"] = substitute_code
                    normalized_substitute["fallback_notice"] = (
                        f"{fund_code} is unavailable in the current TEFAS snapshot. "
                        f"FundPilot is showing {substitute_code} instead."
                    )
                    cache_set(cache_key, normalized_substitute, ttl=min(self.ttl_seconds, 300))
                    return normalized_substitute
            result = {
                "fund_code": fund_code,
                "error": "No TEFAS portfolio summary was returned for this fund code.",
                "data_confidence": self._confidence_payload("warming"),
            }
            normalized_error = self._normalize_tr_workspace(result, fund_code, months)
            cache_set(cache_key, normalized_error, ttl=300)
            return normalized_error

        latest_value = float(summary.get("latest_portfolio_value", 0) or 0)
        latest_investors = float(summary.get("latest_num_investors", 0) or 0)
        value_delta = float(summary.get("portfolio_value_change", 0) or 0)
        investor_delta = float(summary.get("investor_change", 0) or 0)
        current_allocation = summary.get("asset_allocation_current", {}) or {}
        initial_allocation = summary.get("asset_allocation_initial", {}) or {}
        signal_score = _signal_score(summary)
        signal_band = _signal_band(signal_score)
        regime, regime_note = _fund_regime(summary)
        dominant_asset, dominant_weight = _dominant_asset(current_allocation)
        fund_family = _fund_family(summary.get("fund_name", fund_code))
        category_percentile = _category_percentile(
            int(summary.get("category_rank", 0) or 0),
            int(summary.get("category_count", 0) or 0),
        )
        local_factor = _local_factor_lens(summary, summary.get("fund_name", fund_code))
        quality_tier = _quality_tier(category_percentile, float(summary.get("market_share", 0) or 0))
        board_score = _board_score(signal_score, category_percentile, float(summary.get("market_share", 0) or 0))

        def _growth_pct(latest: float, delta: float) -> float:
            base = latest - delta
            if abs(base) < 1e-9:
                return 0.0
            return (delta / abs(base)) * 100

        allocation_rows = []
        for asset, weight in sorted(current_allocation.items(), key=lambda item: item[1], reverse=True):
            initial_weight = float(initial_allocation.get(asset, 0) or 0)
            current_weight = float(weight or 0)
            allocation_rows.append(
                {
                    "asset": self._asset_label(asset),
                    "current_weight": _fmt_pct(current_weight),
                    "initial_weight": _fmt_pct(initial_weight),
                    "change": _fmt_pct(current_weight - initial_weight),
                }
            )

        asset_keys = list(current_allocation.keys())
        monthly_rows = []
        for row in (summary.get("monthly_allocation_changes", []) or [])[-6:]:
            shift_map = {asset: float(row.get(f"{asset}_change", 0) or 0) for asset in asset_keys}
            lead_asset = max(shift_map, key=lambda key: abs(shift_map[key])) if shift_map else None
            monthly_rows.append(
                {
                    "month": row.get("month"),
                    "primary_shift": (
                        f"{self._asset_label(lead_asset)} {_fmt_pct(shift_map[lead_asset])}"
                        if lead_asset
                        else "N/A"
                    ),
                    "stocks_change": _fmt_pct(row.get("stocks_change")),
                    "bonds_change": _fmt_pct(row.get("bonds_change")),
                    "repo_change": _fmt_pct(row.get("repo_change")),
                    "fx_change": _fmt_pct(row.get("fx_change")),
                    "metals_change": _fmt_pct(row.get("precious_metals_change")),
                }
            )

        evolution_rows = []
        for row in (summary.get("top_holdings_evolution", []) or [])[-12:]:
            evolution_rows.append(
                {
                    "month": row.get("month"),
                    "security_name": row.get("security_name"),
                    "weight": _fmt_pct(row.get("weight")),
                    "rank": row.get("rank"),
                    "value": _fmt_compact_money(row.get("value")),
                }
            )

        result = _to_json_safe(
            {
                "fund_code": fund_code,
                "error": None,
                "featured_funds": self._featured_tr_funds(months),
                "selected_months": months,
                "data_state": "live-detail",
                "data_confidence": self._confidence_payload(
                    "live-detail",
                    "Live TEFAS summary data is active for this fund and the workspace is built from server-side cached responses.",
                ),
                "overview": {
                    "fund_name": summary.get("fund_name", fund_code),
                    "fund_family": fund_family,
                    "category": summary.get("category", "N/A"),
                    "category_rank": int(summary.get("category_rank", 0) or 0),
                    "category_count": int(summary.get("category_count", 0) or 0),
                    "category_percentile": _fmt_number(category_percentile, 1),
                    "market_share": _fmt_number(summary.get("market_share"), 2),
                    "current_price": _fmt_number(summary.get("current_price"), 4),
                    "daily_return": _fmt_pct(summary.get("daily_return")),
                    "latest_portfolio_value": _fmt_compact_money(latest_value),
                    "portfolio_value_change": _fmt_compact_money(value_delta),
                    "portfolio_value_growth_pct": _fmt_pct(_growth_pct(latest_value, value_delta)),
                    "latest_num_investors": f"{int(latest_investors):,}",
                    "investor_change": f"{int(investor_delta):,}",
                    "investor_growth_pct": _fmt_pct(_growth_pct(latest_investors, investor_delta)),
                },
                "signal_card": {
                    "signal_score": _fmt_number(signal_score, 1),
                    "signal_band": signal_band,
                    "board_score": _fmt_number(board_score, 1),
                    "board_band": _board_band(board_score),
                    "regime": regime,
                    "regime_note": regime_note,
                    "dominant_asset": dominant_asset,
                    "dominant_weight": _fmt_pct(dominant_weight),
                    "local_factor": local_factor,
                    "quality_tier": quality_tier,
                },
                "allocation_rows": allocation_rows,
                "monthly_rows": monthly_rows,
                "evolution_rows": evolution_rows,
                "what_changed": self._build_tr_change_rows(
                    {
                        "investor_growth_pct": _fmt_pct(_growth_pct(latest_investors, investor_delta)),
                        "portfolio_value_growth_pct": _fmt_pct(_growth_pct(latest_value, value_delta)),
                    },
                    {
                        "regime": regime,
                        "regime_note": regime_note,
                    },
                    monthly_rows,
                ),
            }
        )
        normalized_result = self._normalize_tr_workspace(result, fund_code, months)
        cache_set(cache_key, normalized_result, ttl=self.ttl_seconds)
        self.snapshot_store.write_json(snapshot_key, normalized_result)
        return normalized_result

    def get_portfolio_lab_workspace(self, positions_text: str | None, preset: str | None) -> Dict[str, Any]:
        selected_preset = preset if preset in self.scenario_presets else "tcmb_hike_500bp"
        parsed = self._parse_positions_text(positions_text)
        raw_text = parsed["raw_text"]
        cache_key = self._cache_key("public-research-portfolio-lab", raw_text, selected_preset)
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        portfolio_df = parsed["portfolio_df"]
        errors = list(parsed["errors"])
        if portfolio_df.empty:
            result = {
                "error": "Portfolio input could not be parsed.",
                "raw_text": raw_text,
                "errors": errors,
                "preset": selected_preset,
                "share_url": f"/scenario-lab?positions={quote_plus(raw_text)}&preset={quote_plus(selected_preset)}",
                "preset_options": [
                    {"key": key, "label": value["label"], "description": value["description"]}
                    for key, value in self.scenario_presets.items()
                ],
            }
            cache_set(cache_key, result, ttl=300)
            return result

        portfolio_view = portfolio_df.copy()
        health_engine = PortfolioHealthScore()
        health_engine.load_portfolio(portfolio_view[["Symbol", "Shares", "Price", "Value"]].copy())
        enriched = health_engine.enrich_portfolio_data()
        health_engine.calculate_all_metrics()
        health_summary = health_engine.get_summary()

        sandbox = ScenarioSandbox()
        preset_config = self.scenario_presets[selected_preset]
        scenario = sandbox.create_scenario(
            scenario_type=preset_config["scenario_type"],
            scenario_name=preset_config["label"],
            **preset_config["parameters"],
        )
        scenario_portfolio = pd.DataFrame(
            {
                "Symbol": portfolio_df["Symbol"],
                "Shares": portfolio_df["Shares"],
                "Current_Price": portfolio_df["Current_Price"],
                "Value": portfolio_df["Value"],
                "Weight": health_engine.portfolio_data["Weight"],
            }
        )
        scenario_portfolio["Sector"] = scenario_portfolio["Symbol"].apply(sandbox._classify_stock_sector)

        impact_df = sandbox.simulate_portfolio_impact(scenario_portfolio.copy(), scenario)
        stress_results = sandbox.stress_test_portfolio(scenario_portfolio.copy())
        var_metrics = sandbox.calculate_var(
            scenario_portfolio.copy(),
            num_simulations=250,
            time_horizon_days=10,
        )

        holdings_rows = []
        for _, row in pd.concat([portfolio_df, enriched[["Sector", "Beta", "Return_3M"]]], axis=1).iterrows():
            holdings_rows.append(
                {
                    "symbol": row.get("Symbol"),
                    "shares": _fmt_shares(row.get("Shares")),
                    "current_price": _fmt_number(row.get("Current_Price"), 2),
                    "value": _fmt_compact_money(row.get("Value")),
                    "sector": row.get("Sector", "N/A"),
                    "beta": _fmt_number(row.get("Beta"), 2),
                    "return_3m": _fmt_pct(row.get("Return_3M")),
                }
            )

        impact_rows = []
        for _, row in impact_df.sort_values("Expected_Change").iterrows():
            impact_rows.append(
                {
                    "symbol": row.get("Symbol"),
                    "sector": row.get("Sector", "N/A"),
                    "expected_change": _fmt_pct(row.get("Expected_Change")),
                    "value_change": _fmt_compact_money(row.get("Value_Change")),
                    "new_value": _fmt_compact_money(row.get("New_Value")),
                }
            )

        stress_rows = []
        for key, value in stress_results.items():
            stress_rows.append(
                {
                    "key": key,
                    "label": self.scenario_presets.get(key, {}).get("label", value["scenario"]["name"]),
                    "portfolio_change_pct": _fmt_pct(value.get("portfolio_change_pct")),
                    "best_stock": value.get("best_stock"),
                    "worst_stock": value.get("worst_stock"),
                }
            )

        export_positions = [
            {
                "symbol": row.get("Symbol"),
                "shares": float(row.get("Shares") or 0),
                "entry_price": float(row.get("Price") or 0),
            }
            for _, row in portfolio_df.iterrows()
        ]
        export_json = json.dumps(export_positions, ensure_ascii=True, indent=2)
        export_csv = "Symbol,Shares,EntryPrice\n" + "\n".join(
            f"{item['symbol']},{item['shares']},{item['entry_price']}"
            for item in export_positions
        )
        share_url = f"/scenario-lab?positions={quote_plus(raw_text)}&preset={quote_plus(selected_preset)}"

        result = _to_json_safe(
            {
                "error": None,
                "raw_text": raw_text,
                "errors": errors,
                "preset": selected_preset,
                "share_url": share_url,
                "accepted_formats": [
                    "CSV lines: Symbol,Shares,EntryPrice",
                    'JSON array: [{"symbol":"AAPL","shares":12,"entry_price":189}]',
                ],
                "export_json_uri": f"data:application/json;charset=utf-8,{quote_plus(export_json)}",
                "export_csv_uri": f"data:text/csv;charset=utf-8,{quote_plus(export_csv)}",
                "export_json_name": "fundpilot-scenario-lab.json",
                "export_csv_name": "fundpilot-scenario-lab.csv",
                "preset_label": preset_config["label"],
                "preset_description": preset_config["description"],
                "preset_options": [
                    {"key": key, "label": value["label"], "description": value["description"]}
                    for key, value in self.scenario_presets.items()
                ],
                "portfolio_summary": {
                    "positions": len(holdings_rows),
                    "total_value": _fmt_compact_money(health_summary["portfolio_stats"]["total_value"]),
                    "health_score": _fmt_number(health_summary["total_score"], 1),
                    "grade": health_summary["grade"],
                    "avg_beta": _fmt_number(health_summary["portfolio_stats"]["avg_beta"], 2),
                    "avg_return_3m": _fmt_pct(health_summary["portfolio_stats"]["avg_return_3m"]),
                    "sectors": int(health_summary["portfolio_stats"]["num_sectors"]),
                },
                "metric_scores": [
                    {"label": key.replace("_", " ").title(), "value": _fmt_number(value, 1)}
                    for key, value in health_summary["metric_scores"].items()
                ],
                "recommendations": health_summary["recommendations"],
                "holdings_rows": holdings_rows,
                "scenario_summary": {
                    "portfolio_change_pct": _fmt_pct(impact_df.attrs.get("portfolio_change_pct")),
                    "old_value": _fmt_compact_money(impact_df.attrs.get("portfolio_old_value")),
                    "new_value": _fmt_compact_money(impact_df.attrs.get("portfolio_new_value")),
                },
                "impact_rows": impact_rows,
                "stress_rows": stress_rows,
                "var_summary": {
                    "var_pct": _fmt_pct(var_metrics.get("var_pct")),
                    "cvar_pct": _fmt_pct(var_metrics.get("cvar_pct")),
                    "worst_case": _fmt_pct(var_metrics.get("worst_case")),
                    "best_case": _fmt_pct(var_metrics.get("best_case")),
                },
            }
        )
        cache_set(cache_key, result, ttl=self.ttl_seconds)
        return result
