"""
Shared pytest fixtures for ALYAFBMP backend tests.

Uses an in-memory SQLite engine so no real PostgreSQL or Redis is required.
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.postgresql import UUID as _PgUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from common.database import Base, get_db
from common.models import *  # noqa: F401,F403 – registers all ORM metadata

# ---------------------------------------------------------------------------
# Mock Redis so the rate-limiter and pub/sub code don't hang waiting for a
# real Redis connection.  The rate-limiter imports get_redis lazily (inside
# the function body), so patching the module attribute here is sufficient.
# ---------------------------------------------------------------------------
import common.redis_client as _redis_module

_mock_pipe = MagicMock()
_mock_pipe.execute = AsyncMock(return_value=[0, 0, 0, True])  # count=0 → no 429
_mock_pipe.zremrangebyscore = MagicMock()
_mock_pipe.zadd = MagicMock()
_mock_pipe.zcard = MagicMock()
_mock_pipe.expire = MagicMock()

_mock_redis_client = MagicMock()
_mock_redis_client.pipeline = MagicMock(return_value=_mock_pipe)


async def _mock_get_redis():
    return _mock_redis_client


_redis_module.get_redis = _mock_get_redis

# ---------------------------------------------------------------------------
# Import main *after* patching Redis to avoid startup issues.
# ---------------------------------------------------------------------------
from main import app  # noqa: E402

# ---------------------------------------------------------------------------
# SQLite compatibility: strip the PostgreSQL-specific server_default
# (gen_random_uuid()) from UUID columns so that CREATE TABLE succeeds on
# SQLite.  The UUID(as_uuid=True) type itself is intentionally left intact
# so that bind/result processors remain consistent for storage and lookup.
# ---------------------------------------------------------------------------
for _table in Base.metadata.tables.values():
    for _col in _table.columns:
        if isinstance(_col.type, _PgUUID):
            _col.server_default = None  # gen_random_uuid() is PostgreSQL-only

# ---------------------------------------------------------------------------
# In-memory SQLite (aiosqlite) engine for tests
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
