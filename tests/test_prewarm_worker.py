import pandas as pd

from app.services.prewarm_worker import PublicDataPrewarmWorker


def test_public_prewarm_worker_warms_default_and_top_tr_funds(monkeypatch):
    worker = PublicDataPrewarmWorker(interval_seconds=1)
    worker.public_research_service.screener_universes = {
        "sp500": {
            "symbols": ["AAPL", "NVDA", "MSFT", "AMZN"],
        }
    }

    monkeypatch.setattr(
        worker.tr_funds_service,
        "prewarm",
        lambda months, force_refresh=True: {
            "status": {"status": "healthy"},
            "rows": 3,
            "top_pick": {"fund_code": "ZPE"},
        },
    )
    monkeypatch.setattr(
        worker.tr_funds_service,
        "get_cached_peer_signal_board",
        lambda months: pd.DataFrame([{"fund_code": "ZPE"}, {"fund_code": "GAH"}, {"fund_code": "TCD"}]),
    )
    warmed_enrichments = []

    def _fake_kap_enrichment(symbol, force_refresh=False):
        warmed_enrichments.append((symbol, force_refresh))
        return {"symbol_root": symbol, "source_state": "live", "field_coverage": 2}

    monkeypatch.setattr(
        worker.public_research_service.stock_enrichment_service,
        "get_kap_enrichment",
        _fake_kap_enrichment,
    )

    warmed = []

    def _fake_tr_workspace(code, months, force_refresh=False):
        warmed.append((code, force_refresh))
        return {"fund_code": code, "error": None}

    monkeypatch.setattr(worker.public_research_service, "get_tr_fund_workspace", _fake_tr_workspace)
    warmed_stocks = []

    def _fake_stock_workspace(symbol, force_refresh=False):
        warmed_stocks.append((symbol, force_refresh))
        return {"symbol": symbol, "error": None}

    monkeypatch.setattr(worker.public_research_service, "get_stock_workspace", _fake_stock_workspace)
    warmed_forecasts = []

    def _fake_forecast_workspace(symbol, days):
        warmed_forecasts.append((symbol, days))
        return {"symbol": symbol, "error": None}

    monkeypatch.setattr(worker.public_research_service, "get_forecast_workspace", _fake_forecast_workspace)
    warmed_funds = []

    def _fake_fund_workspace(symbol):
        warmed_funds.append(symbol)
        return {"symbol": symbol, "error": None}

    monkeypatch.setattr(worker.public_research_service, "get_fund_workspace", _fake_fund_workspace)
    monkeypatch.setattr(worker.dashboard_service, "build_snapshot", lambda force_refresh=True: {"generated_at": "2026-05-28T00:00:00Z"})
    monkeypatch.setattr(worker.dashboard_service, "build_influence_workspace", lambda force_refresh=False: {"pair_rows": [1, 2, 3]})
    warmed_screens = []

    def _fake_screener_workspace(universe, screen, limit):
        warmed_screens.append((universe, screen, limit))
        return {"match_count": 4}

    monkeypatch.setattr(worker.public_research_service, "get_screener_workspace", _fake_screener_workspace)
    monkeypatch.setattr(worker.public_research_service, "get_ownership_workspace", lambda symbol, focus: {"exposure_rows": [1, 2]})
    monkeypatch.setattr(worker.public_research_service, "get_sector_rotation_workspace", lambda: {"error": None})
    monkeypatch.setattr(worker.public_research_service, "get_idea_radar_workspace", lambda universe, limit: {"rows": [1, 2, 3]})
    monkeypatch.setattr(worker.public_research_service, "get_catalyst_calendar_workspace", lambda: {"recent_rows": [1, 2]})
    monkeypatch.setattr(worker.public_research_service, "get_bist_quality_board_workspace", lambda limit: {"rows": [1, 2, 3, 4]})
    monkeypatch.setattr(worker.public_research_service, "get_overlap_matrix_workspace", lambda focus: {"pair_rows": [1]})
    monkeypatch.setattr(worker.institutional_pulse_service, "manager_keys", lambda: ["berkshire"])
    monkeypatch.setattr(worker.institutional_pulse_service, "get_manager_dataset", lambda manager_key: {"source_state": "live"})
    monkeypatch.setattr(worker.institutional_pulse_service, "get_workspace", lambda manager: {"source_state": "live"})

    result = worker.run_once()

    assert warmed_enrichments == [("THYAO", True), ("GARAN", True), ("ASELS", True), ("TUPRS", True), ("BIMAS", True)]
    assert warmed == [("TCD", True), ("AFT", True), ("YAT", True), ("GPD", True), ("ZPE", True), ("GAH", True)]
    assert warmed_stocks == [("AAPL", True), ("NVDA", True), ("THYAO", True), ("GARAN", True), ("ASELS", True), ("TUPRS", True), ("BIMAS", True), ("MSFT", True), ("AMZN", True)]
    assert result["kap_enrichments_warmed"] == 5
    assert result["influence_pairs"] == 3
    assert result["kap_enrichment_signals"] == 5
    assert result["kap_enrichment_errors"] == 0
    assert result["tr_workspace_warmed"] == 6
    assert result["stock_workspaces_warmed"] == 9
    assert result["stock_workspace_errors"] == 0
    assert warmed_forecasts == [
        ("AAPL", 21),
        ("NVDA", 21),
        ("THYAO", 21),
        ("GARAN", 21),
        ("ASELS", 21),
        ("TUPRS", 21),
        ("BIMAS", 21),
        ("MSFT", 21),
        ("AMZN", 21),
        ("SPY", 21),
        ("QQQ", 21),
        ("VTI", 21),
        ("AGG", 21),
    ]
    assert result["forecast_workspaces_warmed"] == 9
    assert result["forecast_workspace_errors"] == 0
    assert warmed_funds == ["SPY", "QQQ", "VTI", "AGG"]
    assert result["fund_workspaces_warmed"] == 4
    assert result["fund_workspace_errors"] == 0
    assert result["fund_forecast_workspaces_warmed"] == 4
    assert result["fund_forecast_workspace_errors"] == 0
    assert result["tr_workspace_error"] is None
    assert warmed_screens == [
        ("sp500", "momentum_stocks", 18),
        ("bist", "bist_disclosure_leaders", 8),
        ("bist", "bist_contract_intensity", 8),
    ]
    assert result["bist_disclosure_rows"] == 4
    assert result["bist_contract_rows"] == 4
    assert result["catalyst_recent_rows"] == 2
    assert result["bist_quality_rows"] == 4
    assert result["overlap_pairs"] == 1
