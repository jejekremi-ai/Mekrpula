"""Regression tests for corrected agent integration, add-token gates, and native chart API."""

import os
import sys
import asyncio
from collections import deque

import base58
import pytest
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from nacl.signing import SigningKey

sys.path.append("/app/backend")
import charts  # noqa: E402


load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
FARTCOIN = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"
UNKNOWN_MINT = "11111111111111111111111111111111"

if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL must be defined")


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def api_client():
    return requests.Session()


@pytest.fixture
def auth_headers(api_client):
    key = SigningKey.generate()
    wallet = base58.b58encode(bytes(key.verify_key)).decode()
    challenge = api_client.post(f"{BASE_URL}/api/auth/challenge", json={"wallet": wallet})
    assert challenge.status_code == 200
    payload = challenge.json()
    sig = base58.b58encode(key.sign(payload["message"].encode()).signature).decode()
    verify = api_client.post(f"{BASE_URL}/api/auth/verify", json={"nonce": payload["nonce"], "signature": sig})
    assert verify.status_code == 200
    return {"Authorization": f"Bearer {verify.json()['token']}"}


def valid_agent_payload():
    return {
        "name": "TEST Configured Agent",
        "role": "Community steward",
        "mission": "Coordinate updates and keep the token ecosystem aligned with holder needs.",
        "model_id": "gpt-5-mini",
        "creativity": 0.6,
        "risk": "Balanced",
        "instructions": "Keep communication factual and concise.",
        "capabilities": ["observe", "research", "think", "strategy", "act", "monitor", "learn"],
        "allocation": {"community": 30, "liquidity": 25, "creative": 20, "buyback": 15, "operations": 10},
    }


# Agent public profile and Add Token integration checks
def test_canonical_token_agent_view_unconfigured_shape(api_client):
    response = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/agent")
    assert response.status_code == 200
    data = response.json()
    assert data["profile"] is None
    assert data["model"] is None
    assert data["published"] is False
    assert data["execution_enabled"] is False
    assert isinstance(data["ecosystem"], dict)
    assert set(data["ecosystem"].keys()) == {"listings", "events", "posts"}


def test_add_token_existing_mint_without_agent_is_public_and_non_destructive(api_client):
    response = api_client.post(f"{BASE_URL}/api/tokens", json={"address": FARTCOIN})
    assert response.status_code == 200
    body = response.json()
    assert body["token"]["address"] == FARTCOIN
    assert body["created"] is False
    assert body["agent_configured"] is False


def test_add_token_with_agent_without_auth_returns_401(api_client):
    response = api_client.post(
        f"{BASE_URL}/api/tokens",
        json={"address": FARTCOIN, "agent": valid_agent_payload()},
    )
    assert response.status_code == 401
    assert "sign in" in response.json()["detail"].lower()


def test_add_token_with_agent_wrong_authority_returns_403(api_client, auth_headers):
    response = api_client.post(
        f"{BASE_URL}/api/tokens",
        headers=auth_headers,
        json={"address": FARTCOIN, "agent": valid_agent_payload()},
    )
    assert response.status_code == 403
    assert "metadata update authority" in response.json()["detail"].lower()


def test_add_token_with_invalid_agent_payload_rejected_422(api_client):
    bad = valid_agent_payload()
    bad["allocation"] = {"community": 30, "liquidity": 25, "creative": 20, "buyback": 15, "operations": 11}
    response = api_client.post(
        f"{BASE_URL}/api/tokens",
        json={"address": FARTCOIN, "agent": bad},
    )
    assert response.status_code == 422


# Native chart API contract checks against live endpoint
def test_ohlcv_1h_returns_real_sorted_valid_candles(api_client):
    response = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/ohlcv?interval=1h")
    assert response.status_code == 200
    data = response.json()
    candles = data["candles"]
    assert data["mint"] == FARTCOIN
    assert data["interval"] == "1h"
    assert data["source"] == "GeckoTerminal"
    assert len(candles) == 160
    times = [c["time"] for c in candles]
    assert times == sorted(times)
    for c in candles:
        assert min(c["open"], c["high"], c["low"], c["close"], c["volume"]) >= 0
        assert c["high"] >= max(c["open"], c["close"], c["low"])
        assert c["low"] <= min(c["open"], c["close"])


def test_ohlcv_invalid_interval_returns_422(api_client):
    response = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/ohlcv?interval=5m")
    assert response.status_code == 422


def test_ohlcv_unknown_token_returns_404(api_client):
    response = api_client.get(f"{BASE_URL}/api/tokens/{UNKNOWN_MINT}/ohlcv?interval=1h")
    assert response.status_code == 404


# Isolated chart provider behavior checks with mocks
class StubResponse:
    def __init__(self, status_code=200, payload=None, should_raise=False):
        self.status_code = status_code
        self._payload = payload or {}
        self._should_raise = should_raise

    def raise_for_status(self):
        if self._should_raise:
            import httpx

            raise httpx.HTTPStatusError("boom", request=None, response=None)

    def json(self):
        return self._payload


class FakeCache:
    async def find_one(self, *_args, **_kwargs):
        return None

    async def update_one(self, *_args, **_kwargs):
        return None


class FakeHubs:
    async def update_one(self, *_args, **_kwargs):
        return None


class FakeDB:
    def __init__(self):
        self.ohlcv_cache = FakeCache()
        self.hubs = FakeHubs()


def reset_chart_rate_limit():
    charts._calls = deque()
    charts._blocked_until = 0


def test_request_json_maps_provider_429_to_503(monkeypatch):
    reset_chart_rate_limit()

    class StubClient:
        async def get(self, *_args, **_kwargs):
            return StubResponse(status_code=429)

    monkeypatch.setattr(charts, "http", StubClient())
    with pytest.raises(HTTPException) as exc:
        run(charts.request_json("/path"))
    assert exc.value.status_code == 503
    assert "rate-limited" in exc.value.detail.lower()


def test_request_json_maps_timeout_to_503(monkeypatch):
    reset_chart_rate_limit()

    class StubClient:
        async def get(self, *_args, **_kwargs):
            import httpx

            raise httpx.ReadTimeout("timeout")

    monkeypatch.setattr(charts, "http", StubClient())
    with pytest.raises(HTTPException) as exc:
        run(charts.request_json("/path"))
    assert exc.value.status_code == 503
    assert "temporarily unavailable" in exc.value.detail.lower()


def test_normalize_candles_rejects_malformed_and_sorts_valid_rows():
    rows = [
        [200, 1, 2, 0.5, 1.6, 100],
        [100, 1, 1.5, 0.9, 1.2, 90],
        [100, 99],
        [300, 1, 0.5, 0.8, 0.9, 10],
        [400, "x", 2, 1, 1.2, 10],
    ]
    out = charts.normalize_candles(rows)
    assert [c.time for c in out] == [100, 200]
    assert all(c.high >= max(c.open, c.close, c.low) for c in out)


def test_chart_rejects_provider_wrong_token(monkeypatch):
    reset_chart_rate_limit()

    async def fake_get_hub(_mint):
        return {"pair": "pool-1", "address": "mint-1"}

    async def fake_request_json(_path, _params=None):
        return {
            "data": {"attributes": {"ohlcv_list": [[100, 1, 2, 0.5, 1.2, 50]]}},
            "meta": {"base": {"address": "different-mint"}},
        }

    monkeypatch.setattr(charts, "get_hub", fake_get_hub)
    monkeypatch.setattr(charts, "request_json", fake_request_json)
    monkeypatch.setattr(charts, "db", FakeDB())

    with pytest.raises(HTTPException) as exc:
        run(charts.chart("mint-1", "1h"))
    assert exc.value.status_code == 502
    assert "different token" in exc.value.detail.lower()


def test_chart_returns_404_on_empty_provider_data(monkeypatch):
    reset_chart_rate_limit()

    async def fake_get_hub(_mint):
        return {"pair": None, "address": "mint-1"}

    async def fake_request_json(path, _params=None):
        if "tokens" in path and "pools" in path:
            return {"data": []}
        return {"data": {"attributes": {"ohlcv_list": []}}, "meta": {}}

    monkeypatch.setattr(charts, "get_hub", fake_get_hub)
    monkeypatch.setattr(charts, "request_json", fake_request_json)
    monkeypatch.setattr(charts, "db", FakeDB())

    with pytest.raises(HTTPException) as exc:
        run(charts.chart("mint-1", "1h"))
    assert exc.value.status_code == 404
    assert "no indexed price history" in exc.value.detail.lower()
