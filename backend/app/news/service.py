"""Server-side finance news via Marketaux (https://www.marketaux.com/), free
tier: 100 requests/day. Routed through our own backend and cached hard —
one shared 30-minute cache serves every user, so real traffic never comes
close to the daily cap regardless of how many people open the page.
"""
import logging
import time

import httpx

from app.core.config import get_settings
from app.news.schema import NewsArticle

logger = logging.getLogger("finpilot.news")

CACHE_TTL_SECONDS = 1800
_NEWS_URL = "https://api.marketaux.com/v1/news/all"
_TIMEOUT = 8.0

_cache: tuple[list[NewsArticle], float] | None = None


class NewsUnavailableError(Exception):
    """Raised when the provider fails AND there's no cached value to fall
    back to."""


def _fetch_from_provider(api_key: str) -> list[NewsArticle]:
    params = {
        "api_token": api_key,
        "countries": "in",
        "language": "en",
        "limit": 20,
        "filter_entities": "true",
    }
    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.get(_NEWS_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    if "error" in payload:
        raise NewsUnavailableError(payload["error"].get("message", "Marketaux returned an error."))

    articles = []
    for item in payload.get("data", []):
        articles.append(
            NewsArticle(
                uuid=item["uuid"],
                title=item["title"],
                description=item.get("description") or item.get("snippet") or "",
                url=item["url"],
                image_url=item.get("image_url"),
                source=item.get("source", "Unknown"),
                published_at=item["published_at"],
            )
        )
    return articles


def get_news() -> tuple[list[NewsArticle], bool]:
    """Returns (articles, is_stale). Raises NewsUnavailableError only if
    there's truly nothing — no fresh fetch and no cache — to show."""
    global _cache

    settings = get_settings()
    if not settings.marketaux_api_key:
        raise NewsUnavailableError("MARKETAUX_API_KEY is not configured.")

    now_monotonic = time.monotonic()
    if _cache and (now_monotonic - _cache[1]) < CACHE_TTL_SECONDS:
        return _cache[0], False

    try:
        fresh = _fetch_from_provider(settings.marketaux_api_key)
        _cache = (fresh, now_monotonic)
        return fresh, False
    except Exception as exc:
        logger.warning("News fetch failed: %s", exc)
        if _cache:
            return _cache[0], True
        raise NewsUnavailableError("Could not fetch news and no cached value is available.") from exc
