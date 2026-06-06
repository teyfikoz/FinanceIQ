from __future__ import annotations

import threading
from typing import Any, Dict

from app.core.config import settings
from app.services.public_dashboard import PublicDashboardService
from app.services.institutional_pulse import InstitutionalPulseService
from app.services.public_research import PublicResearchService
from app.services.tr_funds import FEATURED_FUND_CODES, TRFundsService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PublicDataPrewarmWorker:
    def __init__(self, interval_seconds: int | None = None) -> None:
        self.interval_seconds = interval_seconds or settings.PREWARM_INTERVAL_SECONDS
        self.public_tr_funds_months = settings.PUBLIC_TR_FUNDS_MONTHS
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.dashboard_service = PublicDashboardService()
        self.institutional_pulse_service = InstitutionalPulseService()
        self.public_research_service = PublicResearchService()
        self.tr_funds_service = TRFundsService()

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run_forever, name="fundpilot-prewarm", daemon=True)
        self.thread.start()
        logger.info("Started public data prewarm worker", interval_seconds=self.interval_seconds)

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "interval_seconds": self.interval_seconds,
            "alive": bool(self.thread and self.thread.is_alive()),
        }

    def run_once(self) -> Dict[str, Any]:
        tr_result = self.tr_funds_service.prewarm(months=self.public_tr_funds_months, force_refresh=True)
        enrichment_symbols = ["THYAO", "GARAN", "ASELS", "TUPRS", "BIMAS"]
        kap_enrichments_warmed = 0
        kap_enrichment_signals = 0
        kap_enrichment_errors = 0
        for stock_symbol in enrichment_symbols:
            enrichment = self.public_research_service.stock_enrichment_service.get_kap_enrichment(
                stock_symbol,
                force_refresh=True,
            )
            kap_enrichments_warmed += 1
            if enrichment.get("field_coverage", 0):
                kap_enrichment_signals += 1
            if enrichment.get("source_state") == "unavailable":
                kap_enrichment_errors += 1
        dashboard_snapshot = self.dashboard_service.build_snapshot(force_refresh=True)
        influence_workspace = self.dashboard_service.build_influence_workspace(force_refresh=False)
        warm_codes = list(FEATURED_FUND_CODES)
        if settings.PUBLIC_DEFAULT_TR_FUND_CODE not in warm_codes:
            warm_codes.insert(0, settings.PUBLIC_DEFAULT_TR_FUND_CODE)
        top_pick = tr_result.get("top_pick") if isinstance(tr_result, dict) else None
        if isinstance(top_pick, dict) and top_pick.get("fund_code"):
            warm_codes.append(str(top_pick["fund_code"]).upper())

        peer_board = self.tr_funds_service.get_cached_peer_signal_board(months=self.public_tr_funds_months)
        if peer_board is not None and not peer_board.empty:
            warm_codes.extend(str(code).upper() for code in peer_board["fund_code"].head(3).tolist() if code)

        seen_codes = set()
        ordered_codes = []
        for code in warm_codes:
            if code not in seen_codes:
                seen_codes.add(code)
                ordered_codes.append(code)

        tr_workspace = {}
        warmed_tr_workspaces = 0
        for code in ordered_codes:
            workspace = self.public_research_service.get_tr_fund_workspace(
                code,
                self.public_tr_funds_months,
                force_refresh=True,
            )
            warmed_tr_workspaces += 1
            if code == settings.PUBLIC_DEFAULT_TR_FUND_CODE:
                tr_workspace = workspace
        screener_workspace = self.public_research_service.get_screener_workspace(
            settings.PUBLIC_DEFAULT_SCREENER_UNIVERSE,
            settings.PUBLIC_DEFAULT_SCREENER_SCREEN,
            18,
        )
        bist_disclosure_workspace = self.public_research_service.get_screener_workspace(
            "bist",
            "bist_disclosure_leaders",
            8,
        )
        bist_contract_workspace = self.public_research_service.get_screener_workspace(
            "bist",
            "bist_contract_intensity",
            8,
        )
        stock_symbols = [
            settings.PUBLIC_DEFAULT_STOCK_SYMBOL,
            settings.PUBLIC_DEFAULT_FORECAST_SYMBOL,
            *enrichment_symbols,
            *list(
                (
                    self.public_research_service.screener_universes.get(
                        settings.PUBLIC_DEFAULT_SCREENER_UNIVERSE,
                        {},
                    ).get("symbols", [])
                )[:8]
            ),
        ]
        warmed_stock_symbols: list[str] = []
        stock_error_count = 0
        warmed_forecast_symbols: list[str] = []
        forecast_error_count = 0
        for stock_symbol in stock_symbols:
            normalized_symbol = str(stock_symbol).upper()
            if normalized_symbol in warmed_stock_symbols:
                continue
            workspace = self.public_research_service.get_stock_workspace(normalized_symbol, force_refresh=True)
            warmed_stock_symbols.append(normalized_symbol)
            if workspace.get("error"):
                stock_error_count += 1
            forecast_workspace = self.public_research_service.get_forecast_workspace(normalized_symbol, 21)
            warmed_forecast_symbols.append(normalized_symbol)
            if forecast_workspace.get("error"):
                forecast_error_count += 1
        fund_symbols = [settings.PUBLIC_DEFAULT_FUND_SYMBOL, "QQQ", "VTI", "AGG"]
        warmed_fund_symbols: list[str] = []
        fund_error_count = 0
        warmed_fund_forecasts: list[str] = []
        fund_forecast_error_count = 0
        for fund_symbol in fund_symbols:
            normalized_symbol = str(fund_symbol).upper()
            if normalized_symbol in warmed_fund_symbols:
                continue
            workspace = self.public_research_service.get_fund_workspace(normalized_symbol)
            warmed_fund_symbols.append(normalized_symbol)
            if workspace.get("error"):
                fund_error_count += 1
            fund_forecast = self.public_research_service.get_forecast_workspace(normalized_symbol, 21)
            warmed_fund_forecasts.append(normalized_symbol)
            if fund_forecast.get("error"):
                fund_forecast_error_count += 1
        ownership_workspace = self.public_research_service.get_ownership_workspace(
            settings.PUBLIC_DEFAULT_OWNERSHIP_SYMBOL,
            settings.PUBLIC_DEFAULT_OWNERSHIP_FOCUS,
        )
        sector_rotation_workspace = self.public_research_service.get_sector_rotation_workspace()
        idea_radar_workspace = self.public_research_service.get_idea_radar_workspace(
            settings.PUBLIC_DEFAULT_SCREENER_UNIVERSE,
            8,
        )
        catalyst_calendar_workspace = self.public_research_service.get_catalyst_calendar_workspace()
        bist_quality_board_workspace = self.public_research_service.get_bist_quality_board_workspace(12)
        overlap_matrix_workspace = self.public_research_service.get_overlap_matrix_workspace(
            settings.PUBLIC_DEFAULT_OWNERSHIP_FOCUS,
        )
        institutional_states = {}
        for manager_key in self.institutional_pulse_service.manager_keys():
            dataset = self.institutional_pulse_service.get_manager_dataset(manager_key)
            institutional_states[manager_key] = dataset.get("source_state")
        institutional_workspace = self.institutional_pulse_service.get_workspace(settings.PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER)
        result = {
            "tr_funds_status": tr_result.get("status"),
            "tr_funds_rows": tr_result.get("rows", 0),
            "dashboard_generated_at": dashboard_snapshot.get("generated_at"),
            "influence_pairs": len(influence_workspace.get("pair_rows", [])),
            "kap_enrichments_warmed": kap_enrichments_warmed,
            "kap_enrichment_signals": kap_enrichment_signals,
            "kap_enrichment_errors": kap_enrichment_errors,
            "tr_workspace_error": tr_workspace.get("error"),
            "tr_workspace_warmed": warmed_tr_workspaces,
            "screener_rows": screener_workspace.get("match_count", 0),
            "bist_disclosure_rows": bist_disclosure_workspace.get("match_count", 0),
            "bist_contract_rows": bist_contract_workspace.get("match_count", 0),
            "stock_workspaces_warmed": len(warmed_stock_symbols),
            "stock_workspace_errors": stock_error_count,
            "forecast_workspaces_warmed": len(warmed_forecast_symbols),
            "forecast_workspace_errors": forecast_error_count,
            "fund_workspaces_warmed": len(warmed_fund_symbols),
            "fund_workspace_errors": fund_error_count,
            "fund_forecast_workspaces_warmed": len(warmed_fund_forecasts),
            "fund_forecast_workspace_errors": fund_forecast_error_count,
            "ownership_rows": len(ownership_workspace.get("exposure_rows", [])),
            "sector_rotation_error": sector_rotation_workspace.get("error"),
            "idea_radar_rows": len(idea_radar_workspace.get("rows", [])),
            "catalyst_recent_rows": len(catalyst_calendar_workspace.get("recent_rows", [])),
            "bist_quality_rows": len(bist_quality_board_workspace.get("rows", [])),
            "overlap_pairs": len(overlap_matrix_workspace.get("pair_rows", [])),
            "institutional_state": institutional_workspace.get("source_state"),
            "institutional_ready": sum(1 for state in institutional_states.values() if state == "live"),
        }
        logger.info("Completed public data prewarm cycle", **result)
        return result

    def _run_forever(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.run_once()
            except Exception as exc:
                logger.error("Public data prewarm cycle failed", error=str(exc))
            if self.stop_event.wait(self.interval_seconds):
                break
