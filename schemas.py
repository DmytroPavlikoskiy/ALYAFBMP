from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class OrderCreate(BaseModel):
    product_id: int

class ProductShort(BaseModel):
    id: int
    title: str
    price: float

class OrderRead(BaseModel):
    id: int
    product_id: int
    status: str
    created_at: datetime
    product: ProductShort