from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.users.schemas import NotificationItem, PreferencesBody, UserMeResponse
from common.database import get_db
from common.deps import get_current_user_id
from common.models import Notification, Product, User, UserPreference

router = APIRouter()


@router.get("/me", response_model=UserMeResponse)
async def read_me(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """GET /api/v1/users/me — profile of the authenticated user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_banned = bool(
        user.banned_until and user.banned_until > datetime.now(timezone.utc)
    )

    pref_result = await db.execute(
        select(UserPreference.category_id).where(UserPreference.user_id == user_id)
    )
    category_ids = list(pref_result.scalars().all())

    return UserMeResponse(
        id=user.id,
        first_name=user.first_name,
        role=user.role,
        is_banned=is_banned,
        banned_until=user.banned_until,
        selected_categories=category_ids,
    )


@router.post("/me/preferences")
async def save_preferences(
    body: PreferencesBody,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """POST /api/v1/users/me/preferences — replace the user's category preferences."""
    await db.execute(
        delete(UserPreference).where(UserPreference.user_id == user_id)
    )
    for cat_id in body.category_ids:
        db.add(UserPreference(user_id=user_id, category_id=cat_id))
    await db.commit()
    return {"success": True}


@router.get("/me/notifications", response_model=list[NotificationItem])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """GET /api/v1/users/me/notifications — newest-first notification list."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/me/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """PATCH /api/v1/users/me/notifications/{id}/read — mark a notification as read."""
    notif = await db.get(Notification, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    notif.is_read = True
    await db.commit()
    return {"ok": True}


@router.get("/me/products")
async def list_my_products(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """GET /api/v1/users/me/products — all listings created by the authenticated user."""
    result = await db.execute(
        select(Product)
        .where(Product.seller_id == user_id)
        .options(selectinload(Product.images))
        .order_by(Product.created_at.desc())
    )
    products = result.scalars().all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "price": float(p.price),
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "images": [img.image_url for img in p.images],
        }
        for p in products
    ]
