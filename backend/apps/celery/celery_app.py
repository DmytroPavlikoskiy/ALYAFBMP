"""
Celery: фонові задачі (наприклад, очищення прострочених банів).

Запуск воркера з каталогу backend:
  celery -A apps.celery.celery_app.celery_app worker --loglevel=info
  celery -A apps.celery.celery_app.celery_app beat --loglevel=info
"""
from __future__ import annotations

import asyncio
import os
import sys

from celery import Celery
from celery.schedules import crontab

# Корінь backend/ у sys.path для імпортів common.* та config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from common.database import AsyncSessionLocal  # noqa: E402
from config import settings  # noqa: E402

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    timezone="Europe/Kyiv",
    broker_connection_retry_on_startup=True,
)


async def clear_expired_bans_async() -> None:
    """
    Очищення банів, термін яких минув (поле users.banned_until з API-contract.md).

    1. async with AsyncSessionLocal() as session.
    2. Запит: select(User).where(User.banned_until.is_not(None)).
    3. Відфільтруй у Python або SQL: banned_until < datetime.now(timezone.utc).
    4. Для кожного: онови banned_until на NULL, ban_reason на NULL (update(User).where(...).values(...)).
    5. await session.commit().

    Зараз: без реалізації — додайте логіку за цим планом (SQLAlchemy 2.0 async).
    """
    async with AsyncSessionLocal() as session:
        pass


@celery_app.task(name="apps.celery.celery_app.clear_expired_bans")
def clear_expired_bans() -> None:
    """Синхронна обгортка: asyncio.run(clear_expired_bans_async())."""
    asyncio.run(clear_expired_bans_async())


celery_app.conf.beat_schedule = {
    "clear-expired-bans": {
        "task": "apps.celery.celery_app.clear_expired_bans",
        "schedule": crontab(minute="*/5"),
    },
}
