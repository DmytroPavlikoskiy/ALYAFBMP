"""
Спільна розмітка карток модерації (inline-кнопки + відправка фото/тексту).
Використовується в bot.py (Redis) і в botkeyboard.py (черга «Черга модерації»).
"""
from __future__ import annotations

import logging

import httpx
from aiogram import Bot
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from config import settings

logger = logging.getLogger(__name__)


def absolute_media_url(path_or_url: str) -> str:
    p = (path_or_url or "").strip()
    if p.startswith("http://") or p.startswith("https://"):
        return p
    base = settings.API_BASE_URL.rstrip("/")
    return f"{base}/{p.lstrip('/')}"


def build_moderation_keyboard(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
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
        ]
    )


async def send_moderation_card_to_chat(
    bot: Bot,
    *,
    chat_id: int,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    image_url: str | None,
) -> bool:
    """Повертає True, якщо повідомлення доставлено в Telegram."""
    try:
        if image_url:
            fetch_url = absolute_media_url(image_url)
            try:
                async with httpx.AsyncClient(timeout=60.0) as dl:
                    resp = await dl.get(fetch_url)
                    resp.raise_for_status()
                photo = BufferedInputFile(resp.content, filename="product.jpg")
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception as exc:
                logger.exception(
                    "Moderation image download failed (%s), text fallback: %s",
                    fetch_url,
                    exc,
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        return True
    except Exception as exc:
        logger.exception("send_moderation_card_to_chat failed for %s: %s", chat_id, exc)
        return False
