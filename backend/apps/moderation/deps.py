"""Заголовок X-Bot-Secret для дій бота (без доступу до БД з бота)."""
from __future__ import annotations

from fastapi import Header, HTTPException

from config import settings


async def verify_bot_secret(x_bot_secret: str | None = Header(default=None, alias="X-Bot-Secret")) -> bool:
    if x_bot_secret is None or x_bot_secret != settings.BOT_SECRET:
        raise HTTPException(status_code=401, detail="INVALID_BOT_SECRET")
    return True



async def soft_verify_bot_secret(x_bot_secret: str | None = Header(default=None, alias="X-Bot-Secret")) -> bool:
    if x_bot_secret is None or x_bot_secret != settings.BOT_SECRET:
        return False
    return True
