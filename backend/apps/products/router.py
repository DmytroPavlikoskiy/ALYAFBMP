from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from typing import Any

from apps.products.schemas import (
    CategoryOut,
    FeedResponse,
    LikeResponse,
    ProductCreatedResponse,
    ProductDetailResponse,
)
from apps.moderation.deps import verify_bot_secret
from apps.products.services.feed import fetch_smart_feed
from common.database import get_db
from common.deps import get_current_user_id, get_current_user_id_optional
from common.models import Product, User, Category, ProductImage
from common.models import User
from datetime import datetime, timezone, timedelta
from apps.products.schemas import SellerOut, ProductDetailResponse


router = APIRouter()


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """
    GET /api/v1/categories

    1. Виконай select(Category) через await session.execute(select(Category).order_by(Category.id)).
    2. Поверни список CategoryOut (id, name, icon_url).
    """
    raise HTTPException(status_code=501, detail="Група 2: реалізуйте список категорій (SQLAlchemy 2.0 select).")


@router.get("/products/feed", response_model=FeedResponse)
async def product_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id_optional),
):
    """
    GET /api/v1/products/feed

    1. Виклич fetch_smart_feed(db, user_id=user_id, page=page, limit=limit, category_id=category_id).
    2. Збери FeedResponse(items=..., total=...).
    """
    feed_items, total = await fetch_smart_feed(
        db, user_id=user_id, page=page, limit=limit, category_id=category_id
    )
    return FeedResponse(feed_items=feed_items, total=total)


@router.patch("/products/{product_id}/approve")
async def approve_product_via_bot(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_bot_secret),
):
    """
    PATCH /api/v1/products/{id}/approve — виклик з Telegram-бота (httpx), не з БД в боті.

    1. Перевір product_id; онови Product.status на APPROVE (або ACTIVE за контрактом).
    2. commit.
    3. Поверни {"ok": true}.

    Заголовок X-Bot-Secret обов'язковий (verify_bot_secret).
    """
    product = await db.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Товар не знайдено")
    
    try:
        if product:
            product.status = "APPROVE"
            now = datetime.now(timezone.utc)
            product.updated_at = now
            await db.commit()
            return {"ok": True}
    except Exception as ex:
        print(ex)
        await db.rollback()
        return {"ok": False, 'error': str(ex)}


@router.patch("/products/{product_id}/reject")
async def reject_product_via_bot(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_bot_secret),
):
    try:
        # 1. Пошук продукту (використовуємо await db.get для швидкості)
        product = await db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # 2. Оновлюємо статус продукту
        product.status = "REJECTED"
        product.updated_at = datetime.now(timezone.utc)

        # 3. Логіка бану
        ban_duration = timedelta(days=3)
        now = datetime.now(timezone.utc)
        unban_date = now + ban_duration

        # 4. Пошук продавця (User)
        seller = await db.get(User, product.seller_id)
        if seller:
            seller.is_banned = True  
            seller.banned_until = unban_date

        # 5. Збереження
        await db.commit()
        
        # Освіжаємо об'єкт, щоб повернути актуальні дані
        await db.refresh(product)

        return {
            "ok": True,
            "message": "Product rejected and seller banned for 3 days",
            "product_id": product.id,
            "banned_until": unban_date
        }

    except Exception as e:
        await db.rollback()
        print(f"Помилка при відхиленні: {e}")
        return {"ok": False, "error": str(e)}



@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def product_detail(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/v1/products/{id}

    1. select(Product).where(Product.id == product_id).options(selectinload(Product.seller)).
    2. Якщо не знайдено -> 404.
    3. Побудуй SellerOut з іменем продавця (first_name + last_name).
    4. Поверни ProductDetailResponse; поле status узгодьте з БД (PENDING / APPROVE / REJECTED).
    """
    stmt_prod = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            joinedload(Product.seller),
            joinedload(Product.category),
            selectinload(Product.images)
        )
    )
    
    result = await db.execute(stmt_prod)

    product = result.unique().scalar_one_or_none()

    # 2. Если не найдено → 404
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    last_name = product.seller.last_name or ""
    full_name = f"{product.seller.first_name} {last_name}".strip()

    seller_out = SellerOut(
        id=product.seller.id,
        full_name=full_name,
        avatar_url=product.seller.avatar_url
    )

    
    return ProductDetailResponse(
        id=product.id,
        title=product.title,
        description=product.description,
        price=float(product.price),
        status=product.status,
        created_at=product.created_at,
        category_name=product.category.name if product.category else "Без категорії",
        images=[img.image_url for img in product.images], # Витягуємо лише URL
        seller=seller_out
    )


@router.post("/products", status_code=201, response_model=ProductCreatedResponse)
async def create_product(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str | None = Form(None),
    price: float = Form(...),
    category_id: int | None = Form(None),
    images: list[UploadFile] = File(default_factory=list),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Створення оголошення з multipart/form-data (файли + поля форми).
    Контракт також описує JSON з images як URL — можна додати окремий ендпоінт або прапорець пізніше.

    1. Перевір, що користувач не забанений: подивись User.banned_until (логіка в сервісі бану).
    2. Створи Product(seller_id=user_id, title=..., price=..., status='PENDING', ...).
    3. Для кожного UploadFile у images:
       - прочитай байти: content = await file.read() (лише в цьому async-обробнику).
       - збережи файл на диск: наприклад static/products/{product_id}_{safe_filename}.
       - створи ProductImage(product_id=..., image_url=URL_або_шлях).
    4. await session.commit(); отримай product.id.
    5. У фонову задачу передай лише серіалізовані дані (id, title, price, список шляхів до зображень):
       background_tasks.add_task(..., product_id, title, price, saved_paths, str(user_id)).
    6. У функції фону виклич publish_new_product_to_moderation(await get_redis(), ...) або redis.publish.

    ВАЖЛИВО: не передавай об'єкт UploadFile у BackgroundTasks.

    Зараз: логіка не реалізована — піднімаємо 501, щоб студенти заповнили кроки.
    """
    raise HTTPException(
        status_code=501,
        detail="Група 4: реалізуйте збереження файлів у static/ та створення Product згідно docstring.",
    )


@router.post("/products/{product_id}/like", response_model=LikeResponse)
async def toggle_like(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    POST /api/v1/products/{id}/like

    1. Перевір наявність рядка в wishlist (user_id, product_id).
    2. Якщо є — видали (toggle off), якщо немає — додай (toggle on).
    3. Поверни LikeResponse(is_liked=True/False).
    """
    raise HTTPException(status_code=501, detail="Група 4: реалізуйте wishlist.")
