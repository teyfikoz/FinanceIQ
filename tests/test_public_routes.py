import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.api import public as public_api
from app.main import app
from app.web import routes as web_routes


client = TestClient(app)
safe_client = TestClient(app, raise_server_exceptions=False)


def _fake_snapshot():
    influence_workspace = _fake_influence_workspace()
    return {
        "generated_at": "2026-05-26T00:00:00Z",
        "sentiment": {
            "mood": "Constructive",
            "score": 0.61,
            "fear_greed_value": 60,
            "vix_label": "18.40",
        },
        "market_cards": [],
        "entropy_signal": {
            "state": "healthy",
            "state_label": "Healthy",
            "regime": "Constructive Trend",
            "stance": "Signals are orderly.",
            "predictability_score": 61.2,
            "complexity_score": 38.8,
            "leader_asset": "S&P 500",
            "leader_symbol": "^GSPC",
            "window_days": 90,
            "updated_at": "2026-05-26T00:00:00Z",
            "asset_rows": [
                {
                    "label": "S&P 500",
                    "symbol": "^GSPC",
                    "regime": "Trending (Moderate Entropy)",
                    "risk_level": "Low Risk (Trending)",
                    "posture": "Trend Confirming",
                    "predictability_score": 68.0,
                    "complexity_score": 32.0,
                    "change_20d_label": "+3.4%",
                }
            ],
            "note": "Test note",
        },
        "market_physics": {
            "state": "healthy",
            "state_label": "Healthy",
            "phase_regime": "Coherent Trend",
            "stance": "Cross-horizon direction is aligned.",
            "average_phase_score": 72.4,
            "leader_asset": "S&P 500",
            "leader_symbol": "^GSPC",
            "updated_at": "2026-05-26T00:00:00Z",
            "rows": [
                {
                    "label": "S&P 500",
                    "symbol": "^GSPC",
                    "phase_label": "In-Phase Upswing",
                    "phase_score": 78.0,
                    "spectral_clarity": 71.0,
                    "change_5d_label": "+1.4%",
                    "change_20d_label": "+3.4%",
                    "change_60d_label": "+8.4%",
                    "predictability_score": 68.0,
                }
            ],
            "note": "Phase note",
        },
        "macro_cards": [],
        "crypto_cards": [],
        "tr_top_pick": {
            "fund_code": "TCD",
            "fund_name": "Test Fund",
            "signal_band": "Leading",
            "signal_score": 81.2,
            "investor_growth_pct": 11.4,
            "dominant_asset": "Hisse",
        },
        "tr_peer_board": [],
        "bist_catalyst_rows": [
            {
                "symbol": "ASELS.IS",
                "name": "ASELSAN",
                "sector": "Industrials",
                "disclosure_momentum_score": "91.0",
                "contracts_to_sales": "+31.4%",
                "capital_profile": "High Conversion",
                "trend_label": "Trend Confirmed",
                "predictability_score": "66.0",
                "catalyst_clean_score": "82.5",
                "catalyst_tape_label": "Catalyst + Clean Tape",
                "detail_path": "/stocks?symbol=ASELS.IS",
            }
        ],
        "bist_catalyst_summary": {
            "state": "healthy",
            "state_label": "Catalyst + Clean Tape",
            "detail": "BIST lane now blends KAP flow with tape cleanliness.",
            "leader": "ASELS.IS",
            "leader_predictability": "66.0",
            "leader_clean_score": "82.5",
            "active_count": 4,
        },
        "influence_rows": influence_workspace["pair_rows"],
        "influence_summary": influence_workspace["headline"],
        "source_health": [
            {
                "key": "market",
                "label": "Market feed",
                "state": "healthy",
                "state_label": "Healthy",
                "detail": "6 market cards rendered from Yahoo Finance.",
                "updated_at": "2026-05-26T00:00:00Z",
            }
        ],
        "sponsor_slots": [],
        "editorial_cards": [],
        "sponsor_disclosure": "Test disclosure",
        "privacy_promise": "Test privacy promise",
        "coverage_cards": [],
    }


def _fake_reliability_workspace():
    return {
        "generated_at": "2026-06-02T08:00:00Z",
        "source_health": [
            {
                "key": "kap-enrichment",
                "label": "BIST disclosures",
                "state": "healthy",
                "state_label": "Healthy",
                "detail": "Structured KAP enrichment is live for all curated names.",
                "updated_at": "2026-06-02T08:00:00Z",
            },
            {
                "key": "institutional",
                "label": "Institutional filings",
                "state": "degraded",
                "state_label": "Fallback Active",
                "detail": "4 live, 1 snapshot manager.",
                "updated_at": "2026-06-02T08:00:00Z",
            },
        ],
        "kap_health": {
            "summary": {
                "symbols_tracked": 5,
                "live_count": 4,
                "fallback_count": 1,
                "unavailable_count": 0,
                "average_field_coverage": 4.2,
                "latest_disclosure_date": "2026-06-01",
            },
            "rows": [
                {
                    "symbol": "ASELS",
                    "source_state": "live",
                    "field_coverage": 5,
                    "last_disclosure_date": "2026-06-01",
                    "contract_to_sales_ratio_ttm": 0.42,
                    "disclosure_momentum_score": 91.0,
                }
            ],
        },
        "tr_status": {
            "status": "healthy",
            "detail": "Persisted peer board available with 6 rows.",
            "funds_loaded": 6,
            "funds_requested": 6,
            "last_success_at": "2026-06-02T07:50:00Z",
            "error_count": 0,
        },
        "institutional_workspace": _fake_institutional_pulse_workspace("berkshire"),
        "outlook_rows": [
            {
                "horizon": "6 months",
                "label": "Operationally stable",
                "state": "Low risk",
                "detail": "Snapshots and prewarm are keeping the surface reliable.",
            }
        ],
        "next_moves": [
            {
                "title": "Shared cache before multi-worker scale",
                "detail": "Adopt Redis before increasing worker count.",
            }
        ],
    }


def _fake_influence_workspace():
    return {
        "generated_at": "2026-06-04T10:00:00Z",
        "headline": {
            "label": "VIX -> Nasdaq",
            "detail": "VIX is leading Nasdaq more than the reverse loop right now.",
        },
        "summary_cards": [
            {"label": "Directed flows", "value": "7", "detail": "Stable pairs"},
            {"label": "Leading macro source", "value": "VIX", "detail": "Macro leader across targets."},
            {"label": "Most influenced target", "value": "Nasdaq", "detail": "Highest incoming pressure."},
        ],
        "pair_rows": [
            {
                "source_label": "VIX",
                "source_group": "Volatility",
                "target_label": "Nasdaq",
                "target_group": "Equities",
                "state_label": "Source Leading",
                "net_influence": "0.144",
                "forward_te": "0.210",
                "reverse_te": "0.066",
                "source_change_20d": "-6.2%",
                "target_change_20d": "+4.8%",
            }
        ],
        "source_rows": [
            {"label": "VIX", "group": "Volatility", "lead_bias": "Macro leader", "leading_count": 3, "average_net": "0.121"}
        ],
        "target_rows": [
            {"label": "Nasdaq", "group": "Equities", "incoming_pressure": "0.238", "pairs": 3}
        ],
        "methodology": ["Transfer entropy is directional, unlike correlation."],
    }


def _fake_stock_workspace(symbol: str):
    return {
        "symbol": symbol,
        "error": None,
        "featured_symbols": ["AAPL", "NVDA"],
        "compare_cta_path": f"/compare?kind=stocks&left={symbol}&right=NVDA",
        "forecast_cta_path": f"/forecasts?symbol={symbol}&days=21",
        "market_profile": {
            "market_key": "us",
            "market_label": "US Leaders",
            "exchange": "NYSE / Nasdaq",
            "description": "US coverage remains deepest on sector context, curated 13F sponsorship, and ETF ownership overlap.",
        },
        "compare_suggestions": [
            {"symbol": "NVDA", "label": f"{symbol} vs NVDA", "reason": "Same-market compare inside US Leaders.", "path": f"/compare?kind=stocks&left={symbol}&right=NVDA"},
            {"symbol": "MSFT", "label": f"{symbol} vs MSFT", "reason": "Same-market compare inside US Leaders.", "path": f"/compare?kind=stocks&left={symbol}&right=MSFT"},
        ],
        "regional_groups": [
            {
                "market_key": "us",
                "label": "US Leaders",
                "exchange": "NYSE / Nasdaq",
                "selected": True,
                "symbols": ["AAPL", "NVDA", "MSFT"],
                "screener_path": "/screener?universe=sp500&screen=momentum_stocks&limit=8",
                "radar_path": "/idea-radar?universe=global&limit=8",
            },
            {
                "market_key": "japan",
                "label": "Japan Leaders",
                "exchange": "Tokyo Stock Exchange",
                "selected": False,
                "symbols": ["7203.T", "6758.T", "9984.T"],
                "screener_path": "/screener?universe=japan&screen=momentum_stocks&limit=8",
                "radar_path": "/idea-radar?universe=japan&limit=8",
            },
        ],
        "signal_history": [
            {"month": "2026-03", "close": "180.00", "return_1m": "+3.10%", "range": "+7.20%", "volume": "$72M", "volatility": "+18.40%", "posture": "Constructive"},
            {"month": "2026-04", "close": "191.00", "return_1m": "+6.10%", "range": "+8.00%", "volume": "$80M", "volatility": "+20.10%", "posture": "Expansion"},
        ],
        "forecast_lens": {
            "state": "ready",
            "chart_svg": "<svg viewBox='0 0 10 10'></svg>",
            "trend_bias": "Bullish",
            "consensus_price": "212.00",
            "consensus_delta": "+4.10%",
            "trend_persistence": {
                "label": "Persistent",
                "detail": "Recent tape, entropy order, and model consensus are aligned.",
            },
            "validation_summary": {
                "state": "Validated",
                "detail": "Rendered models passed sanity checks.",
            },
            "entropy_signal": {
                "regime": "Structured Trend",
                "predictability_score": 68.4,
                "change_20d_label": "+5.2%",
                "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            },
        },
        "overview": {
            "symbol": symbol,
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "current_price": "200.00",
            "price_change_percent": "+1.20%",
            "market_cap": "$3.1T",
            "pe_ratio": "28.0",
            "beta": "1.12",
            "volume": "$88M",
            "week_52_high": "220.00",
            "week_52_low": "165.00",
        },
        "fundamental_lens": {
            "available": True,
            "summary_cards": [
                {"label": "Overall rating", "value": "Buy", "detail": "Score 72.0/100"},
                {"label": "Valuation stance", "value": "Fair", "detail": "Valuation score 64.0"},
                {"label": "Quality band", "value": "Elite", "detail": "Quality score 81.0"},
                {"label": "Capital profile", "value": "Healthy", "detail": "BIST-only capital efficiency when capital data exists."},
            ],
            "valuation_rows": [
                {"metric": "F/K (P/E)", "value": "28.0x", "detail": "Forward if available, otherwise trailing."},
                {"metric": "PD/DD (P/B)", "value": "7.2x", "detail": "Price to book proxy."},
            ],
            "quality_rows": [
                {"metric": "ROE", "value": "+34.0%", "detail": "Net income over equity."},
                {"metric": "FCF yield", "value": "+3.2%", "detail": "Free cash flow over market cap."},
            ],
            "capital_rows": [
                {"metric": "Paid-in capital", "value": "N/A", "detail": "Most useful on BIST issuers."},
                {"metric": "Net income / paid-in capital", "value": "N/A", "detail": "Capital efficiency on earnings."},
                {"metric": "New contracts / annual sales", "value": "N/A", "detail": "Best-effort KAP disclosure ratio when structured contract values exist."},
            ],
            "growth_profile": {
                "revenue_growth": "+12.0%",
                "earnings_growth": "+16.0%",
                "free_float_pct": "+89.0%",
                "market_cap_to_book": "7.2x",
                "book_value_per_share": "28.00",
                "enterprise_value": "$3.2T",
            },
            "strengths": ["High ROE is supporting capital compounding."],
            "concerns": ["PEG is elevated, so growth may already be priced in."],
            "coverage_note": "Ratios are derived from Yahoo Finance statements.",
        },
        "return_signals": [{"label": "1M", "value": "+4.10%"}],
        "technical_snapshot": {
            "rsi": "58.4",
            "volatility": "+22.10%",
            "bollinger_position": "Orta Ustu",
            "macd_histogram": "0.4221",
            "volume_ratio": "1.14",
        },
        "trend_summary": {
            "trend": "Bullish",
            "confidence": "68.0",
            "recommendation": "Buy - Bullish trend emerging",
            "bullish_signals": 3,
            "bearish_signals": 1,
        },
        "support_resistance": {"support": "192.00", "resistance": "208.00"},
        "patterns": [{"type": "ascending_triangle", "signal": "bullish", "strength": "moderate"}],
        "breakouts": [{"type": "resistance_breakout", "level": 205, "current_price": 206, "strength": "strong"}],
        "sector_context": {
            "available": True,
            "summary": {
                "stock_rank": "Sector Leader",
                "sector": "Technology",
                "sector_etf": "XLK",
                "stock_return": "+28.10%",
                "sector_return": "+22.40%",
            },
            "relative_strength": {"rs_change": "+4.20%", "rs_trend": "Strengthening"},
            "recommendation": {"label": "Buy", "explanation": "Strong sector and stock posture."},
            "trend": {"trend": "Uptrend", "momentum": "Bullish"},
            "valuation": {"pe_vs_sector": "-2.0", "roe_vs_sector": "+8.00%", "margin_vs_sector": "+4.00%"},
            "percentile_rank": "88.0",
            "comparison_rows": [{"symbol": symbol, "name": "Apple Inc.", "price_change_1y": "+28.10%", "roe": "+34.00%", "profit_margin": "+26.00%", "pe_ratio": "28.0"}],
        },
        "institutional": {
            "available": True,
            "summary": {
                "institutional_count": 2,
                "mutual_fund_count": 2,
                "top_institutional_holder": "Vanguard Group",
                "top_mutual_fund_holder": "Fidelity Contrafund",
            },
            "institutional_rows": [{"holder": "Vanguard Group", "shares": "1,200,000", "value": "$240.0M", "ownership_pct": "+2.10%", "reported_at": "2026-05-15"}],
            "mutual_fund_rows": [{"holder": "Fidelity Contrafund", "shares": "520,000", "value": "$104.0M", "ownership_pct": "+0.90%", "reported_at": "2026-05-15"}],
            "major_rows": [],
        },
        "curated_13f": {
            "available": True,
            "coverage": "Curated SEC 13F manager set. This is delayed positioning data, not real-time flow.",
            "signal": "Crowded Long",
            "supported_market": True,
            "manager_rows": [
                {
                    "manager": "Warren Buffett",
                    "manager_label": "Berkshire Hathaway",
                    "style": "Value",
                    "filing_date": "2026-05-15",
                    "signal": "Held",
                    "current_value": "$57.8B",
                    "portfolio_weight": "+22.0%",
                    "weight_change": "-0.6%",
                }
            ],
            "exited_rows": [],
            "summary": {
                "holder_count": 2,
                "total_weight": "+25.4%",
                "top_holder": "Warren Buffett",
                "bullish_managers": 1,
                "bearish_managers": 0,
            },
        },
    }


def _fake_fund_workspace(symbol: str):
    return {
        "symbol": symbol,
        "error": None,
        "featured_symbols": ["SPY", "QQQ"],
        "compare_cta_path": f"/compare?kind=funds&left={symbol}&right=QQQ",
        "overlap_cta_path": "/overlap-matrix?focus=core",
        "forecast_cta_path": f"/forecasts?symbol={symbol}&days=21",
        "market_profile": {
            "market_key": "us-core",
            "market_label": "US Core ETFs",
            "exchange": "US-listed benchmark ETFs",
            "description": "Broad US wrappers remain the cleanest place to compare fee drag, concentration, and benchmark posture.",
        },
        "compare_suggestions": [
            {"symbol": "QQQ", "label": f"{symbol} vs QQQ", "reason": "Same-wrapper compare inside US Core ETFs.", "path": f"/compare?kind=funds&left={symbol}&right=QQQ"},
            {"symbol": "VTI", "label": f"{symbol} vs VTI", "reason": "Core exposure with broader market breadth.", "path": f"/compare?kind=funds&left={symbol}&right=VTI"},
        ],
        "regional_groups": [
            {
                "market_key": "us-core",
                "label": "US Core ETFs",
                "exchange": "US-listed benchmark ETFs",
                "selected": True,
                "symbols": ["QQQ", "VTI", "VOO"],
                "overlap_path": "/overlap-matrix?focus=core",
            },
            {
                "market_key": "japan",
                "label": "Japan ETFs",
                "exchange": "US-listed Japan wrappers",
                "selected": False,
                "symbols": ["EWJ", "DXJ", "JPXN"],
                "overlap_path": "/overlap-matrix?focus=regional",
            },
        ],
        "forecast_lens": {
            "state": "ready",
            "chart_svg": "<svg viewBox='0 0 10 10'></svg>",
            "trend_bias": "Bullish",
            "consensus_price": "603.00",
            "consensus_delta": "+4.80%",
            "trend_persistence": {
                "label": "Persistent",
                "detail": "Wrapper trend, monthly tape, and entropy order are aligned.",
            },
            "validation_summary": {
                "state": "Validated",
                "detail": "Rendered models passed sanity checks.",
            },
            "entropy_signal": {
                "regime": "Structured Trend",
                "predictability_score": 66.0,
                "change_20d_label": "+3.8%",
                "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            },
        },
        "monthly_note": "Asset-base rows are monthly AUM proxies scaled from the latest disclosed total assets and month-end NAV/price.",
        "holdings_timeline_note": "Month-end holdings snapshots use the latest saved ETF/fund file in each month.",
        "overview": {
            "fund_name": "SPDR S&P 500 ETF Trust",
            "category": "Large Blend",
            "fund_family": "State Street",
            "total_assets": "$500.0B",
            "expense_ratio": "+0.09%",
            "yield": "+1.30%",
            "beta": "1.00",
            "morningstar_rating": 5,
        },
        "performance_cards": [{"label": "1Y", "value": "+18.10%"}],
        "risk_snapshot": {
            "volatility": "+14.20%",
            "max_drawdown": "-11.50%",
            "sharpe_ratio": "1.24",
            "sortino_ratio": "1.70",
            "var_95": "-1.90%",
            "correlation_spy": "1.00",
        },
        "holdings_summary": {
            "holdings_count": 500,
            "top_10_concentration": "+32.10%",
            "top_holdings": [{"holdingName": "Apple Inc.", "symbol": "AAPL", "weight": "6.5%"}],
            "sector_allocation": {},
            "geographic_allocation": {},
        },
        "monthly_rows": [
            {
                "month": "2026-05",
                "asset_base_proxy": "$500.0B",
                "asset_change_proxy": "$12.0B",
                "monthly_return": "+2.80%",
                "realized_volatility": "+14.20%",
                "posture": "Expansion",
            }
        ],
        "holdings_timeline_rows": [
            {
                "month": "2026-05",
                "top_holding": "AAPL",
                "top_weight": "+6.50%",
                "top_10_concentration": "+32.10%",
                "primary_shift": "NVDA +0.60%",
            }
        ],
        "rating": {
            "overall_rating": "8.5",
            "performance_rating": 9,
            "risk_rating": 7,
            "cost_rating": 9,
            "explanation": "Good - Strong performance with reasonable risk and costs",
        },
        "benchmark": {"comparison_metrics": {"return_1Y_vs_benchmark": 0.0}},
    }


def _fake_sovereign_workspace(fund: str | None, country: str | None):
    return {
        "selected_fund_key": fund or "norway-gpf",
        "selected_country": country or "All Countries",
        "fund_options": [{"key": "norway-gpf", "label": "Norway Government Pension Fund"}],
        "country_options": ["All Countries", "USA"],
        "data_confidence": {"label": "Estimated", "detail": "Visible sleeve plus deterministic monthly drift proxy."},
        "what_changed": [
            {"impact": "High", "label": "Lead country", "value": "USA · +4.90%", "reason": "Still led by US exposure."}
        ],
        "fund": {
            "display_name": "Norway Government Pension Fund",
            "country": "Norway",
            "aum_label": "$1.6T",
            "holdings_count": 2,
            "country_count": 2,
            "filtered_value_label": "$70.0B",
            "filtered_share_label": "+81.50%",
            "visible_sleeve_weight": "+6.40%",
            "visible_book_value_label": "$86.0B",
        },
        "country_rows": [{"country": "USA", "weight": "+4.90%", "visible_share": "+76.60%", "monthly_drift": "+0.20%"}],
        "allocation_rows": [
            {
                "country": "USA",
                "portfolio_weight": "+4.90%",
                "visible_share": "+76.60%",
                "monthly_drift": "+0.20%",
                "holdings_count": "2",
                "visible_value": "$70.0B",
                "lead_holding": "AAPL",
            }
        ],
        "monthly_rows": [
            {
                "month": "2026-05",
                "visible_value": "$86.0B",
                "lead_country": "USA",
                "lead_weight": "+4.90%",
                "top3_concentration": "+6.40%",
                "largest_shift": "USA +0.20%",
                "posture": "Stable",
            }
        ],
        "holdings_timeline_rows": [
            {
                "month": "2026-05",
                "lead_holding": "AAPL",
                "lead_weight": "+2.80%",
                "top3_concentration": "+6.80%",
                "primary_shift": "MSFT +0.10%",
                "geography": "USA",
            }
        ],
        "holdings": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "country": "USA",
                "weight": "+2.80%",
                "monthly_drift": "+0.10%",
                "visible_share": "+43.80%",
                "value": "$44.0B",
            }
        ],
    }


def _fake_forecast_workspace(symbol: str, days: int):
    return {
        "symbol": symbol,
        "error": None,
        "featured_symbols": ["NVDA", "AAPL"],
        "current_price": "1,000.00",
        "forecast_days": days,
        "consensus_price": "1,080.00",
        "consensus_delta": "+8.00%",
        "trend_bias": "Bullish",
        "model_count": 3,
        "chart_svg": "<svg viewBox='0 0 10 10'></svg>",
        "chart_legend_rows": [
            {"label": "Consensus", "color": "#ffffff", "delta_pct": "+8.00%", "final_price": "1,080.00", "style": "Consensus line"},
            {"label": "Random Forest", "color": "#6ee7b7", "delta_pct": "+9.00%", "final_price": "1,090.00", "style": "Validated model"},
        ],
        "entropy_signal": {
            "regime": "Structured Trend",
            "posture": "Ordered upside tape. Trend-following models deserve more weight.",
            "predictability_score": 72.4,
            "change_20d_label": "+6.2%",
            "note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
        },
        "validation_summary": {
            "state": "Validated",
            "detail": "Every rendered model passed sanity checks for finite prices, positive closes, usable horizon length, and ordered dates.",
            "validated_models": 3,
            "available_models": 3,
            "rejected_models": 0,
            "dispersion_pct": "+4.20%",
        },
        "best_model": {
            "model": "Random Forest",
            "model_label": "Random Forest",
            "final_price": "1,090.00",
            "delta_pct": "+9.00%",
            "rmse": "12.1",
            "mae": "9.8",
            "r2": "0.88",
            "aic": "N/A",
        },
        "model_rows": [
            {
                "model": "Random Forest",
                "model_label": "Random Forest",
                "final_price": "1,090.00",
                "delta_pct": "+9.00%",
                "rmse": "12.1",
                "mae": "9.8",
                "r2": "0.88",
                "aic": "N/A",
                "validation": "Validated",
            }
        ],
        "preview_rows": [{"date": "2026-05-28", "price": "1,010.00"}],
    }


def _fake_screener_workspace(universe: str, screen: str, limit: int):
    return {
        "selected_universe": universe,
        "selected_screen": screen,
        "universe_options": [{"key": "sp500", "label": "US Large Cap", "description": "desc"}],
        "screen_options": [
            {"key": "momentum_stocks", "label": "Momentum Hisseleri", "description": "desc"},
            {"key": "trend_confirmed_accumulation", "label": "Trend-Confirmed Accumulation", "description": "desc"},
            {"key": "entropy_clean_setups", "label": "Entropy-Clean Setups", "description": "desc"},
        ],
        "screen_name": "Momentum Hisseleri",
        "screen_description": "Güçlü yükseliş trendi",
        "universe_label": "US Large Cap",
        "universe_description": "Liquid sample",
        "universe_size": 24,
        "criteria_summary": ["Min 3M change +15.0%", "Entropy predictability must be at least 60."],
        "match_count": 3,
        "match_rate": 12.5,
        "average_3m_change": "+18.20%",
        "average_dividend_yield": "+1.30%",
        "average_rsi": "61.2",
        "average_fundamental_score": "71.4",
        "average_predictability": "68.4",
        "crowded_count": 2,
        "trend_confirmed_count": 2,
        "capital_strong_count": 1,
        "disclosure_active_count": 1,
        "top_match": {
            "symbol": "NVDA",
            "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
        },
        "rows": [
            {
                "symbol": "NVDA",
                "name": "NVIDIA",
                "sector": "Technology",
                "current_price": "1,050.00",
                "market_cap": "$2.5T",
                "price_change_3m": "+24.20%",
                "dividend_yield": "+0.10%",
                "pe_ratio": "38.0",
                "rsi": "63.0",
                "roe": "+48.00%",
                "debt_to_equity": "40.0",
                "curated_13f_signal": "Accumulating",
                "curated_13f_holders": 2,
                "curated_13f_weight": "+16.20%",
                "curated_13f_top_holder": "Stanley Druckenmiller",
                "curated_13f_bullish": 2,
                "curated_13f_bearish": 0,
                "curated_13f_fresh": 1,
                "fundamental_score": "78.4",
                "fundamental_rating": "Buy",
                "fundamental_source": "snapshot",
                "valuation_stance": "Growth At A Reasonable Price",
                "capital_profile": "High Conversion",
                "capital_signal": "81.0",
                "net_income_to_capital": "2.20x",
                "revenue_to_capital": "12.50x",
                "contracts_to_sales": "N/A",
                "material_disclosures_90d": 0,
                "contract_mentions_365d": 0,
                "disclosure_momentum_score": "0.0",
                "trend_label": "Trend Confirmed",
                "trend_detail": "Momentum is not just positive.",
                "trend_persistence": "Persistent",
                "predictability_score": "68.4",
                "entropy_regime": "Structured Trend",
                "trend_bias": "Bullish",
                "forecast_validation": "Validated 5/5",
                "forecast_source": "snapshot",
                "forecast_consensus_delta": "+7.20%",
                "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
                "data_confidence": {"label": "Snapshot-backed"},
                "why_passed": "Passed because trend structure is Trend Confirmed, 3M momentum is already above the liquid-universe threshold, fundamental score 78.4.",
            }
        ],
    }


def _fake_ownership_workspace(symbol: str, focus: str):
    return {
        "symbol": symbol,
        "selected_focus": focus,
        "focus_options": [{"key": "core", "label": "Core Index", "description": "desc"}],
        "featured_symbols": ["AAPL", "NVDA"],
        "focus_label": "Core Index",
        "focus_description": "Broad market",
        "tracked_etfs": ["SPY", "QQQ"],
        "tracked_etf_count": 2,
        "successful_fetches": 2,
        "fetch_counts": [{"etf": "SPY", "rows": 500}],
        "tracker_stats": {"latest_update": "2026-05-27", "unique_funds": 2},
        "summary": {
            "holding_funds": 2,
            "total_weight": "+15.20%",
            "max_weight": "+8.10%",
            "signal": "Bullish",
            "confidence": "68.0",
            "details": "2/2 fonunda ağırlık artışı",
            "latest_update": "2026-05-27",
        },
        "exposure_rows": [
            {
                "fund_code": "QQQ",
                "fund_name": "Invesco QQQ",
                "weight_pct": "+8.10%",
                "share_of_tracked_exposure": "+53.29%",
                "report_date": "2026-05-27",
            }
        ],
        "history_rows": [
            {
                "fund_code": "QQQ",
                "current_weight": "+8.10%",
                "previous_weight": "+7.60%",
                "weight_change": "+0.50%",
                "current_date": "2026-05-27",
                "previous_date": "2026-05-01",
            }
        ],
    }


def _fake_sector_rotation_workspace():
    return {
        "error": None,
        "pattern": "Risk-On Rotation",
        "pattern_note": "Cyclicals are leading.",
        "spread": "+1.40%",
        "cyclical_average": "+2.10%",
        "defensive_average": "+0.70%",
        "leader": {"sector": "Technology", "change_5d": "+3.10%"},
        "laggard": {"sector": "Utilities", "change_5d": "-0.40%"},
        "rows": [
            {
                "sector": "Technology",
                "etf_symbol": "XLK",
                "current_price": "210.00",
                "change_5d": "+3.10%",
                "tone": "positive",
            },
            {
                "sector": "Utilities",
                "etf_symbol": "XLU",
                "current_price": "68.00",
                "change_5d": "-0.40%",
                "tone": "negative",
            },
        ],
    }


def _fake_tr_fund_workspace(fund: str, months: int):
    return {
        "fund_code": fund,
        "error": None,
        "featured_funds": ["TCD", "AFT"],
        "selected_months": months,
        "overview": {
            "fund_name": "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu",
            "fund_family": "Is Portfoy",
            "category": "Hisse",
            "category_rank": 1,
            "category_count": 12,
            "category_percentile": "91.7",
            "market_share": "1.42",
            "current_price": "12.3400",
            "daily_return": "+1.10%",
            "latest_portfolio_value": "$125.0M",
            "portfolio_value_change": "$8.0M",
            "portfolio_value_growth_pct": "+6.80%",
            "latest_num_investors": "14,200",
            "investor_change": "1,100",
            "investor_growth_pct": "+8.40%",
        },
        "signal_card": {
            "signal_score": "82.1",
            "signal_band": "Leading",
            "board_score": "86.4",
            "board_band": "Institutional Leader",
            "regime": "Accumulation",
            "regime_note": "Net deger ve yatirimci ilgisi birlikte artiyor.",
            "dominant_asset": "Hisse",
            "dominant_weight": "+86.00%",
            "local_factor": "Broad BIST Beta",
            "quality_tier": "Elite",
        },
        "allocation_rows": [
            {"asset": "Hisse", "current_weight": "+86.00%", "initial_weight": "+78.00%", "change": "+8.00%"}
        ],
        "monthly_rows": [
            {"month": "2026-04", "primary_shift": "Hisse +3.20%", "stocks_change": "+3.20%", "bonds_change": "-1.00%", "repo_change": "-0.80%"}
        ],
        "evolution_rows": [
            {"month": "2026-04", "security_name": "Stocks", "weight": "+86.00%", "rank": 1, "value": "$108.0M"}
        ],
    }


def _fake_portfolio_lab_workspace(positions: str | None, preset: str | None):
    return {
        "error": None,
        "raw_text": positions or "AAPL,12,189",
        "errors": [],
        "preset": preset or "tcmb_hike_500bp",
        "share_url": "/scenario-lab?positions=AAPL%2C12%2C189&preset=tcmb_hike_500bp",
        "accepted_formats": ["CSV lines: Symbol,Shares,EntryPrice", 'JSON array: [{"symbol":"AAPL","shares":12,"entry_price":189}]'],
        "export_json_uri": "data:application/json;charset=utf-8,%5B%7B%22symbol%22%3A%22AAPL%22%7D%5D",
        "export_csv_uri": "data:text/csv;charset=utf-8,Symbol%2CShares%2CEntryPrice",
        "export_json_name": "fundpilot-scenario-lab.json",
        "export_csv_name": "fundpilot-scenario-lab.csv",
        "preset_label": "TCMB 500bp Hike",
        "preset_description": "Rate shock for BIST-heavy books.",
        "preset_options": [{"key": "tcmb_hike_500bp", "label": "TCMB 500bp Hike", "description": "desc"}],
        "portfolio_summary": {
            "positions": 2,
            "total_value": "$18.0K",
            "health_score": "78.5",
            "grade": "👍 İyi",
            "avg_beta": "1.08",
            "avg_return_3m": "+6.20%",
            "sectors": 2,
        },
        "metric_scores": [{"label": "Diversification", "value": "75.0"}],
        "recommendations": ["Concentration is acceptable but could improve."],
        "holdings_rows": [{"symbol": "AAPL", "shares": "12", "current_price": "200.00", "value": "$2.4K", "sector": "Technology", "beta": "1.12", "return_3m": "+8.40%"}],
        "scenario_summary": {"portfolio_change_pct": "-4.20%", "old_value": "$18.0K", "new_value": "$17.2K"},
        "impact_rows": [{"symbol": "AAPL", "sector": "Technology", "expected_change": "-3.20%", "value_change": "-$77", "new_value": "$2.3K"}],
        "stress_rows": [{"label": "TCMB 500bp Hike", "portfolio_change_pct": "-4.20%", "best_stock": "GARAN", "worst_stock": "THYAO"}],
        "var_summary": {"var_pct": "-8.10%", "cvar_pct": "-11.40%", "worst_case": "-15.20%", "best_case": "+7.80%"},
    }


def _fake_idea_radar_workspace(universe: str, limit: int):
    return {
        "selected_universe": universe,
        "universe_options": [{"key": "global", "label": "Global Mix", "description": "desc"}],
        "universe_label": "Global Mix",
        "universe_description": "Cross-market blend",
        "coverage_size": 12,
        "methodology": ["Momentum uses 3-month price change.", "Entropy and trend persistence reward names where return patterns are ordered enough for trend extrapolation to deserve trust."],
        "top_pick": {
            "symbol": "NVDA",
            "band": "High Conviction",
            "score": 81.4,
            "price_change_3m": "+22.10%",
            "sector_tailwind": "+2.40%",
            "fundamental_score": "78.4",
            "fundamental_rating": "Buy",
            "capital_profile": "High Conversion",
            "disclosure_momentum_score": "72.0",
            "contract_mentions_365d": 3,
            "trend_label": "Trend Confirmed",
            "trend_detail": "Momentum is not just positive. Entropy says return structure is orderly enough for trend-following interpretations to deserve trust.",
            "predictability_score": "68.4",
            "entropy_regime": "Structured Trend",
            "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            "components": {"momentum": "24.0", "rsi": "8.0", "quality": "12.0", "valuation": "7.0", "capital": "8.0", "sector": "7.0", "ownership": "9.0", "institutional": "6.0", "trend": "10.4"},
        },
        "rows": [
            {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "sector": "Technology",
                "score": 81.4,
                "band": "High Conviction",
                "price_change_3m": "+22.10%",
                "rsi": "63.2",
                "roe": "+48.00%",
                "sector_tailwind": "+2.40%",
                "curated_13f_signal": "Accumulating",
                "curated_13f_holders": 2,
                "curated_13f_weight": "+11.40%",
                "curated_13f_fresh": 1,
                "ownership_count": 4,
                "ownership_weight": "+12.80%",
                "fundamental_score": "78.4",
                "fundamental_rating": "Buy",
                "fundamental_source": "snapshot",
                "valuation_stance": "Growth At A Reasonable Price",
                "capital_profile": "High Conversion",
                "capital_signal": "81.0",
                "net_income_to_capital": "2.20x",
                "revenue_to_capital": "12.50x",
                "contracts_to_sales": "N/A",
                "trend_label": "Trend Confirmed",
                "trend_detail": "Momentum is not just positive. Entropy says return structure is orderly enough for trend-following interpretations to deserve trust.",
                "trend_persistence": "Persistent",
                "predictability_score": "68.4",
                "entropy_regime": "Structured Trend",
                "trend_bias": "Bullish",
                "forecast_validation": "Validated 5/5",
                "forecast_source": "live",
                "forecast_consensus_delta": "+7.20%",
                "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
                "components": {"momentum": "24.0", "rsi": "8.0", "quality": "12.0", "valuation": "7.0", "capital": "8.0", "sector": "7.0", "ownership": "9.0", "institutional": "6.0"},
                "why_passed": "This ranks well because of momentum +22.10%, trend Trend Confirmed, curated 13F Accumulating, capital profile High Conversion.",
            }
        ],
    }


def _fake_conviction_board_workspace(universe: str, months: int, limit: int):
    return {
        "selected_universe": universe,
        "selected_months": months,
        "limit": limit,
        "universe_options": [{"key": "global", "label": "Global Mix", "description": "desc"}],
        "month_options": [6, 12, 18],
        "headline": {
            "label": "Cross-Asset Confirmation",
            "detail": "US leadership and TEFAS accumulation are aligned.",
        },
        "sector_pattern": "Risk-On Rotation",
        "top_equity": {
            "symbol": "NVDA",
            "band": "High Conviction",
            "fundamental_score": "78.4",
            "fundamental_rating": "Buy",
            "capital_profile": "High Conversion",
            "disclosure_momentum_score": "72.0",
            "contract_mentions_365d": 3,
            "trend_label": "Trend Confirmed",
            "predictability_score": "68.4",
            "entropy_regime": "Structured Trend",
            "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            "curated_13f_signal": "Crowded Long",
            "curated_13f_holders": 3,
            "ownership_count": 4,
            "why_now": "Institutional breadth and ETF ownership are already reinforcing each other.",
            "detail_path": "/stocks?symbol=NVDA",
        },
        "top_tr_fund": {
            "fund_code": "TCD",
            "signal_band": "Leading",
            "signal_score": "82.1",
            "board_score": "86.4",
            "board_band": "Institutional Leader",
            "fund_family": "Is Portfoy",
            "dominant_asset": "Hisse",
            "regime": "Accumulation",
            "local_factor": "Broad BIST Beta",
            "quality_tier": "Elite",
            "why_now": "Investor growth and portfolio value are rising together in the current TEFAS window.",
            "detail_path": "/turkish-funds?fund=TCD&months=12",
        },
        "scorecards": [
            {"label": "US top pick", "value": "NVDA", "detail": "High Conviction · Crowded Long"},
            {"label": "13F crowding", "value": "2", "detail": "Displayed ideas with multi-manager ownership."},
            {"label": "Fresh buyers", "value": "3", "detail": "Curated manager adds or new positions."},
            {"label": "Trend-confirmed", "value": "2", "detail": "Displayed equity ideas where entropy and persistence are supportive rather than random."},
            {"label": "TEFAS leaders", "value": "2", "detail": "Displayed Turkish funds with constructive posture."},
        ],
        "equity_rows": [
            {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "sector": "Technology",
                "score": 81.4,
                "band": "High Conviction",
                "fundamental_score": "78.4",
                "fundamental_rating": "Buy",
                "capital_profile": "High Conversion",
                "trend_label": "Trend Confirmed",
                "predictability_score": "68.4",
                "entropy_regime": "Structured Trend",
                "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
                "curated_13f_signal": "Crowded Long",
                "curated_13f_holders": 3,
                "curated_13f_weight": "+23.0%",
                "ownership_count": 4,
                "ownership_weight": "+12.80%",
                "why_now": "Institutional breadth and ETF ownership are already reinforcing each other.",
                "detail_path": "/stocks?symbol=NVDA",
            }
        ],
        "tr_fund_rows": [
            {
                "fund_code": "TCD",
                "fund_name_short": "Test Fund",
                "fund_family": "Is Portfoy",
                "signal_score": "82.1",
                "signal_band": "Leading",
                "board_score": "86.4",
                "board_band": "Institutional Leader",
                "regime": "Accumulation",
                "investor_growth_pct": "+8.40%",
                "value_growth_pct": "+6.80%",
                "allocation_drift": "+4.10%",
                "dominant_asset": "Hisse",
                "local_factor": "Broad BIST Beta",
                "quality_tier": "Elite",
                "why_now": "Investor growth and portfolio value are rising together in the current TEFAS window.",
                "detail_path": "/turkish-funds?fund=TCD&months=12",
            }
        ],
        "tefas_health": {"status": "healthy", "detail": "Cached peer board available."},
        "methodology": ["Idea Radar supplies the global equity lane."],
    }


def _fake_compare_workspace(kind: str, left: str | None, right: str | None, months: int):
    return {
        "kind": kind,
        "months": months,
        "kind_options": [{"key": "stocks", "label": "Stocks"}, {"key": "funds", "label": "Funds & ETFs"}, {"key": "tr-funds", "label": "TR Funds"}],
        "left_symbol": left or "AAPL",
        "right_symbol": right or "NVDA",
        "left_name": "Apple Inc.",
        "right_name": "NVIDIA Corporation",
        "summary_cards": [
            {"label": "Left wins", "value": "3", "detail": left or "AAPL"},
            {"label": "Right wins", "value": "2", "detail": right or "NVDA"},
        ],
        "compare_rows": [
            {"metric": "3M change", "left": "+8.0%", "right": "+20.0%", "winner": "Right", "read": "Momentum is stronger on the right."}
        ],
        "regime_workspace": {
            "headline": {
                "winner": "Right",
                "label": "NVDA has the cleaner trend regime.",
                "detail": "NVDA shows bullish bias with stronger tape order than AAPL.",
            },
            "left": {
                "symbol": left or "AAPL",
                "trend_bias": "Bullish",
                "consensus_delta": "+4.10%",
                "predictability": "61.0",
                "persistence": "Developing",
            },
            "right": {
                "symbol": right or "NVDA",
                "trend_bias": "Bullish",
                "consensus_delta": "+9.00%",
                "predictability": "72.4",
                "persistence": "Persistent",
            },
            "rows": [
                {"metric": "Trend persistence", "left": "Developing", "right": "Persistent", "winner": "Right", "read": "The right side has stronger follow-through."},
                {"metric": "Entropy regime", "left": "Constructive Trend", "right": "Structured Trend", "winner": "Right", "read": "Entropy says the right tape is cleaner."},
            ],
        },
        "compare_suggestions": [
            {"symbol": "MSFT", "label": "AAPL vs MSFT", "reason": "Same-market compare inside US Leaders.", "path": "/compare?kind=stocks&left=AAPL&right=MSFT"},
            {"symbol": "AMZN", "label": "AAPL vs AMZN", "reason": "Same-market compare inside US Leaders.", "path": "/compare?kind=stocks&left=AAPL&right=AMZN"},
        ],
        "left_workspace": {
            "data_confidence": {"label": "Live", "detail": "Fresh upstream data."},
            "what_changed": [{"impact": "High", "label": "3M momentum", "value": "+8.0%", "reason": "Momentum improved."}],
        },
        "right_workspace": {
            "data_confidence": {"label": "Snapshot", "detail": "Latest persisted snapshot."},
            "what_changed": [{"impact": "High", "label": "Curated 13F", "value": "Crowded Long", "reason": "Institutional sponsorship is strong."}],
        },
    }


def _fake_catalyst_calendar_workspace():
    return {
        "generated_at": "2026-06-03T10:00:00Z",
        "summary_cards": [
            {"label": "Recent KAP events", "value": "5", "detail": "Structured disclosure rows."},
            {"label": "Recent 13F events", "value": "4", "detail": "Curated manager filings."},
            {"label": "TEFAS lane", "value": "3", "detail": "healthy"},
            {"label": "Clean-tape catalysts", "value": "2", "detail": "BIST names where catalyst pressure and tape structure are aligned."},
        ],
        "recent_rows": [
            {"date": "2026-06-02", "source": "KAP", "subject": "ASELS", "event": "Structured disclosure flow", "detail": "Momentum 91.0", "state": "live"}
        ],
        "upcoming_rows": [
            {"date": "2026-06-04T10:00:00Z", "source": "FundPilot", "subject": "Prewarm cycle", "event": "Next scheduled refresh", "detail": "Background cadence."}
        ],
        "clean_tape_rows": [
            {"symbol": "ASELS", "name": "Aselsan", "label": "Catalyst + Clean Tape", "detail": "Disclosure flow is active and the tape is orderly enough for follow-through to deserve more respect than noise.", "predictability_score": "68.4", "trend_label": "Trend Confirmed", "disclosure_momentum_score": "91.0", "contracts_to_sales": "311.4%", "detail_path": "/stocks?symbol=ASELS"}
        ],
    }


def _fake_bist_quality_board_workspace(limit: int):
    return {
        "top_pick": {
            "symbol": "ASELS",
            "board_score": "84.1",
            "fundamental_rating": "Buy",
            "capital_profile": "High Conversion",
            "predictability_score": "68.4",
            "trend_label": "Trend Confirmed",
            "entropy_note": "We use entropy because it tells us whether return patterns are ordered enough for trend extrapolation to deserve trust.",
            "catalyst_tape": {"label": "Catalyst + Clean Tape"},
            "why_passed": "Passed because capital profile is High Conversion.",
        },
        "methodology": ["Board score blends fundamentals and disclosure flow.", "Entropy matters because local catalysts are more actionable when the tape is orderly enough for trend-following models to deserve trust."],
        "rows": [
            {
                "symbol": "ASELS",
                "name": "Aselsan",
                "sector": "Industrials",
                "board_score": "84.1",
                "fundamental_rating": "Buy",
                "fundamental_score": "79.0",
                "valuation_stance": "Fair",
                "capital_profile": "High Conversion",
                "net_income_to_capital": "1.8x",
                "revenue_to_capital": "6.2x",
                "trend_label": "Trend Confirmed",
                "predictability_score": "68.4",
                "entropy_regime": "Structured Trend",
                "disclosure_momentum_score": "91.0",
                "material_disclosures_90d": "14",
                "contract_mentions_365d": "19",
                "catalyst_clean_score": "82.5",
                "catalyst_tape": {"label": "Catalyst + Clean Tape"},
                "contracts_to_sales": "311.4%",
                "curated_13f_signal": "Unavailable",
                "curated_13f_holders": 0,
                "why_passed": "Passed because capital profile is High Conversion.",
            }
        ],
    }


def _fake_overlap_matrix_workspace(focus: str):
    return {
        "selected_focus": focus,
        "focus_options": [{"key": "core", "label": "Core", "description": "Large cap core ETFs."}],
        "focus_label": "Core",
        "focus_description": "Large cap core ETFs.",
        "etfs": ["SPY", "IVV", "VOO"],
        "summary_cards": [
            {"label": "ETFs compared", "value": "3", "detail": "Core"},
            {"label": "Overlap pairs", "value": "2", "detail": "Pairs with shared holdings."},
        ],
        "pair_rows": [
            {"left": "SPY", "right": "IVV", "overlap_score": "67.0%", "shared_count": 430, "shared_names": "AAPL, MSFT, NVDA"}
        ],
    }


def _fake_institutional_pulse_workspace(manager: str):
    return {
        "selected_manager": manager,
        "manager_options": [{"key": "berkshire", "label": "Berkshire Hathaway", "manager_name": "Warren Buffett", "style": "Value"}],
        "manager": {"label": "Berkshire Hathaway", "manager_name": "Warren Buffett", "style": "Value", "cik": "1067983"},
        "error": None,
        "warning": None,
        "source_state": "live",
        "generated_at": "2026-05-28T00:00:00Z",
        "source_note": "Official SEC EDGAR 13F filings.",
        "summary": {
            "portfolio_value": "$300.0B",
            "holding_count": 40,
            "top_10_weight": "+84.0%",
            "option_exposure": "+0.0%",
            "largest_position": "Apple Inc",
            "largest_position_weight": "+38.0%",
            "filing_lag_days": 12,
            "new_positions": 2,
            "exited_positions": 1,
        },
        "latest_filing": {"filing_date": "2026-05-15", "form": "13F-HR"},
        "previous_filing": {"filing_date": "2026-02-14", "form": "13F-HR"},
        "top_holdings": [{"issuer": "Apple Inc", "class_title": "COM", "put_call": "Equity", "value": "$115.0B", "portfolio_weight": "+38.0%", "shares": "300,000,000"}],
        "new_positions": [{"issuer": "Constellation Brands", "class_title": "COM", "current_value": "$1.2B", "weight_change": "+0.4%"}],
        "added_positions": [{"issuer": "Occidental Petroleum", "class_title": "COM", "value_change": "$900.0M", "weight_change": "+0.3%"}],
        "trimmed_positions": [{"issuer": "Bank of America", "class_title": "COM", "value_change": "$-800.0M", "weight_change": "-0.2%"}],
        "sold_positions": [{"issuer": "Paramount Global", "class_title": "COM", "previous_value": "$600.0M", "weight_change": "-0.2%"}],
        "consensus_rows": [{"issuer": "Apple Inc", "manager_count": 3, "managers": "Warren Buffett, Bill Gates, Ray Dalio", "combined_weight": "+48.0%", "max_weight": "+38.0%", "latest_filing": "2026-05-15"}],
        "consensus_coverage": 4,
        "coverage_summary": {"manager_count": 5, "live_count": 3, "snapshot_count": 1, "warming_count": 1, "latest_filing": "2026-05-15"},
        "coverage_rows": [
            {
                "manager_key": "berkshire",
                "manager_name": "Warren Buffett",
                "label": "Berkshire Hathaway",
                "style": "Value",
                "source_state": "live",
                "latest_filing": "2026-05-15",
                "holding_count": 40,
                "portfolio_value": "$300.0B",
                "largest_position": "Apple Inc",
                "top_10_weight": "+84.0%",
                "new_positions": 2,
                "exited_positions": 1,
                "filing_lag_days": 12,
            }
        ],
        "methodology": ["Latest and previous 13F filings are compared filing-by-filing."],
    }


def test_dashboard_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.dashboard_service, "build_snapshot", _fake_snapshot)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Start with the signal, not the noise." in response.text
    assert "Constructive" in response.text
    assert "How ordered is the tape?" in response.text
    assert "Constructive Trend" in response.text
    assert "When direction and structure stay in phase" in response.text
    assert "Catalyst + Clean Tape" in response.text


def test_legacy_view_redirects(monkeypatch):
    monkeypatch.setattr(web_routes.dashboard_service, "build_snapshot", _fake_snapshot)
    response = client.get("/?view=dashboard", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard"


def test_public_dashboard_api(monkeypatch):
    monkeypatch.setattr(public_api.dashboard_service, "build_snapshot", _fake_snapshot)
    response = client.get("/api/v1/public/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["snapshot"]["sentiment"]["mood"] == "Constructive"


def test_public_influence_map_api(monkeypatch):
    monkeypatch.setattr(public_api.dashboard_service, "build_influence_workspace", _fake_influence_workspace)
    response = client.get("/api/v1/public/influence-map")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["workspace"]["headline"]["label"] == "VIX -> Nasdaq"


def test_public_tr_funds_api_serializes_numpy_scalars(monkeypatch):
    board = pd.DataFrame(
        [
            {
                "fund_code": "TCD",
                "signal_score": np.float64(81.2),
                "category_rank": np.int64(1),
            }
        ]
    )

    monkeypatch.setattr(public_api.tr_funds_service, "get_cached_peer_signal_board", lambda months: board)
    monkeypatch.setattr(
        public_api.tr_funds_service,
        "get_cached_top_pick",
        lambda months: {
            "fund_code": "TCD",
            "signal_score": np.float64(81.2),
            "category_rank": np.int64(1),
        },
    )
    monkeypatch.setattr(
        public_api.tr_funds_service,
        "get_status",
        lambda months: {
            "status": "healthy",
            "funds_requested": np.int64(1),
            "funds_loaded": np.int64(1),
        },
    )
    monkeypatch.setattr(
        public_api.tr_funds_service,
        "get_leadership_snapshot",
        lambda months: {
            "family_rows": [{"fund_family": "Is Portfoy", "house_view": "House Leader", "funds_count": 1}],
            "factor_rows": [{"local_factor": "Broad BIST Beta", "breadth": "Broadening", "funds_count": 1}],
        },
    )

    response = client.get("/api/v1/public/tr-funds")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["top_pick"]["category_rank"] == 1
    assert body["peer_board"][0]["category_rank"] == 1
    assert body["leadership"]["family_rows"][0]["house_view"] == "House Leader"
    assert body["health"]["funds_requested"] == 1


def test_dashboard_head_request(monkeypatch):
    monkeypatch.setattr(web_routes.dashboard_service, "build_snapshot", _fake_snapshot)
    response = client.head("/dashboard")
    assert response.status_code == 200


def test_source_health_api(monkeypatch):
    monkeypatch.setattr(
        public_api.dashboard_service,
        "build_live_source_health",
        lambda: {
            "generated_at": "2026-06-02T00:00:00Z",
            "source_health": _fake_snapshot()["source_health"],
        },
    )
    response = client.get("/api/v1/public/source-health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["source_health"][0]["label"] == "Market feed"


def test_public_reliability_api(monkeypatch):
    monkeypatch.setattr(public_api.dashboard_service, "build_reliability_workspace", _fake_reliability_workspace)
    response = client.get("/api/v1/public/reliability")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["workspace"]["kap_health"]["summary"]["symbols_tracked"] == 5


def test_public_conviction_board_api(monkeypatch):
    monkeypatch.setattr(public_api.public_research_service, "get_conviction_board_workspace", _fake_conviction_board_workspace)
    response = client.get("/api/v1/public/conviction-board?universe=global&months=12&limit=6")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["workspace"]["headline"]["label"] == "Cross-Asset Confirmation"


def test_public_compare_api(monkeypatch):
    monkeypatch.setattr(public_api.public_research_service, "get_compare_workspace", _fake_compare_workspace)
    response = client.get("/api/v1/public/compare?kind=stocks&left=AAPL&right=NVDA")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["workspace"]["compare_rows"][0]["metric"] == "3M change"


def test_public_catalyst_calendar_api(monkeypatch):
    monkeypatch.setattr(public_api.public_research_service, "get_catalyst_calendar_workspace", _fake_catalyst_calendar_workspace)
    response = client.get("/api/v1/public/catalyst-calendar")
    assert response.status_code == 200
    body = response.json()
    assert body["workspace"]["recent_rows"][0]["source"] == "KAP"


def test_public_bist_quality_board_api(monkeypatch):
    monkeypatch.setattr(public_api.public_research_service, "get_bist_quality_board_workspace", _fake_bist_quality_board_workspace)
    response = client.get("/api/v1/public/bist-quality-board?limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["workspace"]["top_pick"]["symbol"] == "ASELS"


def test_public_overlap_matrix_api(monkeypatch):
    monkeypatch.setattr(public_api.public_research_service, "get_overlap_matrix_workspace", _fake_overlap_matrix_workspace)
    response = client.get("/api/v1/public/overlap-matrix?focus=core")
    assert response.status_code == 200
    body = response.json()
    assert body["workspace"]["pair_rows"][0]["left"] == "SPY"


def test_methodology_page_renders():
    response = client.get("/methodology")
    assert response.status_code == 200
    assert "Readable signals, not black-box promises." in response.text


def test_stocks_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_stock_workspace", _fake_stock_workspace)
    response = client.get("/stocks?symbol=AAPL")
    assert response.status_code == 200
    assert "Single-name analysis without the old UI sprawl." in response.text
    assert "Apple Inc." in response.text
    assert "Exchange-aware pairings" in response.text
    assert "Mini trend map inside the stock workspace" in response.text
    assert "Why entropy" in response.text
    assert "Japan Leaders" in response.text
    assert "F/K (P/E)" in response.text
    assert "Net income / paid-in capital" in response.text
    assert "Crowded Long" in response.text


def test_funds_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_fund_workspace", _fake_fund_workspace)
    response = client.get("/funds-etfs?symbol=SPY")
    assert response.status_code == 200
    assert "ETF and fund analysis is back in public read-only form." in response.text
    assert "SPDR S&amp;P 500 ETF Trust" in response.text
    assert "Exchange-aware pairings" in response.text
    assert "Regional ETF Quick Picks" in response.text
    assert "Mini wrapper trend map inside the fund workspace" in response.text
    assert "Why entropy" in response.text
    assert "Monthly Asset Tape" in response.text
    assert "Positioning Drift" in response.text


def test_sovereign_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_sovereign_workspace", _fake_sovereign_workspace)
    response = client.get("/sovereign-funds?fund=norway-gpf")
    assert response.status_code == 200
    assert "Country wealth funds and pensions are visible again." in response.text
    assert "Norway Government Pension Fund" in response.text
    assert "Country Allocation Table" in response.text
    assert "Monthly Allocation Drift" in response.text
    assert "Top Holding Evolution" in response.text


def test_forecasts_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_forecast_workspace", _fake_forecast_workspace)
    response = client.get("/forecasts?symbol=NVDA&days=30")
    assert response.status_code == 200
    assert "Multi-model forecasts are back, without the old runtime risk." in response.text
    assert "1,080.00" in response.text
    assert "Historical anchor plus validated forward paths" in response.text
    assert "Why we use entropy" in response.text
    assert "Validation Layer" in response.text


def test_screener_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_screener_workspace", _fake_screener_workspace)
    response = client.get("/screener?universe=sp500&screen=momentum_stocks")
    assert response.status_code == 200
    assert "Curated screens are back without the old runtime risk." in response.text
    assert "NVDA" in response.text
    assert "Accumulating" in response.text
    assert "Trend Lens" in response.text
    assert "Why entropy" in response.text
    assert "Why Passed" in response.text


def test_ownership_lens_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_ownership_workspace", _fake_ownership_workspace)
    response = client.get("/ownership-lens?symbol=AAPL&focus=core")
    assert response.status_code == 200
    assert "ETF weight tracking is back in public form." in response.text
    assert "Invesco QQQ" in response.text


def test_sector_rotation_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_sector_rotation_workspace", _fake_sector_rotation_workspace)
    response = client.get("/sector-rotation")
    assert response.status_code == 200
    assert "Top-down leadership without the terminal tax." in response.text
    assert "Risk-On Rotation" in response.text


def test_turkish_funds_page_renders(monkeypatch):
    monkeypatch.setattr(
        web_routes.tr_funds_service,
        "get_cached_peer_signal_board",
        lambda months: pd.DataFrame([{"fund_code": "TCD", "fund_name_short": "Test Fund", "signal_score": 82.1, "signal_band": "Leading", "board_score": 86.4, "board_band": "Institutional Leader", "fund_family": "Is Portfoy", "local_factor": "Broad BIST Beta", "quality_tier": "Elite", "category_percentile": 91.7, "regime": "Accumulation", "investor_growth_pct": 8.4, "value_growth_pct": 6.8, "allocation_drift": 4.1, "dominant_asset": "Hisse"}]),
    )
    monkeypatch.setattr(
        web_routes.tr_funds_service,
        "get_cached_top_pick",
        lambda months: {"fund_code": "TCD", "signal_band": "Leading", "signal_score": 82.1, "fund_family": "Is Portfoy", "local_factor": "Broad BIST Beta", "quality_tier": "Elite", "board_score": 86.4, "investor_growth_pct": 8.4, "dominant_asset": "Hisse"},
    )
    monkeypatch.setattr(
        web_routes.tr_funds_service,
        "get_leadership_snapshot",
        lambda months: {
            "family_rows": [{"fund_family": "Is Portfoy", "house_view": "House Leader", "funds_count": 1, "avg_board_score": 86.4, "avg_signal_score": 82.1, "top_fund": "TCD", "avg_category_percentile": 91.7}],
            "factor_rows": [{"local_factor": "Broad BIST Beta", "breadth": "Broadening", "funds_count": 1, "avg_board_score": 86.4, "avg_investor_growth_pct": 8.4, "lead_fund": "TCD", "avg_value_growth_pct": 6.8}],
        },
    )
    monkeypatch.setattr(web_routes.public_research_service, "get_tr_fund_workspace", _fake_tr_fund_workspace)
    response = client.get("/turkish-funds?fund=TCD&months=6")
    assert response.status_code == 200
    assert "TEFAS momentum without the dashboard sprawl." in response.text
    assert "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu" in response.text
    assert "Broad BIST Beta" in response.text
    assert "House Leader" in response.text


def test_turkish_funds_head_request_with_legacy_peer_board(monkeypatch):
    monkeypatch.setattr(
        web_routes.tr_funds_service,
        "get_cached_peer_signal_board",
        lambda months: pd.DataFrame([{"fund_code": "TCD", "fund_name_short": "Legacy Fund", "signal_score": 82.1, "signal_band": "Leading", "regime": "Accumulation", "investor_growth_pct": 8.4, "value_growth_pct": 6.8, "allocation_drift": 4.1}]),
    )
    monkeypatch.setattr(
        web_routes.tr_funds_service,
        "get_cached_top_pick",
        lambda months: {"fund_code": "TCD", "signal_band": "Leading", "signal_score": 82.1, "fund_family": "Is Portfoy", "local_factor": "Broad BIST Beta", "quality_tier": "Elite", "board_score": 86.4, "investor_growth_pct": 8.4, "dominant_asset": "Hisse"},
    )
    monkeypatch.setattr(
        web_routes.tr_funds_service,
        "get_leadership_snapshot",
        lambda months: {"family_rows": [], "factor_rows": []},
    )
    monkeypatch.setattr(web_routes.public_research_service, "get_tr_fund_workspace", _fake_tr_fund_workspace)
    response = client.head("/turkish-funds?fund=TCD&months=6")
    assert response.status_code == 200


def test_scenario_lab_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_portfolio_lab_workspace", _fake_portfolio_lab_workspace)
    response = client.get("/scenario-lab?preset=tcmb_hike_500bp")
    assert response.status_code == 200
    assert "Portfolio health and stress testing are back without an account wall." in response.text
    assert "TCMB 500bp Hike" in response.text
    assert "Open Shareable URL" in response.text


def test_idea_radar_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_idea_radar_workspace", _fake_idea_radar_workspace)
    response = client.get("/idea-radar?universe=global&limit=8")
    assert response.status_code == 200
    assert "Generic quote pages stop at data. This page starts at conviction." in response.text
    assert "NVDA" in response.text
    assert "Accumulating" in response.text
    assert "Trend Lens" in response.text
    assert "Why entropy" in response.text
    assert "Why Passed" in response.text


def test_compare_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_compare_workspace", _fake_compare_workspace)
    response = client.get("/compare?kind=stocks&left=AAPL&right=NVDA")
    assert response.status_code == 200
    assert "Put two candidates on one sheet and force a decision." in response.text
    assert "Exchange-aware compare presets" in response.text
    assert "Regime Check" in response.text
    assert "Persistence and predictability side by side" in response.text
    assert "3M change" in response.text


def test_catalyst_calendar_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_catalyst_calendar_workspace", _fake_catalyst_calendar_workspace)
    response = client.get("/catalyst-calendar")
    assert response.status_code == 200
    assert "Know when your inputs can change before price forces your attention." in response.text
    assert "Structured disclosure flow" in response.text
    assert "Clean-tape catalysts" in response.text
    assert "Catalyst + Clean Tape" in response.text


def test_bist_quality_board_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_bist_quality_board_workspace", _fake_bist_quality_board_workspace)
    response = client.get("/bist-quality-board?limit=10")
    assert response.status_code == 200
    assert "Rank local names by capital efficiency, not just price action." in response.text
    assert "ASELS" in response.text
    assert "Trend Lens" in response.text
    assert "Why entropy" in response.text


def test_overlap_matrix_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_overlap_matrix_workspace", _fake_overlap_matrix_workspace)
    response = client.get("/overlap-matrix?focus=core")
    assert response.status_code == 200
    assert "See where passive ownership is quietly crowding the same trades." in response.text
    assert "SPY" in response.text


def test_conviction_board_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.public_research_service, "get_conviction_board_workspace", _fake_conviction_board_workspace)
    response = client.get("/conviction-board?universe=global&months=12&limit=6")
    assert response.status_code == 200
    assert "This page shows where conviction is clustering." in response.text
    assert "Cross-Asset Confirmation" in response.text
    assert "Crowded Long" in response.text
    assert "Trend-confirmed" in response.text
    assert "Why entropy" in response.text
    assert "Test Fund" in response.text
    assert "Institutional Leader" in response.text


def test_institutional_pulse_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.institutional_pulse_service, "get_workspace", _fake_institutional_pulse_workspace)
    response = client.get("/institutional-pulse?manager=berkshire")
    assert response.status_code == 200
    assert "Real 13F position changes, not synthetic whale theater." in response.text
    assert "Manager Coverage" in response.text
    assert "Coverage Board" in response.text
    assert "Berkshire Hathaway" in response.text


def test_reliability_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.dashboard_service, "build_reliability_workspace", _fake_reliability_workspace)
    response = client.get("/reliability")
    assert response.status_code == 200
    assert "See where the data spine is strong, stale, or warming." in response.text
    assert "KAP enrichment monitor" in response.text
    assert "How this stack should age over 6, 12, 24, and 48 months" in response.text
    assert "Shared cache before multi-worker scale" in response.text


def test_influence_map_page_renders(monkeypatch):
    monkeypatch.setattr(web_routes.dashboard_service, "build_influence_workspace", _fake_influence_workspace)
    response = client.get("/influence-map")
    assert response.status_code == 200
    assert "Who is leading the tape, and who is just reacting?" in response.text
    assert "Transfer Entropy" in response.text
    assert "VIX -&gt; Nasdaq" in response.text or "VIX -> Nasdaq" in response.text


def test_favicon_route_redirects():
    response = client.get("/favicon.ico", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/favicon.svg"


def test_dashboard_failure_renders_friendly_html(monkeypatch):
    def _boom():
        raise RuntimeError("raw traceback should not leak")

    monkeypatch.setattr(web_routes.dashboard_service, "build_snapshot", _boom)
    response = safe_client.get("/dashboard")
    assert response.status_code == 500
    assert "Temporary issue on the public workspace." in response.text
    assert "raw traceback should not leak" not in response.text
