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

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery

from apps.bot.botkeyboard import router as user_flow_router
from config import settings

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
    """
    Фонова задача: підписка на Redis і розсилка карток модерації адміну.

    ПСЕВДОКОД (студенти реалізують; БД не чіпати):

    1. Імпортувати redis.asyncio (окремо від проєктного common.redis — щоб не тягнути FastAPI-залежності, якщо не потрібно):
       redis = Redis.from_url(settings.REDIS_URL, decode_responses=True).
    2. pubsub = redis.pubsub(); await pubsub.subscribe("moderation_channel").
    3. У циклі while True:
         msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)
         якщо msg is None або msg["type"] != "message": continue
    4. data = json.loads(msg["data"])  # очікуй product_id, image_url (або images), title, price
    5. НЕ викликати сесію БД. Використати лише product_id та URL зображення з повідомлення.
    6. Побудувати InlineKeyboard: callback "mod:approve:{product_id}", "mod:reject:{product_id}"
    7. await bot.send_message(chat_id=settings.ADMIN_ID, text=..., reply_markup=...)
    8. Обробляти винятки, логувати.

    Зараз: pass (порожня заглушка).
    """
    pass


async def approve_callback_handler(query: CallbackQuery) -> None:
    """
    Inline-кнопка «Схвалити».

    ПСЕВДОКОД:

    1. Виділити product_id з query.data після префікса "mod:approve:".
    2. async with create_httpx_client() as client:
    3. response = await client.patch(
           f"/api/v1/products/{product_id}/approve",
           headers={"X-Bot-Secret": settings.BOT_SECRET},
       )
    4. Якщо response.is_success: await query.answer("OK"); відредагувати повідомлення («Схвалено»).
    5. Інакше: await query.answer("Помилка API", show_alert=True).

    Зараз: pass.
    """
    pass


async def reject_callback_handler(query: CallbackQuery) -> None:
    """
    Inline-кнопка «Відхилити».

    ПСЕВДОКОД:

    1. product_id з "mod:reject:".
    2. await client.patch(
           f"/api/v1/products/{product_id}/reject",
           headers={"X-Bot-Secret": settings.BOT_SECRET},
       )
    3. Аналогічно оновити UI повідомлення в Telegram.

    Зараз: pass.
    """
    pass


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
