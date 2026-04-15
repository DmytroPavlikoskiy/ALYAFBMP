from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from jose import JWTError, jwt

from apps.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, RegisterResponse, TokenResponse
from apps.auth.utils import (
    create_access_token,
    create_refresh_token,
    is_password_strong,
    password_hash,
    verify_password,
)
from apps.moderation.deps import soft_verify_bot_secret
from common.database import get_db
from common.models import User
from common.rate_limit import rate_limit
from config import settings
import logging

router = APIRouter()

logging.basicConfig(level=logging.WARNING)

#Сніжана, Ксенія, Юра

@router.post("/register", status_code=201, response_model=RegisterResponse)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    is_bot: bool = Depends(soft_verify_bot_secret),
    _rl: None = Depends(rate_limit(max_requests=10, window_seconds=60)),
) -> RegisterResponse:
    # 1. Перевірка існуючого юзера
    result = await db.execute(select(User).where(User.email == body.email))
    user_already = result.scalar_one_or_none()
    
    if user_already:
        raise HTTPException(status_code=400, detail="USER_ALREADY_EXISTS")

    # 2. Валідація пароля
    if not await is_password_strong(body.password):
        raise HTTPException(
            status_code=400, 
            detail="Password is too weak! Use 8+ chars, digits and uppercase."
        )

    # 3. Хешування та створення
    hashed_pass = await password_hash(body.password)
    
    new_user = User(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone=body.phone,
        # Якщо запит від бота — довіряємо tg_chat_id
        tg_chat_id=body.tg_chat_id if is_bot else None,
        password_hash=hashed_pass # впевнись, що в моделі поле називається саме так
    )

    db.add(new_user)
    try:
        await db.commit()
        # new_user.id is set by the Python default=uuid.uuid4 before INSERT,
        # so db.refresh() is not needed to obtain the id.
        return RegisterResponse(user_id=new_user.id, status="success")
    except Exception as e:
        await db.rollback()
        logging.error(f"Register error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(max_requests=5, window_seconds=60)),
) -> TokenResponse:

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not await verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")

    if body.tg_chat_id:
        user.tg_chat_id = body.tg_chat_id
        db.add(user)
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email, "role": user.role})

    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """POST /api/v1/auth/refresh — exchange a valid refresh token for new access + refresh tokens."""
    try:
        payload = jwt.decode(
            body.refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise ValueError("Missing sub claim")
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token") from exc

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    new_refresh = create_refresh_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(access_token=new_access, refresh_token=new_refresh, token_type="bearer")
