"""
Публікація подій модерації в Redis (канал moderation_channel).
"""
from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis


async def build_moderation_payload(
    product_id: int,
    title: str,
    price: float,
    image_urls: list[str],
    seller_id: str,
) -> dict[str, Any]:
    """
    Допоміжна функція для формування JSON, який піде в Redis / Telegram.
    Поверни dict з ключами, узгодженими з ботом.
    """
    return {
        "product_id": str(product_id),
        "title": title,
        "price": price,
        "images": image_urls,
        "seller_id": seller_id,
    }


async def publish_new_product_to_moderation(
    redis: Redis,
    *,
    product_id: int,
    title: str,
    price: float,
    image_urls: list[str],
    seller_id: str,
) -> None:
    """
    1. Збери dict payload: product_id, title, price, images (список рядків URL або /static/...), seller_id.
    2. json.dumps(payload).
    3. await redis.publish("moderation_channel", message).
    4. Не передавай сюди UploadFile — лише вже збережені шляхи/URL.

    Зараз: навмисно порожньо — реалізує Група 4/5.
    """

    payload = await build_moderation_payload(
        product_id=product_id,
        title=title,
        price=price,
        image_urls=image_urls,
        seller_id=seller_id
    )

    message = json.dumps(payload, ensure_ascii=False)
    await redis.publish("moderation_channel", message)

