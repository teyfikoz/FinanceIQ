import logging
import sys
from typing import Any

from app.core.config import settings

try:
    import structlog
except Exception:
    structlog = None


class StdlibCompatLogger:
    """Small adapter so stdlib logging accepts structlog-style keyword context."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def bind(self, **_: Any) -> "StdlibCompatLogger":
        return self

    def new(self, **_: Any) -> "StdlibCompatLogger":
        return self

    def _emit(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        exc_info = kwargs.pop("exc_info", None)
        stack_info = kwargs.pop("stack_info", False)
        extra = kwargs.pop("extra", None)
        if kwargs:
            context = " ".join(f"{key}={value!r}" for key, value in sorted(kwargs.items()))
            message = f"{message} | {context}"
        self._logger.log(
            level,
            message,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            extra=extra,
        )

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.ERROR, message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("exc_info", True)
        self._emit(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.CRITICAL, message, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._logger, name)


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
        return StdlibCompatLogger(logging.getLogger(name))
    return structlog.get_logger(name)


setup_logging()
logger = get_logger(__name__)
