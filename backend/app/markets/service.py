"""Server-side market index lookups. Deliberately never called from the
browser: the upstream provider doesn't send CORS headers for this endpoint
(a browser fetch would just fail), and routing it through our own backend
is also what lets us cache it — polling every client's browser directly
against a free public endpoint every 60s would get us rate-limited fast.
"""
import logging
import time

import httpx

from app.markets.schema import IndexData, IntradayPoint

logger = logging.getLogger("finpilot.markets")

INDICES = [
    {"symbol": "^NSEI", "name": "Nifty 50"},
    {"symbol": "^BSESN", "name": "Sensex"},
]

CACHE_TTL_SECONDS = 60
_QUOTE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FinPilotAI/1.0)"}
_TIMEOUT = 6.0


class MarketDataUnavailableError(Exception):
    """Raised when the provider fails AND there's no cached value to fall
    back to — the honest response at that point is an error, not a zero."""


_cache: dict[str, tuple[IndexData, float]] = {}  # symbol -> (data, fetched_at_monotonic)


def _fetch_from_provider(symbol: str, name: str) -> IndexData:
    url = _QUOTE_URL.format(symbol=symbol.replace("^", "%5E"))
    with httpx.Client(timeout=_TIMEOUT, headers=_HEADERS) as client:
        response = client.get(url, params={"interval": "5m", "range": "1d"})
        response.raise_for_status()
        payload = response.json()

    result = payload["chart"]["result"][0]
    meta = result["meta"]

    current = float(meta["regularMarketPrice"])
    previous_close = float(meta.get("previousClose") or meta["chartPreviousClose"])
    change = current - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0.0

    timestamps = result.get("timestamp") or []
    closes = result["indicators"]["quote"][0].get("close") or []
    points = [
        IntradayPoint(timestamp=ts, value=round(close, 2))
        for ts, close in zip(timestamps, closes)
        if close is not None
    ]

    trading_window = meta.get("currentTradingPeriod", {}).get("regular", {})
    now = int(time.time())
    is_open = bool(trading_window) and trading_window["start"] <= now <= trading_window["end"]

    return IndexData(
        name=name,
        symbol=symbol,
        current=round(current, 2),
        change=round(change, 2),
        change_pct=round(change_pct, 2),
        previous_close=round(previous_close, 2),
        points=points,
        timestamp=int(meta.get("regularMarketTime", now)),
        is_open=is_open,
        is_stale=False,
    )


def get_index(symbol: str, name: str) -> IndexData:
    """Cache-first with a 60s TTL. On a fresh fetch failure, serves the last
    known-good value (flagged stale) rather than erroring the whole
    dashboard — only raises if there's truly nothing cached yet."""
    cached = _cache.get(symbol)
    now_monotonic = time.monotonic()

    if cached and (now_monotonic - cached[1]) < CACHE_TTL_SECONDS:
        return cached[0]

    try:
        fresh = _fetch_from_provider(symbol, name)
        _cache[symbol] = (fresh, now_monotonic)
        return fresh
    except Exception as exc:
        logger.warning("Market data fetch failed for %s: %s", symbol, exc)
        if cached:
            stale_data = cached[0].model_copy(update={"is_stale": True})
            return stale_data
        raise MarketDataUnavailableError(f"Could not fetch {name} and no cached value is available.") from exc
