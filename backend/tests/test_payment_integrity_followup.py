"""Isolated fixture-controlled tests for payment integrity, launch confirm checks, and authority paths."""

import asyncio
import base64
import hashlib
from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction

import sys

sys.path.append("/app/backend")
import chain  # noqa: E402
import hubs  # noqa: E402
import launch  # noqa: E402
import market  # noqa: E402
import social  # noqa: E402


def run(coro):
    return asyncio.run(coro)


def _legacy_signed_tx(lamports: int = 1):
    payer = Keypair()
    recipient = Keypair().pubkey()
    ix = transfer(TransferParams(from_pubkey=payer.pubkey(), to_pubkey=recipient, lamports=lamports))
    blockhash = Hash.default()
    message = Message.new_with_blockhash([ix], payer.pubkey(), blockhash)
    tx = Transaction.new_signed_with_payer([ix], payer.pubkey(), [payer], blockhash)
    return message, tx


@dataclass
class FakeUpdateResult:
    modified_count: int
    matched_count: int


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs
        self._limit = None

    def limit(self, n):
        self._limit = n
        return self

    async def to_list(self, n):
        docs = list(self._docs)
        cap = self._limit if self._limit is not None else n
        return [dict(x) for x in docs[:cap]]


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def _match(self, doc, query):
        for key, expected in query.items():
            if isinstance(expected, dict):
                if "$gt" in expected:
                    if not (doc.get(key, 0) > expected["$gt"]):
                        return False
                else:
                    return False
            elif doc.get(key) != expected:
                return False
        return True

    def _project(self, doc, projection):
        if not projection:
            return dict(doc)
        out = dict(doc)
        if projection.get("_id") == 0:
            out.pop("_id", None)
        return out

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._match(doc, query):
                return self._project(doc, projection)
        return None

    def find(self, query, projection=None):
        matched = [self._project(x, projection) for x in self.docs if self._match(x, query)]
        return FakeCursor(matched)

    async def update_one(self, query, update):
        for i, doc in enumerate(self.docs):
            if not self._match(doc, query):
                continue
            changed = False
            if "$set" in update:
                for k, v in update["$set"].items():
                    if doc.get(k) != v:
                        doc[k] = v
                        changed = True
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    doc[k] = doc.get(k, 0) + v
                    changed = True
            self.docs[i] = doc
            return FakeUpdateResult(modified_count=1 if changed else 0, matched_count=1)
        return FakeUpdateResult(modified_count=0, matched_count=0)


class FakeDB:
    def __init__(self, orders=None, listings=None, launches=None, hubs_docs=None, events=None):
        self.orders = FakeCollection(orders)
        self.listings = FakeCollection(listings)
        self.launches = FakeCollection(launches)
        self.hubs = FakeCollection(hubs_docs)
        self.events = FakeCollection(events)


# payment helper integrity tests
def test_exact_payment_accepts_legacy_signed_transaction_message():
    message, tx = _legacy_signed_tx(1)
    result = {"meta": {"err": None}, "transaction": [base64.b64encode(bytes(tx)).decode()]}
    assert market.exact_payment(result, hashlib.sha256(bytes(message)).hexdigest()) is True


@pytest.mark.parametrize("lamports", [2, 3, 4])
def test_exact_payment_rejects_wrong_recipient_or_mint_or_amount_by_hash_mismatch(lamports):
    message_expected, _ = _legacy_signed_tx(1)
    _, tx_wrong = _legacy_signed_tx(lamports)
    result = {"meta": {"err": None}, "transaction": [base64.b64encode(bytes(tx_wrong)).decode()]}
    assert market.exact_payment(result, hashlib.sha256(bytes(message_expected)).hexdigest()) is False


def test_exact_payment_rejects_wrong_message_and_malformed_payload_and_failed_meta():
    message, tx = _legacy_signed_tx(1)
    expected = hashlib.sha256(bytes(message)).hexdigest()

    malformed = {"meta": {"err": None}, "transaction": ["not-base64"]}
    assert market.exact_payment(malformed, expected) is False

    wrong_message = {"meta": {"err": None}, "transaction": [base64.b64encode(bytes(tx)).decode()]}
    assert market.exact_payment(wrong_message, "deadbeef" * 8) is False

    failed_meta = {"meta": {"err": {"InstructionError": [0, "Custom"]}}, "transaction": [base64.b64encode(bytes(tx)).decode()]}
    assert market.exact_payment(failed_meta, expected) is False


# reservation reconciliation tests
def test_settle_expired_reservations_finalized_exact_payment_marks_paid(monkeypatch):
    message, tx = _legacy_signed_tx(1)
    fake_db = FakeDB(
        orders=[
            {
                "id": "o1",
                "token": "MINT",
                "listing_id": "l1",
                "status": "pending",
                "last_valid_height": 10,
                "signature": "sig1",
                "message_hash": hashlib.sha256(bytes(message)).hexdigest(),
            }
        ],
        listings=[{"id": "l1", "quantity": 0}],
    )

    async def fake_rpc(method, params):
        if method == "getBlockHeight":
            return 99
        if method == "getSignatureStatuses":
            return {"value": [{"err": None, "confirmationStatus": "finalized"}]}
        if method == "getTransaction":
            return {"meta": {"err": None}, "transaction": [base64.b64encode(bytes(tx)).decode()]}
        raise AssertionError(f"Unexpected rpc method {method}")

    monkeypatch.setattr(market, "db", fake_db)
    monkeypatch.setattr(market, "rpc", fake_rpc)
    run(market.settle_expired_reservations("MINT"))

    assert fake_db.orders.docs[0]["status"] == "paid"
    assert fake_db.listings.docs[0]["quantity"] == 0


def test_settle_expired_reservations_pending_confirmation_stays_reserved(monkeypatch):
    fake_db = FakeDB(
        orders=[
            {
                "id": "o2",
                "token": "MINT",
                "listing_id": "l2",
                "status": "pending",
                "last_valid_height": 10,
                "signature": "sig2",
                "message_hash": "x" * 64,
            }
        ],
        listings=[{"id": "l2", "quantity": 0}],
    )

    async def fake_rpc(method, params):
        if method == "getBlockHeight":
            return 99
        if method == "getSignatureStatuses":
            return {"value": [{"err": None, "confirmationStatus": "confirmed"}]}
        raise AssertionError(f"Unexpected rpc method {method}")

    monkeypatch.setattr(market, "db", fake_db)
    monkeypatch.setattr(market, "rpc", fake_rpc)
    run(market.settle_expired_reservations("MINT"))

    assert fake_db.orders.docs[0]["status"] == "pending"
    assert fake_db.listings.docs[0]["quantity"] == 0


def test_settle_expired_reservations_unsigned_and_failed_release_stock_once(monkeypatch):
    fake_db = FakeDB(
        orders=[
            {
                "id": "o3",
                "token": "MINT",
                "listing_id": "l3",
                "status": "pending",
                "last_valid_height": 10,
            },
            {
                "id": "o4",
                "token": "MINT",
                "listing_id": "l4",
                "status": "pending",
                "last_valid_height": 10,
                "signature": "sig4",
                "message_hash": "z" * 64,
            },
        ],
        listings=[{"id": "l3", "quantity": 0}, {"id": "l4", "quantity": 0}],
    )

    async def fake_rpc(method, params):
        if method == "getBlockHeight":
            return 99
        if method == "getSignatureStatuses":
            return {"value": [{"err": {"InstructionError": [0, "Custom"]}, "confirmationStatus": "finalized"}]}
        raise AssertionError(f"Unexpected rpc method {method}")

    monkeypatch.setattr(market, "db", fake_db)
    monkeypatch.setattr(market, "rpc", fake_rpc)

    run(market.settle_expired_reservations("MINT"))
    run(market.settle_expired_reservations("MINT"))

    assert fake_db.orders.docs[0]["status"] == "cancelled"
    assert fake_db.orders.docs[1]["status"] == "cancelled"
    assert fake_db.listings.docs[0]["quantity"] == 1
    assert fake_db.listings.docs[1]["quantity"] == 1


# verify payment endpoint idempotence + mismatch rejection
def test_verify_payment_idempotent_after_finalize(monkeypatch):
    message, tx = _legacy_signed_tx(1)
    expected = hashlib.sha256(bytes(message)).hexdigest()
    fake_db = FakeDB(
        orders=[
            {
                "id": "order-idem",
                "buyer": "buyer1",
                "status": "pending",
                "signature": "sig-idem",
                "message_hash": expected,
            }
        ]
    )

    async def fake_rpc(method, params):
        assert method == "getTransaction"
        return {"meta": {"err": None}, "transaction": [base64.b64encode(bytes(tx)).decode()]}

    monkeypatch.setattr(market, "db", fake_db)
    monkeypatch.setattr(market, "rpc", fake_rpc)

    first = run(market.verify_payment("order-idem", wallet="buyer1"))
    second = run(market.verify_payment("order-idem", wallet="buyer1"))

    assert first["status"] == "paid"
    assert second["status"] == "paid"


def test_verify_payment_rejects_finalized_mismatch(monkeypatch):
    _, tx = _legacy_signed_tx(1)
    fake_db = FakeDB(
        orders=[
            {
                "id": "order-bad",
                "buyer": "buyer2",
                "status": "pending",
                "signature": "sig-bad",
                "message_hash": "0" * 64,
            }
        ]
    )

    async def fake_rpc(method, params):
        return {"meta": {"err": None}, "transaction": [base64.b64encode(bytes(tx)).decode()]}

    monkeypatch.setattr(market, "db", fake_db)
    monkeypatch.setattr(market, "rpc", fake_rpc)

    with pytest.raises(HTTPException) as exc:
        run(market.verify_payment("order-bad", wallet="buyer2"))
    assert exc.value.status_code == 422


# launch confirmation integrity (isolated monkeypatched rpc)
def test_launch_confirm_requires_exact_serialized_message_and_creates_hub(monkeypatch):
    message, tx = _legacy_signed_tx(1)
    expected = hashlib.sha256(bytes(message)).hexdigest()
    fake_db = FakeDB(
        launches=[
            {
                "id": "launch-ok",
                "wallet": "w1",
                "mint": "mint1",
                "signature": "sig-l",
                "metadata": {"description": "d", "image": "i", "banner": "b"},
                "message_hash": expected,
                "status": "prepared",
            }
        ],
        hubs_docs=[{"address": "mint1"}],
    )
    calls = {"add_hub": 0}

    async def fake_rpc(method, params):
        assert method == "getTransaction"
        return {"meta": {"err": None}, "transaction": [base64.b64encode(bytes(tx)).decode()]}

    async def fake_add_hub(mint):
        calls["add_hub"] += 1
        return {"address": mint}, True

    monkeypatch.setattr(launch, "db", fake_db)
    monkeypatch.setattr(launch, "rpc", fake_rpc)
    monkeypatch.setattr(launch, "add_hub", fake_add_hub)

    result = run(launch.confirm("launch-ok", wallet="w1"))
    assert result["address"] == "mint1"
    assert calls["add_hub"] == 1
    assert fake_db.launches.docs[0]["status"] == "confirmed"


def test_launch_confirm_failed_or_unfinalized_never_creates_hub(monkeypatch):
    message, _ = _legacy_signed_tx(1)
    expected = hashlib.sha256(bytes(message)).hexdigest()
    base_launch = {
        "id": "launch-z",
        "wallet": "wz",
        "mint": "mint-z",
        "signature": "sig-z",
        "metadata": {"description": "d", "image": "i", "banner": "b"},
        "message_hash": expected,
        "status": "prepared",
    }

    for mode in ["unfinalized", "failed"]:
        fake_db = FakeDB(launches=[dict(base_launch)], hubs_docs=[{"address": "mint-z"}])
        calls = {"add_hub": 0}

        async def fake_add_hub(mint):
            calls["add_hub"] += 1
            return {"address": mint}, True

        async def fake_rpc(method, params):
            if mode == "unfinalized":
                return None
            return {"meta": {"err": {"InstructionError": [0, "Custom"]}}, "transaction": [""]}

        monkeypatch.setattr(launch, "db", fake_db)
        monkeypatch.setattr(launch, "rpc", fake_rpc)
        monkeypatch.setattr(launch, "add_hub", fake_add_hub)

        with pytest.raises(HTTPException) as exc:
            run(launch.confirm("launch-z", wallet="wz"))
        assert exc.value.status_code == 409
        assert calls["add_hub"] == 0


def test_launch_confirm_rejects_finalized_mismatched_message(monkeypatch):
    _, tx = _legacy_signed_tx(1)
    fake_db = FakeDB(
        launches=[
            {
                "id": "launch-mis",
                "wallet": "w2",
                "mint": "mint2",
                "signature": "sig2",
                "metadata": {"description": "d", "image": "i", "banner": "b"},
                "message_hash": "f" * 64,
                "status": "prepared",
            }
        ]
    )
    calls = {"add_hub": 0}

    async def fake_rpc(method, params):
        return {"meta": {"err": None}, "transaction": [base64.b64encode(bytes(tx)).decode()]}

    async def fake_add_hub(mint):
        calls["add_hub"] += 1
        return {"address": mint}, True

    monkeypatch.setattr(launch, "db", fake_db)
    monkeypatch.setattr(launch, "rpc", fake_rpc)
    monkeypatch.setattr(launch, "add_hub", fake_add_hub)

    with pytest.raises(HTTPException) as exc:
        run(launch.confirm("launch-mis", wallet="w2"))
    assert exc.value.status_code == 422
    assert calls["add_hub"] == 0


# authority checks + isolated claim/event status update
def test_current_authority_match_mismatch_and_empty_metadata(monkeypatch):
    async def md_match(_mint):
        return {"update_authority": "wallet-ok"}

    monkeypatch.setattr(chain, "metadata", md_match)
    run(chain.current_authority("mint", "wallet-ok"))

    async def md_mismatch(_mint):
        return {"update_authority": "wallet-other"}

    monkeypatch.setattr(chain, "metadata", md_mismatch)
    with pytest.raises(HTTPException) as mismatch:
        run(chain.current_authority("mint", "wallet-ok"))
    assert mismatch.value.status_code == 403

    async def md_empty(_mint):
        return {}

    monkeypatch.setattr(chain, "metadata", md_empty)
    with pytest.raises(HTTPException) as empty:
        run(chain.current_authority("mint", "wallet-ok"))
    assert empty.value.status_code == 403


def test_claim_and_event_status_update_success_paths_with_isolated_records(monkeypatch):
    fake_hubs_db = FakeDB(hubs_docs=[{"address": "mint-claim", "claimed_by": None}])
    fake_social_db = FakeDB(events=[{"id": "evt1", "token": "mint-claim", "status": "upcoming"}])

    authority_calls = {"count": 0}

    async def fake_current_authority(_mint, _wallet):
        authority_calls["count"] += 1

    monkeypatch.setattr(hubs, "db", fake_hubs_db)
    monkeypatch.setattr(hubs, "current_authority", fake_current_authority)

    claimed = run(hubs.claim("mint-claim", wallet="wallet-ok"))
    assert claimed["claimed_by"] == "wallet-ok"

    async def fake_get_hub(_mint):
        return {"address": "mint-claim", "claimed_by": "wallet-ok"}

    monkeypatch.setattr(social, "db", fake_social_db)
    monkeypatch.setattr(social, "get_hub", fake_get_hub)
    monkeypatch.setattr(social, "current_authority", fake_current_authority)

    updated = run(social.update_event("evt1", social.EventStatus(status="live"), wallet="wallet-ok"))
    assert updated["status"] == "live"
    assert authority_calls["count"] >= 2
