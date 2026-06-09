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
    public_app_url: str
    public_app_host: str
    app_display_name: str
    support_email: str


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
    public_app_url = (_get_setting("FINANCEIQ_PUBLIC_APP_URL") or "https://fundpilot.techsyncanalytica.com").rstrip("/")
    public_app_host = _get_setting("FINANCEIQ_PUBLIC_APP_HOST") or public_app_url.replace("https://", "").replace("http://", "")
    app_display_name = _get_setting("FINANCEIQ_APP_DISPLAY_NAME") or "FundPilot"
    support_email = _get_setting("FINANCEIQ_SUPPORT_EMAIL") or "techsyncanalytica@gmail.com"

    return AppConfig(
        env=env,
        require_auth=require_auth,
        allow_direct_access=allow_direct_access,
        create_demo_user=create_demo_user,
        public_app_url=public_app_url,
        public_app_host=public_app_host,
        app_display_name=app_display_name,
        support_email=support_email,
    )
