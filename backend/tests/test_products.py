"""Tests for product feed and categories."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient, email: str, password: str = "StrongPass1") -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "first_name": "Prod"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_categories_empty(client: AsyncClient):
    resp = await client.get("/api/v1/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_feed_empty(client: AsyncClient):
    resp = await client.get("/api/v1/products/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert "feed_items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_feed_requires_no_auth(client: AsyncClient):
    """Feed is public — no auth header needed."""
    resp = await client.get("/api/v1/products/feed?page=1&limit=5")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_users_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_users_me_authenticated(client: AsyncClient):
    token = await _get_token(client, "me@example.com")
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Prod"
    assert "role" in body
    assert "is_banned" in body
