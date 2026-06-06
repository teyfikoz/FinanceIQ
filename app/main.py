from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import time
from typing import Dict, Any
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.utils.logger import get_logger
from app.api.endpoints import router as api_router
from app.api.public import router as public_router
from app.api.public import tr_funds_service
from app.web.routes import router as web_router
from app.services.prewarm_worker import PublicDataPrewarmWorker

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    static_dir = Path(__file__).resolve().parent / "web" / "static"
    template_dir = Path(__file__).resolve().parent / "web" / "templates"
    templates = Jinja2Templates(directory=str(template_dir))

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Global Liquidity & Market Correlation Dashboard API",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENABLE_API_DOCS else None,
        docs_url="/docs" if settings.ENABLE_API_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.state.prewarm_worker = None

    def is_api_request(request: Request) -> bool:
        return request.url.path.startswith("/api")

    def render_error_page(
        request: Request,
        status_code: int,
        title: str,
        message: str,
    ) -> HTMLResponse:
        context = {
            "request": request,
            "active_page": "error",
            "app_name": settings.APP_DISPLAY_NAME,
            "public_site_url": settings.PUBLIC_SITE_URL,
            "support_email": settings.SUPPORT_EMAIL,
            "current_year": time.gmtime().tm_year,
            "error_code": status_code,
            "error_title": title,
            "error_message": message,
        }
        return templates.TemplateResponse(request, "error.html", context, status_code=status_code)

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self'; "
            "script-src 'self'; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )

        # Log request
        logger.info(
            "Request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
        )
        return response

    # Exception handler
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if is_api_request(request):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
        if exc.status_code == 404:
            return render_error_page(
                request,
                status_code=404,
                title="Page not found.",
                message="This route is not part of the public FundPilot surface. Use the dashboard or Turkish funds pages instead.",
            )
        return render_error_page(
            request,
            status_code=exc.status_code,
            title="This section is temporarily unavailable.",
            message="The request reached FundPilot, but the page could not be rendered safely. Try again shortly.",
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            method=request.method,
        )
        if is_api_request(request):
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        return render_error_page(
            request,
            status_code=500,
            title="Temporary issue on the public workspace.",
            message="The page failed gracefully and no account data was exposed. Please retry in a moment.",
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint."""
        tr_status = tr_funds_service.get_status(months=settings.PUBLIC_TR_FUNDS_MONTHS)
        worker = getattr(app.state, "prewarm_worker", None)
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": time.time(),
            "prewarm_worker": worker.snapshot() if worker else {"enabled": False, "alive": False},
            "tr_funds": tr_status,
        }

    @app.get("/api")
    async def api_index() -> Dict[str, str]:
        """API index endpoint."""
        return {
            "message": "FundPilot public API",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(public_router, prefix=settings.API_V1_STR)
    app.include_router(web_router)

    @app.on_event("startup")
    async def startup_prewarm_worker() -> None:
        if not settings.ENABLE_PREWARM_WORKER:
            logger.info("Public data prewarm worker disabled")
            return
        worker = PublicDataPrewarmWorker()
        app.state.prewarm_worker = worker
        worker.start()

    @app.on_event("shutdown")
    async def shutdown_prewarm_worker() -> None:
        worker = getattr(app.state, "prewarm_worker", None)
        if worker:
            worker.stop()

    logger.info("FastAPI application created successfully")
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
