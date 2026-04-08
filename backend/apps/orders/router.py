from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.orders.schemas import OrderCreateBody, OrderCreatedResponse
from common.database import get_db
from common.deps import get_current_user_id

router = APIRouter()


@router.post("/", status_code=201, response_model=OrderCreatedResponse)
async def create_order(
    body: OrderCreateBody,
    db: AsyncSession = Depends(get_db),
    buyer_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    POST /api/v1/orders

    1. Перевір, що product існує і статус дозволяє покупку.
    2. Створи Order(buyer_id=buyer_id, product_id=..., status='CREATED').
    3. commit; поверни order_id.

    Роутер змонтовано з префіксом /orders -> шлях "" дає POST /api/v1/orders.
    """
    raise HTTPException(status_code=501, detail="Група 6: реалізуйте замовлення.")
