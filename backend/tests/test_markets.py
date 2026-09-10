import time

import pytest

from app.markets import service
from app.markets.schema import IndexData, IntradayPoint
from app.markets.service import MarketDataUnavailableError, get_index

SAMPLE = IndexData(
    name="Nifty 50",
    symbol="^NSEI",
    current=24570.65,
    change=-65.35,
    change_pct=-0.27,
    previous_close=24636.0,
    points=[IntradayPoint(timestamp=1786074300, value=24592.2)],
    timestamp=1786096873,
    is_open=False,
    is_stale=False,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    service._cache.clear()
    yield
    service._cache.clear()


def test_get_index_uses_provider_on_cold_cache(monkeypatch):
    calls = {"count": 0}

    def fake_fetch(symbol, name):
        calls["count"] += 1
        return SAMPLE

    monkeypatch.setattr(service, "_fetch_from_provider", fake_fetch)
    result = get_index("^NSEI", "Nifty 50")

    assert result.current == 24570.65
    assert calls["count"] == 1


def test_get_index_serves_from_cache_within_ttl(monkeypatch):
    calls = {"count": 0}

    def fake_fetch(symbol, name):
        calls["count"] += 1
        return SAMPLE

    monkeypatch.setattr(service, "_fetch_from_provider", fake_fetch)
    get_index("^NSEI", "Nifty 50")
    get_index("^NSEI", "Nifty 50")
    get_index("^NSEI", "Nifty 50")

    assert calls["count"] == 1  # only the first call actually hit the provider


def test_get_index_refetches_after_ttl_expires(monkeypatch):
    calls = {"count": 0}

    def fake_fetch(symbol, name):
        calls["count"] += 1
        return SAMPLE

    monkeypatch.setattr(service, "_fetch_from_provider", fake_fetch)
    monkeypatch.setattr(service, "CACHE_TTL_SECONDS", 0)  # expire immediately
    get_index("^NSEI", "Nifty 50")
    time.sleep(0.01)
    get_index("^NSEI", "Nifty 50")

    assert calls["count"] == 2


def test_get_index_falls_back_to_stale_cache_on_failure(monkeypatch):
    monkeypatch.setattr(service, "_fetch_from_provider", lambda symbol, name: SAMPLE)
    first = get_index("^NSEI", "Nifty 50")
    assert first.is_stale is False

    def always_fails(symbol, name):
        raise RuntimeError("provider is down")

    monkeypatch.setattr(service, "_fetch_from_provider", always_fails)
    monkeypatch.setattr(service, "CACHE_TTL_SECONDS", 0)  # force a refetch attempt
    second = get_index("^NSEI", "Nifty 50")

    assert second.is_stale is True
    assert second.current == SAMPLE.current  # never fabricated — same last-known value


def test_get_index_raises_when_no_cache_and_provider_fails(monkeypatch):
    def always_fails(symbol, name):
        raise RuntimeError("provider is down")

    monkeypatch.setattr(service, "_fetch_from_provider", always_fails)

    with pytest.raises(MarketDataUnavailableError):
        get_index("^NSEI", "Nifty 50")


def test_indices_router_omits_failed_index_instead_of_erroring(auth_client, monkeypatch):
    def one_fails_one_succeeds(symbol, name):
        if symbol == "^NSEI":
            raise RuntimeError("provider down for this one")
        return SAMPLE.model_copy(update={"symbol": symbol, "name": name})

    monkeypatch.setattr(service, "_fetch_from_provider", one_fails_one_succeeds)
    response = auth_client.get("/markets/indices")

    assert response.status_code == 200
    symbols = [i["symbol"] for i in response.json()["indices"]]
    assert "^NSEI" not in symbols
    assert "^BSESN" in symbols


def test_indices_router_requires_auth(client):
    response = client.get("/markets/indices")
    assert response.status_code == 401
