"""Helpers for normalizing news payloads across providers."""

from typing import Any, Dict, Iterable, List


def _pick(obj: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        val = obj.get(key)
        if val not in (None, ""):
            return val
    return None


def normalize_yfinance_news(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize yfinance news payloads to a flat schema."""
    normalized: List[Dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        base = item.get("content") if isinstance(item.get("content"), dict) else item
        if not isinstance(base, dict):
            continue
        title = _pick(base, "title", "headline") or ""
        summary = _pick(base, "summary", "description") or ""

        provider = ""
        if isinstance(base, dict):
            provider = _pick(base, "publisher", "source") or ""
            provider_obj = base.get("provider") if isinstance(base.get("provider"), dict) else {}
            if not provider and isinstance(provider_obj, dict):
                provider = provider_obj.get("displayName", "") or ""

        link = ""
        if isinstance(base, dict):
            link = _pick(base, "link", "url") or ""
            if not link:
                canonical = base.get("canonicalUrl") if isinstance(base.get("canonicalUrl"), dict) else {}
                click = base.get("clickThroughUrl") if isinstance(base.get("clickThroughUrl"), dict) else {}
                link = canonical.get("url") or click.get("url") or ""

        publish_time = _pick(base, "providerPublishTime", "pubDate", "displayTime")

        normalized.append({
            "title": title,
            "summary": summary,
            "publisher": provider,
            "link": link,
            "publish_time": publish_time,
        })

    return normalized


def normalize_generic_news(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize generic news items (Finnhub/NewsAPI style)."""
    normalized: List[Dict[str, Any]] = []
    for item in items or []:
        title = _pick(item, "title", "headline") or ""
        summary = _pick(item, "summary", "description") or ""
        publisher = _pick(item, "source", "publisher") or ""
        link = _pick(item, "url", "link") or ""
        publish_time = _pick(item, "datetime", "time", "providerPublishTime", "pubDate", "displayTime")
        normalized.append({
            "title": title,
            "summary": summary,
            "publisher": publisher,
            "link": link,
            "publish_time": publish_time,
        })
    return normalized


def extract_news_text(items: Iterable[Dict[str, Any]], max_items: int = 6) -> str:
    """Flatten news items into a single text blob for summarization."""
    lines: List[str] = []
    for item in list(items or [])[:max_items]:
        title = item.get("title", "") if isinstance(item, dict) else ""
        summary = item.get("summary", "") if isinstance(item, dict) else ""
        if title:
            lines.append(title)
        if summary:
            lines.append(summary)
    return "\n".join(lines)
