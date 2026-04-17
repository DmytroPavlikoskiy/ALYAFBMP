"""
Публікація подій модерації в Redis (канал moderation_channel) + відстеження доставки.

Після publish зберігаємо payload і помічаємо товар як «ще не доставлено жодному адміну».
Бот ставить прапорець після першої успішної доставки; фонова задача повторює спроби,
поки хоча б один адмін не отримає картку (щоб не було «мертвих» PENDING товарів).
"""
from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

# TTL для payload / прапорців (7 днів)
_MODERATION_KEY_TTL_SEC = 7 * 24 * 3600

PENDING_FIRST_DELIVERY_SET = "moderation:pending_first_delivery"


def _payload_key(product_id: int) -> str:
    return f"moderation:payload:{product_id}"


def _flag_key(product_id: int) -> str:
    return f"moderation:first_delivery_ok:{product_id}"


async def build_moderation_payload(
    product_id: int,
    title: str,
    price: float,
    image_urls: list[str],
    seller_id: str,
) -> dict[str, Any]:
    return {
        "product_id": str(product_id),
        "title": title,
        "price": price,
        "images": image_urls,
        "seller_id": str(seller_id),
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
    payload = await build_moderation_payload(
        product_id=product_id,
        title=title,
        price=price,
        image_urls=image_urls,
        seller_id=seller_id,
    )
    message = json.dumps(payload, ensure_ascii=False)

    await redis.publish("moderation_channel", message)

    # Прапорець «ще ніхто з адмінів не отримав» + payload для повторних спроб
    await redis.setex(_payload_key(product_id), _MODERATION_KEY_TTL_SEC, message)
    await redis.setex(_flag_key(product_id), _MODERATION_KEY_TTL_SEC, "0")
    await redis.sadd(PENDING_FIRST_DELIVERY_SET, str(product_id))


async def mark_moderation_first_delivery_ok(redis: Redis, product_id: int) -> None:
    """Викликає бот після першої успішної доставки хоча б одному адміну."""
    await redis.setex(_flag_key(product_id), _MODERATION_KEY_TTL_SEC, "1")
    await redis.srem(PENDING_FIRST_DELIVERY_SET, str(product_id))


async def clear_moderation_delivery_tracking(redis: Redis, product_id: int) -> None:
    """
    Прибрати трекінг після approve/reject (товар уже не в черзі модерації).
    """
    await redis.srem(PENDING_FIRST_DELIVERY_SET, str(product_id))
    await redis.delete(_payload_key(product_id), _flag_key(product_id))
