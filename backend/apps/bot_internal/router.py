"""
Ендпоінти для Telegram-бота (лише заголовок X-Bot-Secret, без JWT).
Бот викликає їх після подій у Redis (наприклад moderation_channel).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot_internal.schemas import AdminOut, AdminsResponse, PendingProductOut
from apps.moderation.deps import verify_bot_secret
from common.database import get_db
from common.models import Product, User
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("/get_admins", response_model=AdminsResponse)
async def get_admins_for_bot(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_bot_secret),
):
    """
    GET /api/v1/bot-internal/get_admins

    Список користувачів з role == ADMIN для розсилки карток модерації в Telegram.
    Бот надсилає повідомлення лише на ті `tg_chat_id`, які не null (користувач
    уже писав боту / пройшов лінк акаунту).
    """
    result = await db.execute(select(User).where(User.role == "ADMIN").order_by(User.email))
    rows = result.scalars().all()
    admins = [
        AdminOut(
            user_id=u.id,
            tg_chat_id=u.tg_chat_id,
            email=u.email,
        )
        for u in rows
    ]
    return AdminsResponse(admins=admins)


@router.get("/pending-products", response_model=list[PendingProductOut])
async def list_pending_products_for_bot(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_bot_secret),
):
    """
    GET /api/v1/bot-internal/pending-products

    Усі товари зі статусом PENDING (чекають approve/reject у боті).
    Викликається лише ботом (X-Bot-Secret).
    """
    result = await db.execute(
        select(Product)
        .where(Product.status == "PENDING")
        .options(selectinload(Product.images))
        .order_by(Product.id.desc())
        .limit(100)
    )
    rows = result.scalars().unique().all()
    return [
        PendingProductOut(
            id=p.id,
            title=p.title,
            price=float(p.price),
            seller_id=p.seller_id,
            images=[img.image_url for img in p.images],
            created_at=p.created_at,
        )
        for p in rows
    ]
