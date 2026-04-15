from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.orders.schemas import OrderCreateBody, OrderCreatedResponse, OrderDetailResponse
from common.database import get_db
from common.deps import get_current_user_id
from common.models import Order, Product

logger = logging.getLogger(__name__)
router = APIRouter()

# Allowed status transitions
_TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"CANCELLED"},
    "CANCELLED": set(),
}

#Марк Кондрацький

@router.post("/", status_code=201, response_model=OrderCreatedResponse)
async def create_order(
    body: OrderCreateBody,
    db: AsyncSession = Depends(get_db),
    buyer_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    POST /api/v1/orders — place an order for an approved product.
    Uses SELECT FOR UPDATE to prevent race conditions between two buyers.
    Sets product status to RESERVED to block further orders.
    """
    result = await db.execute(
        select(Product)
        .where(Product.id == body.product_id, Product.status == "APPROVE")
        .with_for_update()
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found or not available for ordering",
        )

    if product.seller_id == buyer_id:
        raise HTTPException(status_code=400, detail="Cannot order your own product")

    existing = await db.execute(
        select(Order).where(
            Order.buyer_id == buyer_id,
            Order.product_id == body.product_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Order already exists")

    product.status = "RESERVED"
    new_order = Order(
        buyer_id=buyer_id,
        product_id=product.id,
        status="CREATED",
    )
    db.add(new_order)

    try:
        await db.commit()
        await db.refresh(new_order)
    except Exception as exc:
        logger.error("Order creation error: %s", exc)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create order")

    # Fire-and-forget: notify the seller via Celery
    try:
        from apps.celery.celery_app import notify_seller_new_order
        notify_seller_new_order.delay(new_order.id, str(product.seller_id))
    except Exception as exc:
        logger.warning("Could not enqueue seller notification: %s", exc)

    return OrderCreatedResponse(order_id=new_order.id)


@router.get("/", response_model=list[OrderDetailResponse])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    buyer_id: uuid.UUID = Depends(get_current_user_id),
):
    """GET /api/v1/orders — order history for the authenticated buyer."""
    result = await db.execute(
        select(Order)
        .where(Order.buyer_id == buyer_id)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    buyer_id: uuid.UUID = Depends(get_current_user_id),
):
    """GET /api/v1/orders/{id} — single order detail (buyer only)."""
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != buyer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return order


@router.patch("/{order_id}/confirm", response_model=OrderDetailResponse)
async def confirm_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    buyer_id: uuid.UUID = Depends(get_current_user_id),
):
    """PATCH /api/v1/orders/{id}/confirm — buyer confirms receipt; product → SOLD."""
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != buyer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if "CONFIRMED" not in _TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot confirm an order with status '{order.status}'",
        )

    order.status = "CONFIRMED"
    product = await db.get(Product, order.product_id)
    if product:
        product.status = "SOLD"

    await db.commit()
    await db.refresh(order)
    return order


@router.patch("/{order_id}/cancel", response_model=OrderDetailResponse)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    buyer_id: uuid.UUID = Depends(get_current_user_id),
):
    """PATCH /api/v1/orders/{id}/cancel — cancel an order; product reverts to APPROVE."""
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != buyer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if "CANCELLED" not in _TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel an order with status '{order.status}'",
        )

    order.status = "CANCELLED"
    product = await db.get(Product, order.product_id)
    if product and product.status == "RESERVED":
        product.status = "APPROVE"

    await db.commit()
    await db.refresh(order)
    return order
