"""
Залежності FastAPI: поточний користувач, перевірка JWT.
Логіка навмисно не реалізована — заповнює Група 1.
"""
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    """
    1. Якщо credentials is None -> HTTPException 401 (не автентифіковано).
    2. Витягни access-токен з credentials.credentials.
    3. Декодуй JWT (python-jose / jose.jwt.decode) з SECRET та ALGORITHM з config.settings.
    4. З payload візьми sub (user_id як uuid) або custom claim.
    5. Опційно: завантаж User з БД через select(User).where(User.id == ...) і перевір, що користувач існує.
    6. Поверни uuid користувача.

    Зараз: заглушка — піднімає 501, доки не буде реалізовано JWT.
    """
    raise HTTPException(
        status_code=501,
        detail="Група 1: реалізуйте JWT і поверніть user_id з токена.",
    )


async def get_current_user_id_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID | None:
    """
    Те саме, що get_current_user_id, але якщо токена немає — поверни None (для публічних ендпоінтів).

    Поки JWT не реалізовано:
    - якщо credentials is None -> None;
    - якщо токен передано -> поки що також None (або викинь 501, коли почнете перевіряти підпис).
    """
    if credentials is None:
        return None
    # TODO Група 1: декодувати JWT і повернути uuid; поки що ігноруємо переданий токен.
    return None
