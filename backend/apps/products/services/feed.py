"""
Логіка Smart Feed: спочатку товари з обраних категорій, потім інші.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


async def fetch_smart_feed(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    page: int,
    limit: int,
    category_id: int | None,
) -> tuple[list[dict[str, Any]], int]:
    """
    1. Завантаж user_preferences для user_id (select category_id).
    2. Зроби два запити або один з CASE/ORDER BY:
       - товари зі статусом APPROVE або ACTIVE (узгодьте з контрактом) у обраних категоріях,
       - потім решта.
    3. Застосуй пагінацію offset=(page-1)*limit, limit=limit.
    4. Порахуй total (count) для фільтрів.
    5. Для кожного рядка визнач is_priority (чи входить category_id у preferences).
    6. Поверни (список dict для FeedItem, total).

    Зараз: заглушка — поверни ([], 0).
    """
    return [], 0
