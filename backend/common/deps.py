from __future__ import annotations

import uuid
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from common.database import get_db
from common.models import User

security = HTTPBearer(auto_error=False)


JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")


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
    """

    
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    
    token = credentials.credentials

    try:
        
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
        )

        
        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_uuid = uuid.UUID(user_id)

    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

   
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    
    return user_uuid



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
