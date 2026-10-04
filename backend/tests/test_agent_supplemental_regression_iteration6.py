"""Supplemental correction coverage: launch snapshot/confirm, add-token agent import, and public agent view privacy."""

import asyncio
import base64
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction

import sys

sys.path.append("/app/backend")
import agents  # noqa: E402
import hubs  # noqa: E402
import launch  # noqa: E402


def run(coro):
    return asyncio.run(coro)


@dataclass
class FakeUpdateResult:
    matched_count: int = 0
    modified_count: int = 0
    upserted_id: str | None = None


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])
        self.inserted = []

    def _match(self, doc, query):
        return all(doc.get(k) == v for k, v in query.items())

    def _project(self, doc, projection):
        out = dict(doc)
        if projection and projection.get("_id") == 0:
            out.pop("_id", None)
        return out

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        self.inserted.append(dict(doc))
        return type("Insert", (), {"inserted_id": doc.get("id")})()

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._match(doc, query):
                return self._project(doc, projection)
        return None

    async def update_one(self, query, update, upsert=False):
        for idx, doc in enumerate(self.docs):
            if not self._match(doc, query):
                continue
            changed = False
            if "$set" in update:
                for key, value in update["$set"].items():
                    if doc.get(key) != value:
                        doc[key] = value
                        changed = True
            if "$setOnInsert" in update:
                # setOnInsert has no effect on matched existing docs
                pass
            self.docs[idx] = doc
            return FakeUpdateResult(matched_count=1, modified_count=1 if changed else 0)

        if upsert:
            new_doc = dict(query)
            if "$setOnInsert" in update:
                new_doc.update(update["$setOnInsert"])
            if "$set" in update:
                new_doc.update(update["$set"])
            self.docs.append(new_doc)
            return FakeUpdateResult(matched_count=0, modified_count=0, upserted_id=new_doc.get("id") or "upsert")
        return FakeUpdateResult(matched_count=0, modified_count=0)


class FakeDB:
    def __init__(self, metadata=None, launches=None, hubs_docs=None, agents_docs=None):
        self.metadata = FakeCollection(metadata)
        self.launches = FakeCollection(launches)
        self.hubs = FakeCollection(hubs_docs)
        self.agents = FakeCollection(agents_docs)
        self.listings = type("Counts", (), {"count_documents": staticmethod(lambda *_a, **_k: _async_zero())})
        self.events = type("Counts", (), {"count_documents": staticmethod(lambda *_a, **_k: _async_zero())})
        self.posts = type("Counts", (), {"count_documents": staticmethod(lambda *_a, **_k: _async_zero())})


async def _async_zero():
    return 0


class FakeHTTPResponse:
    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content


class FakeHTTPClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def post(self, url, json):
        self.calls.append({"url": url, "json": json})
        return self.response


def build_versioned_compatible_bytes(wallet_kp: Keypair, mint_kp: Keypair) -> bytes:
    """Create realistic signed tx bytes where signer set == {wallet, mint}."""
    recipient = Keypair().pubkey()
    ix_wallet = transfer(
        TransferParams(from_pubkey=wallet_kp.pubkey(), to_pubkey=recipient, lamports=1)
    )
    ix_mint = transfer(
        TransferParams(from_pubkey=mint_kp.pubkey(), to_pubkey=recipient, lamports=1)
    )
    blockhash = Hash.default()
    msg = Message.new_with_blockhash([ix_wallet, ix_mint], wallet_kp.pubkey(), blockhash)
    tx = Transaction.new_signed_with_payer([ix_wallet, ix_mint], wallet_kp.pubkey(), [wallet_kp, mint_kp], blockhash)
    # Keep msg referenced for readability / realism even though launch reads tx bytes.
    assert len(bytes(msg)) > 0
    return bytes(tx)


def valid_agent_profile(name="TEST Agent"):
    return {
        "name": name,
        "role": "Community steward",
        "mission": "Keep the market and community informed with transparent updates.",
        "model_id": "gpt-5-mini",
        "creativity": 0.6,
        "risk": "Balanced",
        "instructions": "Private creator guidance that must stay private.",
        "capabilities": ["observe", "research", "think", "strategy", "act", "monitor", "learn"],
        "allocation": {
            "community": 30,
            "liquidity": 25,
            "creative": 20,
            "buyback": 15,
            "operations": 10,
        },
    }


@pytest.fixture
def isolated_fake_db():
    return FakeDB()


# launch.prepare snapshot/storage checks (agent snapshot in launches only; metadata excludes agent)
def test_launch_prepare_stores_agent_snapshot_and_keeps_metadata_public_only(monkeypatch, isolated_fake_db):
    wallet_kp = Keypair()
    mint_kp = Keypair()
    wallet = str(wallet_kp.pubkey())
    mint = str(mint_kp.pubkey())
    tx_bytes = build_versioned_compatible_bytes(wallet_kp, mint_kp)
    fake_http = FakeHTTPClient(FakeHTTPResponse(status_code=200, content=tx_bytes))

    ids = iter(["meta-id-1", "launch-id-1"])
    monkeypatch.setattr(launch, "uid", lambda: next(ids))
    monkeypatch.setattr(launch, "now", lambda: datetime(2026, 2, 1, tzinfo=timezone.utc))
    monkeypatch.setattr(launch, "db", isolated_fake_db)
    monkeypatch.setattr(launch, "http", fake_http)
    monkeypatch.setenv("APP_ORIGIN", "https://pulse-ai-hub.preview.emergentagent.com")
    monkeypatch.setenv("PUMP_LOCAL_URL", "https://pump.local/mock")

    body = launch.LaunchInput(
        name="TEST Token",
        symbol="TEST",
        description="A long enough description for launch flow coverage.",
        image="https://pulse-ai-hub.preview.emergentagent.com/api/images/test-logo",
        banner="https://pulse-ai-hub.preview.emergentagent.com/api/images/test-banner",
        website="https://example.org",
        twitter="https://x.com/example",
        telegram="https://t.me/example",
        mint=mint,
        amount=0.5,
        slippage=10,
        agent=agents.AgentProfile(**valid_agent_profile()),
    )

    result = run(launch.prepare(body, wallet=wallet))

    assert set(result.keys()) == {"id", "transaction", "mint"}
    assert result["id"] == "launch-id-1"
    assert result["mint"] == mint
    assert base64.b64decode(result["transaction"]) == tx_bytes

    assert len(isolated_fake_db.metadata.docs) == 1
    metadata_row = isolated_fake_db.metadata.docs[0]
    assert metadata_row["id"] == "meta-id-1"
    assert metadata_row["metadata"]["name"] == "TEST Token"
    assert "agent" not in metadata_row["metadata"]
    assert "mint" not in metadata_row["metadata"]

    assert len(isolated_fake_db.launches.docs) == 1
    launch_row = isolated_fake_db.launches.docs[0]
    assert launch_row["wallet"] == wallet
    assert launch_row["mint"] == mint
    assert launch_row["metadata"]["description"] == body.description
    assert launch_row["agent_profile"]["model_id"] == "gpt-5-mini"
    expected_hash = hashlib.sha256(
        bytes(launch.VersionedTransaction.from_bytes(tx_bytes).message)
    ).hexdigest()
    assert launch_row["message_hash"] == expected_hash

    assert fake_http.calls[0]["json"]["tokenMetadata"]["uri"].endswith("/api/metadata/meta-id-1")
    assert fake_http.calls[0]["json"]["publicKey"] == wallet


def _launch_row_for_confirm(launch_id, wallet, mint, tx_bytes, profile=None):
    return {
        "id": launch_id,
        "wallet": wallet,
        "mint": mint,
        "signature": "sig-confirm",
        "metadata": {"description": "desc", "image": "img", "banner": "bnr"},
        "agent_profile": profile,
        "message_hash": hashlib.sha256(bytes(launch.VersionedTransaction.from_bytes(tx_bytes).message)).hexdigest(),
        "status": "prepared",
    }


# launch.confirm success, finalized rpc contract, attach source wallet provenance, and idempotent replay
def test_launch_confirm_success_finalized_attaches_profile_and_is_idempotent(monkeypatch):
    wallet_kp = Keypair()
    mint_kp = Keypair()
    wallet = str(wallet_kp.pubkey())
    mint = str(mint_kp.pubkey())
    tx_bytes = build_versioned_compatible_bytes(wallet_kp, mint_kp)

    shared_db = FakeDB(
        launches=[_launch_row_for_confirm("launch-1", wallet, mint, tx_bytes, valid_agent_profile("MART Launch Agent"))],
        hubs_docs=[{"address": mint}],
        agents_docs=[],
    )
    monkeypatch.setattr(launch, "db", shared_db)
    monkeypatch.setattr(agents, "db", shared_db)

    rpc_calls = []

    async def fake_rpc(method, params):
        rpc_calls.append((method, params))
        assert method == "getTransaction"
        assert params[1]["commitment"] == "finalized"
        return {"meta": {"err": None}, "transaction": [base64.b64encode(tx_bytes).decode()]}

    add_hub_calls = []

    async def fake_add_hub(mint_value):
        add_hub_calls.append(mint_value)
        return {"address": mint_value}, False

    # confirm should not invoke authority checks for mart-launch provenance
    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("current_authority should not be called during confirm")

    monkeypatch.setattr(launch, "rpc", fake_rpc)
    monkeypatch.setattr(launch, "add_hub", fake_add_hub)
    monkeypatch.setattr(hubs, "current_authority", fail_if_called)

    first = run(launch.confirm("launch-1", wallet=wallet))
    second = run(launch.confirm("launch-1", wallet=wallet))

    assert first["address"] == mint
    assert second["address"] == mint
    assert len(rpc_calls) == 2
    assert add_hub_calls == [mint, mint]

    assert len(shared_db.agents.docs) == 1
    stored_agent = shared_db.agents.docs[0]
    assert stored_agent["source"] == "mart-launch"
    assert stored_agent["updated_by"] == wallet
    assert stored_agent["profile"]["name"] == "MART Launch Agent"
    assert len(stored_agent["activity"]) == 1


@pytest.mark.parametrize(
    "mode, expected_status",
    [
        ("wrong_wallet", 404),
        ("no_finalized", 409),
        ("tx_err", 409),
        ("wrong_message", 422),
    ],
)
def test_launch_confirm_failure_paths_keep_agent_absent_and_no_hub_activity(monkeypatch, mode, expected_status):
    wallet_kp = Keypair()
    mint_kp = Keypair()
    wallet = str(wallet_kp.pubkey())
    mint = str(mint_kp.pubkey())
    tx_bytes = build_versioned_compatible_bytes(wallet_kp, mint_kp)
    launch_row = _launch_row_for_confirm("launch-f", wallet, mint, tx_bytes, valid_agent_profile("ShouldNotAttach"))
    if mode == "wrong_message":
        launch_row["message_hash"] = "0" * 64

    shared_db = FakeDB(launches=[launch_row], hubs_docs=[{"address": mint}], agents_docs=[])
    monkeypatch.setattr(launch, "db", shared_db)
    monkeypatch.setattr(agents, "db", shared_db)

    add_hub_calls = []

    async def fake_add_hub(mint_value):
        add_hub_calls.append(mint_value)
        return {"address": mint_value}, False

    async def fake_rpc(method, _params):
        assert method == "getTransaction"
        if mode == "no_finalized":
            return None
        if mode == "tx_err":
            return {"meta": {"err": {"InstructionError": [0, "Custom"]}}, "transaction": [""]}
        return {"meta": {"err": None}, "transaction": [base64.b64encode(tx_bytes).decode()]}

    monkeypatch.setattr(launch, "add_hub", fake_add_hub)
    monkeypatch.setattr(launch, "rpc", fake_rpc)

    with pytest.raises(HTTPException) as exc:
        run(launch.confirm("launch-f", wallet="wrong" if mode == "wrong_wallet" else wallet))
    assert exc.value.status_code == expected_status
    assert add_hub_calls == []
    assert shared_db.agents.docs == []


# hubs.add with optional agent: authority gates, idempotent same profile, 409 different profile, no-agent import non-destructive
def test_hubs_add_with_agent_authority_idempotence_and_conflict(monkeypatch):
    wallet = str(Keypair().pubkey())
    mint = str(Keypair().pubkey())
    shared_db = FakeDB(hubs_docs=[{"address": mint}], agents_docs=[])
    monkeypatch.setattr(hubs, "db", shared_db)
    monkeypatch.setattr(agents, "db", shared_db)

    calls = {"authority": 0, "add_hub": 0}

    async def fake_user(_authorization):
        return wallet

    async def fake_current_authority(mint_value, wallet_value):
        assert mint_value == mint
        assert wallet_value == wallet
        calls["authority"] += 1

    async def fake_add_hub(mint_value):
        calls["add_hub"] += 1
        return {"address": mint_value, "symbol": "TST"}, False

    monkeypatch.setattr(hubs, "user", fake_user)
    monkeypatch.setattr(hubs, "current_authority", fake_current_authority)
    monkeypatch.setattr(hubs, "add_hub", fake_add_hub)

    profile = agents.AgentProfile(**valid_agent_profile("Authority Agent"))
    same = agents.AgentProfile(**valid_agent_profile("Authority Agent"))
    different = agents.AgentProfile(**valid_agent_profile("Different Agent"))

    first = run(hubs.add(hubs.AddToken(address=mint, agent=profile), authorization="Bearer test"))
    second = run(hubs.add(hubs.AddToken(address=mint, agent=same), authorization="Bearer test"))

    assert first["agent_configured"] is True
    assert second["agent_configured"] is True
    assert shared_db.agents.docs[0]["profile"]["name"] == "Authority Agent"

    with pytest.raises(HTTPException) as conflict:
        run(hubs.add(hubs.AddToken(address=mint, agent=different), authorization="Bearer test"))
    assert conflict.value.status_code == 409
    assert shared_db.agents.docs[0]["profile"]["name"] == "Authority Agent"

    no_agent = run(hubs.add(hubs.AddToken(address=mint, agent=None), authorization=""))
    assert no_agent["agent_configured"] is False
    assert shared_db.agents.docs[0]["profile"]["name"] == "Authority Agent"
    assert calls["authority"] >= 3
    assert calls["add_hub"] >= 3


def test_hubs_add_with_agent_authority_failure_blocks_write_before_add(monkeypatch):
    wallet = str(Keypair().pubkey())
    mint = str(Keypair().pubkey())
    shared_db = FakeDB(hubs_docs=[{"address": mint}], agents_docs=[])
    monkeypatch.setattr(hubs, "db", shared_db)
    monkeypatch.setattr(agents, "db", shared_db)

    calls = {"add_hub": 0}

    async def fake_user(_authorization):
        return wallet

    async def reject_authority(_mint_value, _wallet_value):
        raise HTTPException(403, "Not authority")

    async def fake_add_hub(mint_value):
        calls["add_hub"] += 1
        return {"address": mint_value, "symbol": "TST"}, False

    monkeypatch.setattr(hubs, "user", fake_user)
    monkeypatch.setattr(hubs, "current_authority", reject_authority)
    monkeypatch.setattr(hubs, "add_hub", fake_add_hub)

    with pytest.raises(HTTPException) as exc:
        run(hubs.add(hubs.AddToken(address=mint, agent=agents.AgentProfile(**valid_agent_profile())), authorization="Bearer test"))
    assert exc.value.status_code == 403
    assert calls["add_hub"] == 0
    assert shared_db.agents.docs == []


# agents public view privacy and configuration-only runtime defaults
def test_agents_public_view_excludes_private_fields_and_legacy_updated_by(monkeypatch):
    mint = str(Keypair().pubkey())
    legacy_row = {
        "token": mint,
        "profile": valid_agent_profile("Legacy Public Agent"),
        "updated_by": "wallet-legacy",
        "source": "verified-authority",
        "updated_at": "2026-02-01T00:00:00+00:00",
        "activity": [{"id": "a1", "title": "configured", "at": "2026-02-01T00:00:00+00:00", "kind": "configuration"}],
    }
    shared_db = FakeDB(hubs_docs=[{"address": mint}], agents_docs=[legacy_row])
    monkeypatch.setattr(agents, "db", shared_db)

    async def fake_get_hub(_mint):
        return {"address": mint}

    monkeypatch.setattr(agents, "get_hub", fake_get_hub)

    result = run(agents.agent(mint))
    payload = result.model_dump()

    assert payload["published"] is True
    assert payload["execution_enabled"] is False
    assert payload["profile"]["name"] == "Legacy Public Agent"
    assert "instructions" not in payload["profile"]
    assert "updated_by" not in payload


def test_agents_public_view_unconfigured_has_no_fake_defaults(monkeypatch):
    mint = str(Keypair().pubkey())
    shared_db = FakeDB(hubs_docs=[{"address": mint}], agents_docs=[])
    monkeypatch.setattr(agents, "db", shared_db)

    async def fake_get_hub(_mint):
        return {"address": mint}

    monkeypatch.setattr(agents, "get_hub", fake_get_hub)

    result = run(agents.agent(mint)).model_dump()
    assert result["profile"] is None
    assert result["model"] is None
    assert result["published"] is False
    assert result["execution_enabled"] is False
