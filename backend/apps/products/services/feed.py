"""
Логіка Smart Feed: спочатку товари з обраних категорій, потім інші.
"""
from __future__ import annotations

import uuid
from typing import Any
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from common.models import UserPreference, Product, User, Category, ProductImage
from sqlalchemy import select, func, case, and_
from sqlalchemy.orm import selectinload, joinedload


async def fetch_smart_feed(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    page: int,
    limit: int,
    category_id: int | None,
    search: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> tuple[list[dict[str, Any]], int]:
    
    """ 
    
    Збираємо дані за пріорітетом користувача,
    одразу беремо через звязки дані про користувача,
    категорії, картики товару, для запобігання N+1 запитів.

    """
    
    pref_user_cat_ids = []
    if user_id:
        pref_stmt = select(UserPreference.category_id).where(UserPreference.user_id == user_id)
        pref_res = await db.execute(pref_stmt)
        pref_user_cat_ids = pref_res.scalars().all()
    
    base_filter = Product.status.in_(["APPROVE", "ACTIVE"])
    if category_id:
        base_filter = and_(base_filter, Product.category_id == category_id)
    if search:
        base_filter = and_(base_filter, Product.title.ilike(f"%{search}%"))
    if min_price is not None:
        base_filter = and_(base_filter, Product.price >= min_price)
    if max_price is not None:
        base_filter = and_(base_filter, Product.price <= max_price)

    priority_col = case(
        (Product.category_id.in_(pref_user_cat_ids), 1),
        else_=2
    ).label("is_priority")

    stmt = (
        select(Product, priority_col)
        .options(
            joinedload(Product.seller),
            joinedload(Product.category),
            selectinload(Product.images)
        )
        .where(base_filter)
        .order_by(priority_col, Product.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    
    count_stmt = select(func.count()).select_from(Product).where(base_filter)

    result, total_result = await asyncio.gather(
        db.execute(stmt),
        db.execute(count_stmt)
    )

    products_with_priority = result.unique().all()
    total = total_result.scalar() or 0

    feed_items = []
    for product, is_priority in products_with_priority:
        feed_items.append({
            "id": product.id,
            "title": product.title,
            "price": float(product.price),
            "status": product.status,
            "is_priority": is_priority == 1,
            "category": {
                "id": product.category_id,
                "name": product.category.name if product.category else "Без категорії"
            },
            "seller": {
                "id": product.seller.id,
                "first_name": product.seller.first_name,
                "avatar_url": product.seller.avatar_url,
            },
            "images": [img.image_url for img in product.images],
            "created_at": product.created_at.isoformat() if product.created_at else None,
        })

    return feed_items, total
