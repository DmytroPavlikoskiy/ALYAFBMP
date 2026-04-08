from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.schemas import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from common.database import get_db

router = APIRouter()


@router.post("/register", status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """
    Ендпоінт: POST /api/v1/auth/register (див. API-contract.md).

    1. Перевір, чи немає користувача з таким email: select(User).where(User.email == body.email).
    2. Якщо є -> HTTPException 400 з detail USER_ALREADY_EXISTS.
    3. Захешуй пароль (passlib bcrypt).
    4. Створи User(first_name=..., password_hash=..., ...). Якщо передано tg_chat_id — збережи в полі tg_chat_id.
    5. await session.add(user); await session.flush(); отримай user.id.
    6. Згенеруй JWT access + refresh (Група 1: jose / python-jose).
    7. Поверни RegisterResponse(user_id=...) та встанови токени в тілі відповіді, якщо контракт розширено (зараз контракт 201 лише user_id — узгодьте з викладачем).

    Повертає: user_id після реалізації.
    """
    raise HTTPException(
        status_code=501,
        detail="Група 1: реалізуйте реєстрацію за псевдокодом у docstring.",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Ендпоінт: POST /api/v1/auth/login.

    1. select(User).where(User.email == body.email); scalar_one_or_none().
    2. Якщо None -> 401 INVALID_CREDENTIALS.
    3. Перевір пароль через bcrypt verify.
    4. Якщо передано tg_chat_id — онови users.tg_chat_id для цього користувача.
    5. Згенеруй access + refresh JWT.
    6. Поверни TokenResponse(access=..., refresh=...).
    """
    raise HTTPException(status_code=501, detail="Група 1: реалізуйте логін.")
