from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from typing import List


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


# -----------------------------------------------------------------------
# Feed
# -----------------------------------------------------------------------

class FeedCategoryInfo(BaseModel):
    id: int | None
    name: str


class FeedSellerInfo(BaseModel):
    id: UUID
    first_name: str
    avatar_url: str | None


class FeedItem(BaseModel):
    id: int
    title: str
    price: float
    status: str
    is_priority: bool
    category: FeedCategoryInfo | None = None
    seller: FeedSellerInfo
    images: list[str] = Field(default_factory=list)
    created_at: str | None = None


class FeedResponse(BaseModel):
    feed_items: list[FeedItem]
    total: int


# -----------------------------------------------------------------------
# Product detail
# -----------------------------------------------------------------------

class SellerOut(BaseModel):
    id: UUID
    full_name: str
    avatar_url: str | None = None


class ProductDetailResponse(BaseModel):
    id: int
    title: str
    description: str | None
    price: float
    seller: SellerOut
    status: str
    created_at: datetime.datetime | None = None
    category_name: str | None = None
    images: list[str] = Field(default_factory=list)


class LikeResponse(BaseModel):
    is_liked: bool


class ProductsListLike(BaseModel):
    product: ProductDetailResponse
    is_like: bool


class ProductsListLikeResponse(BaseModel):
    products: List[ProductsListLike]
