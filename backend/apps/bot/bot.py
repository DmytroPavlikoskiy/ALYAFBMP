"""
Головна точка входу Telegram-бота (окремий процес від FastAPI).

Архітектура: жодних імпортів common.database, common.models, sqlalchemy —
інтеграція з системою лише через httpx.AsyncClient до REST API.

Запуск з каталогу backend:
  python -m apps.bot.bot
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging

import httpx
import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from apps.bot.botkeyboard import router as user_flow_router
from config import settings

# =============================================================================
# ЗАБОРОНЕНО в цьому пакеті: from common.database / from common.models / sqlalchemy
# =============================================================================

logger = logging.getLogger(__name__)


def create_httpx_client() -> httpx.AsyncClient:
    """Клієнт для всіх викликів API (базовий URL з config.API_BASE_URL)."""
    return httpx.AsyncClient(
        base_url=settings.API_BASE_URL.rstrip("/"),
        timeout=30.0,
    )


async def listen_to_redis_task(bot: Bot) -> None:
    """
    Фонова задача: підписка на Redis-канал moderation_channel і
    розсилка карток модерації адміністратору через Telegram.
    БД не використовується — лише дані з повідомлення Redis.
    """
    r = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("moderation_channel")
    logger.info("Bot subscribed to moderation_channel")

    while True:
        try:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)

            if msg is None or msg["type"] != "message":
                await asyncio.sleep(0.1)
                continue

            data = json.loads(msg["data"])

            product_id = data.get("product_id")
            title = data.get("title", "—")
            price = data.get("price", "—")
            images: list[str] = data.get("images", [])
            image_url = images[0] if images else None

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Схвалити",
                        callback_data=f"mod:approve:{product_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Відхилити",
                        callback_data=f"mod:reject:{product_id}",
                    ),
                ]
            ])

            caption = f"📦 <b>{title}</b>\n💰 Ціна: {price}\n🆔 ID: {product_id}"

            if image_url:
                await bot.send_photo(
                    chat_id=settings.ADMIN_ID,
                    photo=image_url,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            else:
                await bot.send_message(
                    chat_id=settings.ADMIN_ID,
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("listen_to_redis_task error: %s", exc)
            await asyncio.sleep(5)

    await pubsub.unsubscribe("moderation_channel")
    await r.aclose()


async def approve_callback_handler(query: CallbackQuery) -> None:
    """Inline-кнопка «Схвалити» — PATCH /api/v1/products/{id}/approve."""
    product_id = query.data.split(":")[-1]
    async with create_httpx_client() as client:
        response = await client.patch(
            f"/api/v1/products/{product_id}/approve",
            headers={"X-Bot-Secret": settings.BOT_SECRET},
        )
    if response.is_success:
        await query.answer("Схвалено!")
        await query.message.edit_caption(caption="✅ Статус: Схвалено", reply_markup=None)
    else:
        logger.error("approve failed: %s %s", response.status_code, response.text)
        await query.answer("Помилка API", show_alert=True)


async def reject_callback_handler(query: CallbackQuery) -> None:
    """Inline-кнопка «Відхилити» — PATCH /api/v1/products/{id}/reject."""
    product_id = query.data.split(":")[-1]
    async with create_httpx_client() as client:
        response = await client.patch(
            f"/api/v1/products/{product_id}/reject",
            headers={"X-Bot-Secret": settings.BOT_SECRET},
        )
    if response.is_success:
        await query.answer("Відхилено!")
        await query.message.edit_caption(caption="❌ Статус: Відхилено", reply_markup=None)
    else:
        logger.error("reject failed: %s %s", response.status_code, response.text)
        await query.answer("Помилка API", show_alert=True)


def register_moderation_callbacks(dp: Dispatcher) -> None:
    """Реєстрація callback для модерації (окремо від сценарію реєстрації в botkeyboard)."""
    dp.callback_query.register(approve_callback_handler, F.data.startswith("mod:approve:"))
    dp.callback_query.register(reject_callback_handler, F.data.startswith("mod:reject:"))


async def main() -> None:
    """Polling: об’єднує сценарії користувача (keyboard) та модерацію."""
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(user_flow_router)
    register_moderation_callbacks(dp)

    redis_task = asyncio.create_task(listen_to_redis_task(bot))
    try:
        await dp.start_polling(bot)
    finally:
        redis_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await redis_task
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
