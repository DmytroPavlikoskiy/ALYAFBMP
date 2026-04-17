"""
Головна точка входу Telegram-бота (окремий процес від FastAPI).

Архітектура: жодних імпортів common.database, common.models, sqlalchemy —
інтеграція з системою лише через httpx.AsyncClient до REST API.

Redis (get_redis) дозволений для прапорців доставки модерації.

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
from aiogram.types import CallbackQuery, Message

from apps.bot.botkeyboard import router as user_flow_router
from apps.bot.moderation_cards import build_moderation_keyboard, send_moderation_card_to_chat
from apps.products.services.moderation_redis import (
    PENDING_FIRST_DELIVERY_SET,
    mark_moderation_first_delivery_ok,
)
from common.redis_client import get_redis
from config import settings

# =============================================================================
# ЗАБОРОНЕНО: from common.database / from common.models / sqlalchemy
# =============================================================================

logger = logging.getLogger(__name__)

MODERATION_RETRY_INTERVAL_SEC = 50


def create_httpx_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.API_BASE_URL.rstrip("/"),
        timeout=30.0,
    )


async def fetch_admin_telegram_chat_ids(client: httpx.AsyncClient) -> list[int]:
    response = await client.get(
        "/api/v1/bot-internal/get_admins",
        headers={"X-Bot-Secret": settings.BOT_SECRET},
    )
    response.raise_for_status()
    payload = response.json()
    chats: list[int] = []
    for row in payload.get("admins", []):
        tid = row.get("tg_chat_id")
        if tid is not None:
            chats.append(int(tid))
    return chats


async def deliver_moderation_notifications(bot: Bot, data: dict) -> bool:
    """
    Розсилає картку всім адмінам з tg_chat_id.
    Повертає True, якщо хоча б один адмін успішно отримав повідомлення.
    """
    product_id = data.get("product_id")
    title = data.get("title", "—")
    price = data.get("price", "—")
    images: list[str] = data.get("images", [])
    image_url = images[0] if images else None

    keyboard = build_moderation_keyboard(str(product_id))
    caption = f"📦 <b>{title}</b>\n💰 Ціна: {price}\n🆔 ID: {product_id}"

    async with create_httpx_client() as client:
        try:
            chat_ids = await fetch_admin_telegram_chat_ids(client)
        except Exception as exc:
            logger.exception("get_admins failed: %s", exc)
            return False

    if not chat_ids:
        logger.warning(
            "Moderation not delivered: no admins with tg_chat_id. "
            "Set role ADMIN and ensure admins /start the bot."
        )
        return False

    any_ok = False
    for admin_chat in chat_ids:
        ok = await send_moderation_card_to_chat(
            bot,
            chat_id=admin_chat,
            caption=caption,
            keyboard=keyboard,
            image_url=image_url,
        )
        if ok:
            any_ok = True
    return any_ok


async def _maybe_mark_delivered(product_id: int, success: bool) -> None:
    if not success:
        return
    redis = await get_redis()
    await mark_moderation_first_delivery_ok(redis, product_id)


async def retry_undelivered_moderation_loop(bot: Bot) -> None:
    """
    Періодично повторює доставку для товарів, які ще не дійшли хоча б до одного адміна
    (ключі залишились у moderation:pending_first_delivery).
    """
    while True:
        try:
            await asyncio.sleep(MODERATION_RETRY_INTERVAL_SEC)
            redis = await get_redis()
            ids = await redis.smembers(PENDING_FIRST_DELIVERY_SET)
            if not ids:
                continue
            for pid_str in ids:
                try:
                    pid = int(pid_str)
                except ValueError:
                    continue
                raw = await redis.get(f"moderation:payload:{pid}")
                if not raw:
                    await redis.srem(PENDING_FIRST_DELIVERY_SET, pid_str)
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Bad moderation payload JSON for product %s", pid)
                    continue
                ok = await deliver_moderation_notifications(bot, data)
                await _maybe_mark_delivered(pid, ok)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("retry_undelivered_moderation_loop")


async def _finalize_moderation_message(query: CallbackQuery, approved: bool) -> None:
    text = "✅ Статус: Схвалено" if approved else "❌ Статус: Відхилено"
    msg: Message | None = query.message
    if not msg:
        return
    try:
        if msg.photo:
            await msg.edit_caption(caption=text, reply_markup=None)
        else:
            await msg.edit_text(text=text, reply_markup=None)
    except Exception as exc:
        logger.debug("Could not edit moderation message: %s", exc)


async def listen_to_redis_task(bot: Bot) -> None:
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
            try:
                pid = int(data.get("product_id"))
            except (TypeError, ValueError):
                logger.warning("moderation_channel message without product_id: %s", data)
                continue
            ok = await deliver_moderation_notifications(bot, data)
            await _maybe_mark_delivered(pid, ok)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("listen_to_redis_task error: %s", exc)
            await asyncio.sleep(5)

    await pubsub.unsubscribe("moderation_channel")
    await r.aclose()


async def approve_callback_handler(query: CallbackQuery) -> None:
    product_id = query.data.split(":")[-1]
    async with create_httpx_client() as client:
        response = await client.patch(
            f"/api/v1/products/{product_id}/approve",
            headers={"X-Bot-Secret": settings.BOT_SECRET},
        )
    if response.is_success:
        await query.answer("Схвалено!")
        await _finalize_moderation_message(query, approved=True)
    else:
        logger.error("approve failed: %s %s", response.status_code, response.text)
        await query.answer("Помилка API", show_alert=True)


async def reject_callback_handler(query: CallbackQuery) -> None:
    product_id = query.data.split(":")[-1]
    async with create_httpx_client() as client:
        response = await client.patch(
            f"/api/v1/products/{product_id}/reject",
            headers={"X-Bot-Secret": settings.BOT_SECRET},
        )
    if response.is_success:
        await query.answer("Відхилено!")
        await _finalize_moderation_message(query, approved=False)
    else:
        logger.error("reject failed: %s %s", response.status_code, response.text)
        await query.answer("Помилка API", show_alert=True)


def register_moderation_callbacks(dp: Dispatcher) -> None:
    dp.callback_query.register(approve_callback_handler, F.data.startswith("mod:approve:"))
    dp.callback_query.register(reject_callback_handler, F.data.startswith("mod:reject:"))


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(user_flow_router)
    register_moderation_callbacks(dp)

    redis_task = asyncio.create_task(listen_to_redis_task(bot))
    retry_task = asyncio.create_task(retry_undelivered_moderation_loop(bot))
    try:
        await dp.start_polling(bot)
    finally:
        redis_task.cancel()
        retry_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await redis_task
        with contextlib.suppress(asyncio.CancelledError):
            await retry_task
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
