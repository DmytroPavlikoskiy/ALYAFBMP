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
from itertools import product

import httpx
import redis
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dns.e164 import query

from ALYAFBMP.backend.apps.bot.botkeyboard import router as user_flow_router
from ALYAFBMP.backend.config import settings

# =============================================================================
# ЗАБОРОНЕНО в цьому пакеті: from common.database / from common.models / sqlalchemy
# =============================================================================


def create_httpx_client() -> httpx.AsyncClient:
    """Клієнт для всіх викликів API (базовий URL з config.API_BASE_URL)."""
    return httpx.AsyncClient(
        base_url=settings.API_BASE_URL.rstrip("/"),
        timeout=30.0,
    )


async def listen_to_redis_task(bot: Bot) -> None:
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()

    await redis.pubsub.subscribe("незнаю яка назва канала")

    while True:
        try:
            msg = pubsub.get_message(ignore_subscribe_menu=True, timeout=30)

            if msg is None or msg["type"] != "message":
                continue

            data = json.loads(msg["data"])

            product_id = data.get("product_id")
            title = data.get("title")
            image_url = data.get("image_url")
            price = data.get("price")

            keyboard_AJ = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Схвалити", callback_data=f"mod:approve:{product_id}"),
                    InlineKeyboardButton(text="Відхилити", callback_data=f"mod:reject:{product_id}")
                ]
            ])

            await bot.send_photo(
                chat_id=settings.ADMIN_ID,
                photo=image_url,
                caption=f"Товар:{title}\nЦіна: {price}",
                reply_markup=keyboard_AJ
            )

        except Exception as e:
            print(f"Помилка: {e}")
            await asyncio.sleep(5)

    pass


async def approve_callback_handler(query: CallbackQuery) -> None:
    product_id = query.data.split(":")[-1]
    async with httpx.AsyncClient() as client:
        response = await client.patch(f"URL/products/{product_id}/approve")
        if response.is_success:
            await query.answer("Схвалено!")
            await query.message.edit_caption(caption="Статус: Схвалено ", reply_markup=None)
        else:
            await query.answer("Помилка",show_alert=True)



async def reject_callback_handler(query: CallbackQuery) -> None:
    product_id = query.data.split(":")[-1]
    async with httpx.AsyncClient() as client:
        response = await client.patch(f"URL/products/{product_id}/reject")
        if response.is_success:
            await query.answer("Відхилeно!")
            await query.message.edit_caption(caption="Статус: Відхилeно ", reply_markup=None)
        else:
            await query.answer("Помилка",show_alert=True)

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
