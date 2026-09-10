"""Minimal in-memory fixed-window rate limiter, keyed by client IP.

In-memory is fine for a single-process local/demo deployment; a
multi-instance deploy would swap this for a Redis-backed counter without
changing call sites. Used on endpoints that cost real money per call (the
screenshot extraction endpoint calls the Claude API).
"""
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_WINDOW_SECONDS = 60
_hits: dict[str, list[float]] = defaultdict(list)


def enforce_ip_rate_limit(request: Request, key_prefix: str, max_per_minute: int) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{key_prefix}:{client_ip}"
    now = time.monotonic()
    window_start = now - _WINDOW_SECONDS

    hits = [t for t in _hits[key] if t > window_start]
    if len(hits) >= max_per_minute:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests, please slow down.")

    hits.append(now)
    _hits[key] = hits
