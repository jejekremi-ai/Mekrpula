"""Iteration11 regression: community posts must resolve via token-scoped route only."""

from __future__ import annotations

import os

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")

FARTCOIN = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"
BONK = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL must be defined")


@pytest.fixture(scope="module")
def api_client():
    return requests.Session()


# social api contract: token-scoped posts route is valid for real hubs
@pytest.mark.parametrize("mint", [FARTCOIN, BONK])
def test_token_scoped_posts_route_returns_200_and_list(api_client, mint):
    response = api_client.get(f"{BASE_URL}/api/tokens/{mint}/posts")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


# social api contract: legacy query route must stay invalid (prevents silent route drift)
@pytest.mark.parametrize("mint", [FARTCOIN, BONK])
def test_legacy_posts_query_route_returns_404(api_client, mint):
    response = api_client.get(f"{BASE_URL}/api/posts?token={mint}")
    assert response.status_code == 404
