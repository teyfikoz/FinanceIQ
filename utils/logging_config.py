#!/usr/bin/env python3
"""Logging configuration for FinanceIQ."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional


def _json_formatter(record: logging.LogRecord) -> str:
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": record.levelname,
        "logger": record.name,
        "message": record.getMessage(),
    }
    if record.exc_info:
        payload["exc_info"] = logging.Formatter().formatException(record.exc_info)
    return json.dumps(payload)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return _json_formatter(record)


def configure_logging(default_level: str = "INFO") -> None:
    level = os.getenv("FINANCEIQ_LOG_LEVEL", default_level).upper()
    use_json = os.getenv("FINANCEIQ_LOG_JSON", "false").lower() in ("1", "true", "yes")

    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler()
    if use_json:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))

    root.addHandler(handler)
    root.setLevel(level)
