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
    create_demo_user: bool


def _get_secret(name: str) -> str | None:
    try:
        import streamlit as st  # type: ignore
        if name in st.secrets:
            return st.secrets.get(name)
        if "app" in st.secrets and name in st.secrets["app"]:
            return st.secrets["app"].get(name)
    except Exception:
        return None
    return None


def _get_setting(name: str) -> str | None:
    env_val = os.getenv(name)
    if env_val not in (None, ""):
        return env_val
    secret_val = _get_secret(name)
    if secret_val not in (None, ""):
        return str(secret_val)
    return None


def get_app_config() -> AppConfig:
    env = _get_setting("FINANCEIQ_ENV") or "production"
    require_auth = _truthy(_get_setting("FINANCEIQ_REQUIRE_AUTH"), default=False)
    allow_direct_access = _truthy(_get_setting("FINANCEIQ_DIRECT_ACCESS"), default=not require_auth)
    default_demo = "false" if env.lower() in ("production", "prod") else "true"
    create_demo_user = _truthy(_get_setting("FINANCEIQ_CREATE_DEMO_USER") or default_demo, default=False)

    return AppConfig(
        env=env,
        require_auth=require_auth,
        allow_direct_access=allow_direct_access,
        create_demo_user=create_demo_user,
    )
