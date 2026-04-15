"""
Redis-backed token store for the Telegram bot.

Tokens are stored as a JSON hash under key `bot:tokens:{tg_chat_id}`.
TTL mirrors the access token lifetime so stale entries are auto-cleaned.
"""
from __future__ import annotations

import json
import logging

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)

_BOT_REDIS: aioredis.Redis | None = None

# Keep tokens for 7 days (refresh token lifetime)
_TOKEN_TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86_400


def _get_redis() -> aioredis.Redis:
    global _BOT_REDIS
    if _BOT_REDIS is None:
        _BOT_REDIS = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _BOT_REDIS


def _key(tg_chat_id: int) -> str:
    return f"bot:tokens:{tg_chat_id}"


async def save_tokens(tg_chat_id: int, access_token: str, refresh_token: str) -> None:
    r = _get_redis()
    payload = json.dumps({"access_token": access_token, "refresh_token": refresh_token})
    await r.set(_key(tg_chat_id), payload, ex=_TOKEN_TTL)
    logger.debug("Saved tokens for chat %s", tg_chat_id)


async def get_access_token(tg_chat_id: int) -> str | None:
    r = _get_redis()
    raw = await r.get(_key(tg_chat_id))
    if not raw:
        return None
    try:
        return json.loads(raw).get("access_token")
    except (json.JSONDecodeError, AttributeError):
        return None


async def delete_tokens(tg_chat_id: int) -> None:
    r = _get_redis()
    await r.delete(_key(tg_chat_id))
    logger.debug("Deleted tokens for chat %s", tg_chat_id)
