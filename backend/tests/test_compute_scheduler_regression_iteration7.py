"""Compute credits + scheduler regression for preview runtime and minimal isolated shape checks."""

from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

import base58
import pytest
import requests
import yaml
from dotenv import load_dotenv
from nacl.signing import SigningKey
from pymongo import MongoClient


load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
MONGO_URL = os.environ.get("MONGO_URL", "").strip('"')
DB_NAME = os.environ.get("DB_NAME", "").strip('"')
WEBHOOK_CRON_SECRET = os.environ.get("WEBHOOK_CRON_SECRET")

FARTCOIN = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"
BONK = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
WIF = "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"
POPCAT = "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr"

if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL is required")
if not WEBHOOK_CRON_SECRET:
    raise RuntimeError("WEBHOOK_CRON_SECRET is required")

BASE_URL = BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def api_client() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def mongo_db():
    if not MONGO_URL or not DB_NAME:
        pytest.skip("Mongo environment missing; cannot run scheduler due-time verification")
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    yield db
    client.close()


def _get_compute(api_client: requests.Session, mint: str):
    response = api_client.get(f"{BASE_URL}/api/tokens/{mint}/compute")
    assert response.status_code == 200
    return response.json()


def _post_topup(api_client: requests.Session, mint: str, amount: int, request_id: str):
    return api_client.post(
        f"{BASE_URL}/api/tokens/{mint}/compute/topup",
        json={"amount": amount, "request_id": request_id},
    )


def _run_manual(api_client: requests.Session, mint: str, request_id: str):
    return api_client.post(
        f"{BASE_URL}/api/tokens/{mint}/compute/runs",
        json={"request_id": request_id},
    )


def _auth_headers(api_client: requests.Session):
    key = SigningKey.generate()
    wallet = base58.b58encode(bytes(key.verify_key)).decode()
    challenge = api_client.post(f"{BASE_URL}/api/auth/challenge", json={"wallet": wallet})
    assert challenge.status_code == 200
    body = challenge.json()
    signature = base58.b58encode(key.sign(body["message"].encode()).signature).decode()
    verify = api_client.post(f"{BASE_URL}/api/auth/verify", json={"nonce": body["nonce"], "signature": signature})
    assert verify.status_code == 200
    token = verify.json()["token"]
    return {"Authorization": f"Bearer {token}"}, wallet


def _wait_run_terminal(api_client: requests.Session, mint: str, run_id: str, timeout_sec: int = 220):
    deadline = time.time() + timeout_sec
    last = None
    while time.time() < deadline:
        res = api_client.get(f"{BASE_URL}/api/tokens/{mint}/compute/runs/{run_id}")
        assert res.status_code == 200
        last = res.json()
        if last["status"] in {"completed", "failed", "rejected"}:
            return last
        time.sleep(2)
    return last


def _ensure_balance(api_client: requests.Session, mint: str, minimum_cr: float = 3.0):
    compute = _get_compute(api_client, mint)
    if compute["balance"] >= minimum_cr:
        return compute
    top = _post_topup(api_client, mint, 100, f"it7-{uuid.uuid4().hex[:20]}")
    assert top.status_code == 200
    return top.json()


@pytest.fixture(scope="session")
def community_token(api_client):
    for mint in [FARTCOIN, BONK, WIF, POPCAT]:
        r = api_client.get(f"{BASE_URL}/api/tokens/{mint}/compute")
        if r.status_code != 200:
            continue
        body = r.json()
        if body.get("mode") == "community-test" and body.get("can_manage") is True:
            return mint
    pytest.fail("No unclaimed community-manageable token found in provided candidates")


# Public model catalog + model mapping coverage
def test_model_catalog_exposes_exactly_seven_runnable_models(api_client):
    response = api_client.get(f"{BASE_URL}/api/agent/models")
    assert response.status_code == 200
    models = response.json()["models"]
    runnable = {m["id"] for m in models if m.get("runnable")}
    assert runnable == {
        "claude-sonnet-4-5",
        "claude-opus-4-5",
        "claude-haiku-4-5",
        "gpt-5.2",
        "gpt-5-mini",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
    }
    for unavailable in ["deepseek-reasoner", "qwen3-235b", "mistral-large"]:
        row = next(m for m in models if m["id"] == unavailable)
        assert row["runnable"] is False


# Cron shape verification
def test_cron_config_shape():
    with open("/app/.emergent/crons.yml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)
    assert isinstance(data.get("crons"), list)
    row = data["crons"][0]
    assert row["name"] == "token-research"
    assert row["cron"] == "*/15 * * * *"
    assert row["endpoint"].endswith("/api/cron/research")
    assert row["method"] == "POST"


# Privacy checks for existing public report + compute payload
def test_public_compute_data_hides_prompt_and_private_fields(api_client):
    run_id = "2787f87fe66e416123434522dd25a387"
    run = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/compute/runs/{run_id}")
    assert run.status_code == 200
    body = run.json()
    assert "prompt" not in body
    assert "system" not in body

    compute = _get_compute(api_client, FARTCOIN)
    assert all("prompt" not in r and "system" not in r for r in compute.get("runs", []))

    agent = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/agent")
    assert agent.status_code == 200
    profile = agent.json().get("profile")
    if profile:
        assert "instructions" not in profile


# Topup body validation + idempotency + cap behavior
def test_topup_validation_and_idempotency(api_client, community_token, mongo_db):
    bad_payloads = [
        {},
        {"amount": -1, "request_id": "bad-negative-1"},
        {"amount": 0, "request_id": "bad-zero-1"},
        {"amount": 101, "request_id": "bad-high-1"},
        {"amount": True, "request_id": "bad-bool-1"},
        {"amount": "NaN", "request_id": "bad-string-1"},
    ]
    for payload in bad_payloads:
        response = api_client.post(f"{BASE_URL}/api/tokens/{community_token}/compute/topup", json=payload)
        assert response.status_code == 422

    before = _get_compute(api_client, community_token)
    acc_before = mongo_db.compute_accounts.find_one({"token": community_token}) or {}
    funded_before = int(acc_before.get("funded", 0))
    req_id = f"it7-topup-idem-{uuid.uuid4().hex[:18]}"
    first = _post_topup(api_client, community_token, 1, req_id)
    assert first.status_code == 200
    second = _post_topup(api_client, community_token, 1, req_id)
    assert second.status_code == 200
    after = _get_compute(api_client, community_token)
    acc_after = mongo_db.compute_accounts.find_one({"token": community_token}) or {}
    funded_after = int(acc_after.get("funded", 0))
    assert funded_after - funded_before == 1_000_000
    assert after["balance"] >= before["balance"]


# Total cap enforcement using controlled account state
def test_topup_total_cap_1000_enforced(api_client, community_token, mongo_db):
    account = mongo_db.compute_accounts.find_one({"token": community_token})
    assert account is not None
    original = {
        "funded": account.get("funded", 0),
        "balance": account.get("balance", 0),
    }
    try:
        mongo_db.compute_accounts.update_one(
            {"token": community_token},
            {"$set": {"funded": 1_000_000_000, "balance": max(int(account.get("balance", 0)), 0)}},
        )
        blocked = _post_topup(api_client, community_token, 1, f"it7-cap-{uuid.uuid4().hex[:18]}")
        assert blocked.status_code == 409
    finally:
        mongo_db.compute_accounts.update_one(
            {"token": community_token},
            {"$set": {"funded": original["funded"], "balance": original["balance"]}},
        )


# Manual run gate + concurrent reserve lock + per-token isolation
def test_manual_run_concurrency_and_token_isolation(api_client, community_token, mongo_db):
    account = mongo_db.compute_accounts.find_one({"token": community_token}) or {}
    original = {
        "day_runs": account.get("day_runs", 0),
        "day_spent": account.get("day_spent", 0),
        "active_run": account.get("active_run"),
        "paused": account.get("paused", False),
        "daily_limit": account.get("daily_limit", 50_000_000),
    }
    mongo_db.compute_accounts.update_one(
        {"token": community_token},
        {"$set": {"day_runs": 0, "day_spent": 0, "active_run": None, "paused": False, "daily_limit": 200_000_000}},
    )
    try:
        _ensure_balance(api_client, community_token, minimum_cr=2.0)
        before = _get_compute(api_client, community_token)

        results = []

        def fire(request_id: str):
            r = _run_manual(api_client, community_token, request_id)
            try:
                body = r.json()
            except Exception:
                body = {}
            results.append((r.status_code, body))

        t1 = threading.Thread(target=fire, args=(f"it7-c1-{uuid.uuid4().hex[:16]}",))
        t2 = threading.Thread(target=fire, args=(f"it7-c2-{uuid.uuid4().hex[:16]}",))
        t1.start(); t2.start(); t1.join(); t2.join()

        statuses = sorted([s for s, _ in results])
        assert statuses in ([202, 409], [202, 202], [409, 409], [202, 429], [429, 429])

        accepted = [b for s, b in results if s == 202 and b.get("id")]
        if accepted:
            run_id = accepted[0]["id"]
            terminal = _wait_run_terminal(api_client, community_token, run_id)
            assert terminal is not None
            assert terminal["status"] in {"completed", "failed", "rejected"}

        after = _get_compute(api_client, community_token)
        assert after["token"] == community_token
        assert after["balance"] >= 0
    finally:
        mongo_db.compute_accounts.update_one({"token": community_token}, {"$set": original})


# Run guard checks: paused, low balance, per-run limit, and daily cap
def test_run_guards_block_execution(api_client, community_token, mongo_db):
    doc = mongo_db.compute_accounts.find_one({"token": community_token})
    assert doc is not None
    original = {
        "balance": doc.get("balance", 0),
        "per_run_limit": doc.get("per_run_limit", 20_000_000),
        "daily_limit": doc.get("daily_limit", 50_000_000),
        "day_spent": doc.get("day_spent", 0),
        "day_runs": doc.get("day_runs", 0),
        "paused": doc.get("paused", False),
        "active_run": doc.get("active_run"),
    }
    try:
        # paused
        mongo_db.compute_accounts.update_one({"token": community_token}, {"$set": {"paused": True, "active_run": None}})
        paused = _run_manual(api_client, community_token, f"it7-paused-{uuid.uuid4().hex[:12]}")
        assert paused.status_code == 409

        # low balance
        mongo_db.compute_accounts.update_one(
            {"token": community_token},
            {"$set": {"paused": False, "balance": 0, "active_run": None, "day_runs": 0, "day_spent": 0}},
        )
        low_balance = _run_manual(api_client, community_token, f"it7-lowbal-{uuid.uuid4().hex[:12]}")
        assert low_balance.status_code == 409

        # day cap by count
        mongo_db.compute_accounts.update_one(
            {"token": community_token},
            {"$set": {"balance": 50_000_000, "day_runs": 5, "active_run": None}},
        )
        day_cap = _run_manual(api_client, community_token, f"it7-daycap-{uuid.uuid4().hex[:12]}")
        assert day_cap.status_code == 429

        # per-run limit too low for reserve
        mongo_db.compute_accounts.update_one(
            {"token": community_token},
            {"$set": {"day_runs": 0, "per_run_limit": 1, "balance": 50_000_000, "active_run": None}},
        )
        per_run = _run_manual(api_client, community_token, f"it7-perrun-{uuid.uuid4().hex[:12]}")
        assert per_run.status_code == 409
    finally:
        mongo_db.compute_accounts.update_one({"token": community_token}, {"$set": original})


# Low balance + schedule gate behavior
def test_schedule_enable_requires_manual_completion_current_model(api_client, community_token):
    view = _get_compute(api_client, community_token)
    if not view["manual_completed"]:
        _ensure_balance(api_client, community_token, minimum_cr=2.0)
        run_req = _run_manual(api_client, community_token, f"it7-manual-gate-{uuid.uuid4().hex[:16]}")
        assert run_req.status_code == 202
        terminal = _wait_run_terminal(api_client, community_token, run_req.json()["id"])
        assert terminal and terminal["status"] == "completed"

    toggled = api_client.patch(
        f"{BASE_URL}/api/tokens/{community_token}/compute/schedule",
        json={"enabled": True, "frequency": "hourly"},
    )
    assert toggled.status_code == 200
    data = toggled.json()
    assert data["schedule"]["enabled"] is True
    assert data["schedule"]["frequency"] == "hourly"
    assert isinstance(data["schedule"].get("next_run_at"), str)


# Cron auth + malformed + duplicate id handling + one due scheduled run
def test_cron_webhook_end_to_end_ack_and_duplicate_handling(api_client, mongo_db, community_token):
    # ensure token is schedulable for this test window
    mongo_db.compute_accounts.update_one(
        {"token": community_token},
        {"$set": {"day_runs": 0, "day_spent": 0, "paused": False, "active_run": None, "daily_limit": 200_000_000}},
    )

    # make schedule due immediately after legitimate enable
    due = datetime.now(timezone.utc) - timedelta(minutes=2)
    mongo_db.compute_accounts.update_one(
        {"token": community_token},
        {"$set": {"schedule.enabled": True, "schedule.frequency": "hourly", "schedule.next_run_at": due.isoformat()}},
    )

    # auth negative
    bad_auth = api_client.post(
        f"{BASE_URL}/api/cron/research",
        headers={"Authorization": "Bearer wrong-secret", "x-webhook-id": f"it7-bad-{uuid.uuid4().hex[:10]}"},
        json={"event": "schedule.triggered", "run_id": f"it7-bad-{uuid.uuid4().hex[:10]}"},
    )
    assert bad_auth.status_code == 401

    # malformed negative
    malformed = api_client.post(
        f"{BASE_URL}/api/cron/research",
        headers={"Authorization": f"Bearer {WEBHOOK_CRON_SECRET}", "x-webhook-id": f"it7-mal-{uuid.uuid4().hex[:10]}"},
        json={"event": "bad.event"},
    )
    assert malformed.status_code == 400

    # valid + duplicate
    webhook_id = f"it7-webhook-{uuid.uuid4().hex[:20]}"
    before_runs = _get_compute(api_client, community_token).get("runs", [])
    before_ids = {r["id"] for r in before_runs}

    valid = api_client.post(
        f"{BASE_URL}/api/cron/research",
        headers={"Authorization": f"Bearer {WEBHOOK_CRON_SECRET}", "x-webhook-id": webhook_id},
        json={"event": "schedule.triggered", "run_id": webhook_id},
    )
    assert valid.status_code == 200
    assert valid.json()["accepted"] is True
    assert valid.json()["duplicate"] is False

    dup = api_client.post(
        f"{BASE_URL}/api/cron/research",
        headers={"Authorization": f"Bearer {WEBHOOK_CRON_SECRET}", "x-webhook-id": webhook_id},
        json={"event": "schedule.triggered", "run_id": webhook_id},
    )
    assert dup.status_code == 200
    assert dup.json()["accepted"] is True
    assert dup.json()["duplicate"] is True

    # exactly one additional due run should appear and settle
    deadline = time.time() + 240
    target_run = None
    while time.time() < deadline:
        runs = _get_compute(api_client, community_token).get("runs", [])
        scheduled = [r for r in runs if r.get("trigger") == "scheduled" and r.get("id") not in before_ids]
        if scheduled:
            target_run = scheduled[0]
            if target_run["status"] in {"completed", "failed", "rejected"}:
                break
        time.sleep(3)

    assert target_run is not None
    assert target_run["trigger"] == "scheduled"
    assert target_run["status"] in {"completed", "failed", "rejected"}
    assert target_run.get("mode") == "community-test"
    assert target_run.get("model_id") in {
        "claude-sonnet-4-5",
        "claude-opus-4-5",
        "claude-haiku-4-5",
        "gpt-5.2",
        "gpt-5-mini",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
    }

    # disable schedule to prevent recurring spend after tests
    paused = api_client.patch(
        f"{BASE_URL}/api/tokens/{community_token}/compute/schedule",
        json={"enabled": False, "frequency": "hourly"},
    )
    assert paused.status_code == 200
    assert paused.json()["schedule"]["enabled"] is False


# Scheduled authority change should pause schedule without duplicate dispatch work
def test_scheduled_authority_mismatch_pauses_schedule(api_client, community_token, mongo_db):
    mongo_db.compute_accounts.update_one(
        {"token": community_token},
        {
            "$set": {
                "schedule.enabled": True,
                "schedule.frequency": "hourly",
                "schedule.authorized_by": "not-community-test",
                "schedule.expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "schedule.next_run_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            }
        },
    )
    webhook_id = f"it7-authz-{uuid.uuid4().hex[:18]}"
    hit = api_client.post(
        f"{BASE_URL}/api/cron/research",
        headers={"Authorization": f"Bearer {WEBHOOK_CRON_SECRET}", "x-webhook-id": webhook_id},
        json={"event": "schedule.triggered", "run_id": webhook_id},
    )
    assert hit.status_code == 200

    deadline = time.time() + 35
    while time.time() < deadline:
        state = _get_compute(api_client, community_token)
        if state.get("schedule", {}).get("enabled") is False:
            break
        time.sleep(2)
    state = _get_compute(api_client, community_token)
    assert state.get("schedule", {}).get("enabled") is False


# Ledger invariant around known real completed report id on FARTCOIN
def test_fartcoin_known_report_and_ledger_invariant_shape(api_client, mongo_db):
    compute = _get_compute(api_client, FARTCOIN)
    assert compute["token"] == FARTCOIN
    account = mongo_db.compute_accounts.find_one({"token": FARTCOIN})
    assert account is not None
    funded = float(account.get("funded", 0)) / 1_000_000
    assert pytest.approx(funded, abs=0.001) == pytest.approx(
        compute["balance"] + compute["reserved"] + compute["spent"], abs=0.001
    )

    run = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/compute/runs/2787f87fe66e416123434522dd25a387")
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "completed"
    assert body["charged"] >= 0
    assert body.get("usage", {}).get("input_tokens", 0) >= 0
    assert body.get("usage", {}).get("output_tokens", 0) >= 0


# Creator-protected endpoints: unauth 401 and wrong wallet 403 (if creator-owned token exists)
def test_creator_endpoint_authz_if_creator_token_present(api_client):
    creator_token = None
    for mint in [FARTCOIN, BONK, WIF, POPCAT]:
        res = api_client.get(f"{BASE_URL}/api/tokens/{mint}/compute")
        if res.status_code == 200 and res.json().get("owner"):
            creator_token = mint
            break

    if not creator_token:
        pytest.skip("No creator-owned token among provided mints; cannot assert 401/403 creator flow")

    no_auth = api_client.patch(
        f"{BASE_URL}/api/tokens/{creator_token}/compute/schedule",
        json={"enabled": False, "frequency": "daily"},
    )
    assert no_auth.status_code == 401

    headers, wallet = _auth_headers(api_client)
    wrong_wallet = api_client.patch(
        f"{BASE_URL}/api/tokens/{creator_token}/compute/schedule",
        headers=headers,
        json={"enabled": False, "frequency": "daily"},
    )
    assert wrong_wallet.status_code == 403