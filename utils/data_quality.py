#!/usr/bin/env python3
"""Data quality metadata and UI helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class DataQuality:
    """Data provenance and freshness metadata."""
    status: str  # "real", "cache", "fallback"
    provider: str  # "yfinance", "tradingview", "synthetic", "unknown"
    fetched_at: datetime
    cache_age_s: Optional[float] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "provider": self.provider,
            "fetched_at": self.fetched_at.isoformat(),
            "cache_age_s": self.cache_age_s,
            "note": self.note,
        }


STATUS_LABELS = {
    "real": "✅ Real",
    "cache": "🗃️ Cache",
    "fallback": "⚠️ Fallback",
}

STATUS_COLORS = {
    "real": "#16a34a",
    "cache": "#2563eb",
    "fallback": "#f59e0b",
}


def format_quality_badge(quality: DataQuality) -> str:
    """Return HTML badge for Streamlit markdown."""
    label = STATUS_LABELS.get(quality.status, quality.status.title())
    color = STATUS_COLORS.get(quality.status, "#64748b")
    provider = quality.provider
    fetched = quality.fetched_at.strftime("%Y-%m-%d %H:%M:%S")
    cache_note = ""
    if quality.cache_age_s is not None:
        cache_note = f" • cache_age={int(quality.cache_age_s)}s"
    note = f" • {quality.note}" if quality.note else ""

    return (
        f"<div style=\"display:inline-flex;align-items:center;gap:8px;"
        f"padding:6px 10px;border-radius:999px;background:{color}20;"
        f"border:1px solid {color};color:{color};font-weight:600;font-size:0.85rem;\">"
        f"{label} • {provider} • {fetched}{cache_note}{note}"
        f"</div>"
    )
