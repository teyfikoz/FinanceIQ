from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from app.services.cache import cache_clear
from app.services import public_research as public_research_module
from app.services.public_research import PublicResearchService
from app.services.snapshot_store import SnapshotStore


def test_parse_positions_text_builds_portfolio_frame(monkeypatch):
    service = PublicResearchService()

    monkeypatch.setattr(
        service,
        "_resolve_quote",
        lambda symbol: {"symbol": symbol, "name": symbol, "current_price": 100.0},
    )

    parsed = service._parse_positions_text("AAPL,2,90\nTHYAO,5,300")

    assert parsed["errors"] == []
    assert len(parsed["portfolio_df"]) == 2
    assert parsed["portfolio_df"]["Value"].sum() == 700.0


def test_parse_positions_text_reports_invalid_lines(monkeypatch):
    service = PublicResearchService()

    monkeypatch.setattr(
        service,
        "_resolve_quote",
        lambda symbol: {"symbol": symbol, "name": symbol, "current_price": 100.0},
    )

    parsed = service._parse_positions_text("AAPL,2\nMSFT,abc,90")

    assert parsed["portfolio_df"].empty
    assert len(parsed["errors"]) == 2


def test_public_research_service_exposes_regional_stock_universes():
    service = PublicResearchService()

    assert "europe" in service.screener_universes
    assert "japan" in service.screener_universes
    assert "south-korea" in service.screener_universes
    assert "china" in service.screener_universes
    assert "hong-kong" in service.screener_universes
    assert "regional" in service.ownership_focuses

    featured = service._featured_stock_symbols()
    assert "7203.T" in featured
    assert "005930.KS" in featured
    assert "0700.HK" in featured


def test_sovereign_workspace_exposes_country_and_monthly_drift_tables():
    service = PublicResearchService()

    workspace = service.get_sovereign_workspace("norway-gpf", None)

    assert workspace["selected_fund_key"] == "norway-gpf"
    assert workspace["data_confidence"]["label"] == "Estimated"
    assert workspace["allocation_rows"]
    assert workspace["monthly_rows"]
    assert workspace["holdings_timeline_rows"]
    assert workspace["country_rows"]
    assert workspace["fund"]["visible_sleeve_weight"] != "N/A"
    assert "portfolio_weight" in workspace["allocation_rows"][0]
    assert "largest_shift" in workspace["monthly_rows"][0]
    assert "primary_shift" in workspace["holdings_timeline_rows"][0]


def test_idea_score_components_rewards_quality_and_tailwinds():
    service = PublicResearchService()
    item = {"price_change_3m": 18.0, "rsi": 61.0, "roe": 22.0, "debt_to_equity": 35.0}

    score = service._idea_score_components(item, sector_tailwind=2.1, ownership_count=3, ownership_weight=8.0)

    assert score["total"] > 60
    assert score["momentum"] > 0
    assert score["quality"] > 0


def test_idea_score_components_reward_curated_13f_breadth():
    service = PublicResearchService()
    item = {"price_change_3m": 18.0, "rsi": 61.0, "roe": 22.0, "debt_to_equity": 35.0}

    base_score = service._idea_score_components(item, sector_tailwind=2.1, ownership_count=3, ownership_weight=8.0)
    enhanced_score = service._idea_score_components(
        item,
        sector_tailwind=2.1,
        ownership_count=3,
        ownership_weight=8.0,
        curated_holders=3,
        fresh_buyers=2,
    )

    assert enhanced_score["institutional"] > base_score["institutional"]
    assert enhanced_score["total"] > base_score["total"]


def test_idea_score_components_reward_entropy_confirmed_trend():
    service = PublicResearchService()
    item = {"price_change_3m": 18.0, "rsi": 61.0, "roe": 22.0, "debt_to_equity": 35.0}

    base_score = service._idea_score_components(item, sector_tailwind=2.1, ownership_count=3, ownership_weight=8.0)
    enhanced_score = service._idea_score_components(
        item,
        sector_tailwind=2.1,
        ownership_count=3,
        ownership_weight=8.0,
        trend_confirmation_component=10.5,
    )

    assert enhanced_score["trend"] > base_score["trend"]
    assert enhanced_score["total"] > base_score["total"]


def test_forecast_overlay_uses_snapshot_lens(monkeypatch):
    service = PublicResearchService()

    monkeypatch.setattr(
        service,
        "_read_stock_snapshot",
        lambda symbol: {
            "data_state": "snapshot",
            "forecast_lens": {
                "state": "ready",
                "trend_bias": "Bullish",
                "consensus_delta": "+7.20%",
                "trend_persistence": {"label": "Persistent"},
                "entropy_signal": {
                    "regime": "Structured Trend",
                    "predictability_score": 68.4,
                    "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
                },
                "validation_summary": {"state": "Validated 5/5"},
            },
        },
    )

    overlay = service._forecast_overlay("NVDA")

    assert overlay["trend_label"] == "Trend Confirmed"
    assert overlay["entropy_regime"] == "Structured Trend"
    assert overlay["trend_component"] > 8


def test_get_screener_workspace_filters_for_curated_13f_accumulation(monkeypatch):
    service = PublicResearchService()

    monkeypatch.setattr(
        service.screener,
        "screen_stocks",
        lambda symbols, criteria: [
            {
                "symbol": "NVDA",
                "name": "NVIDIA",
                "sector": "Technology",
                "current_price": 1050.0,
                "market_cap": 2_500_000_000_000,
                "price_change_3m": 24.2,
                "dividend_yield": 0.1,
                "pe_ratio": 38.0,
                "pb_ratio": 12.0,
                "rsi": 63.0,
                "roe": 48.0,
                "profit_margin": 29.0,
                "debt_to_equity": 40.0,
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft",
                "sector": "Technology",
                "current_price": 420.0,
                "market_cap": 3_000_000_000_000,
                "price_change_3m": 18.0,
                "dividend_yield": 0.7,
                "pe_ratio": 34.0,
                "pb_ratio": 10.0,
                "rsi": 59.0,
                "roe": 35.0,
                "profit_margin": 31.0,
                "debt_to_equity": 31.0,
            },
            {
                "symbol": "KO",
                "name": "Coca-Cola",
                "sector": "Consumer Staples",
                "current_price": 64.0,
                "market_cap": 275_000_000_000,
                "price_change_3m": 4.0,
                "dividend_yield": 3.0,
                "pe_ratio": 24.0,
                "pb_ratio": 8.0,
                "rsi": 48.0,
                "roe": 18.0,
                "profit_margin": 22.0,
                "debt_to_equity": 120.0,
            },
        ],
    )

    def _fake_signal(symbol, issuer_name=None):
        signals = {
            "NVDA": {
                "signal": "Accumulating",
                "summary": {
                    "holder_count": 2,
                    "total_weight": "+16.20%",
                    "top_holder": "Stanley Druckenmiller",
                    "bullish_managers": 2,
                    "bearish_managers": 0,
                    "fresh_buyers": 1,
                },
            },
            "MSFT": {
                "signal": "Crowded Long",
                "summary": {
                    "holder_count": 3,
                    "total_weight": "+18.40%",
                    "top_holder": "Bill Gates",
                    "bullish_managers": 2,
                    "bearish_managers": 0,
                    "fresh_buyers": 2,
                },
            },
            "KO": {
                "signal": "Held",
                "summary": {
                    "holder_count": 1,
                    "total_weight": "+2.10%",
                    "top_holder": "Warren Buffett",
                    "bullish_managers": 0,
                    "bearish_managers": 0,
                    "fresh_buyers": 0,
                },
            },
        }
        return signals[symbol]

    monkeypatch.setattr(service.institutional_pulse_service, "get_symbol_signal", _fake_signal)

    workspace = service.get_screener_workspace("sp500", "institutional_accumulation", limit=12)

    assert workspace["match_count"] == 2
    assert workspace["crowded_count"] == 2
    assert [row["symbol"] for row in workspace["rows"]] == ["MSFT", "NVDA"]
    assert workspace["rows"][0]["curated_13f_signal"] == "Crowded Long"
    assert workspace["rows"][0]["fundamental_rating"] in {"Buy", "Strong Buy", "Hold"}
    assert workspace["rows"][0]["capital_profile"] in {"High Conversion", "Healthy", "Mixed", "Asset Heavy"}


def test_get_idea_radar_workspace_includes_trend_overlay(monkeypatch):
    service = PublicResearchService()
    service.screener_universes = {
        "global": {
            "label": "Global Mix",
            "description": "Cross-market blend",
            "symbols": ["NVDA"],
        }
    }

    monkeypatch.setattr(
        service.screener,
        "screen_stocks",
        lambda symbols, criteria: [
            {
                "symbol": "NVDA",
                "name": "NVIDIA",
                "sector": "Technology",
                "current_price": 1050.0,
                "market_cap": 2_500_000_000_000,
                "price_change_3m": 24.2,
                "rsi": 63.0,
                "roe": 48.0,
                "debt_to_equity": 40.0,
            }
        ],
    )
    monkeypatch.setattr(service, "_sector_tailwind_map", lambda: {"Technology": 2.4})
    monkeypatch.setattr(service.etf_tracker, "fetch_etf_holdings", lambda etf, force_refresh=False: pd.DataFrame())
    monkeypatch.setattr(service.etf_tracker, "get_funds_for_stock", lambda symbol, min_weight=0.05: pd.DataFrame())
    monkeypatch.setattr(
        service.institutional_pulse_service,
        "get_symbol_signal",
        lambda symbol, name: {"signal": "Accumulating", "summary": {"holder_count": 2, "fresh_buyers": 1, "total_weight": "+11.4%"}},
    )
    monkeypatch.setattr(
        service,
        "_fundamental_overlay",
        lambda symbol, item: {
            "source": "snapshot",
            "overall": 78.4,
            "overall_rating": "Buy",
            "valuation": 70.0,
            "quality": 80.0,
            "capital": 82.0,
            "valuation_stance": "Growth At A Reasonable Price",
            "capital_profile": "High Conversion",
            "net_income_to_capital": "2.20x",
            "revenue_to_capital": "12.50x",
            "contracts_to_sales": "N/A",
            "material_disclosures_90d": 0,
            "contract_mentions_365d": 0,
            "disclosure_momentum_score": 0.0,
        },
    )
    monkeypatch.setattr(
        service,
        "_forecast_overlay",
        lambda symbol: {
            "state": "ready",
            "source": "snapshot",
            "trend_bias": "Bullish",
            "trend_persistence": "Persistent",
            "predictability_score": 68.4,
            "entropy_regime": "Structured Trend",
            "validation_state": "Validated 5/5",
            "trend_label": "Trend Confirmed",
            "trend_detail": "Momentum is not just positive.",
            "trend_component": 10.4,
            "consensus_delta": "+7.20%",
            "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
        },
    )

    workspace = service.get_idea_radar_workspace("global", 8)

    assert workspace["rows"][0]["trend_label"] == "Trend Confirmed"
    assert workspace["rows"][0]["components"]["trend"] == "10.4"
    assert workspace["rows"][0]["entropy_regime"] == "Structured Trend"
    assert "Entropy and trend persistence reward names" in workspace["methodology"][3]


def test_get_screener_workspace_ranks_bist_disclosure_leaders(monkeypatch):
    service = PublicResearchService()

    monkeypatch.setattr(
        service.screener,
        "screen_stocks",
        lambda symbols, criteria: [
            {"symbol": "ASELS.IS", "name": "Aselsan", "sector": "Industrials", "current_price": 138.0, "market_cap": 20_000_000_000, "price_change_3m": 22.0, "dividend_yield": 0.0, "pe_ratio": 18.0, "rsi": 58.0, "roe": 24.0, "debt_to_equity": 30.0},
            {"symbol": "TUPRS.IS", "name": "Tupras", "sector": "Energy", "current_price": 236.0, "market_cap": 18_000_000_000, "price_change_3m": 9.0, "dividend_yield": 0.0, "pe_ratio": 6.0, "rsi": 42.0, "roe": 19.0, "debt_to_equity": 28.0},
            {"symbol": "AAPL", "name": "Apple", "sector": "Technology", "current_price": 200.0, "market_cap": 3_000_000_000_000, "price_change_3m": 18.0, "dividend_yield": 0.5, "pe_ratio": 28.0, "rsi": 56.0, "roe": 34.0, "debt_to_equity": 120.0},
        ],
    )
    monkeypatch.setattr(
        service.institutional_pulse_service,
        "get_symbol_signal",
        lambda symbol, issuer_name=None: {"signal": "Unavailable", "summary": {}},
    )

    overlays = {
        "ASELS.IS": {
            "source": "approx+kap",
            "overall": 78.0,
            "overall_rating": "Buy",
            "valuation": 68.0,
            "quality": 76.0,
            "capital": 88.0,
            "valuation_stance": "Fair",
            "capital_profile": "High Conversion",
            "net_income_to_capital": "1.20x",
            "revenue_to_capital": "3.40x",
            "contracts_to_sales": "+45.0%",
            "material_disclosures_90d": 10,
            "contract_mentions_365d": 7,
            "disclosure_momentum_score": 92.0,
        },
        "TUPRS.IS": {
            "source": "approx+kap",
            "overall": 74.0,
            "overall_rating": "Strong Buy",
            "valuation": 80.0,
            "quality": 78.0,
            "capital": 84.0,
            "valuation_stance": "Compressed",
            "capital_profile": "High Conversion",
            "net_income_to_capital": "1.50x",
            "revenue_to_capital": "4.10x",
            "contracts_to_sales": "N/A",
            "material_disclosures_90d": 4,
            "contract_mentions_365d": 1,
            "disclosure_momentum_score": 61.0,
        },
        "AAPL": {
            "source": "approx",
            "overall": 70.0,
            "overall_rating": "Buy",
            "valuation": 62.0,
            "quality": 74.0,
            "capital": 66.0,
            "valuation_stance": "Fair",
            "capital_profile": "Unavailable",
            "net_income_to_capital": "N/A",
            "revenue_to_capital": "N/A",
            "contracts_to_sales": "N/A",
            "material_disclosures_90d": 0,
            "contract_mentions_365d": 0,
            "disclosure_momentum_score": 0.0,
        },
    }
    monkeypatch.setattr(service, "_fundamental_overlay", lambda symbol, item: overlays[symbol])

    workspace = service.get_screener_workspace("bist", "bist_disclosure_leaders", limit=8)

    assert workspace["match_count"] == 2
    assert workspace["disclosure_active_count"] == 2
    assert [row["symbol"] for row in workspace["rows"]] == ["ASELS.IS", "TUPRS.IS"]
    assert workspace["rows"][0]["disclosure_momentum_score"] == "92.0"


def test_get_screener_workspace_filters_trend_confirmed_accumulation(monkeypatch):
    service = PublicResearchService()
    service.screener_universes = {
        "sp500": {"label": "US Large Cap", "description": "desc", "symbols": ["NVDA", "MSFT", "KO"]}
    }

    monkeypatch.setattr(
        service.screener,
        "screen_stocks",
        lambda symbols, criteria: [
            {"symbol": "NVDA", "name": "NVIDIA", "sector": "Technology", "current_price": 1050.0, "market_cap": 2_500_000_000_000, "price_change_3m": 24.2, "dividend_yield": 0.1, "pe_ratio": 38.0, "rsi": 63.0, "roe": 48.0, "debt_to_equity": 40.0},
            {"symbol": "MSFT", "name": "Microsoft", "sector": "Technology", "current_price": 420.0, "market_cap": 3_000_000_000_000, "price_change_3m": 18.0, "dividend_yield": 0.7, "pe_ratio": 34.0, "rsi": 60.0, "roe": 38.0, "debt_to_equity": 32.0},
            {"symbol": "KO", "name": "Coca-Cola", "sector": "Consumer Defensive", "current_price": 64.0, "market_cap": 250_000_000_000, "price_change_3m": 6.0, "dividend_yield": 3.0, "pe_ratio": 24.0, "rsi": 52.0, "roe": 18.0, "debt_to_equity": 140.0},
        ],
    )

    signals = {
        "NVDA": {"signal": "Crowded Long", "summary": {"holder_count": 3, "total_weight": "+23.0%", "top_holder": "Druckenmiller", "bullish_managers": 3, "bearish_managers": 0, "fresh_buyers": 2}},
        "MSFT": {"signal": "Accumulating", "summary": {"holder_count": 1, "total_weight": "+3.4%", "top_holder": "Coatue", "bullish_managers": 1, "bearish_managers": 0, "fresh_buyers": 1}},
        "KO": {"signal": "Held", "summary": {"holder_count": 1, "total_weight": "+2.1%", "top_holder": "Berkshire", "bullish_managers": 0, "bearish_managers": 0, "fresh_buyers": 0}},
    }
    monkeypatch.setattr(service.institutional_pulse_service, "get_symbol_signal", lambda symbol, name: signals[symbol])
    monkeypatch.setattr(
        service,
        "_fundamental_overlay",
        lambda symbol, item: {
            "source": "snapshot",
            "overall": 78.4 if symbol == "NVDA" else 72.0 if symbol == "MSFT" else 61.0,
            "overall_rating": "Buy",
            "valuation": 70.0,
            "quality": 80.0,
            "capital": 82.0 if symbol != "KO" else 49.0,
            "valuation_stance": "Fair",
            "capital_profile": "High Conversion" if symbol != "KO" else "Mixed",
            "net_income_to_capital": "2.20x",
            "revenue_to_capital": "12.50x",
            "contracts_to_sales": "N/A",
            "material_disclosures_90d": 0,
            "contract_mentions_365d": 0,
            "disclosure_momentum_score": 0.0,
        },
    )
    overlays = {
        "NVDA": {"trend_label": "Trend Confirmed", "trend_detail": "detail", "trend_persistence": "Persistent", "predictability_score": 68.4, "entropy_regime": "Structured Trend", "trend_bias": "Bullish", "validation_state": "Validated 5/5", "source": "snapshot", "consensus_delta": "+7.2%", "entropy_note": "note"},
        "MSFT": {"trend_label": "Constructive Trend", "trend_detail": "detail", "trend_persistence": "Developing", "predictability_score": 58.0, "entropy_regime": "Constructive Trend", "trend_bias": "Bullish", "validation_state": "Validated 5/5", "source": "snapshot", "consensus_delta": "+4.1%", "entropy_note": "note"},
        "KO": {"trend_label": "Warming", "trend_detail": "detail", "trend_persistence": "Fragile", "predictability_score": 45.0, "entropy_regime": "Transitional", "trend_bias": "Mixed", "validation_state": "Validated 5/5", "source": "snapshot", "consensus_delta": "+1.0%", "entropy_note": "note"},
    }
    monkeypatch.setattr(service, "_forecast_overlay", lambda symbol: overlays[symbol])

    workspace = service.get_screener_workspace("sp500", "trend_confirmed_accumulation", limit=12)

    assert [row["symbol"] for row in workspace["rows"]] == ["NVDA", "MSFT"]
    assert workspace["trend_confirmed_count"] == 2
    assert workspace["rows"][0]["trend_label"] == "Trend Confirmed"


def test_get_screener_workspace_filters_entropy_clean_setups(monkeypatch):
    service = PublicResearchService()
    service.screener_universes = {
        "sp500": {"label": "US Large Cap", "description": "desc", "symbols": ["NVDA", "AMZN", "XOM"]}
    }

    monkeypatch.setattr(
        service.screener,
        "screen_stocks",
        lambda symbols, criteria: [
            {"symbol": "NVDA", "name": "NVIDIA", "sector": "Technology", "current_price": 1050.0, "market_cap": 2_500_000_000_000, "price_change_3m": 24.2, "dividend_yield": 0.1, "pe_ratio": 38.0, "rsi": 63.0, "roe": 48.0, "debt_to_equity": 40.0},
            {"symbol": "AMZN", "name": "Amazon", "sector": "Consumer Cyclical", "current_price": 190.0, "market_cap": 2_000_000_000_000, "price_change_3m": 14.0, "dividend_yield": 0.0, "pe_ratio": 45.0, "rsi": 58.0, "roe": 27.0, "debt_to_equity": 55.0},
            {"symbol": "XOM", "name": "Exxon", "sector": "Energy", "current_price": 118.0, "market_cap": 500_000_000_000, "price_change_3m": 3.0, "dividend_yield": 3.4, "pe_ratio": 12.0, "rsi": 47.0, "roe": 16.0, "debt_to_equity": 18.0},
        ],
    )
    monkeypatch.setattr(
        service.institutional_pulse_service,
        "get_symbol_signal",
        lambda symbol, name: {"signal": "Held", "summary": {"holder_count": 1, "total_weight": "+2.0%", "top_holder": "N/A", "bullish_managers": 0, "bearish_managers": 0, "fresh_buyers": 0}},
    )
    monkeypatch.setattr(
        service,
        "_fundamental_overlay",
        lambda symbol, item: {
            "source": "snapshot",
            "overall": 70.0,
            "overall_rating": "Buy",
            "valuation": 66.0,
            "quality": 72.0,
            "capital": 68.0,
            "valuation_stance": "Fair",
            "capital_profile": "Healthy",
            "net_income_to_capital": "1.40x",
            "revenue_to_capital": "6.80x",
            "contracts_to_sales": "N/A",
            "material_disclosures_90d": 0,
            "contract_mentions_365d": 0,
            "disclosure_momentum_score": 0.0,
        },
    )
    overlays = {
        "NVDA": {"trend_label": "Trend Confirmed", "trend_detail": "detail", "trend_persistence": "Persistent", "predictability_score": 68.4, "entropy_regime": "Structured Trend", "trend_bias": "Bullish", "validation_state": "Validated 5/5", "source": "snapshot", "consensus_delta": "+7.2%", "entropy_note": "note"},
        "AMZN": {"trend_label": "Constructive Trend", "trend_detail": "detail", "trend_persistence": "Developing", "predictability_score": 61.0, "entropy_regime": "Constructive Trend", "trend_bias": "Bullish", "validation_state": "Validated 5/5", "source": "snapshot", "consensus_delta": "+4.1%", "entropy_note": "note"},
        "XOM": {"trend_label": "Orderly Downtrend", "trend_detail": "detail", "trend_persistence": "Orderly Risk-Off", "predictability_score": 73.0, "entropy_regime": "Structured Trend", "trend_bias": "Bearish", "validation_state": "Validated 5/5", "source": "snapshot", "consensus_delta": "-5.0%", "entropy_note": "note"},
    }
    monkeypatch.setattr(service, "_forecast_overlay", lambda symbol: overlays[symbol])

    workspace = service.get_screener_workspace("sp500", "entropy_clean_setups", limit=12)

    assert [row["symbol"] for row in workspace["rows"]] == ["NVDA", "AMZN"]
    assert workspace["average_predictability"] == "64.7"
    assert workspace["rows"][0]["trend_label"] == "Trend Confirmed"


def test_get_bist_quality_board_workspace_blends_clean_tape_and_catalysts(monkeypatch):
    service = PublicResearchService()

    monkeypatch.setattr(public_research_module, "get_bist_stocks", lambda: ["ASELS", "TUPRS"])
    monkeypatch.setattr(service.screener, "screen_stocks", lambda symbols, criteria: [{"symbol": "ASELS"}, {"symbol": "TUPRS"}])
    monkeypatch.setattr(
        service,
        "_screen_rows_with_curated_13f",
        lambda raw_results: [
            {
                "symbol": "ASELS",
                "name": "Aselsan",
                "sector": "Industrials",
                "fundamental_rating": "Buy",
                "fundamental_score": "79.0",
                "valuation_stance": "Fair",
                "capital_profile": "High Conversion",
                "capital_signal": "82.0",
                "net_income_to_capital": "1.8x",
                "revenue_to_capital": "6.2x",
                "trend_label": "Trend Confirmed",
                "predictability_score": "68.4",
                "entropy_regime": "Structured Trend",
                "disclosure_momentum_score": "91.0",
                "material_disclosures_90d": 14,
                "contract_mentions_365d": 19,
                "contracts_to_sales": "311.4%",
                "curated_13f_signal": "Unavailable",
                "curated_13f_holders": 0,
                "why_passed": "seed",
            },
            {
                "symbol": "TUPRS",
                "name": "Tupras",
                "sector": "Energy",
                "fundamental_rating": "Buy",
                "fundamental_score": "73.0",
                "valuation_stance": "Fair",
                "capital_profile": "Healthy",
                "capital_signal": "70.0",
                "net_income_to_capital": "1.3x",
                "revenue_to_capital": "4.9x",
                "trend_label": "Catalyst Active",
                "predictability_score": "48.0",
                "entropy_regime": "Transitional",
                "disclosure_momentum_score": "72.0",
                "material_disclosures_90d": 7,
                "contract_mentions_365d": 4,
                "contracts_to_sales": "18.0%",
                "curated_13f_signal": "Unavailable",
                "curated_13f_holders": 0,
                "why_passed": "seed",
            },
        ],
    )

    workspace = service.get_bist_quality_board_workspace(10)

    assert workspace["top_pick"]["symbol"] == "ASELS"
    assert workspace["rows"][0]["catalyst_tape"]["label"] == "Catalyst + Clean Tape"
    assert workspace["rows"][0]["catalyst_clean_score"] != "N/A"
    assert "clean-tape confirmation" in workspace["methodology"][0]


def test_get_catalyst_calendar_workspace_includes_clean_tape_lane(monkeypatch):
    service = PublicResearchService()

    monkeypatch.setattr(
        service.stock_enrichment_service,
        "get_health_snapshot",
        lambda: {"rows": [{"last_disclosure_date": "2026-06-02", "symbol": "ASELS", "disclosure_momentum_score": "91.0", "field_coverage": 4, "source_state": "live"}]},
    )
    monkeypatch.setattr(
        service.tr_funds_service,
        "get_status",
        lambda months: {"funds_loaded": 3, "status": "healthy", "detail": "Cached peer board available.", "last_snapshot_at": "2026-06-03T10:00:00Z"},
    )
    monkeypatch.setattr(
        service.institutional_pulse_service,
        "get_workspace",
        lambda manager: {"coverage_rows": [{"latest_filing": "2026-05-15", "manager_name": "Berkshire Hathaway", "holding_count": 42, "top_10_weight": "88.0%", "source_state": "live"}]},
    )
    monkeypatch.setattr(
        service,
        "get_bist_quality_board_workspace",
        lambda limit=6: {
            "rows": [
                {
                    "symbol": "ASELS",
                    "name": "Aselsan",
                    "catalyst_tape": {"label": "Catalyst + Clean Tape", "detail": "Disclosure flow is active and the tape is orderly enough for follow-through to deserve more respect than noise."},
                    "predictability_score": "68.4",
                    "trend_label": "Trend Confirmed",
                    "disclosure_momentum_score": "91.0",
                    "contracts_to_sales": "311.4%",
                },
                {
                    "symbol": "TUPRS",
                    "name": "Tupras",
                    "catalyst_tape": {"label": "Watch", "detail": "Watch"},
                    "predictability_score": "48.0",
                    "trend_label": "Warming",
                    "disclosure_momentum_score": "72.0",
                    "contracts_to_sales": "18.0%",
                },
            ]
        },
    )

    workspace = service.get_catalyst_calendar_workspace()

    assert workspace["summary_cards"][3]["value"] == "1"
    assert workspace["clean_tape_rows"][0]["symbol"] == "ASELS"
    assert workspace["clean_tape_rows"][0]["label"] == "Catalyst + Clean Tape"


def test_get_conviction_board_workspace_blends_equity_and_tefas_lanes(monkeypatch):
    service = PublicResearchService()

    monkeypatch.setattr(
        service,
        "get_idea_radar_workspace",
        lambda universe, limit: {
            "rows": [
                {
                    "symbol": "NVDA",
                    "name": "NVIDIA Corporation",
                    "sector": "Technology",
                    "score": 81.4,
                    "band": "High Conviction",
                    "trend_label": "Trend Confirmed",
                    "predictability_score": "68.4",
                    "entropy_regime": "Structured Trend",
                    "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
                    "curated_13f_signal": "Crowded Long",
                    "curated_13f_holders": 3,
                    "curated_13f_weight": "+23.0%",
                    "curated_13f_fresh": 2,
                    "ownership_count": 4,
                    "ownership_weight": "+12.80%",
                },
                {
                    "symbol": "MSFT",
                    "name": "Microsoft",
                    "sector": "Technology",
                    "score": 74.2,
                    "band": "Actionable",
                    "trend_label": "Constructive Trend",
                    "predictability_score": "55.0",
                    "entropy_regime": "Constructive Trend",
                    "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
                    "curated_13f_signal": "Accumulating",
                    "curated_13f_holders": 1,
                    "curated_13f_weight": "+3.4%",
                    "curated_13f_fresh": 1,
                    "ownership_count": 4,
                    "ownership_weight": "+8.20%",
                },
            ]
        },
    )
    monkeypatch.setattr(
        service.tr_funds_service,
        "get_cached_peer_signal_board",
        lambda months: pd.DataFrame(
            [
                {
                    "fund_code": "TCD",
                    "fund_name": "Test Fund",
                    "fund_name_short": "Test Fund",
                    "signal_score": 82.1,
                    "signal_band": "Leading",
                    "board_score": 86.4,
                    "board_band": "Institutional Leader",
                    "regime": "Accumulation",
                    "investor_growth_pct": 8.4,
                    "value_growth_pct": 6.8,
                    "allocation_drift": 4.1,
                    "dominant_asset": "Hisse",
                    "fund_family": "Is Portfoy",
                    "local_factor": "Broad BIST Beta",
                    "quality_tier": "Elite",
                }
            ]
        ),
    )
    monkeypatch.setattr(
        service.tr_funds_service,
        "get_status",
        lambda months: {"status": "healthy", "detail": "Cached peer board available."},
    )
    monkeypatch.setattr(
        service,
        "get_sector_rotation_workspace",
        lambda: {"pattern": "Risk-On Rotation"},
    )

    workspace = service.get_conviction_board_workspace("global", 12, 6)

    assert workspace["headline"]["label"] == "Cross-Asset Confirmation"
    assert workspace["scorecards"][1]["value"] == "1"
    assert workspace["scorecards"][2]["value"] == "3"
    assert workspace["scorecards"][3]["value"] == "2"
    assert workspace["equity_rows"][0]["symbol"] == "NVDA"
    assert workspace["equity_rows"][0]["trend_label"] == "Trend Confirmed"
    assert workspace["tr_fund_rows"][0]["fund_code"] == "TCD"
    assert workspace["tr_fund_rows"][0]["local_factor"] == "Broad BIST Beta"
    assert workspace["top_tr_fund"]["fund_family"] == "Is Portfoy"


def test_get_fundamental_lens_builds_bist_capital_efficiency(monkeypatch):
    service = PublicResearchService()

    class _FakeTicker:
        def __init__(self):
            self.info = {
                "forwardPE": 8.2,
                "priceToBook": 1.4,
                "priceToSalesTrailing12Months": 0.9,
                "pegRatio": 0.8,
                "enterpriseToRevenue": 0.7,
                "enterpriseToEbitda": 4.1,
                "marketCap": 25_000_000_000,
                "enterpriseValue": 24_000_000_000,
                "sharesOutstanding": 1_000_000_000,
                "floatShares": 420_000_000,
                "bookValue": 17.5,
                "revenueGrowth": 0.18,
                "earningsGrowth": 0.22,
                "profitMargins": 0.12,
                "operatingMargins": 0.17,
                "returnOnEquity": 0.24,
                "returnOnAssets": 0.09,
                "operatingCashflow": 3_200_000_000,
                "freeCashflow": 2_100_000_000,
                "ebitda": 4_400_000_000,
            }
            self.financials = pd.DataFrame(
                {
                    pd.Timestamp("2025-12-31"): {
                        "Total Revenue": 12_500_000_000,
                        "Net Income": 2_200_000_000,
                        "Gross Profit": 4_900_000_000,
                        "Operating Income": 3_100_000_000,
                        "Interest Expense": -400_000_000,
                    }
                }
            )
            self.balance_sheet = pd.DataFrame(
                {
                    pd.Timestamp("2025-12-31"): {
                        "Total Assets": 28_000_000_000,
                        "Total Debt": 6_500_000_000,
                        "Stockholders Equity": 9_200_000_000,
                        "Current Assets": 8_100_000_000,
                        "Current Liabilities": 4_200_000_000,
                        "Cash And Cash Equivalents": 2_600_000_000,
                    }
                }
            )
            self.cashflow = pd.DataFrame(
                {
                    pd.Timestamp("2025-12-31"): {
                        "Operating Cash Flow": 3_200_000_000,
                        "Free Cash Flow": 2_100_000_000,
                    }
                }
            )

    monkeypatch.setattr("app.services.public_research.yf.Ticker", lambda symbol: _FakeTicker())
    monkeypatch.setattr(
        service.stock_enrichment_service,
        "get_kap_enrichment",
        lambda symbol: {"source_state": "unavailable", "coverage_note": "Unavailable"},
    )

    lens = service._get_fundamental_lens("THYAO.IS", {"market_cap": 25_000_000_000, "pe_ratio": 8.2})

    assert lens["available"] is True
    assert lens["summary_cards"][0]["value"] in {"Buy", "Strong Buy"}
    assert lens["capital_rows"][0]["value"] == "TRY 1.0B"
    assert lens["capital_rows"][1]["value"] == "2.20x"
    assert lens["capital_rows"][2]["value"] == "12.50x"
    assert any(row["metric"] == "Operating cash flow / paid-in capital" for row in lens["capital_rows"])
    assert any(row["metric"] == "EV/FCF" for row in lens["valuation_rows"])


def test_get_fundamental_lens_uses_kap_enrichment_snapshot_fields(monkeypatch):
    service = PublicResearchService()

    class _FakeTicker:
        def __init__(self):
            self.info = {
                "forwardPE": 10.0,
                "priceToBook": 1.8,
                "marketCap": 18_000_000_000,
                "sharesOutstanding": 1_200_000_000,
                "revenueGrowth": 0.11,
                "earningsGrowth": 0.09,
                "profitMargins": 0.10,
                "operatingMargins": 0.15,
                "returnOnEquity": 0.19,
                "returnOnAssets": 0.08,
                "operatingCashflow": 2_000_000_000,
                "freeCashflow": 1_400_000_000,
                "ebitda": 3_100_000_000,
            }
            self.financials = pd.DataFrame(
                {
                    pd.Timestamp("2025-12-31"): {
                        "Total Revenue": 10_000_000_000,
                        "Net Income": 1_800_000_000,
                        "Gross Profit": 3_200_000_000,
                        "Operating Income": 2_400_000_000,
                        "Interest Expense": -300_000_000,
                    }
                }
            )
            self.balance_sheet = pd.DataFrame(
                {
                    pd.Timestamp("2025-12-31"): {
                        "Total Assets": 24_000_000_000,
                        "Total Debt": 5_000_000_000,
                        "Stockholders Equity": 8_500_000_000,
                        "Current Assets": 6_000_000_000,
                        "Current Liabilities": 3_000_000_000,
                        "Cash And Cash Equivalents": 1_800_000_000,
                    }
                }
            )
            self.cashflow = pd.DataFrame(
                {
                    pd.Timestamp("2025-12-31"): {
                        "Operating Cash Flow": 2_000_000_000,
                        "Free Cash Flow": 1_400_000_000,
                    }
                }
            )

    monkeypatch.setattr("app.services.public_research.yf.Ticker", lambda symbol: _FakeTicker())
    monkeypatch.setattr(
        service.stock_enrichment_service,
        "get_kap_enrichment",
        lambda symbol: {
            "source_state": "live",
            "coverage_note": "Structured KAP enrichment is live.",
            "paid_in_capital": 900_000_000,
            "capital_method": "Exact KAP field via enrichment snapshot",
            "contract_value_ttm": 2_500_000_000,
            "contract_to_sales_ratio_ttm": 0.4115,
            "disclosures_count": 14,
            "material_disclosures_90d": 5,
            "contract_mentions_365d": 4,
            "disclosure_momentum_score": 77.5,
            "last_disclosure_date": "2026-05-28",
        },
    )

    lens = service._get_fundamental_lens("ASELS.IS", {"market_cap": 18_000_000_000, "pe_ratio": 10.0})

    capital_rows = {row["metric"]: row for row in lens["capital_rows"]}
    assert capital_rows["Paid-in capital"]["value"] == "TRY 900.0M"
    assert capital_rows["Net income / paid-in capital"]["value"] == "2.00x"
    assert capital_rows["New contracts / annual sales"]["value"] == "+41.1%"
    assert capital_rows["Recent disclosures"]["value"] == "14"
    assert capital_rows["Material disclosures (90d)"]["value"] == "5"
    assert capital_rows["Contract mentions (365d)"]["value"] == "4"
    assert capital_rows["Disclosure momentum"]["value"] == "77.5"
    assert capital_rows["Last disclosure"]["value"] == "2026-05-28"
    assert "KAP enrichment snapshots" in lens["coverage_note"]


def test_get_stock_workspace_uses_persisted_snapshot_when_cache_empty(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        monkeypatch.setattr(service, "_build_stock_forecast_lens", lambda symbol, signal_history, trend_summary: {"state": "ready"})
        persisted = {
            "requested_symbol": "THYAO",
            "symbol": "THYAO.IS",
            "error": None,
            "featured_symbols": ["AAPL", "THYAO"],
            "overview": {
                "symbol": "THYAO.IS",
                "name": "Turkish Airlines",
                "sector": "Industrials",
                "industry": "Airlines",
                "current_price": "302.40",
                "price_change_percent": "+1.20%",
            },
            "fundamental_lens": {
                "available": True,
                "summary_cards": [],
                "valuation_rows": [],
                "quality_rows": [],
                "capital_rows": [
                    {"metric": "Paid-in capital", "value": "TRY 1.4B", "detail": "Public KAP company general page"},
                    {"metric": "Material disclosures (90d)", "value": "4", "detail": "Special-situation flow in the last 90 days."},
                    {"metric": "Contract mentions (365d)", "value": "2", "detail": "KAP contract-style disclosures deduplicated by notice chain."},
                    {"metric": "Disclosure momentum", "value": "68.0", "detail": "Composite KAP flow score using recency, materiality, and contract intensity."},
                    {"metric": "Last disclosure", "value": "2026-05-28", "detail": "Most recent structured KAP disclosure date if available."},
                ],
                "score": {"overall": 71.0, "valuation": 54.0, "quality": 73.0, "capital": 68.0},
                "coverage_note": "Ratios are derived from Yahoo Finance statements. BIST paid-in capital uses KAP enrichment snapshots when available; otherwise a shares-outstanding proxy is used. KAP enrichment snapshots are live.",
            },
        }
        snapshot_store.write_json(service._stock_snapshot_key("THYAO"), persisted)
        monkeypatch.setattr(
            service,
            "_resolve_stock_payload",
            lambda symbol, period="1y": (_ for _ in ()).throw(AssertionError("live fetch should not run")),
        )

        workspace = service.get_stock_workspace("THYAO")

        assert workspace["overview"]["name"] == "Turkish Airlines"
        assert workspace["symbol"] == "THYAO.IS"
        assert workspace["requested_symbol"] == "THYAO"
        assert workspace["market_profile"]["market_key"] == "bist"
        assert workspace["compare_suggestions"]
        assert workspace["compare_suggestions"][0]["symbol"] != "THYAO.IS"
        assert any(group["market_key"] == "japan" for group in workspace["regional_groups"])


def test_get_stock_workspace_refreshes_legacy_persisted_snapshot(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        monkeypatch.setattr(service, "_build_stock_forecast_lens", lambda symbol, signal_history, trend_summary: {"state": "ready"})
        persisted = {
            "requested_symbol": "ASELS",
            "symbol": "ASELS.IS",
            "error": None,
            "featured_symbols": ["AAPL", "ASELS"],
            "overview": {
                "symbol": "ASELS.IS",
                "name": "ASELSAN",
                "sector": "Industrials",
                "industry": "Defense",
                "current_price": "380.25",
                "price_change_percent": "+1.20%",
            },
            "fundamental_lens": {
                "available": True,
                "score": {"overall": 70.0, "valuation": 55.0, "quality": 75.0},
                "summary_cards": [],
                "valuation_rows": [],
                "quality_rows": [],
                "capital_rows": [],
                "coverage_note": "Old snapshot note",
            },
        }
        snapshot_store.write_json(service._stock_snapshot_key("ASELS"), persisted)

        payload = {
            "symbol": "ASELS.IS",
            "name": "ASELSAN",
            "sector": "Industrials",
            "industry": "Defense",
            "current_price": 380.25,
            "price_change_percent": 1.2,
            "market_cap": 18_000_000_000,
            "pe_ratio": 10.0,
            "beta": 1.0,
            "volume": 1_500_000,
            "52_week_high": 420.0,
            "52_week_low": 200.0,
            "ohlcv_data": [
                {"date": "2026-05-26", "open": 375.0, "high": 382.0, "low": 370.0, "close": 380.25, "volume": 1_500_000},
                {"date": "2026-05-27", "open": 380.0, "high": 386.0, "low": 378.0, "close": 381.1, "volume": 1_620_000},
            ],
        }
        monkeypatch.setattr(service, "_resolve_stock_payload", lambda symbol, period="1y": payload)
        monkeypatch.setattr(
            service.stocks_analyzer,
            "calculate_technical_indicators",
            lambda df: {"RSI": 55.4, "volatility": 21.1, "Bollinger": {"position": "Mid"}, "MACD": {"histogram": 0.32}, "volume_ratio": 1.04, "support_resistance": {"support": 360.0, "resistance": 395.0}},
        )
        monkeypatch.setattr(service.stocks_analyzer, "calculate_returns", lambda series: {"1M": 3.2, "3M": 9.4})
        monkeypatch.setattr(
            service.trend_analyzer,
            "comprehensive_trend_analysis",
            lambda df: {
                "overall_assessment": {"overall_trend": "bullish", "confidence": 64.0, "recommendation": "Buy", "bullish_signals": 4, "bearish_signals": 1},
                "patterns": {"patterns": []},
                "breakouts": {"breakouts": []},
            },
        )
        monkeypatch.setattr(
            service,
            "_get_fundamental_lens",
            lambda symbol, payload: {
                "available": True,
                "summary_cards": [],
                "valuation_rows": [],
                "quality_rows": [],
                "capital_rows": [{"metric": "Last disclosure", "value": "2026-05-28", "detail": "Most recent structured KAP disclosure date if available."}],
                "score": {"overall": 72.0, "valuation": 55.0, "quality": 74.0, "capital": 69.0},
                "growth_profile": {},
                "strengths": [],
                "concerns": [],
                "coverage_note": "Ratios are derived from Yahoo Finance statements. BIST paid-in capital uses KAP enrichment snapshots when available; otherwise a shares-outstanding proxy is used.",
            },
        )
        monkeypatch.setattr(service, "_get_sector_context", lambda symbol: {"available": False})
        monkeypatch.setattr(service, "_get_institutional_snapshot", lambda symbol: {"available": False})
        monkeypatch.setattr(service, "_get_curated_13f_signal", lambda symbol, issuer_name=None: {"available": False})
        monkeypatch.setattr(service.collector, "search_symbol", lambda symbol: [])

        workspace = service.get_stock_workspace("ASELS")
        refreshed = snapshot_store.read_json(service._stock_snapshot_key("ASELS"))

        assert workspace["symbol"] == "ASELS.IS"
        assert workspace["fundamental_lens"]["score"]["capital"] == 69.0
        assert refreshed is not None
        assert refreshed["fundamental_lens"]["capital_rows"][0]["metric"] == "Last disclosure"


def test_stock_snapshot_is_not_current_when_bist_kap_fields_are_proxy_only():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        snapshot = {
            "symbol": "TUPRS.IS",
            "overview": {"name": "Tupras", "current_price": "236.20"},
            "fundamental_lens": {
                "score": {"capital": 95.0},
                "capital_rows": [
                    {
                        "metric": "Paid-in capital",
                        "value": "TRY 1.9B",
                        "detail": "Nominal capital proxy from shares outstanding (TRY 1 par assumption)",
                    },
                    {
                        "metric": "Last disclosure",
                        "value": "N/A",
                        "detail": "Most recent structured KAP disclosure date if available.",
                    },
                ],
                "coverage_note": (
                    "Ratios are derived from Yahoo Finance statements. "
                    "BIST paid-in capital uses KAP enrichment snapshots when available; "
                    "otherwise a shares-outstanding proxy is used. "
                    "KAP enrichment is temporarily unavailable."
                ),
            },
        }

        assert service._stock_snapshot_is_current(snapshot) is False


def test_stock_snapshot_is_not_current_when_bist_disclosure_metrics_are_missing():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        snapshot = {
            "symbol": "ASELS.IS",
            "overview": {"name": "Aselsan", "current_price": "138.40"},
            "fundamental_lens": {
                "score": {"capital": 88.0},
                "capital_rows": [
                    {
                        "metric": "Paid-in capital",
                        "value": "TRY 4.6B",
                        "detail": "Public KAP company general page",
                    },
                    {
                        "metric": "Last disclosure",
                        "value": "2026-05-22",
                        "detail": "Most recent structured KAP disclosure date if available.",
                    },
                ],
                "coverage_note": (
                    "Ratios are derived from Yahoo Finance statements. "
                    "BIST paid-in capital uses KAP enrichment snapshots when available; "
                    "otherwise a shares-outstanding proxy is used. "
                    "KAP public general page and public disclosure feed were parsed successfully."
                ),
            },
        }

        assert service._stock_snapshot_is_current(snapshot) is False


def test_fundamental_overlay_uses_kap_enrichment_for_bist_rows_without_stock_snapshot(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        monkeypatch.setattr(
            service.stock_enrichment_service,
            "get_kap_enrichment",
            lambda symbol: {
                "source_state": "live",
                "paid_in_capital": 1_000_000_000,
                "contract_value_ttm": 1_500_000_000,
                "disclosures_count": 9,
                "last_disclosure_date": "2026-05-28",
            },
        )

        overlay = service._fundamental_overlay(
            "THYAO.IS",
            {
                "market_cap": 24_000_000_000,
                "pe_ratio": 8.0,
                "pb_ratio": 1.2,
                "profit_margin": 12.0,
                "roe": 24.0,
                "debt_to_equity": 35.0,
            },
        )

        assert overlay["source"] == "approx+kap"
        assert overlay["capital_profile"] in {"High Conversion", "Healthy"}
        assert overlay["net_income_to_capital"] == "3.00x"
        assert overlay["contracts_to_sales"] == "+6.0%"


def test_get_stock_workspace_force_refresh_persists_requested_and_resolved_snapshots(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        monkeypatch.setattr(service, "_build_stock_forecast_lens", lambda symbol, signal_history, trend_summary: {"state": "ready"})
        payload = {
            "symbol": "THYAO.IS",
            "name": "Turkish Airlines",
            "sector": "Industrials",
            "industry": "Airlines",
            "current_price": 302.4,
            "price_change_percent": 1.2,
            "market_cap": 25_000_000_000,
            "pe_ratio": 7.8,
            "beta": 1.12,
            "volume": 12_500_000,
            "52_week_high": 355.0,
            "52_week_low": 220.0,
            "ohlcv_data": [
                {"date": "2026-05-26", "open": 298.0, "high": 304.0, "low": 296.5, "close": 302.4, "volume": 12_500_000},
                {"date": "2026-05-27", "open": 301.0, "high": 306.0, "low": 299.5, "close": 303.2, "volume": 13_000_000},
            ],
        }
        monkeypatch.setattr(service, "_resolve_stock_payload", lambda symbol, period="1y": payload)
        monkeypatch.setattr(
            service.stocks_analyzer,
            "calculate_technical_indicators",
            lambda df: {"RSI": 58.4, "volatility": 22.1, "Bollinger": {"position": "Mid"}, "MACD": {"histogram": 0.42}, "volume_ratio": 1.14, "support_resistance": {"support": 292.0, "resistance": 312.0}},
        )
        monkeypatch.setattr(service.stocks_analyzer, "calculate_returns", lambda series: {"1M": 4.2, "3M": 8.1})
        monkeypatch.setattr(
            service.trend_analyzer,
            "comprehensive_trend_analysis",
            lambda df: {
                "overall_assessment": {"overall_trend": "bullish", "confidence": 68.0, "recommendation": "Buy", "bullish_signals": 3, "bearish_signals": 1},
                "patterns": {"patterns": []},
                "breakouts": {"breakouts": []},
            },
        )
        monkeypatch.setattr(service, "_get_fundamental_lens", lambda symbol, payload: {"available": True, "summary_cards": [], "valuation_rows": [], "quality_rows": [], "capital_rows": [], "growth_profile": {}, "strengths": [], "concerns": [], "coverage_note": "Test"})
        monkeypatch.setattr(service, "_get_sector_context", lambda symbol: {"available": False})
        monkeypatch.setattr(service, "_get_institutional_snapshot", lambda symbol: {"available": False})
        monkeypatch.setattr(service, "_get_curated_13f_signal", lambda symbol, issuer_name=None: {"available": False})
        monkeypatch.setattr(service.collector, "search_symbol", lambda symbol: [])

        workspace = service.get_stock_workspace("THYAO", force_refresh=True)
        requested_snapshot = snapshot_store.read_json(service._stock_snapshot_key("THYAO"))
        resolved_snapshot = snapshot_store.read_json(service._stock_snapshot_key("THYAO.IS"))

        assert workspace["symbol"] == "THYAO.IS"
        assert workspace["requested_symbol"] == "THYAO"
        assert requested_snapshot is not None
        assert resolved_snapshot is not None
        assert requested_snapshot["overview"]["name"] == "Turkish Airlines"
        assert resolved_snapshot["overview"]["symbol"] == "THYAO.IS"


def test_build_stock_forecast_lens_uses_entropy_and_validation(monkeypatch):
    service = PublicResearchService()
    monkeypatch.setattr(
        service,
        "get_forecast_workspace",
        lambda symbol, days: {
            "chart_svg": "<svg viewBox='0 0 10 10'></svg>",
            "trend_bias": "Bullish",
            "consensus_price": "210.00",
            "consensus_delta": "+5.00%",
            "best_model": {"model_label": "Random Forest"},
            "entropy_signal": {
                "regime": "Structured Trend",
                "predictability_score": 68.0,
                "change_20d_label": "+4.2%",
                "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            },
            "validation_summary": {
                "state": "Validated",
                "detail": "Rendered models passed sanity checks.",
            },
        },
    )

    lens = service._build_stock_forecast_lens(
        "AAPL",
        [
            {"month": "2026-03", "return_1m": "+2.4%", "posture": "Constructive"},
            {"month": "2026-04", "return_1m": "+4.1%", "posture": "Expansion"},
            {"month": "2026-05", "return_1m": "+3.2%", "posture": "Trend Up"},
        ],
        {"bullish_signals": 3, "bearish_signals": 1},
    )

    assert lens["state"] == "ready"
    assert lens["trend_persistence"]["label"] == "Persistent"
    assert lens["entropy_signal"]["regime"] == "Structured Trend"
    assert lens["validation_summary"]["state"] == "Validated"


def test_get_compare_workspace_uses_exchange_aware_default_for_regional_stocks(monkeypatch):
    service = PublicResearchService()

    def _fake_stock_workspace(symbol: str, force_refresh: bool = False):
        normalized = str(symbol).upper()
        return {
            "symbol": normalized,
            "overview": {"symbol": normalized, "name": normalized, "pe_ratio": "20.0"},
            "return_signals": [{"label": "3M", "value": "+10.0%"}],
            "fundamental_lens": {"score": {"overall": 60.0, "capital": 55.0}, "capital_rows": []},
            "curated_13f": {"summary": {"holder_count": 0}},
            "forecast_lens": {
                "trend_bias": "Bullish",
                "consensus_delta": "+5.0%",
                "trend_persistence": {"label": "Persistent"},
                "entropy_signal": {"regime": "Structured Trend", "predictability_score": 68.0},
                "validation_summary": {"state": "Validated"},
            },
            "what_changed": [],
            "data_confidence": {"label": "Live"},
        }

    monkeypatch.setattr(service, "get_stock_workspace", _fake_stock_workspace)

    workspace = service.get_compare_workspace("stocks", "7203.T", None)

    assert workspace["left_symbol"] == "7203.T"
    assert workspace["right_symbol"] == "6758.T"
    assert workspace["compare_suggestions"]
    assert workspace["compare_suggestions"][0]["symbol"] == "6758.T"
    assert workspace["regime_workspace"]["headline"]["winner"] in {"Left", "Even", "Right"}
    assert workspace["regime_workspace"]["rows"][0]["metric"] == "Trend persistence"


def test_get_tr_fund_workspace_uses_persisted_snapshot_when_cache_empty(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        persisted = {
            "fund_code": "TCD",
            "error": None,
            "featured_funds": ["TCD", "AFT", "YAT", "GPD"],
            "selected_months": 6,
            "overview": {"fund_name": "Persisted Fund", "latest_portfolio_value": "$1.0M", "latest_num_investors": "1,250"},
            "signal_card": {"signal_band": "Leading"},
            "allocation_rows": [],
            "monthly_rows": [],
            "evolution_rows": [],
        }
        snapshot_store.write_json(service._tr_fund_snapshot_key("TCD", 6), persisted)
        monkeypatch.setattr(
            service.tr_funds_service,
            "get_cached_peer_signal_board",
            lambda months: pd.DataFrame([{"fund_code": "GAH"}]),
        )
        monkeypatch.setattr(
            service.tr_funds_service,
            "get_fund_summary",
            lambda fund_code, months, force_refresh=False: (_ for _ in ()).throw(AssertionError("live fetch should not run")),
        )

        workspace = service.get_tr_fund_workspace("TCD", 6)

        assert workspace["overview"]["fund_name"] == "Persisted Fund"
        assert workspace["signal_card"]["signal_band"] == "Leading"
        assert workspace["featured_funds"] == ["TCD", "GAH"]


def test_get_fund_workspace_restores_monthly_asset_and_holdings_drift(monkeypatch):
    cache_clear()
    service = PublicResearchService()
    monkeypatch.setattr(
        service,
        "_build_fund_forecast_lens",
        lambda symbol, monthly_rows, performance_cards: {
            "state": "ready",
            "trend_persistence": {"label": "Persistent", "detail": "Wrapper trend is aligned."},
        },
    )

    monthly_index = pd.date_range("2025-11-28", periods=7, freq="M")
    fund_history = pd.DataFrame(
        {
            "Close": [500.0, 510.0, 520.0, 505.0, 530.0, 545.0, 560.0],
            "Volume": [10_000_000, 10_500_000, 11_200_000, 9_800_000, 12_100_000, 12_600_000, 13_400_000],
            "High": [505.0, 515.0, 525.0, 510.0, 535.0, 550.0, 565.0],
            "Low": [495.0, 505.0, 515.0, 500.0, 525.0, 540.0, 555.0],
        },
        index=monthly_index,
    )

    class FakeFundAnalyzer:
        def __init__(self, symbol: str):
            self.fund_symbol = symbol
            self.fund_data = fund_history

        def get_comprehensive_analysis(self):
            return {
                "basic_info": {
                    "fund_name": "SPDR S&P 500 ETF Trust",
                    "fund_family": "State Street",
                    "category": "Large Blend",
                    "total_assets": 500_000_000_000,
                    "expense_ratio": 0.000945,
                    "yield": 0.013,
                    "beta": 1.0,
                    "morningstar_rating": 5,
                },
                "performance_metrics": {
                    "return_1M": 2.8,
                    "return_3M": 7.4,
                    "return_1Y": 18.1,
                    "return_3Y": 31.0,
                    "annual_volatility": 14.2,
                    "max_drawdown": -11.5,
                    "sharpe_ratio": 1.24,
                },
                "risk_metrics": {
                    "sortino_ratio": 1.7,
                    "var_95": -1.9,
                    "correlation_spy": 1.0,
                },
                "holdings_analysis": {
                    "holdings_count": 500,
                    "top_10_concentration": 32.1,
                    "top_holdings": [{"holdingName": "Apple Inc.", "symbol": "AAPL", "weight": 6.5}],
                    "sector_allocation": {"Technology": 28.5},
                    "geographic_allocation": {"United States": 100.0},
                },
                "fund_rating": {
                    "overall_rating": 8.5,
                    "performance_rating": 9,
                    "risk_rating": 7,
                    "cost_rating": 9,
                    "rating_explanation": "Good - Strong performance with reasonable risk and costs",
                },
            }

        def compare_with_benchmark(self, benchmark_symbol: str = "SPY"):
            return {"comparison_metrics": {"return_1Y_vs_benchmark": 0.0}}

    monkeypatch.setattr(public_research_module, "ComprehensiveFundAnalyzer", FakeFundAnalyzer)
    monkeypatch.setattr(service.etf_tracker, "fetch_etf_holdings", lambda symbol, force_refresh=False: pd.DataFrame())
    monkeypatch.setattr(
        service.etf_tracker,
        "get_fund_snapshot_history",
        lambda symbol, months=6, top_n=10: pd.DataFrame(
            [
                {
                    "month": "2026-04",
                    "top_holding": "AAPL",
                    "top_weight": 6.2,
                    "top_10_concentration": 31.4,
                    "holdings_count": 500,
                    "primary_shift_symbol": "MSFT",
                    "primary_shift_pct": 0.4,
                    "added_count": 2,
                    "removed_count": 1,
                },
                {
                    "month": "2026-05",
                    "top_holding": "AAPL",
                    "top_weight": 6.5,
                    "top_10_concentration": 32.1,
                    "holdings_count": 500,
                    "primary_shift_symbol": "NVDA",
                    "primary_shift_pct": 0.6,
                    "added_count": 1,
                    "removed_count": 0,
                },
            ]
        ),
    )

    workspace = service.get_fund_workspace("SPY")

    assert workspace["overview"]["fund_name"] == "SPDR S&P 500 ETF Trust"
    assert workspace["market_profile"]["market_key"] == "us-core"
    assert workspace["compare_cta_path"].endswith("left=SPY&right=QQQ")
    assert workspace["overlap_cta_path"].endswith("focus=core")
    assert workspace["forecast_cta_path"].endswith("symbol=SPY&days=21")
    assert workspace["forecast_lens"]["state"] == "ready"
    assert workspace["compare_suggestions"][0]["symbol"] == "QQQ"
    assert workspace["regional_groups"][0]["market_key"] == "us-core"
    assert workspace["monthly_rows"]
    assert workspace["monthly_rows"][-1]["asset_base_proxy"].startswith("$")
    assert workspace["monthly_note"].startswith("Asset-base rows are monthly AUM proxies")
    assert workspace["holdings_timeline_rows"][0]["primary_shift"] == "MSFT +0.40%"
    assert workspace["holdings_timeline_note"].startswith("Month-end holdings snapshots")


def test_get_compare_workspace_uses_region_aware_default_for_funds(monkeypatch):
    service = PublicResearchService()

    def _fake_fund_workspace(symbol: str):
        normalized = str(symbol).upper()
        return {
            "symbol": normalized,
            "overview": {
                "fund_name": normalized,
                "expense_ratio": "+0.45%",
            },
            "performance_cards": [{"label": "1Y", "value": "+12.0%"}],
            "risk_snapshot": {"volatility": "+14.0%"},
            "holdings_summary": {"top_10_concentration": "+28.0%"},
            "monthly_rows": [{"posture": "Balanced"}],
            "forecast_lens": {
                "trend_bias": "Bullish",
                "consensus_delta": "+3.0%",
                "trend_persistence": {"label": "Developing"},
                "entropy_signal": {"regime": "Constructive Trend", "predictability_score": 60.0},
                "validation_summary": {"state": "Validated"},
            },
            "compare_suggestions": [],
        }

    monkeypatch.setattr(service, "get_fund_workspace", _fake_fund_workspace)

    workspace = service.get_compare_workspace("funds", "EWJ", None)

    assert workspace["left_symbol"] == "EWJ"
    assert workspace["right_symbol"] == "DXJ"
    assert workspace["compare_suggestions"]
    assert workspace["compare_suggestions"][0]["symbol"] == "DXJ"
    assert workspace["regime_workspace"]["rows"][1]["metric"] == "Entropy regime"


def test_build_fund_forecast_lens_uses_entropy_and_validation(monkeypatch):
    service = PublicResearchService()
    monkeypatch.setattr(
        service,
        "get_forecast_workspace",
        lambda symbol, days: {
            "chart_svg": "<svg viewBox='0 0 10 10'></svg>",
            "trend_bias": "Bullish",
            "consensus_price": "603.00",
            "consensus_delta": "+4.80%",
            "best_model": {"model_label": "Random Forest"},
            "entropy_signal": {
                "regime": "Structured Trend",
                "predictability_score": 66.0,
                "change_20d_label": "+3.8%",
                "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            },
            "validation_summary": {
                "state": "Validated",
                "detail": "Rendered models passed sanity checks.",
            },
        },
    )

    lens = service._build_fund_forecast_lens(
        "SPY",
        [
            {"month": "2026-03", "monthly_return": "+1.4%", "posture": "Constructive"},
            {"month": "2026-04", "monthly_return": "+2.6%", "posture": "Expansion"},
            {"month": "2026-05", "monthly_return": "+1.9%", "posture": "Balanced"},
        ],
        [
            {"label": "1M", "value": "+1.9%"},
            {"label": "1Y", "value": "+18.1%"},
        ],
    )

    assert lens["state"] == "ready"
    assert lens["trend_persistence"]["label"] == "Persistent"
    assert lens["entropy_signal"]["regime"] == "Structured Trend"
    assert lens["validation_summary"]["state"] == "Validated"


def test_get_forecast_workspace_builds_chart_entropy_and_validation(monkeypatch):
    cache_clear()
    service = PublicResearchService()

    history_index = pd.date_range("2026-01-02", periods=140, freq="B")
    history = pd.DataFrame(
        {
            "Close": np.linspace(120.0, 165.0, len(history_index)),
        },
        index=history_index,
    )

    class FakePredictionEngine:
        def __init__(self, symbol: str, period: str = "2y"):
            self.symbol = symbol
            self.period = period
            self.data = history

        def get_all_predictions(self, days: int = 30):
            future_dates = pd.date_range(start=history.index[-1] + pd.Timedelta(days=1), periods=days)
            return {
                "Random Forest": {
                    "model_name": "Random Forest",
                    "predictions": np.linspace(166.0, 174.0, days),
                    "dates": future_dates,
                    "metrics": {"RMSE": 4.2, "MAE": 3.1, "R²": 0.82},
                },
                "Linear Regression": {
                    "model_name": "Linear Regression",
                    "predictions": np.linspace(165.5, 171.0, days),
                    "dates": future_dates,
                    "metrics": {"RMSE": 6.8, "MAE": 5.0, "R²": 0.71},
                },
                "Broken Model": {
                    "model_name": "Broken Model",
                    "predictions": np.array([np.nan] * days),
                    "dates": future_dates,
                    "metrics": {"RMSE": 99.0, "MAE": 99.0},
                },
            }

    monkeypatch.setattr(public_research_module, "PublicPricePredictionEngine", FakePredictionEngine)

    workspace = service.get_forecast_workspace("NVDA", 30)

    assert workspace["chart_svg"].startswith("<svg")
    assert workspace["chart_legend_rows"][0]["label"] == "Consensus"
    assert workspace["validation_summary"]["state"] == "Partial"
    assert workspace["validation_summary"]["rejected_models"] == 1
    assert workspace["entropy_signal"]["predictability_score"] is not None
    assert workspace["entropy_signal"]["note"].startswith("We use entropy because")
    assert workspace["model_rows"][0]["model_label"] == "Random Forest"
    assert all(row["validation"] == "Validated" for row in workspace["model_rows"])


def test_get_tr_fund_workspace_force_refresh_persists_snapshot(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        monkeypatch.setattr(
            service.tr_funds_service,
            "get_fund_summary",
            lambda fund_code, months, force_refresh=False: {
                "fund_name": "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu",
                "latest_portfolio_value": 200.0,
                "portfolio_value_change": 40.0,
                "latest_num_investors": 120.0,
                "investor_change": 30.0,
                "asset_allocation_current": {"stocks": 62.0, "repo": 12.0},
                "asset_allocation_initial": {"stocks": 58.0, "repo": 15.0},
                "monthly_allocation_changes": [{"month": "2026-05", "stocks_change": 4.0, "repo_change": -3.0}],
                "top_holdings_evolution": [{"month": "2026-05", "security_name": "BIST30", "weight": 8.2, "rank": 1, "value": 82.0}],
                "category": "Equity",
                "category_rank": 1,
                "category_count": 14,
                "market_share": 1.2,
                "current_price": 12.3456,
                "daily_return": 1.1,
            },
        )

        workspace = service.get_tr_fund_workspace("TCD", 6, force_refresh=True)
        persisted = snapshot_store.read_json(service._tr_fund_snapshot_key("TCD", 6))

        assert workspace["overview"]["fund_name"] == "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu"
        assert persisted is not None
        assert persisted["signal_card"]["board_band"] == "Institutional Leader"


def test_get_tr_fund_workspace_falls_back_to_peer_board_when_summary_missing(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        monkeypatch.setattr(
            service.tr_funds_service,
            "get_fund_summary",
            lambda fund_code, months, force_refresh=False: {},
        )
        monkeypatch.setattr(
            service.tr_funds_service,
            "get_cached_peer_signal_board",
            lambda months: pd.DataFrame(
                [
                    {
                        "fund_code": "TCD",
                        "fund_name": "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu",
                        "fund_name_short": "Is Dow Jones Istanbul 30",
                        "signal_score": 28.1,
                        "signal_band": "Under Pressure",
                        "board_score": 31.4,
                        "board_band": "Low Conviction",
                        "regime": "Distribution",
                        "latest_portfolio_value": 1_417_946_849.5,
                        "portfolio_value_change": -59_718_826.22,
                        "value_growth_pct": -4.0,
                        "latest_num_investors": 12456,
                        "investor_change": -678,
                        "investor_growth_pct": -5.2,
                        "dominant_asset": "Hisse",
                        "dominant_weight": 67.87,
                        "fund_family": "Is Portfoy",
                        "local_factor": "Balanced Allocation",
                        "quality_tier": "Established",
                        "category": "Değişken Fon",
                        "category_rank": 55,
                        "category_count": 172,
                        "category_percentile": 68.4,
                        "market_share": 1.19,
                    }
                ]
            ),
        )

        workspace = service.get_tr_fund_workspace("TCD", 6)

        assert workspace["error"] is None
        assert workspace["data_state"] == "signal-board-fallback"
        assert workspace["overview"]["fund_name"] == "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu"
        assert workspace["signal_card"]["regime_note"].startswith("Detailed TEFAS allocation snapshot is unavailable")


def test_get_tr_fund_workspace_substitutes_best_available_fund_when_requested_code_is_unavailable(monkeypatch):
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        snapshot_store.write_json(
            service._tr_fund_snapshot_key("AFT", 6),
            {
                "fund_code": "AFT",
                "error": None,
                "featured_funds": ["AFT"],
                "selected_months": 6,
                "overview": {
                    "fund_name": "",
                    "latest_portfolio_value": "$0",
                    "latest_num_investors": "0",
                },
                "signal_card": {"signal_band": "Neutral"},
                "allocation_rows": [],
                "monthly_rows": [],
                "evolution_rows": [],
            },
        )

        def _summary(fund_code, months, force_refresh=False):
            if fund_code == "AFT":
                return {
                    "fund_name": "",
                    "latest_portfolio_value": 0.0,
                    "portfolio_value_change": 0.0,
                    "latest_num_investors": 0.0,
                    "investor_change": 0.0,
                    "asset_allocation_current": {"stocks": 98.7},
                    "asset_allocation_initial": {"stocks": 98.7},
                    "monthly_allocation_changes": [],
                    "top_holdings_evolution": [],
                }
            if fund_code == "GAH":
                return {
                    "fund_name": "Garanti Portfoy Dynamic Fund",
                    "latest_portfolio_value": 300.0,
                    "portfolio_value_change": 30.0,
                    "latest_num_investors": 200.0,
                    "investor_change": 20.0,
                    "asset_allocation_current": {"stocks": 54.0, "repo": 18.0},
                    "asset_allocation_initial": {"stocks": 49.0, "repo": 20.0},
                    "monthly_allocation_changes": [],
                    "top_holdings_evolution": [],
                    "category": "Equity",
                    "category_rank": 4,
                    "category_count": 21,
                    "market_share": 0.9,
                    "current_price": 10.5,
                    "daily_return": 0.4,
                }
            return {}

        monkeypatch.setattr(service.tr_funds_service, "get_fund_summary", _summary)
        monkeypatch.setattr(
            service.tr_funds_service,
            "get_cached_peer_signal_board",
            lambda months: pd.DataFrame(
                [
                    {
                        "fund_code": "GAH",
                        "fund_name": "Garanti Portfoy Dynamic Fund",
                        "fund_name_short": "Garanti Dynamic",
                        "signal_score": 61.0,
                        "signal_band": "Constructive",
                        "board_score": 64.2,
                        "board_band": "Actionable",
                        "regime": "Accumulation",
                        "latest_portfolio_value": 3_000_000.0,
                        "portfolio_value_change": 100_000.0,
                        "value_growth_pct": 3.4,
                        "latest_num_investors": 20_000,
                        "investor_change": 800,
                        "investor_growth_pct": 4.2,
                        "dominant_asset": "Hisse",
                        "dominant_weight": 54.0,
                        "fund_family": "Garanti Portfoy",
                        "local_factor": "Broad BIST Beta",
                        "quality_tier": "Established",
                        "category": "Equity",
                        "category_rank": 4,
                        "category_count": 21,
                        "category_percentile": 81.0,
                        "market_share": 0.9,
                    }
                ]
            ),
        )

        workspace = service.get_tr_fund_workspace("AFT", 6)

        assert workspace["error"] is None
        assert workspace["fund_code"] == "GAH"
        assert workspace["requested_fund_code"] == "AFT"
        assert workspace["fallback_notice"].startswith("AFT is unavailable")


def test_featured_tr_funds_prefers_available_snapshots_and_peer_board(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service = PublicResearchService(snapshot_store=snapshot_store)
        snapshot_store.write_json(
            service.tr_funds_service._summary_snapshot_key("YAT", 6),
            {"saved_at": "2026-05-28T00:00:00Z", "fund_code": "YAT", "months": 6, "summary": {"fund_name": "YAT"}},
        )
        monkeypatch.setattr(
            service.tr_funds_service,
            "get_cached_peer_signal_board",
            lambda months: pd.DataFrame([{"fund_code": "GAH"}, {"fund_code": "ZPE"}]),
        )

        featured = service._featured_tr_funds(6)

        assert featured == ["TCD", "YAT", "GAH", "ZPE"]
