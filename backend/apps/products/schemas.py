from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserPref(BaseModel):
    user_id: UUID = Field(..., description="ID користувача")
    category_id: int = Field(..., gt=0)

    model_config = {"from_attributes": True}


class CategoryOut(BaseModel):
    id: int
    name: str
    icon_url: str | None

    model_config = {"from_attributes": True}


class ProductCreateJson(BaseModel):
    """Варіант тіла з контракту (images як URL). Окремо від multipart-завантаження файлів."""

    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    price: float = Field(..., gt=0)
    category_id: int | None = None
    images: list[str] = Field(default_factory=list)


class ProductCreatedResponse(BaseModel):
    id: int
    status: str


class FeedItem(BaseModel):
    id: int
    title: str
    price: float
    is_priority: bool


class FeedResponse(BaseModel):
    items: list[FeedItem]
    total: int


class SellerOut(BaseModel):
    id: UUID
    name: str


class ProductDetailResponse(BaseModel):
    id: int
    title: str
    description: str | None
    price: float
    seller: SellerOut
    status: str


class LikeResponse(BaseModel):
    is_liked: bool
