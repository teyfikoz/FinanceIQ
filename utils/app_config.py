#!/usr/bin/env python3
"""Application config helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class AppConfig:
    env: str
    require_auth: bool
    allow_direct_access: bool


def get_app_config() -> AppConfig:
    env = os.getenv("FINANCEIQ_ENV", "production")
    require_auth = _truthy(os.getenv("FINANCEIQ_REQUIRE_AUTH"), default=False)
    allow_direct_access = _truthy(os.getenv("FINANCEIQ_DIRECT_ACCESS"), default=not require_auth)

    return AppConfig(
        env=env,
        require_auth=require_auth,
        allow_direct_access=allow_direct_access,
    )
