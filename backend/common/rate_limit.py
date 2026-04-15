"""
Redis-backed sliding-window rate limiter.

Usage as a FastAPI dependency:

    from common.rate_limit import rate_limit

    @router.post("/login")
    async def login(
        request: Request,
        _: None = Depends(rate_limit(max_requests=5, window_seconds=60)),
        ...
    ):
        ...
"""
from __future__ import annotations

import logging
import time
from functools import lru_cache

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Return a FastAPI dependency that enforces a sliding-window rate limit.

    Key: IP address of the request.
    Storage: Redis sorted set `rl:{endpoint}:{ip}`.
    """
    async def dependency(request: Request) -> None:
        try:
            from common.redis_client import get_redis

            r = await get_redis()
            ip = request.client.host if request.client else "unknown"
            endpoint = request.url.path.replace("/", "_")
            key = f"rl:{endpoint}:{ip}"
            now = time.time()
            window_start = now - window_seconds

            pipe = r.pipeline()
            pipe.zremrangebyscore(key, "-inf", window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window_seconds)
            results = await pipe.execute()

            count = results[2]
            if count > max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Limit: {max_requests} per {window_seconds}s.",
                    headers={"Retry-After": str(window_seconds)},
                )
        except HTTPException:
            raise
        except Exception as exc:
            # If Redis is unavailable, fail open (don't block the request)
            logger.warning("Rate limiter unavailable: %s", exc)

    return dependency
