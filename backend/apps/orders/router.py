from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.orders.schemas import OrderCreateBody, OrderCreatedResponse
from common.database import get_db
from common.deps import get_current_user_id

from backend.common.models import Product, Order

router = APIRouter()


@router.post("/", status_code=201, response_model=OrderCreatedResponse)
async def create_order(
    body: OrderCreateBody,
    db: AsyncSession = Depends(get_db),
    buyer_id: uuid.UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Product).where(Product.id == body.product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Product not available")

    new_order = Order(
        buyer_id=buyer_id,
        product_id=product.id,
        status="CREATED"
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    return OrderCreatedResponse(order_id=new_order.id)