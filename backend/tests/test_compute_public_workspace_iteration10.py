"""Iteration10 compute public workspace regression: public payload hygiene and archive English integrity."""

from __future__ import annotations

import hashlib
import os
import re

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
MONGO_URL = os.environ.get("MONGO_URL", "").strip('"')
DB_NAME = os.environ.get("DB_NAME", "").strip('"')

FARTCOIN = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"


if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL must be defined")


@pytest.fixture(scope="module")
def api_client():
    return requests.Session()


@pytest.fixture(scope="module")
def mongo_db():
    if not MONGO_URL or not DB_NAME:
        pytest.skip("Mongo credentials missing; cannot verify archive translation integrity")
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


# compute api view: enforce public payload hygiene and English-facing structure
def test_compute_view_public_payload_hygiene(api_client):
    response = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/compute")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data.get("activity"), list)
    assert isinstance(data.get("runs"), list)

    for run in data["runs"]:
        assert "prompt" not in run
        assert "system" not in run
        assert run.get("display_language") == "en"

    completed = [r for r in data["runs"] if r.get("status") == "completed" and (r.get("display_output") or "").strip()]
    assert completed, "Expected at least one completed run with visible display_output"
    latest = completed[0]
    text = latest.get("display_output", "")
    assert "Summary" in text
    assert "Market" in text
    assert "Event" in text


# compute api presentation: normalize legacy activity labels away from Indonesian terms
def test_compute_view_activity_titles_are_english(api_client):
    response = api_client.get(f"{BASE_URL}/api/tokens/{FARTCOIN}/compute")
    assert response.status_code == 200
    activity = response.json().get("activity", [])
    assert activity, "Expected non-empty activity on populated FARTCOIN hub"

    forbidden = re.compile(r"\b(riset|jadwal|kreator|berakhir|dijeda|hanya)\b", re.IGNORECASE)
    for item in activity:
        title = item.get("title", "")
        assert not forbidden.search(title), f"Found non-English activity title: {title}"


# archive migration: seven historical non-English runs must keep original output and hash integrity
def test_archive_translation_hash_integrity_for_fartcoin(mongo_db):
    rows = list(
        mongo_db.compute_runs.find(
            {
                "token": FARTCOIN,
                "output": {"$nin": ["", None]},
                "language": {"$ne": "en"},
            },
            {"_id": 0, "id": 1, "output": 1, "output_en": 1, "translation_original_hash": 1},
        )
    )

    assert len(rows) >= 7, f"Expected at least 7 archived non-English runs, got {len(rows)}"

    for row in rows:
        output = row.get("output") or ""
        output_en = row.get("output_en") or ""
        expected_hash = hashlib.sha256(output.encode()).hexdigest()
        assert output_en.strip(), f"Missing output_en for archived run {row.get('id')}"
        assert row.get("translation_original_hash") == expected_hash, f"Hash mismatch for archived run {row.get('id')}"
