"""
Celery: background tasks (ban cleanup, order notifications).

Run worker from the backend/ directory:
  celery -A apps.celery.celery_app.celery_app worker --loglevel=info
  celery -A apps.celery.celery_app.celery_app beat --loglevel=info
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from celery import Celery
from celery.schedules import crontab

# Ensure backend/ root is on sys.path for common.* imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from common.database import AsyncSessionLocal  # noqa: E402
from config import settings  # noqa: E402

logger = logging.getLogger(__name__)

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    timezone="Europe/Kyiv",
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

#Марк .Б

# ---------------------------------------------------------------------------
# Task: clear expired bans (runs every 5 minutes via beat)
# ---------------------------------------------------------------------------

async def clear_expired_bans_async() -> None:
    from sqlalchemy import update
    from common.models import User

    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.banned_until.is_not(None), User.banned_until <= now)
            .values(banned_until=None, ban_reason=None, is_banned=False)
        )
        await session.commit()
    logger.info("clear_expired_bans: cleaned up bans expired before %s", now)


@celery_app.task(
    name="apps.celery.celery_app.clear_expired_bans",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
)
def clear_expired_bans() -> None:
    asyncio.run(clear_expired_bans_async())


# ---------------------------------------------------------------------------
# Task: notify seller about a new order
# ---------------------------------------------------------------------------

async def notify_seller_new_order_async(order_id: int, seller_id: str) -> None:
    import uuid as _uuid
    from common.models import Notification, Order

    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        if not order:
            logger.warning("notify_seller_new_order: order %s not found", order_id)
            return

        notification = Notification(
            user_id=_uuid.UUID(seller_id),
            text_notification=f"New order #{order_id} has been placed for your product.",
            type="NEW_ORDER",
        )
        session.add(notification)
        await session.commit()
        logger.info("Notified seller %s about order %s", seller_id, order_id)


@celery_app.task(
    name="apps.celery.celery_app.notify_seller_new_order",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
)
def notify_seller_new_order(order_id: int, seller_id: str) -> None:
    asyncio.run(notify_seller_new_order_async(order_id, seller_id))


# ---------------------------------------------------------------------------
# Beat schedule
# ---------------------------------------------------------------------------

celery_app.conf.beat_schedule = {
    "clear-expired-bans": {
        "task": "apps.celery.celery_app.clear_expired_bans",
        "schedule": crontab(minute="*/5"),
    },
}
