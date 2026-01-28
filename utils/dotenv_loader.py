"""Minimal .env loader to populate os.environ for local dev."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional


def _parse_line(line: str) -> Optional[tuple[str, str]]:
    if not line or line.startswith("#"):
        return None
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip("'").strip('"')
    if not key:
        return None
    return key, value


def load_dotenv(path: str | Path = ".env", override: bool = False, only: Optional[Iterable[str]] = None) -> bool:
    env_path = Path(path)
    if not env_path.exists():
        return False

    allowed = set(only or [])
    try:
        for raw in env_path.read_text().splitlines():
            parsed = _parse_line(raw.strip())
            if not parsed:
                continue
            key, value = parsed
            if allowed and key not in allowed:
                continue
            if override or key not in os.environ:
                os.environ[key] = value
        return True
    except Exception:
        return False
