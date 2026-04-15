"""Tests for the order lifecycle."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _register_and_login(
    client: AsyncClient, email: str, password: str = "StrongPass1", first_name: str = "User"
) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "first_name": first_name},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_order_list_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/orders/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_order_list_empty(client: AsyncClient):
    token = await _register_and_login(client, "buyer_orders@example.com")
    resp = await client.get(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_order_nonexistent_product(client: AsyncClient):
    token = await _register_and_login(client, "buyer_no_prod@example.com")
    resp = await client.post(
        "/api/v1/orders/",
        json={"product_id": 999999},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
