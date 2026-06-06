from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from app.services.cache import cache_clear, cache_set
from app.services.snapshot_store import SnapshotStore
from app.services.tr_funds import TRFundsService


class FakeTracker:
    def generate_portfolio_summary(self, fund_code: str, months: int = 12):
        samples = {
            "TCD": {
                "fund_name": "Tacirler Portfoy Degisken Fon",
                "latest_portfolio_value": 200.0,
                "portfolio_value_change": 40.0,
                "latest_num_investors": 120.0,
                "investor_change": 30.0,
                "total_new_holdings": 3,
                "total_removed_holdings": 1,
                "asset_allocation_current": {"stocks": 62.0, "repo": 12.0},
                "monthly_allocation_changes": [{"stocks_change": 4.5, "repo_change": -2.0}],
                "category": "Equity",
                "category_rank": 1,
                "category_count": 14,
                "market_share": 1.2,
            },
            "YAT": {
                "latest_portfolio_value": 160.0,
                "portfolio_value_change": -8.0,
                "latest_num_investors": 90.0,
                "investor_change": -5.0,
                "total_new_holdings": 1,
                "total_removed_holdings": 4,
                "asset_allocation_current": {"stocks": 42.0, "bonds": 25.0},
                "monthly_allocation_changes": [{"stocks_change": -3.0, "bonds_change": 1.0}],
                "category": "Mixed",
                "category_rank": 9,
                "category_count": 14,
                "market_share": 0.8,
            },
        }
        return samples.get(fund_code, {})

    def get_fund_identity(self, fund_code: str):
        identities = {
            "TCD": {
                "fund_code": "TCD",
                "fund_name": "Tacirler Portfoy Degisken Fon",
                "category": "Degisken Fon",
                "category_rank": 3,
                "category_count": 24,
                "market_share": 0.6,
            }
        }
        return identities.get(fund_code, {})


def test_tr_funds_service_ranks_top_pick():
    service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1)
    top_pick = service.get_top_pick(months=12)
    assert top_pick is not None
    assert top_pick["fund_code"] == "TCD"
    assert top_pick["signal_band"] in {"Leading", "Constructive"}


def test_tr_funds_service_returns_sorted_peer_board():
    service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1)
    peer_board = service.get_peer_signal_board(months=12)
    assert not peer_board.empty
    assert list(peer_board["fund_code"])[0] == "TCD"
    assert "signal_score" in peer_board.columns
    assert "fund_family" in peer_board.columns
    assert "local_factor" in peer_board.columns
    assert "board_score" in peer_board.columns


def test_tr_funds_status_degrades_if_warming_too_long():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        cache_set(
            service._status_key(12),
            {
                "status": "warming",
                "detail": "Refreshing TEFAS peer board.",
                "last_attempt_at": "2026-05-27T10:00:00Z",
                "last_success_at": None,
                "last_failure_at": None,
                "funds_requested": 6,
                "funds_loaded": 0,
                "error_count": 0,
                "cache_ttl_seconds": 600,
            },
            ttl=60,
        )
        status = service.get_status(months=12)
        assert status["status"] == "degraded"


def test_tr_funds_service_reads_last_good_snapshot_when_cache_empty():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        store.write_json(
            "tr-funds-peer-board-12",
            {
                "saved_at": "2026-05-27T10:00:00Z",
                "months": 12,
                "rows": [
                    {
                        "fund_code": "TCD",
                        "fund_name": "Test Fund",
                        "fund_name_short": "Test",
                        "signal_score": 81.2,
                        "signal_band": "Leading",
                        "investor_growth_pct": 11.4,
                        "value_growth_pct": 8.0,
                    }
                ],
            },
        )
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        peer_board = service.get_cached_peer_signal_board(months=12)
        assert not peer_board.empty
        assert peer_board.iloc[0]["fund_code"] == "TCD"


def test_tr_funds_status_uses_snapshot_when_cache_is_empty():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        store.write_json(
            "tr-funds-peer-board-12",
            {
                "saved_at": "2026-05-27T10:00:00Z",
                "months": 12,
                "rows": [
                    {
                        "fund_code": "TCD",
                        "fund_name": "Test Fund",
                        "fund_name_short": "Test",
                        "signal_score": 81.2,
                        "signal_band": "Leading",
                        "investor_growth_pct": 11.4,
                        "value_growth_pct": 8.0,
                    }
                ],
            },
        )
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        status = service.get_status(months=12)
        assert status["status"] == "healthy"
        assert status["funds_loaded"] == 1


def test_tr_funds_service_ignores_empty_cached_frame_and_uses_snapshot():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        store.write_json(
            "tr-funds-peer-board-12",
            {
                "saved_at": "2026-05-27T10:00:00Z",
                "months": 12,
                "rows": [
                    {
                        "fund_code": "TCD",
                        "fund_name": "Test Fund",
                        "fund_name_short": "Test",
                        "signal_score": 81.2,
                        "signal_band": "Leading",
                    }
                ],
            },
        )
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        cache_set("tr-funds:peer-board:12", pd.DataFrame(), ttl=60)
        peer_board = service.get_cached_peer_signal_board(months=12)
        assert not peer_board.empty
        assert peer_board.iloc[0]["fund_code"] == "TCD"


def test_tr_funds_service_enriches_legacy_snapshot_rows():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        store.write_json(
            "tr-funds-peer-board-12",
            {
                "saved_at": "2026-05-27T10:00:00Z",
                "months": 12,
                "rows": [
                    {
                        "fund_code": "TCD",
                        "fund_name": "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu",
                        "fund_name_short": "Is Dow Jones Istanbul 30",
                        "signal_score": 81.2,
                        "signal_band": "Leading",
                        "category": "Equity",
                        "category_rank": 1,
                        "category_count": 14,
                        "market_share": 1.2,
                        "dominant_asset": "Hisse",
                        "dominant_weight": 62.0,
                    }
                ],
            },
        )
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        peer_board = service.get_cached_peer_signal_board(months=12)
        row = peer_board.iloc[0]
        assert row["fund_name"] == "Tacirler Portfoy Degisken Fon"
        assert row["fund_family"] == "Tacirler Portfoy"
        assert row["local_factor"] == "Balanced Allocation"
        assert row["quality_tier"] == "Established"
        assert row["board_band"] == "Institutional Leader"
        assert float(row["category_percentile"]) == 91.3


def test_tr_funds_service_refreshes_legacy_peer_board_identity():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        store.write_json(
            "tr-funds-peer-board-12",
            {
                "saved_at": "2026-05-27T10:00:00Z",
                "months": 12,
                "rows": [
                    {
                        "fund_code": "TCD",
                        "fund_name": "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu",
                        "fund_name_short": "Is Dow Jones Istanbul 30",
                        "signal_score": 52.2,
                        "signal_band": "Neutral",
                        "category": "Equity",
                        "category_rank": 1,
                        "category_count": 14,
                        "market_share": 1.2,
                        "dominant_asset": "Hisse",
                        "dominant_weight": 62.0,
                    }
                ],
            },
        )
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        peer_board = service.get_cached_peer_signal_board(months=12)
        row = peer_board.iloc[0]
        assert row["fund_name"] == "Tacirler Portfoy Degisken Fon"
        assert row["fund_name_short"] == "Tacirler Degisken Fon"
        persisted = store.read_json("tr-funds-peer-board-12")
        assert persisted["rows"][0]["fund_name"] == "Tacirler Portfoy Degisken Fon"


def test_tr_funds_service_builds_leadership_snapshot():
    service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1)
    leadership = service.get_leadership_snapshot(months=12)
    assert leadership["family_rows"]
    assert leadership["factor_rows"]
    assert leadership["family_rows"][0]["house_view"] in {"House Leader", "Selective Strength", "Mixed Bench"}
    assert leadership["factor_rows"][0]["lead_fund"] == "TCD"


def test_tr_funds_service_uses_persisted_summary_snapshot_when_cache_empty():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        store.write_json(
            "tr-funds-summary-TCD-12",
            {
                "saved_at": "2026-05-27T10:00:00Z",
                "fund_code": "TCD",
                "months": 12,
                "summary": {"fund_name": "Persisted TCD", "latest_portfolio_value": 321.0},
            },
        )
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        summary = service.get_fund_summary("TCD", months=12)
        assert summary["fund_name"] == "Persisted TCD"


def test_tr_funds_service_persists_summary_snapshot_after_live_refresh():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        summary = service.get_fund_summary("TCD", months=12, force_refresh=True)
        persisted = store.read_json("tr-funds-summary-TCD-12")
        assert summary["latest_portfolio_value"] == 200.0
        assert persisted is not None
        assert persisted["summary"]["latest_portfolio_value"] == 200.0
        assert persisted["summary"]["fund_name"] == "Tacirler Portfoy Degisken Fon"


def test_tr_funds_service_ignores_empty_cached_summary_and_uses_persisted_snapshot():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        store.write_json(
            "tr-funds-summary-TCD-12",
            {
                "saved_at": "2026-05-27T10:00:00Z",
                "fund_code": "TCD",
                "months": 12,
                "summary": {"fund_name": "Persisted TCD", "latest_portfolio_value": 321.0},
            },
        )
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        cache_set("tr-funds:summary:TCD:12", {}, ttl=60)
        summary = service.get_fund_summary("TCD", months=12)
        assert summary["fund_name"] == "Persisted TCD"


def test_tr_funds_service_refreshes_legacy_seed_name_with_live_identity():
    cache_clear()
    with TemporaryDirectory() as tmpdir:
        store = SnapshotStore(base_dir=Path(tmpdir))
        store.write_json(
            "tr-funds-summary-TCD-12",
            {
                "saved_at": "2026-05-27T10:00:00Z",
                "fund_code": "TCD",
                "months": 12,
                "summary": {
                    "fund_name": "Is Portfoy Dow Jones Istanbul 30 Endeks Hisse Senedi Fonu",
                    "latest_portfolio_value": 321.0,
                },
            },
        )
        service = TRFundsService(tracker_cls=FakeTracker, ttl_seconds=1, snapshot_store=store)
        summary = service.get_fund_summary("TCD", months=12)
        assert summary["fund_name"] == "Tacirler Portfoy Degisken Fon"
