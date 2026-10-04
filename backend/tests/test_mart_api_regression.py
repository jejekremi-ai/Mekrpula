"""Core MART API regression tests: auth, token hubs, community, listings, and orders."""

import base64
import io
import os
from typing import Dict

import base58
import pytest
import requests
from dotenv import load_dotenv
from nacl.signing import SigningKey
from PIL import Image
from pymongo import MongoClient


load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
MONGO_URL = os.environ.get("MONGO_URL", "").strip('"')
DB_NAME = os.environ.get("DB_NAME", "").strip('"')
FARTCOIN = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"

if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL must be defined in environment or frontend/.env")


@pytest.fixture
def api_client():
    session = requests.Session()
    return session


def _new_wallet() -> SigningKey:
    return SigningKey.generate()


def _wallet_address(signing_key: SigningKey) -> str:
    return base58.b58encode(bytes(signing_key.verify_key)).decode()


def _auth_token(api_client: requests.Session, signing_key: SigningKey) -> Dict[str, str]:
    wallet = _wallet_address(signing_key)
    challenge = api_client.post(f"{BASE_URL}/api/auth/challenge", json={"wallet": wallet})
    assert challenge.status_code == 200
    payload = challenge.json()
    signed = signing_key.sign(payload["message"].encode())
    verify = api_client.post(
        f"{BASE_URL}/api/auth/verify",
        json={"nonce": payload["nonce"], "signature": base58.b58encode(signed.signature).decode()},
    )
    assert verify.status_code == 200
    data = verify.json()
    assert data["wallet"] == wallet
    assert isinstance(data["token"], str) and len(data["token"]) > 20
    return data


@pytest.fixture
def auth_context(api_client):
    key = _new_wallet()
    auth = _auth_token(api_client, key)
    return {
        "key": key,
        "wallet": auth["wallet"],
        "headers": {"Authorization": f"Bearer {auth['token']}"},
    }


@pytest.fixture
def second_auth_context(api_client):
    key = _new_wallet()
    auth = _auth_token(api_client, key)
    return {
        "key": key,
        "wallet": auth["wallet"],
        "headers": {"Authorization": f"Bearer {auth['token']}"},
    }


@pytest.fixture
def third_auth_context(api_client):
    key = _new_wallet()
    auth = _auth_token(api_client, key)
    return {
        "key": key,
        "wallet": auth["wallet"],
        "headers": {"Authorization": f"Bearer {auth['token']}"},
    }


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_content():
    yield
    if MONGO_URL and DB_NAME:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        db.posts.delete_many({"text": {"$regex": r"^TEST_"}})
        db.listings.delete_many({"name": {"$regex": r"^TEST_"}})
        db.orders.delete_many({"item_name": {"$regex": r"^TEST_"}})
        client.close()


def _upload_image(api_client: requests.Session, headers: Dict[str, str]) -> str:
    image = Image.new("RGB", (32, 32), color=(12, 200, 155))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    response = api_client.post(
        f"{BASE_URL}/api/uploads",
        headers={"Authorization": headers["Authorization"]},
        files={"file": ("test.png", buf.read(), "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["url"].startswith(f"{BASE_URL}/api/images/")
    return body["url"]


# Auth + route protection
def test_health_endpoint(api_client):
    response = api_client.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["network"] == "solana-mainnet"


def test_protected_wallet_route_requires_auth(api_client):
    response = api_client.get(f"{BASE_URL}/api/wallet")
    assert response.status_code == 401
    assert "sign in" in response.json()["detail"].lower()


def test_auth_rejects_invalid_signature_identity_spoof(api_client):
    wallet_a = _new_wallet()
    wallet_b = _new_wallet()
    challenge = api_client.post(
        f"{BASE_URL}/api/auth/challenge", json={"wallet": _wallet_address(wallet_a)}
    )
    assert challenge.status_code == 200
    payload = challenge.json()
    forged = wallet_b.sign(payload["message"].encode()).signature
    verify = api_client.post(
        f"{BASE_URL}/api/auth/verify",
        json={"nonce": payload["nonce"], "signature": base58.b58encode(forged).decode()},
    )
    assert verify.status_code == 401
    assert "could not be verified" in verify.json()["detail"].lower()


def test_auth_rejects_replay_nonce(api_client):
    key = _new_wallet()
    wallet = _wallet_address(key)
    challenge = api_client.post(f"{BASE_URL}/api/auth/challenge", json={"wallet": wallet})
    assert challenge.status_code == 200
    payload = challenge.json()
    sig = base58.b58encode(key.sign(payload["message"].encode()).signature).decode()
    first = api_client.post(f"{BASE_URL}/api/auth/verify", json={"nonce": payload["nonce"], "signature": sig})
    second = api_client.post(f"{BASE_URL}/api/auth/verify", json={"nonce": payload["nonce"], "signature": sig})
    assert first.status_code == 200
    assert second.status_code == 401
    assert "expired" in second.json()["detail"].lower()


def test_auth_rejects_unknown_nonce(api_client):
    key = _new_wallet()
    fake_sig = base58.b58encode(key.sign(b"random").signature).decode()
    response = api_client.post(
        f"{BASE_URL}/api/auth/verify",
        json={"nonce": "deadbeefdeadbeef", "signature": fake_sig},
    )
    assert response.status_code == 401


# Token hubs + duplicate prevention
def test_add_token_invalid_input_rejected(api_client):
    response = api_client.post(f"{BASE_URL}/api/tokens", json={"address": "not-a-solana-address"})
    assert response.status_code == 422
    assert "valid solana address" in response.json()["detail"].lower()


def test_add_token_duplicate_opens_same_hub(api_client):
    first = api_client.post(f"{BASE_URL}/api/tokens", json={"address": FARTCOIN})
    second = api_client.post(f"{BASE_URL}/api/tokens", json={"address": FARTCOIN})
    assert first.status_code == 200
    assert second.status_code == 200
    first_token = first.json()["token"]
    second_token = second.json()["token"]
    assert first_token["address"] == FARTCOIN
    assert second_token["address"] == FARTCOIN
    assert second.json()["created"] is False


# Upload + community isolation
def test_upload_rejects_invalid_mime(auth_context, api_client):
    response = api_client.post(
        f"{BASE_URL}/api/uploads",
        headers={"Authorization": auth_context["headers"]["Authorization"]},
        files={"file": ("bad.txt", b"not-an-image", "text/plain")},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    text = detail if isinstance(detail, str) else str(detail)
    assert "valid png" in text.lower()


def test_upload_rejects_oversize_payload(auth_context, api_client):
    large = b"x" * 5_100_100
    response = api_client.post(
        f"{BASE_URL}/api/uploads",
        headers={"Authorization": auth_context["headers"]["Authorization"]},
        files={"file": ("huge.jpg", large, "image/jpeg")},
    )
    assert response.status_code == 413


def test_community_post_like_reply_flow(auth_context, second_auth_context, api_client):
    create = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/posts",
        headers=auth_context["headers"],
        json={"text": "TEST_post_content_wallet_a", "image": ""},
    )
    assert create.status_code == 200
    post = create.json()
    assert post["author"] == auth_context["wallet"]
    assert post["token"] == FARTCOIN
    post_id = post["id"]

    like_once = api_client.post(f"{BASE_URL}/api/posts/{post_id}/like", headers=second_auth_context["headers"])
    assert like_once.status_code == 200
    assert len(like_once.json()["likes"]) == 1

    like_twice = api_client.post(f"{BASE_URL}/api/posts/{post_id}/like", headers=second_auth_context["headers"])
    assert like_twice.status_code == 200
    assert len(like_twice.json()["likes"]) == 0

    reply = api_client.post(
        f"{BASE_URL}/api/posts/{post_id}/replies",
        headers=second_auth_context["headers"],
        json={"text": "TEST_reply_from_wallet_b", "image": ""},
    )
    assert reply.status_code == 200
    assert any(r["text"] == "TEST_reply_from_wallet_b" for r in reply.json()["replies"])

    posts = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/posts")
    assert posts.status_code == 200
    listed = posts.json()
    assert any(p["id"] == post_id and p["text"] == "TEST_post_content_wallet_a" for p in listed)


def test_community_blank_post_validation(auth_context, api_client):
    response = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/posts",
        headers=auth_context["headers"],
        json={"text": "   ", "image": ""},
    )
    assert response.status_code == 422
    assert "write something" in response.json()["detail"].lower()


def test_unclaimed_token_profile_edit_denied(auth_context, api_client):
    response = api_client.patch(
        f"{BASE_URL}/api/tokens/{FARTCOIN}",
        headers=auth_context["headers"],
        json={"description": "TEST unauthorized edit", "banner": ""},
    )
    assert response.status_code == 403
    assert "verified token authority" in response.json()["detail"].lower()


def test_unclaimed_token_event_create_denied(auth_context, api_client):
    response = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/events",
        headers=auth_context["headers"],
        json={
            "title": "TEST unauthorized event",
            "image": "",
            "type": "Other",
            "description": "TEST should fail because wallet is not verified authority.",
            "status": "upcoming",
        },
    )
    assert response.status_code == 403
    assert "claim this token" in response.json()["detail"].lower()


# Listings + owner constraints
def test_listing_price_validation_rejects_bad_values(auth_context, api_client):
    image_url = _upload_image(api_client, auth_context["headers"])
    response = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/listings",
        headers=auth_context["headers"],
        json={
            "name": "TEST_bad_price_listing",
            "image": image_url,
            "type": "Artwork",
            "description": "TEST_Invalid price should be rejected.",
            "price": "0",
            "quantity": 1,
        },
    )
    assert response.status_code == 422
    assert "positive price" in response.json()["detail"].lower()


def test_listing_sets_seller_and_owner_only_delete(auth_context, second_auth_context, api_client):
    image_url = _upload_image(api_client, auth_context["headers"])
    create = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/listings",
        headers=auth_context["headers"],
        json={
            "name": "TEST_owner_delete_listing",
            "image": image_url,
            "type": "Poster",
            "description": "TEST_listing_owner_controls_delete_and_seller_wallet.",
            "price": "1",
            "quantity": 2,
        },
    )
    assert create.status_code == 200
    listing = create.json()
    assert listing["seller"] == auth_context["wallet"]
    listing_id = listing["id"]

    non_owner_delete = api_client.delete(
        f"{BASE_URL}/api/listings/{listing_id}", headers=second_auth_context["headers"]
    )
    assert non_owner_delete.status_code == 404

    owner_delete = api_client.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=auth_context["headers"])
    assert owner_delete.status_code == 200
    assert owner_delete.json()["ok"] is True


# Orders + transaction guarding (without sending real tx)
def test_order_blocks_self_purchase(auth_context, api_client):
    image_url = _upload_image(api_client, auth_context["headers"])
    create = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/listings",
        headers=auth_context["headers"],
        json={
            "name": "TEST_self_purchase_blocked",
            "image": image_url,
            "type": "Artwork",
            "description": "TEST_listing_for_self_purchase_guard.",
            "price": "1",
            "quantity": 1,
        },
    )
    assert create.status_code == 200
    listing_id = create.json()["id"]

    order = api_client.post(
        f"{BASE_URL}/api/orders",
        headers=auth_context["headers"],
        json={"listing_id": listing_id, "delivery": "TEST digital delivery"},
    )
    assert order.status_code == 400
    assert "cannot purchase your own" in order.json()["detail"].lower()


def test_order_reservation_prevents_oversell(auth_context, second_auth_context, third_auth_context, api_client):
    image_url = _upload_image(api_client, auth_context["headers"])
    create = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/listings",
        headers=auth_context["headers"],
        json={
            "name": "TEST_oversell_guard",
            "image": image_url,
            "type": "Sticker",
            "description": "TEST_listing_for_quantity_reservation_guard.",
            "price": "1",
            "quantity": 1,
        },
    )
    assert create.status_code == 200
    listing_id = create.json()["id"]

    first_order = api_client.post(
        f"{BASE_URL}/api/orders",
        headers=second_auth_context["headers"],
        json={"listing_id": listing_id, "delivery": "TEST buyer one delivery"},
    )
    assert first_order.status_code == 200
    order_doc = first_order.json()
    assert order_doc["status"] == "pending"
    assert isinstance(order_doc["transaction"], str) and len(order_doc["transaction"]) > 100
    assert isinstance(order_doc["message_hash"], str) and len(order_doc["message_hash"]) == 64

    second_order = api_client.post(
        f"{BASE_URL}/api/orders",
        headers=third_auth_context["headers"],
        json={"listing_id": listing_id, "delivery": "TEST buyer two delivery"},
    )
    assert second_order.status_code == 409
    assert "reserved" in second_order.json()["detail"].lower() or "sold out" in second_order.json()["detail"].lower()


def test_order_submit_conflicting_signature_rejected(auth_context, second_auth_context, api_client):
    image_url = _upload_image(api_client, auth_context["headers"])
    create = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/listings",
        headers=auth_context["headers"],
        json={
            "name": "TEST_signature_conflict",
            "image": image_url,
            "type": "Hoodie",
            "description": "TEST_signature_conflict_order_flow.",
            "price": "1",
            "quantity": 1,
        },
    )
    assert create.status_code == 200

    order = api_client.post(
        f"{BASE_URL}/api/orders",
        headers=second_auth_context["headers"],
        json={"listing_id": create.json()["id"], "delivery": "TEST signature delivery"},
    )
    assert order.status_code == 200
    order_id = order.json()["id"]

    sig_one = base58.b58encode(os.urandom(64)).decode()
    sig_two = base58.b58encode(os.urandom(64)).decode()
    first = api_client.post(
        f"{BASE_URL}/api/orders/{order_id}/submit",
        headers=second_auth_context["headers"],
        json={"signature": sig_one},
    )
    assert first.status_code == 200
    assert first.json()["ok"] is True

    second = api_client.post(
        f"{BASE_URL}/api/orders/{order_id}/submit",
        headers=second_auth_context["headers"],
        json={"signature": sig_two},
    )
    assert second.status_code == 409
    assert "already attached" in second.json()["detail"].lower()


def test_send_transaction_rejects_wrong_payload(auth_context, second_auth_context, api_client):
    image_url = _upload_image(api_client, auth_context["headers"])
    create = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/listings",
        headers=auth_context["headers"],
        json={
            "name": "TEST_wrong_tx_payload",
            "image": image_url,
            "type": "Poster",
            "description": "TEST_wrong_signed_transaction_validation.",
            "price": "1",
            "quantity": 1,
        },
    )
    assert create.status_code == 200

    order = api_client.post(
        f"{BASE_URL}/api/orders",
        headers=second_auth_context["headers"],
        json={"listing_id": create.json()["id"], "delivery": "TEST malformed tx"},
    )
    assert order.status_code == 200
    order_id = order.json()["id"]

    bad_payload = base64.b64encode(b"not-a-transaction").decode()
    send = api_client.post(
        f"{BASE_URL}/api/transactions/send",
        headers=second_auth_context["headers"],
        json={"kind": "order", "id": order_id, "transaction": bad_payload},
    )
    assert send.status_code == 422
    assert "does not match" in send.json()["detail"].lower()


def test_order_cancel_guard_before_expiry(auth_context, second_auth_context, api_client):
    image_url = _upload_image(api_client, auth_context["headers"])
    create = api_client.post(
        f"{BASE_URL}/api/tokens/{FARTCOIN}/listings",
        headers=auth_context["headers"],
        json={
            "name": "TEST_cancel_guard",
            "image": image_url,
            "type": "Sticker",
            "description": "TEST_cannot_cancel_pending_order_before_expiry.",
            "price": "1",
            "quantity": 1,
        },
    )
    assert create.status_code == 200

    order = api_client.post(
        f"{BASE_URL}/api/orders",
        headers=second_auth_context["headers"],
        json={"listing_id": create.json()["id"], "delivery": "TEST cancel guard"},
    )
    assert order.status_code == 200
    order_id = order.json()["id"]

    cancel = api_client.post(f"{BASE_URL}/api/orders/{order_id}/cancel", headers=second_auth_context["headers"])
    assert cancel.status_code == 409
    assert "wait" in cancel.json()["detail"].lower()
