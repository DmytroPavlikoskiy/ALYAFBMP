"""
Асинхронний клієнт Redis (HTTP-залежності, pub/sub модерації).
"""
from __future__ import annotations

from redis.asyncio import Redis

from config import settings

_redis: Redis | None = None


async def init_redis() -> Redis:
    """
    Ініціалізує глобальний клієнт і перевіряє з’єднання (PING).
    Викликати один раз при старті застосунку (lifespan startup).
    """
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    await _redis.ping()
    return _redis


async def get_redis() -> Redis:
    """
    Повертає клієнт Redis. Якщо ще не створений — створює без окремого ping
    (після init_redis на старті зазвичай уже готовий).
    """
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    """Коректно закриває з’єднання (lifespan shutdown)."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
