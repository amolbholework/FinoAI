"""Holds an uploaded CSV's raw bytes between the /preview and /commit calls so
the browser doesn't have to re-upload the whole file just to confirm a column
mapping. In-memory + TTL is enough for a single-process local demo; a real
deployment would put this in object storage or a short-lived DB row instead.
"""
import time
import uuid

_TTL_SECONDS = 15 * 60
_staged: dict[str, tuple[bytes, float]] = {}


def stage(raw: bytes) -> str:
    token = str(uuid.uuid4())
    _staged[token] = (raw, time.monotonic() + _TTL_SECONDS)
    _evict_expired()
    return token


def retrieve(token: str) -> bytes | None:
    entry = _staged.get(token)
    if not entry:
        return None
    raw, expires_at = entry
    if time.monotonic() > expires_at:
        del _staged[token]
        return None
    return raw


def _evict_expired() -> None:
    now = time.monotonic()
    expired = [t for t, (_, exp) in _staged.items() if exp < now]
    for t in expired:
        del _staged[t]
