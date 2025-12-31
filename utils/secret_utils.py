import os
from typing import Optional


def _read_streamlit_secrets():
    try:
        import streamlit as st
    except Exception:
        return None

    return getattr(st, "secrets", None)


def _get_from_source(source, name: str) -> Optional[str]:
    try:
        if name in source:
            value = source[name]
            return None if value in (None, "") else str(value)
    except Exception:
        pass

    try:
        value = source.get(name)
        return None if value in (None, "") else str(value)
    except Exception:
        return None


def get_secret(*names: str, default: Optional[str] = None) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value

    secrets = _read_streamlit_secrets()
    if secrets is None:
        return default

    sources = [secrets]
    try:
        if "api_keys" in secrets:
            sources.append(secrets["api_keys"])
    except Exception:
        pass

    for source in sources:
        for name in names:
            value = _get_from_source(source, name)
            if value:
                return value

    return default
