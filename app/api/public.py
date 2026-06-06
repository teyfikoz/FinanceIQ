from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings
from app.services.public_dashboard import PublicDashboardService
from app.services.institutional_pulse import InstitutionalPulseService
from app.services.public_research import PublicResearchService
from app.services.tr_funds import TRFundsService

router = APIRouter()

dashboard_service = PublicDashboardService()
institutional_pulse_service = InstitutionalPulseService()
public_research_service = PublicResearchService()
tr_funds_service = TRFundsService()


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


@router.get("/public/dashboard")
async def get_public_dashboard() -> Dict[str, Any]:
    return {
        "status": "success",
        "app_name": settings.APP_DISPLAY_NAME,
        "snapshot": dashboard_service.build_snapshot(),
    }


@router.get("/public/tr-funds")
async def get_public_tr_funds() -> Dict[str, Any]:
    months = settings.PUBLIC_TR_FUNDS_MONTHS
    peer_board = tr_funds_service.get_cached_peer_signal_board(months=months)
    peer_board_records = peer_board.to_dict("records") if not peer_board.empty else []
    return {
        "status": "success",
        "top_pick": _to_json_safe(tr_funds_service.get_cached_top_pick(months=months)),
        "peer_board": _to_json_safe(peer_board_records),
        "leadership": _to_json_safe(tr_funds_service.get_leadership_snapshot(months=months)),
        "health": _to_json_safe(tr_funds_service.get_status(months=months)),
    }


@router.get("/public/source-health")
async def get_public_source_health() -> Dict[str, Any]:
    snapshot = dashboard_service.build_live_source_health()
    return {
        "status": "success",
        "generated_at": snapshot.get("generated_at"),
        "source_health": snapshot.get("source_health", []),
    }


@router.get("/public/reliability")
async def get_public_reliability() -> Dict[str, Any]:
    return {
        "status": "success",
        "workspace": _to_json_safe(dashboard_service.build_reliability_workspace()),
    }


@router.get("/public/institutional-pulse")
async def get_public_institutional_pulse(manager: str = settings.PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER) -> Dict[str, Any]:
    return {
        "status": "success",
        "workspace": _to_json_safe(institutional_pulse_service.get_workspace(manager)),
    }


@router.get("/public/conviction-board")
async def get_public_conviction_board(
    universe: str = settings.PUBLIC_DEFAULT_SCREENER_UNIVERSE,
    months: int = settings.PUBLIC_TR_FUNDS_MONTHS,
    limit: int = 6,
) -> Dict[str, Any]:
    return {
        "status": "success",
        "workspace": _to_json_safe(public_research_service.get_conviction_board_workspace(universe, months, limit)),
    }


@router.get("/public/influence-map")
async def get_public_influence_map() -> Dict[str, Any]:
    return {
        "status": "success",
        "workspace": _to_json_safe(dashboard_service.build_influence_workspace()),
    }


@router.get("/public/compare")
async def get_public_compare(
    kind: str = "stocks",
    left: str | None = None,
    right: str | None = None,
    months: int = settings.PUBLIC_TR_FUNDS_MONTHS,
) -> Dict[str, Any]:
    return {
        "status": "success",
        "workspace": _to_json_safe(public_research_service.get_compare_workspace(kind, left, right, months)),
    }


@router.get("/public/catalyst-calendar")
async def get_public_catalyst_calendar() -> Dict[str, Any]:
    return {
        "status": "success",
        "workspace": _to_json_safe(public_research_service.get_catalyst_calendar_workspace()),
    }


@router.get("/public/bist-quality-board")
async def get_public_bist_quality_board(limit: int = 12) -> Dict[str, Any]:
    return {
        "status": "success",
        "workspace": _to_json_safe(public_research_service.get_bist_quality_board_workspace(limit)),
    }


@router.get("/public/overlap-matrix")
async def get_public_overlap_matrix(focus: str = settings.PUBLIC_DEFAULT_OWNERSHIP_FOCUS) -> Dict[str, Any]:
    return {
        "status": "success",
        "workspace": _to_json_safe(public_research_service.get_overlap_matrix_workspace(focus)),
    }
