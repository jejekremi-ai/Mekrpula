"""Agent catalog/profile validation, publish gates, auth replay, and object storage upload regressions."""

import io
import os
import asyncio

import base58
import pytest
import requests
from dotenv import load_dotenv
from nacl.signing import SigningKey
from PIL import Image
from pymongo import MongoClient
from fastapi import HTTPException

import sys

sys.path.append("/app/backend")
import agents  # noqa: E402


load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
MONGO_URL = os.environ.get("MONGO_URL").strip('"')
DB_NAME = os.environ.get("DB_NAME").strip('"')
FARTCOIN = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"

if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL must be defined")


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def api_client():
    return requests.Session()


@pytest.fixture
def mongo_db():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        yield db
    finally:
        client.close()


def _wallet_address(signing_key: SigningKey) -> str:
    return base58.b58encode(bytes(signing_key.verify_key)).decode()


def _auth_token(api_client: requests.Session):
    key = SigningKey.generate()
    wallet = _wallet_address(key)
    challenge = api_client.post(f"{BASE_URL}/api/auth/challenge", json={"wallet": wallet})
    assert challenge.status_code == 200
    payload = challenge.json()
    signature = base58.b58encode(key.sign(payload["message"].encode()).signature).decode()
    verify = api_client.post(f"{BASE_URL}/api/auth/verify", json={"nonce": payload["nonce"], "signature": signature})
    assert verify.status_code == 200
    body = verify.json()
    return {"wallet": wallet, "token": body["token"]}


@pytest.fixture
def auth_headers(api_client):
    auth = _auth_token(api_client)
    return {"Authorization": f"Bearer {auth['token']}"}


# Agent API catalog/profile/validation and publish authorization checks
def test_agent_models_catalog_has_10_and_execution_off(api_client):
    response = api_client.get(f"{BASE_URL}/api/agent/models")
    assert response.status_code == 200
    data = response.json()
    assert data["execution_enabled"] is False
    assert data["mode"] == "configuration-only"
    assert len(data["models"]) == 10
    providers = {m["provider"] for m in data["models"]}
    assert providers == {"Anthropic", "OpenAI", "Google", "DeepSeek", "Qwen", "Mistral"}


def test_agent_profile_for_canonical_token_defaults_shape(api_client):
    response = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/agent")
    assert response.status_code == 200
    data = response.json()
    assert data["execution_enabled"] is False
    assert "profile" in data and isinstance(data["profile"], dict)
    assert data["profile"]["name"].endswith("Agent")
    assert isinstance(data["activity"], list)
    assert set(data["ecosystem"].keys()) == {"listings", "events", "posts"}
    assert all(isinstance(v, int) for v in data["ecosystem"].values())


def test_agent_profile_unknown_token_returns_404(api_client):
    response = api_client.get(f"{BASE_URL}/api/tokens/UNKNOWN_TEST_MINT/agent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def _valid_agent_payload():
    return {
        "name": "TEST Agent",
        "role": "Community steward",
        "mission": "Bring token holders together with useful updates and community action.",
        "model_id": "gpt-5-mini",
        "creativity": 0.7,
        "risk": "Balanced",
        "instructions": "Keep responses concise and transparent.",
        "capabilities": ["observe", "research", "think", "strategy", "act", "monitor", "learn"],
        "allocation": {
            "community": 30,
            "liquidity": 25,
            "creative": 20,
            "buyback": 15,
            "operations": 10,
        },
    }


def test_agent_validate_accepts_valid_payload(api_client):
    payload = _valid_agent_payload()
    response = api_client.post(f"{BASE_URL}/api/agent/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["model_id"] == payload["model_id"]
    assert data["allocation"]["community"] == 30


@pytest.mark.parametrize(
    "patch",
    [
        {"model_id": "not-a-model"},
        {"capabilities": ["observe", "observe"]},
        {"capabilities": ["observe", "unsupported-capability"]},
        {"allocation": {"community": 20, "liquidity": 20, "creative": 20, "buyback": 20, "operations": 20.5}},
        {"allocation": {"community": 101, "liquidity": 0, "creative": 0, "buyback": 0, "operations": -1}},
        {"name": " "},
        {"mission": " "},
        {"name": "A"},
        {"creativity": 1.5},
        {"risk": "Aggressive"},
    ],
)
def test_agent_validate_rejects_invalid_payloads(api_client, patch):
    payload = _valid_agent_payload()
    payload.update(patch)
    response = api_client.post(f"{BASE_URL}/api/agent/validate", json=payload)
    assert response.status_code == 422


def test_agent_validate_rejects_extra_fields(api_client):
    payload = _valid_agent_payload()
    payload["unknown_field"] = "forbidden"
    response = api_client.post(f"{BASE_URL}/api/agent/validate", json=payload)
    assert response.status_code == 422


def test_agent_publish_anonymous_requires_auth(api_client):
    response = api_client.patch(f"{BASE_URL}/api/tokens/{FARTCOIN}/agent", json=_valid_agent_payload())
    assert response.status_code == 401
    assert "sign in" in response.json()["detail"].lower()


def test_agent_publish_non_authority_blocked_403(api_client, auth_headers):
    response = api_client.patch(f"{BASE_URL}/api/tokens/{FARTCOIN}/agent", headers=auth_headers, json=_valid_agent_payload())
    assert response.status_code == 403
    assert "verified token authority" in response.json()["detail"].lower()


class FakeAgentsCollection:
    def __init__(self, existing_activity=35):
        self.doc = {
            "token": "mint-isolated",
            "profile": _valid_agent_payload(),
            "updated_at": "2026-01-01T00:00:00+00:00",
            "updated_by": "wallet-1",
            "activity": [{"id": f"old-{i}", "title": "Old", "at": "2026-01-01T00:00:00+00:00", "kind": "configuration"} for i in range(existing_activity)],
        }
        self.update_calls = 0

    async def update_one(self, query, update, upsert=False):
        self.update_calls += 1
        self.doc["token"] = query["token"]
        self.doc["profile"] = update["$set"]["profile"]
        self.doc["updated_at"] = update["$set"]["updated_at"]
        self.doc["updated_by"] = update["$set"]["updated_by"]
        entries = update["$push"]["activity"]["$each"] + self.doc["activity"]
        self.doc["activity"] = entries[:30]


class FakeDB:
    def __init__(self):
        self.agents = FakeAgentsCollection()


def test_publish_isolated_success_persists_and_caps_history(monkeypatch):
    fake_db = FakeDB()

    async def fake_get_hub(mint):
        return {"address": mint, "claimed_by": "wallet-1"}

    async def fake_current_authority(mint, wallet):
        assert mint == "mint-isolated"
        assert wallet == "wallet-1"

    async def fake_agent(mint):
        return {
            "profile": fake_db.agents.doc["profile"],
            "published": True,
            "execution_enabled": False,
            "updated_at": fake_db.agents.doc["updated_at"],
            "updated_by": fake_db.agents.doc["updated_by"],
            "activity": fake_db.agents.doc["activity"],
            "ecosystem": {"listings": 0, "events": 0, "posts": 0},
        }

    monkeypatch.setattr(agents, "db", fake_db)
    monkeypatch.setattr(agents, "get_hub", fake_get_hub)
    monkeypatch.setattr(agents, "current_authority", fake_current_authority)
    monkeypatch.setattr(agents, "agent", fake_agent)

    result = run(agents.publish("mint-isolated", agents.AgentProfile(**_valid_agent_payload()), wallet="wallet-1"))
    assert result["published"] is True
    assert result["profile"]["name"] == "TEST Agent"
    assert len(result["activity"]) == 30
    assert result["activity"][0]["title"] == "Agent profile published"
    assert fake_db.agents.update_calls == 1


def test_publish_isolated_authority_failure_fails_closed(monkeypatch):
    fake_db = FakeDB()

    async def fake_get_hub(mint):
        return {"address": mint, "claimed_by": "wallet-1"}

    async def fake_current_authority(mint, wallet):
        raise HTTPException(403, "Only on-chain authority can publish")

    monkeypatch.setattr(agents, "db", fake_db)
    monkeypatch.setattr(agents, "get_hub", fake_get_hub)
    monkeypatch.setattr(agents, "current_authority", fake_current_authority)

    with pytest.raises(HTTPException) as exc:
        run(agents.publish("mint-isolated", agents.AgentProfile(**_valid_agent_payload()), wallet="wallet-1"))
    assert exc.value.status_code == 403
    assert fake_db.agents.update_calls == 0


# Off-chain auth challenge/verify/replay regression
def test_auth_challenge_verify_and_replay_rejected(api_client):
    key = SigningKey.generate()
    wallet = _wallet_address(key)
    challenge = api_client.post(f"{BASE_URL}/api/auth/challenge", json={"wallet": wallet})
    assert challenge.status_code == 200
    payload = challenge.json()
    signature = base58.b58encode(key.sign(payload["message"].encode()).signature).decode()

    first = api_client.post(f"{BASE_URL}/api/auth/verify", json={"nonce": payload["nonce"], "signature": signature})
    second = api_client.post(f"{BASE_URL}/api/auth/verify", json={"nonce": payload["nonce"], "signature": signature})
    assert first.status_code == 200
    assert second.status_code == 401
    assert "expired" in second.json()["detail"].lower()


# Upload/image object storage regression (metadata only in Mongo)
def test_upload_and_image_read_uses_storage_path_not_binary(api_client, auth_headers, mongo_db):
    image = Image.new("RGB", (20, 20), color=(30, 160, 90))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    upload = api_client.post(
        f"{BASE_URL}/api/uploads",
        headers=auth_headers,
        files={"file": ("tiny.png", buf.read(), "image/png")},
    )
    assert upload.status_code == 200
    url = upload.json()["url"]
    assert url.startswith(f"{BASE_URL}/api/images/")
    image_id = url.split("/")[-1]

    image_read = api_client.get(url)
    assert image_read.status_code == 200
    assert image_read.headers["content-type"].startswith("image/jpeg")
    assert len(image_read.content) > 0

    row = mongo_db.images.find_one({"id": image_id})
    assert row is not None
    assert isinstance(row.get("storage_path"), str) and row["storage_path"]
    assert row.get("data") is None

    mongo_db.images.delete_one({"id": image_id})


def test_upload_rejects_invalid_image_and_oversize(api_client, auth_headers):
    invalid = api_client.post(
        f"{BASE_URL}/api/uploads",
        headers=auth_headers,
        files={"file": ("bad.txt", b"not-image", "text/plain")},
    )
    assert invalid.status_code == 422

    oversize = api_client.post(
        f"{BASE_URL}/api/uploads",
        headers=auth_headers,
        files={"file": ("huge.jpg", b"x" * 5_100_200, "image/jpeg")},
    )
    assert oversize.status_code == 413
