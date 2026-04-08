from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PreferencesBody(BaseModel):
    category_ids: list[int] = Field(..., min_length=1)


class UserMeResponse(BaseModel):
    id: UUID
    first_name: str
    is_banned: bool
    banned_until: datetime | None
    selected_categories: list[int]


class NotificationItem(BaseModel):
    id: int
    text: str
    type: str
    created_at: datetime
