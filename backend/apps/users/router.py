from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.schemas import NotificationItem, PreferencesBody, UserMeResponse
from common.database import get_db
from common.deps import get_current_user_id

router = APIRouter()


@router.get("/me", response_model=UserMeResponse)
async def read_me(
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    """
    GET /api/v1/users/me

    1. За user_id завантаж User (select + where).
    2. Обчисли is_banned: user.banned_until is not None і banned_until > now() (timezone-aware).
    3. Завантаж обрані категорії: join user_preferences або relationship user.preferences -> список category_id.
    4. Поверни UserMeResponse.
    """
    raise HTTPException(status_code=501, detail="Група 1–2: реалізуйте профіль.")


@router.post("/me/preferences")
async def save_preferences(
    body: PreferencesBody,
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    """
    POST /api/v1/users/me/preferences

    1. Видали старі рядки user_preferences для цього user_id (delete(UserPreference).where(...)) або upsert.
    2. Для кожного id в body.category_ids додай UserPreference(user_id=..., category_id=...).
    3. await session.commit().
    4. Поверни {"success": true} згідно з контрактом.
    """
    raise HTTPException(status_code=501, detail="Група 2: збережіть preferences.")


@router.get("/me/notifications", response_model=list[NotificationItem])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    """
    GET /api/v1/users/me/notifications

    1. select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).
    2. Смапи в NotificationItem.
    """
    raise HTTPException(status_code=501, detail="Група 5: реалізуйте сповіщення.")
