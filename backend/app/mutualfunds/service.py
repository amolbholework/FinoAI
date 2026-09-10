"""Server-side mutual fund NAV lookups against api.mfapi.in (sourced from
AMFI, no key required). Routed through our own backend rather than called
from the browser so we can cache — MFAPI's data only changes once a day
(NAVs are published end-of-day), so an hour-long cache is generous, not
aggressive, and keeps us well clear of any rate limiting.
"""
import logging
import time

import httpx

from app.mutualfunds.schema import NavPoint, SchemeDetail, SchemeSearchResult

logger = logging.getLogger("finpilot.mutualfunds")

CACHE_TTL_SECONDS = 3600
_BASE_URL = "https://api.mfapi.in/mf"
_TIMEOUT = 8.0
_HISTORY_POINTS = 30


class MutualFundDataUnavailableError(Exception):
    """Raised when the provider fails AND there's no cached value to fall
    back to."""


_scheme_cache: dict[int, tuple[SchemeDetail, float]] = {}  # scheme_code -> (detail, fetched_at_monotonic)
_search_cache: dict[str, tuple[list[SchemeSearchResult], float]] = {}


def _parse_detail(payload: dict) -> SchemeDetail:
    meta = payload["meta"]
    data = payload["data"]

    if not data:
        raise MutualFundDataUnavailableError(f"No NAV history returned for scheme {meta.get('scheme_code')}.")

    recent = data[:_HISTORY_POINTS]
    latest = recent[0]
    change_pct_30d = None
    if len(recent) > 1:
        oldest_in_window = recent[-1]
        old_nav = float(oldest_in_window["nav"])
        if old_nav:
            change_pct_30d = round((float(latest["nav"]) - old_nav) / old_nav * 100, 2)

    history = [NavPoint(date=p["date"], nav=float(p["nav"])) for p in reversed(recent)]

    return SchemeDetail(
        scheme_code=meta["scheme_code"],
        scheme_name=meta["scheme_name"],
        fund_house=meta.get("fund_house", ""),
        scheme_category=meta.get("scheme_category", ""),
        latest_nav=float(latest["nav"]),
        latest_date=latest["date"],
        change_pct_30d=change_pct_30d,
        history=history,
        is_stale=False,
    )


def get_scheme_detail(scheme_code: int) -> SchemeDetail:
    """Cache-first with a 1hr TTL. On a fresh fetch failure, serves the last
    known-good value (flagged stale) rather than erroring — only raises if
    there's truly nothing cached yet."""
    cached = _scheme_cache.get(scheme_code)
    now_monotonic = time.monotonic()

    if cached and (now_monotonic - cached[1]) < CACHE_TTL_SECONDS:
        return cached[0]

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.get(f"{_BASE_URL}/{scheme_code}")
            response.raise_for_status()
            payload = response.json()
        fresh = _parse_detail(payload)
        _scheme_cache[scheme_code] = (fresh, now_monotonic)
        return fresh
    except Exception as exc:
        logger.warning("Mutual fund fetch failed for %s: %s", scheme_code, exc)
        if cached:
            stale = cached[0].model_copy(update={"is_stale": True})
            return stale
        raise MutualFundDataUnavailableError(f"Could not fetch scheme {scheme_code} and no cached value is available.") from exc


def search_schemes(query: str) -> list[SchemeSearchResult]:
    key = query.strip().lower()
    cached = _search_cache.get(key)
    now_monotonic = time.monotonic()

    if cached and (now_monotonic - cached[1]) < CACHE_TTL_SECONDS:
        return cached[0]

    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.get(f"{_BASE_URL}/search", params={"q": query})
        response.raise_for_status()
        payload = response.json()

    results = [SchemeSearchResult(scheme_code=item["schemeCode"], scheme_name=item["schemeName"]) for item in payload[:25]]
    _search_cache[key] = (results, now_monotonic)
    return results
