from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from app.analytics.entropy_metrics import EntropyCalculator
from app.services.cache import cache_clear
from app.services.public_dashboard import PublicDashboardService
from app.services.snapshot_store import SnapshotStore


def test_public_dashboard_uses_persisted_snapshot_when_cache_empty():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        service = PublicDashboardService(ttl_seconds=1)
        service.snapshot_store = SnapshotStore(base_dir=Path(tmpdir))
        service.snapshot_store.write_json(
            service._snapshot_key(),
            {
                "generated_at": "2026-05-27T00:00:00Z",
                "market_cards": [{"label": "S&P 500"}],
                "macro_cards": [],
                "crypto_cards": [],
                "sentiment": {"mood": "Constructive"},
                "tr_top_pick": None,
                "tr_peer_board": [],
                "source_health": [],
                "coverage_cards": [],
                "sponsor_slots": [],
                "editorial_cards": [],
                "sponsor_disclosure": "Test",
                "privacy_promise": "Test",
            },
        )

        snapshot = service.build_snapshot()
        assert snapshot["generated_at"] == "2026-05-27T00:00:00Z"
        assert snapshot["market_cards"][0]["label"] == "S&P 500"
        assert snapshot["entropy_signal"]["state"] == "warming"
        assert snapshot["entropy_signal"]["window_days"] == 90
        assert snapshot["market_physics"]["state"] == "warming"
        assert snapshot["influence_rows"] == []
        assert snapshot["influence_summary"]["label"] == "Refreshing"
        assert snapshot["bist_catalyst_rows"] == []
        assert snapshot["bist_catalyst_summary"]["state"] == "warming"


def test_public_dashboard_returns_placeholder_without_snapshot():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        service = PublicDashboardService(ttl_seconds=1)
        service.snapshot_store = SnapshotStore(base_dir=Path(tmpdir))

        snapshot = service.build_snapshot()
        assert snapshot["sentiment"]["mood"] == "Refreshing"
        assert snapshot["market_cards"] == []
        assert snapshot["entropy_signal"]["state"] == "warming"
        assert snapshot["source_health"][0]["state"] == "warming"


def test_public_dashboard_force_refresh_serializes_numpy_scalars(monkeypatch):
    cache_clear()
    service = PublicDashboardService(ttl_seconds=1)

    monkeypatch.setattr(
        service,
        "_build_market_cards",
        lambda generated_at: (
            [{"label": "S&P 500", "price": np.float64(100.5)}],
            {"key": "market", "label": "Market", "state": "healthy", "state_label": "Healthy", "detail": "ok", "updated_at": generated_at},
        ),
    )
    monkeypatch.setattr(
        service,
        "_build_macro_cards",
        lambda generated_at: (
            [],
            {"key": "macro", "label": "Macro", "state": "healthy", "state_label": "Healthy", "detail": "ok", "updated_at": generated_at},
        ),
    )
    monkeypatch.setattr(
        service,
        "_build_entropy_signal",
        lambda generated_at: {
            "state": "healthy",
            "state_label": "Healthy",
            "regime": "Structured Trend",
            "stance": "Clean tape",
            "predictability_score": np.float64(66.5),
            "complexity_score": np.float64(33.5),
            "leader_asset": "S&P 500",
            "leader_symbol": "^GSPC",
            "window_days": np.int64(90),
            "updated_at": generated_at,
            "asset_rows": [{"label": "S&P 500", "predictability_score": np.float64(66.5)}],
            "note": "Test",
        },
    )
    monkeypatch.setattr(
        service,
        "_build_market_physics",
        lambda entropy_signal, generated_at: {
            "state": "healthy",
            "state_label": "Healthy",
            "phase_regime": "Coherent Trend",
            "stance": "Aligned",
            "average_phase_score": np.float64(74.5),
            "leader_asset": "S&P 500",
            "leader_symbol": "^GSPC",
            "updated_at": generated_at,
            "rows": [{"label": "S&P 500", "phase_score": np.float64(74.5)}],
            "note": "Phase note",
        },
    )
    monkeypatch.setattr(
        service,
        "build_influence_workspace",
        lambda force_refresh=False: {
            "headline": {"label": "VIX -> Nasdaq", "detail": "Test influence"},
            "pair_rows": [{"source_label": "VIX", "target_label": "Nasdaq", "net_influence": np.float64(0.144)}],
        },
    )
    monkeypatch.setattr(
        service,
        "_build_crypto_cards",
        lambda generated_at: (
            [],
            {"key": "crypto", "label": "Crypto", "state": "healthy", "state_label": "Healthy", "detail": "ok", "updated_at": generated_at},
        ),
    )
    monkeypatch.setattr(service, "_build_sentiment", lambda: {"score": np.float64(0.7), "mood": "Risk-on"})
    monkeypatch.setattr(service, "_build_cached_tr_top_pick", lambda: {"fund_code": "TCD", "category_rank": np.int64(1)})
    monkeypatch.setattr(service, "_build_cached_tr_peer_board", lambda: [{"fund_code": "TCD", "category_rank": np.int64(1)}])
    monkeypatch.setattr(
        service,
        "_build_tr_status",
        lambda generated_at, tr_peer_board: {
            "key": "tr-funds",
            "label": "TR funds",
            "state": "healthy",
            "state_label": "Healthy",
            "detail": "ok",
            "updated_at": generated_at,
        },
    )
    monkeypatch.setattr(
        service.institutional,
        "get_health_snapshot",
        lambda: {
            "key": "institutional",
            "label": "Institutional filings",
            "state": "degraded",
            "state_label": "Degraded",
            "detail": "3 live, 1 snapshot, 1 warming managers.",
            "updated_at": "2026-05-28T00:00:00Z",
            "summary": {"manager_count": 5},
        },
    )
    monkeypatch.setattr(
        service.stock_enrichment,
        "get_health_snapshot",
        lambda: {
            "key": "kap-enrichment",
            "label": "BIST disclosures",
            "state": "healthy",
            "state_label": "Healthy",
            "detail": "ok",
            "updated_at": "2026-05-28T00:00:00Z",
            "summary": {"symbols_tracked": 5},
            "rows": [],
        },
    )
    monkeypatch.setattr(
        service,
        "_build_bist_catalyst_lane",
        lambda: (
            [{"symbol": "ASELS.IS", "disclosure_momentum_score": np.float64(88.0)}],
            {"state": "healthy", "state_label": "Catalyst Active", "detail": "ok", "leader": "ASELS.IS", "active_count": np.int64(3)},
        ),
    )

    snapshot = service.build_snapshot(force_refresh=True)
    assert snapshot["market_cards"][0]["price"] == 100.5
    assert snapshot["entropy_signal"]["predictability_score"] == 66.5
    assert snapshot["entropy_signal"]["window_days"] == 90
    assert snapshot["market_physics"]["average_phase_score"] == 74.5
    assert snapshot["influence_summary"]["label"] == "VIX -> Nasdaq"
    assert snapshot["influence_rows"][0]["net_influence"] == 0.144
    assert snapshot["tr_top_pick"]["category_rank"] == 1
    assert snapshot["tr_peer_board"][0]["category_rank"] == 1
    assert snapshot["bist_catalyst_rows"][0]["disclosure_momentum_score"] == 88.0
    assert snapshot["bist_catalyst_summary"]["active_count"] == 3
    assert snapshot["source_health"][-2]["key"] == "tr-funds"
    assert snapshot["source_health"][-1]["key"] == "institutional"
    assert any(item["key"] == "kap-enrichment" for item in snapshot["source_health"])


def test_public_dashboard_builds_entropy_signal_from_history(monkeypatch):
    cache_clear()
    service = PublicDashboardService(ttl_seconds=1)

    def _hist(symbol, drift):
        prices = np.linspace(100 + drift, 112 + drift, 60) + np.sin(np.linspace(0, 4, 60))
        return {
            "symbol": [symbol] * 60,
            "close_price": prices,
        }

    monkeypatch.setattr(
        service.yahoo,
        "get_historical_data",
        lambda start_date, end_date, symbol, interval="1d": pd.DataFrame(
            _hist(symbol, {"^GSPC": 0, "^IXIC": 5, "XU100.IS": -3, "BTC-USD": 12}.get(symbol, 0))
        ),
    )

    entropy_signal = service._build_entropy_signal("2026-05-28T00:00:00Z")

    assert entropy_signal["state"] == "healthy"
    assert entropy_signal["leader_asset"] is not None
    assert len(entropy_signal["asset_rows"]) == 4
    assert entropy_signal["asset_rows"][0]["predictability_score"] is not None
    assert "change_5d_label" in entropy_signal["asset_rows"][0]
    assert "change_60d_label" in entropy_signal["asset_rows"][0]


def test_public_dashboard_builds_market_physics_from_entropy_rows():
    cache_clear()
    service = PublicDashboardService(ttl_seconds=1)

    market_physics = service._build_market_physics(
        {
            "asset_rows": [
                {
                    "label": "S&P 500",
                    "symbol": "^GSPC",
                    "predictability_score": 68.0,
                    "spectral_clarity": 71.0,
                    "change_5d": 1.1,
                    "change_5d_label": "+1.1%",
                    "change_20d": 3.4,
                    "change_20d_label": "+3.4%",
                    "change_60d": 8.2,
                    "change_60d_label": "+8.2%",
                },
                {
                    "label": "Bitcoin",
                    "symbol": "BTC-USD",
                    "predictability_score": 44.0,
                    "spectral_clarity": 39.0,
                    "change_5d": 4.2,
                    "change_5d_label": "+4.2%",
                    "change_20d": -2.0,
                    "change_20d_label": "-2.0%",
                    "change_60d": 11.0,
                    "change_60d_label": "+11.0%",
                },
            ]
        },
        "2026-05-28T00:00:00Z",
    )

    assert market_physics["state"] == "degraded"
    assert market_physics["leader_asset"] == "S&P 500"
    assert market_physics["rows"][0]["phase_label"] in {"In-Phase Upswing", "Constructive Alignment"}
    assert market_physics["rows"][1]["phase_label"] == "Fractured Tape"


def test_public_dashboard_builds_influence_workspace_from_history(monkeypatch):
    cache_clear()
    service = PublicDashboardService(ttl_seconds=1)

    def _hist(symbol):
        base = {
            "^VIX": np.linspace(20, 16, 120) + np.sin(np.linspace(0, 4, 120)),
            "^TNX": np.linspace(4.0, 4.4, 120) + np.sin(np.linspace(0, 3, 120)) * 0.08,
            "UUP": np.linspace(28, 29, 120) + np.cos(np.linspace(0, 5, 120)) * 0.1,
            "CL=F": np.linspace(70, 77, 120) + np.sin(np.linspace(0, 6, 120)),
            "BTC-USD": np.linspace(60000, 68000, 120) + np.sin(np.linspace(0, 10, 120)) * 800,
            "^GSPC": np.linspace(5000, 5400, 120) + np.sin(np.linspace(0, 4, 120)) * 20,
            "^IXIC": np.linspace(17000, 18400, 120) + np.sin(np.linspace(0, 5, 120)) * 35,
            "XU100.IS": np.linspace(10000, 11200, 120) + np.sin(np.linspace(0, 6, 120)) * 30,
            "GC=F": np.linspace(2200, 2360, 120) + np.cos(np.linspace(0, 4, 120)) * 12,
        }[symbol]
        return pd.DataFrame({"symbol": [symbol] * len(base), "close_price": base})

    monkeypatch.setattr(
        service.yahoo,
        "get_historical_data",
        lambda start_date, end_date, symbol, interval="1d": _hist(symbol),
    )

    workspace = service.build_influence_workspace(force_refresh=True)

    assert workspace["summary_cards"][0]["label"] == "Directed flows"
    assert workspace["pair_rows"]
    assert "->" in workspace["headline"]["label"]
    assert workspace["source_rows"]
    assert workspace["target_rows"]


def test_public_dashboard_live_source_health_overrides_cached_operational_lanes(monkeypatch):
    cache_clear()
    service = PublicDashboardService(ttl_seconds=1)
    monkeypatch.setattr(
        service,
        "build_snapshot",
        lambda force_refresh=False: {
            "generated_at": "2026-06-02T00:00:00Z",
            "source_health": [
                {"key": "market", "label": "Market feed", "state": "healthy", "state_label": "Healthy", "detail": "ok", "updated_at": "2026-06-02T00:00:00Z"},
                {"key": "kap-enrichment", "label": "BIST disclosures", "state": "warming", "state_label": "Refreshing", "detail": "stale", "updated_at": "2026-06-02T00:00:00Z"},
            ],
        },
    )
    monkeypatch.setattr(
        service.stock_enrichment,
        "get_health_snapshot",
        lambda: {
            "key": "kap-enrichment",
            "label": "BIST disclosures",
            "state": "healthy",
            "state_label": "Healthy",
            "detail": "live",
            "updated_at": "2026-06-02T01:00:00Z",
        },
    )
    monkeypatch.setattr(
        service,
        "_build_macro_cards",
        lambda generated_at: (
            [],
            {
                "key": "macro",
                "label": "Macro feed",
                "state": "healthy",
                "state_label": "Healthy",
                "detail": "live macro",
                "updated_at": generated_at,
            },
        ),
    )
    monkeypatch.setattr(
        service,
        "_build_cached_tr_peer_board",
        lambda: [],
    )
    monkeypatch.setattr(
        service,
        "_build_tr_status",
        lambda generated_at, tr_peer_board: {
            "key": "tr-funds",
            "label": "TR funds",
            "state": "degraded",
            "state_label": "Degraded",
            "detail": "live tr",
            "updated_at": generated_at,
        },
    )
    monkeypatch.setattr(
        service.institutional,
        "get_health_snapshot",
        lambda: {
            "key": "institutional",
            "label": "Institutional filings",
            "state": "healthy",
            "state_label": "Healthy",
            "detail": "live inst",
            "updated_at": "2026-06-02T01:00:00Z",
        },
    )

    snapshot = service.build_live_source_health()

    items = {item["key"]: item for item in snapshot["source_health"]}
    assert items["macro"]["detail"] == "live macro"
    assert items["kap-enrichment"]["detail"] == "live"
    assert items["tr-funds"]["detail"] == "live tr"
    assert items["institutional"]["detail"] == "live inst"


def test_entropy_calculator_shannon_entropy_stays_normalized():
    calc = EntropyCalculator()
    returns = pd.Series(np.linspace(-0.003, 0.003, 120))

    entropy = calc.shannon_entropy(returns)

    assert 0.0 <= entropy <= 1.0


def test_public_dashboard_clamps_entropy_scores(monkeypatch):
    cache_clear()
    service = PublicDashboardService(ttl_seconds=1)

    prices = pd.DataFrame(
        {
            "symbol": ["^GSPC"] * 70,
            "close_price": np.linspace(100, 120, 70),
        }
    )

    monkeypatch.setattr(
        service.yahoo,
        "get_historical_data",
        lambda start_date, end_date, symbol, interval="1d": prices.assign(symbol=symbol),
    )
    monkeypatch.setattr(service.entropy, "shannon_entropy", lambda returns: -4.0)
    monkeypatch.setattr(service.entropy, "permutation_entropy", lambda returns: 1.4)
    monkeypatch.setattr(service.entropy, "approximate_entropy", lambda returns: -3.0)
    monkeypatch.setattr(service.entropy, "spectral_entropy", lambda returns: 2.0)

    entropy_signal = service._build_entropy_signal("2026-06-06T00:00:00Z")
    first_row = entropy_signal["asset_rows"][0]

    assert entropy_signal["state"] == "healthy"
    assert entropy_signal["complexity_score"] == 33.3
    assert entropy_signal["predictability_score"] == 66.7
    assert first_row["shannon_entropy"] == 0.0
    assert first_row["permutation_entropy"] == 100.0
    assert first_row["spectral_clarity"] == 0.0


def test_public_dashboard_macro_cards_merge_official_sources(monkeypatch):
    cache_clear()
    service = PublicDashboardService(ttl_seconds=1)
    monkeypatch.setattr("app.services.public_dashboard.settings.FRED_API_KEY", "test-key")
    monkeypatch.setattr("app.services.public_dashboard.settings.TCMB_EVDS_API_KEY", "test-evds")

    monkeypatch.setattr(
        service.fred,
        "get_liquidity_indicators",
        lambda: {
            "liquidity_indicators": {
                "WALCL": {
                    "display_value": 6_700_000_000_000,
                    "change_percent": -0.4,
                    "currency_code": "USD",
                },
                "M2SL": {
                    "display_value": 22_300_000_000_000,
                    "change_percent": 0.2,
                    "currency_code": "USD",
                },
                "ECBASSETSW": {
                    "display_value": 6_100_000_000_000,
                    "change_percent": -0.1,
                    "currency_code": "EUR",
                },
            }
        },
    )
    monkeypatch.setattr(
        service.evds,
        "get_macro_indicators",
        lambda: {
            "macro_indicators": {
                "TCMB_RESERVES_TOTAL": {
                    "display_value": 154_560_000_000,
                    "change_percent": 1.4,
                    "display_kind": "money",
                    "currency_code": "USD",
                    "tone_multiplier": 1,
                },
                "TP.AB.C2": {
                    "display_value": 71_885_000_000,
                    "change_percent": 1.8,
                    "display_kind": "money",
                    "currency_code": "USD",
                    "tone_multiplier": 1,
                },
            }
        },
    )
    monkeypatch.setattr(
        service.fiscaldata,
        "get_fiscal_indicators",
        lambda: {
            "fiscal_indicators": {
                "tot_pub_debt_out_amt": {
                    "display_value": 36_500_000_000_000,
                    "change_percent": 0.05,
                    "currency_code": "USD",
                },
                "debt_held_public_amt": {
                    "display_value": 28_700_000_000_000,
                    "change_percent": 0.08,
                    "currency_code": "USD",
                },
            }
        },
    )

    cards, status = service._build_macro_cards("2026-06-06T00:00:00Z")

    labels = {card["label"] for card in cards}
    assert "Fed Balance Sheet" in labels
    assert "CBRT Total Reserves" in labels
    assert "US Public Debt" in labels
    assert status["state"] == "healthy"
    assert "FRED" in status["detail"]
    assert "TCMB EVDS" in status["detail"]
    assert "U.S. Treasury" in status["detail"]
