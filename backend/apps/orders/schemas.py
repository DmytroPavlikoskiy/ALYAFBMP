from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class OrderCreateBody(BaseModel):
    product_id: int


class OrderCreatedResponse(BaseModel):
    order_id: int


class OrderDetailResponse(BaseModel):
    id: int
    product_id: int
    buyer_id: uuid.UUID
    status: str
    created_at: datetime | None

    model_config = {"from_attributes": True}
