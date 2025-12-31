import logging
import sys
from typing import Any

from app.core.config import settings

try:
    import structlog
except Exception:
    structlog = None


def setup_logging() -> None:
    """Configure structured logging for the application."""

    if structlog is not None:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )


def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    if structlog is None:
        return logging.getLogger(name)
    return structlog.get_logger(name)


setup_logging()
logger = get_logger(__name__)
