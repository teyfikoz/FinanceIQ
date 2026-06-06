from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.services.public_dashboard import PublicDashboardService
from app.services.institutional_pulse import InstitutionalPulseService
from app.services.public_research import PublicResearchService
from app.services.tr_funds import TRFundsService

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
dashboard_service = PublicDashboardService()
public_research_service = PublicResearchService()
institutional_pulse_service = InstitutionalPulseService()
tr_funds_service = TRFundsService()

LEGACY_VIEW_REDIRECTS = {
    "dashboard": "/dashboard",
    "conviction-board": "/conviction-board",
    "compare": "/compare",
    "influence-map": "/influence-map",
    "catalyst-calendar": "/catalyst-calendar",
    "overlap-matrix": "/overlap-matrix",
    "bist-quality-board": "/bist-quality-board",
    "stock-analysis": "/stocks",
    "fund-analysis": "/funds-etfs",
    "turkish-markets": "/turkish-funds",
    "sector-rotation": "/sector-rotation",
    "scenario-lab": "/scenario-lab",
    "idea-radar": "/idea-radar",
    "institutional-pulse": "/institutional-pulse",
    "reliability": "/reliability",
    "education": "/privacy",
    "privacy": "/privacy",
}


def _base_context(request: Request) -> dict:
    return {
        "request": request,
        "app_name": settings.APP_DISPLAY_NAME,
        "public_site_url": settings.PUBLIC_SITE_URL,
        "support_email": settings.SUPPORT_EMAIL,
        "current_year": datetime.utcnow().year,
        "page_description": (
            "Privacy-first market intelligence with open-access dashboarding, "
            "Turkish fund signals, and no account wall."
        ),
        "canonical_path": request.url.path,
    }


@router.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def homepage(request: Request, view: str | None = None) -> HTMLResponse:
    if view and view in LEGACY_VIEW_REDIRECTS:
        return RedirectResponse(url=LEGACY_VIEW_REDIRECTS[view], status_code=307)
    return await dashboard_page(request)


@router.api_route("/dashboard", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def dashboard_page(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "dashboard",
            "canonical_path": "/dashboard",
            "page_description": (
                "FundPilot dashboard for public market pulse, macro context, crypto risk proxy, "
                "and Turkish fund signal monitoring."
            ),
            "snapshot": dashboard_service.build_snapshot(),
        }
    )
    return templates.TemplateResponse(request, "dashboard.html", context)


@router.api_route("/conviction-board", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def conviction_board_page(
    request: Request,
    universe: str = settings.PUBLIC_DEFAULT_SCREENER_UNIVERSE,
    months: int = settings.PUBLIC_TR_FUNDS_MONTHS,
    limit: int = 6,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "conviction-board",
            "canonical_path": "/conviction-board",
            "page_description": (
                "Cross-asset conviction board combining TEFAS leaders, ETF crowding, "
                "and curated SEC 13F accumulation."
            ),
            "workspace": public_research_service.get_conviction_board_workspace(universe, months, limit),
        }
    )
    return templates.TemplateResponse(request, "conviction_board.html", context)


@router.api_route("/influence-map", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def influence_map_page(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "influence-map",
            "canonical_path": "/influence-map",
            "page_description": (
                "Directional market influence map using transfer entropy to show which macro and risk assets are leading."
            ),
            "workspace": dashboard_service.build_influence_workspace(),
        }
    )
    return templates.TemplateResponse(request, "influence_map.html", context)


@router.api_route("/compare", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def compare_page(
    request: Request,
    kind: str = "stocks",
    left: str | None = None,
    right: str | None = None,
    months: int = settings.PUBLIC_TR_FUNDS_MONTHS,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "compare",
            "canonical_path": "/compare",
            "page_description": (
                "Side-by-side comparison for stocks, ETFs, and Turkish funds with fast public decision metrics."
            ),
            "workspace": public_research_service.get_compare_workspace(kind, left, right, months),
        }
    )
    return templates.TemplateResponse(request, "compare.html", context)


@router.api_route("/turkish-funds", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def turkish_funds_page(
    request: Request,
    fund: str = settings.PUBLIC_DEFAULT_TR_FUND_CODE,
    months: int = settings.PUBLIC_TR_FUNDS_MONTHS,
) -> HTMLResponse:
    months = max(3, min(months or settings.PUBLIC_TR_FUNDS_MONTHS, 18))
    peer_board = tr_funds_service.get_cached_peer_signal_board(months=months)
    context = _base_context(request)
    context.update(
        {
            "active_page": "turkish-funds",
            "canonical_path": "/turkish-funds",
            "page_description": (
                "Public TEFAS signal board with Turkish fund momentum, allocation drift, "
                "and investor growth context."
            ),
            "top_pick": tr_funds_service.get_cached_top_pick(months=months),
            "peer_board": peer_board.to_dict("records") if not peer_board.empty else [],
            "leadership": tr_funds_service.get_leadership_snapshot(months=months),
            "fund_workspace": public_research_service.get_tr_fund_workspace(fund, months),
        }
    )
    return templates.TemplateResponse(request, "turkish_funds.html", context)


@router.api_route("/stocks", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def stocks_page(request: Request, symbol: str = settings.PUBLIC_DEFAULT_STOCK_SYMBOL) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "stocks",
            "canonical_path": "/stocks",
            "page_description": (
                "Single-stock research workspace with return signals, technical read, "
                "support-resistance levels, and trend assessment."
            ),
            "workspace": public_research_service.get_stock_workspace(symbol),
        }
    )
    return templates.TemplateResponse(request, "stocks.html", context)


@router.api_route("/funds-etfs", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def funds_page(request: Request, symbol: str = settings.PUBLIC_DEFAULT_FUND_SYMBOL) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "funds-etfs",
            "canonical_path": "/funds-etfs",
            "page_description": (
                "ETF and fund research workspace with performance, risk, holdings, "
                "benchmark context, and fee-aware review."
            ),
            "workspace": public_research_service.get_fund_workspace(symbol),
        }
    )
    return templates.TemplateResponse(request, "funds_etfs.html", context)


@router.api_route("/sovereign-funds", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def sovereign_funds_page(
    request: Request,
    fund: str | None = None,
    country: str | None = None,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "sovereign-funds",
            "canonical_path": "/sovereign-funds",
            "page_description": (
                "Country wealth fund and pension fund allocations with holdings, country exposure, "
                "and concentration context."
            ),
            "workspace": public_research_service.get_sovereign_workspace(fund, country),
        }
    )
    return templates.TemplateResponse(request, "sovereign_funds.html", context)


@router.api_route("/forecasts", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def forecasts_page(
    request: Request,
    symbol: str = settings.PUBLIC_DEFAULT_FORECAST_SYMBOL,
    days: int = settings.PUBLIC_DEFAULT_FORECAST_DAYS,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "forecasts",
            "canonical_path": "/forecasts",
            "page_description": (
                "Multi-model price forecast workspace with model comparison, "
                "consensus target, and public trend bias."
            ),
            "workspace": public_research_service.get_forecast_workspace(symbol, days),
        }
    )
    return templates.TemplateResponse(request, "forecasts.html", context)


@router.api_route("/screener", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def screener_page(
    request: Request,
    universe: str = settings.PUBLIC_DEFAULT_SCREENER_UNIVERSE,
    screen: str = settings.PUBLIC_DEFAULT_SCREENER_SCREEN,
    limit: int = 18,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "screener",
            "canonical_path": "/screener",
            "page_description": (
                "Curated screener workspace with predefined momentum, value, quality, and BIST-focused scans."
            ),
            "workspace": public_research_service.get_screener_workspace(universe, screen, limit),
        }
    )
    return templates.TemplateResponse(request, "screener.html", context)


@router.api_route("/bist-quality-board", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def bist_quality_board_page(request: Request, limit: int = 12) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "bist-quality-board",
            "canonical_path": "/bist-quality-board",
            "page_description": (
                "BIST quality and capital efficiency board with disclosure-aware scoring."
            ),
            "workspace": public_research_service.get_bist_quality_board_workspace(limit),
        }
    )
    return templates.TemplateResponse(request, "bist_quality_board.html", context)


@router.api_route("/ownership-lens", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def ownership_lens_page(
    request: Request,
    symbol: str = settings.PUBLIC_DEFAULT_OWNERSHIP_SYMBOL,
    focus: str = settings.PUBLIC_DEFAULT_OWNERSHIP_FOCUS,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "ownership-lens",
            "canonical_path": "/ownership-lens",
            "page_description": (
                "ETF weight tracker and reverse-lookup workspace showing which tracked funds own a stock."
            ),
            "workspace": public_research_service.get_ownership_workspace(symbol, focus),
        }
    )
    return templates.TemplateResponse(request, "ownership_lens.html", context)


@router.api_route("/overlap-matrix", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def overlap_matrix_page(
    request: Request,
    focus: str = settings.PUBLIC_DEFAULT_OWNERSHIP_FOCUS,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "overlap-matrix",
            "canonical_path": "/overlap-matrix",
            "page_description": (
                "ETF overlap matrix showing where popular tracked funds are crowding into the same names."
            ),
            "workspace": public_research_service.get_overlap_matrix_workspace(focus),
        }
    )
    return templates.TemplateResponse(request, "overlap_matrix.html", context)


@router.api_route("/sector-rotation", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def sector_rotation_page(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "sector-rotation",
            "canonical_path": "/sector-rotation",
            "page_description": (
                "Sector leadership and rotation workspace based on major US sector ETFs."
            ),
            "workspace": public_research_service.get_sector_rotation_workspace(),
        }
    )
    return templates.TemplateResponse(request, "sector_rotation.html", context)


@router.api_route("/scenario-lab", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def scenario_lab_page(
    request: Request,
    positions: str | None = None,
    preset: str | None = None,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "scenario-lab",
            "canonical_path": "/scenario-lab",
            "page_description": (
                "Local-first portfolio health and macro stress testing workspace with no login and no storage."
            ),
            "workspace": public_research_service.get_portfolio_lab_workspace(positions, preset),
        }
    )
    return templates.TemplateResponse(request, "scenario_lab.html", context)


@router.api_route("/idea-radar", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def idea_radar_page(
    request: Request,
    universe: str = settings.PUBLIC_DEFAULT_SCREENER_UNIVERSE,
    limit: int = 8,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "idea-radar",
            "canonical_path": "/idea-radar",
            "page_description": (
                "Conviction-ranked idea board combining momentum, quality, sector leadership, and ETF crowding."
            ),
            "workspace": public_research_service.get_idea_radar_workspace(universe, limit),
        }
    )
    return templates.TemplateResponse(request, "idea_radar.html", context)


@router.api_route("/catalyst-calendar", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def catalyst_calendar_page(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "catalyst-calendar",
            "canonical_path": "/catalyst-calendar",
            "page_description": (
                "Catalyst calendar for KAP disclosures, TEFAS refreshes, and curated SEC 13F update windows."
            ),
            "workspace": public_research_service.get_catalyst_calendar_workspace(),
        }
    )
    return templates.TemplateResponse(request, "catalyst_calendar.html", context)


@router.api_route("/institutional-pulse", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def institutional_pulse_page(
    request: Request,
    manager: str = settings.PUBLIC_DEFAULT_INSTITUTIONAL_MANAGER,
) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "institutional-pulse",
            "canonical_path": "/institutional-pulse",
            "page_description": (
                "Official SEC 13F workspace tracking curated institutional managers, "
                "their biggest holdings, adds, trims, and overlap."
            ),
            "workspace": institutional_pulse_service.get_workspace(manager),
        }
    )
    return templates.TemplateResponse(request, "institutional_pulse.html", context)


@router.api_route("/reliability", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def reliability_page(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "reliability",
            "canonical_path": "/reliability",
            "page_description": (
                "FundPilot reliability center covering source health, curated enrichment coverage, "
                "and long-horizon operating risks."
            ),
            "workspace": dashboard_service.build_reliability_workspace(),
        }
    )
    return templates.TemplateResponse(request, "reliability.html", context)


@router.api_route("/portfolio", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def portfolio_page(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "portfolio",
            "canonical_path": "/portfolio",
            "page_description": (
                "Local-first portfolio import/export and sync. All positions stay in your browser."
            ),
        }
    )
    return templates.TemplateResponse(request, "portfolio.html", context)


@router.api_route("/privacy", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def privacy_page(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "privacy",
            "canonical_path": "/privacy",
            "page_description": (
                "FundPilot privacy note covering the public read-only build, direct sponsor placements, "
                "and low-retention operating posture."
            ),
        }
    )
    return templates.TemplateResponse(request, "privacy.html", context)


@router.api_route("/methodology", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def methodology_page(request: Request) -> HTMLResponse:
    context = _base_context(request)
    context.update(
        {
            "active_page": "methodology",
            "canonical_path": "/methodology",
            "page_description": (
                "FundPilot methodology: data sources, cache cadence, signal construction, "
                "and public-surface operating principles."
            ),
        }
    )
    return templates.TemplateResponse(request, "methodology.html", context)


@router.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon() -> RedirectResponse:
    return RedirectResponse(url="/static/favicon.svg", status_code=307)
