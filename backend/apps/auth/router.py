from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.auth.schemas import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from common.database import get_db
from moderation.deps import soft_verify_bot_secret
from common.models import User
from apps.auth.utils import (verify_password, password_hash,
                             is_password_strong, create_access_token, create_refresh_token)
import logging

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)


@router.post("/register", status_code=201, response_model=RegisterResponse)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    is_bot: bool = Depends(soft_verify_bot_secret)
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
        await db.refresh(new_user) # щоб отримати id
        return RegisterResponse(user_id=new_user.id, status="success")
    except Exception as e:
        await db.rollback()
        logging.error(f"Register error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
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
