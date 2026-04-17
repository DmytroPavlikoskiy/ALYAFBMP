from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PreferencesBody(BaseModel):
    category_ids: list[int] = Field(..., min_length=1)


class UserMeResponse(BaseModel):
    id: UUID
    first_name: str
    role: str
    is_banned: bool
    banned_until: datetime | None
    selected_categories: list[int]


class NotificationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    # ORM attribute is text_notification; keep the JSON key as "text" for frontend compatibility
    text: str = Field(validation_alias="text_notification")
    type: str
    is_read: bool
    created_at: datetime
