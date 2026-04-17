from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AdminOut(BaseModel):
    user_id: UUID
    tg_chat_id: int | None
    email: str

    model_config = {"from_attributes": False}


class AdminsResponse(BaseModel):
    admins: list[AdminOut]


class PendingProductOut(BaseModel):
    id: int
    title: str
    price: float
    seller_id: UUID
    images: list[str]
    created_at: datetime | None

    model_config = {"from_attributes": False}
