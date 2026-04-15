"""
WebSocket ConnectionManager with Redis pub/sub fan-out.

Single-worker: works exactly like the old in-memory dict.
Multi-worker: each worker subscribes to Redis channel `chat:{chat_id}`
when a client connects and re-broadcasts any published message to its
local WebSocket connections.  When a worker calls `broadcast()` it
publishes to Redis so every other worker also delivers the message.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        # chat_id → list of local WebSocket connections on this worker
        self.active_connections: dict[uuid.UUID, list[WebSocket]] = {}
        # chat_id → asyncio.Task running the Redis subscriber loop
        self._redis_tasks: dict[uuid.UUID, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket, chat_id: uuid.UUID) -> None:
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
            await self._start_redis_listener(chat_id)
        self.active_connections[chat_id].append(websocket)

    def disconnect(self, websocket: WebSocket, chat_id: uuid.UUID) -> None:
        conns = self.active_connections.get(chat_id)
        if conns is None:
            return
        try:
            conns.remove(websocket)
        except ValueError:
            pass
        if not conns:
            del self.active_connections[chat_id]
            self._cancel_redis_listener(chat_id)

    async def broadcast(self, message: dict, chat_id: uuid.UUID) -> None:
        """
        Publish the message to the Redis channel so ALL workers (including
        this one) deliver it to their local connections via the listener task.
        Falls back to direct delivery if Redis is not available.
        """
        try:
            from common.redis_client import get_redis  # avoid circular import at module level
            r = await get_redis()
            await r.publish(f"chat:{chat_id}", json.dumps(message))
        except Exception as exc:
            logger.warning("Redis broadcast failed (%s), falling back to local delivery", exc)
            await self._local_broadcast(message, chat_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _local_broadcast(self, message: dict, chat_id: uuid.UUID) -> None:
        """Deliver a message directly to local WebSocket connections."""
        dead: list[WebSocket] = []
        for ws in list(self.active_connections.get(chat_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, chat_id)

    async def _redis_listener_loop(self, chat_id: uuid.UUID) -> None:
        """Subscribe to `chat:{chat_id}` and fan out to local connections."""
        try:
            from common.redis_client import get_redis
            r = await get_redis()
            pubsub = r.pubsub()
            await pubsub.subscribe(f"chat:{chat_id}")
            logger.debug("WS Redis listener started for chat %s", chat_id)

            while chat_id in self.active_connections:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg["type"] == "message":
                    try:
                        data = json.loads(msg["data"])
                    except (json.JSONDecodeError, TypeError):
                        continue
                    await self._local_broadcast(data, chat_id)
                else:
                    await asyncio.sleep(0.05)

            await pubsub.unsubscribe(f"chat:{chat_id}")
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception("Redis listener error for chat %s: %s", chat_id, exc)

    async def _start_redis_listener(self, chat_id: uuid.UUID) -> None:
        task = asyncio.create_task(self._redis_listener_loop(chat_id))
        self._redis_tasks[chat_id] = task

    def _cancel_redis_listener(self, chat_id: uuid.UUID) -> None:
        task = self._redis_tasks.pop(chat_id, None)
        if task and not task.done():
            task.cancel()


manager = ConnectionManager()
