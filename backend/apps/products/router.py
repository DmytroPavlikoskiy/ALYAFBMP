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
from pathlib import Path
import aiofiles
from apps.moderation.deps import verify_bot_secret
from apps.products.services.feed import fetch_smart_feed
from common.database import get_db
from common.redis_client import get_redis
from common.redis_client import get_redis
from common.deps import get_current_user_id, get_current_user_id_optional, verify_user_not_banned
from common.rate_limit import rate_limit
from common.models import Product, User, Category, ProductImage, Wishlist
from datetime import datetime, timezone, timedelta
from apps.products.schemas import (SellerOut, ProductDetailResponse,
                                   ProductsListLikeResponse, ProductsListLike)
from apps.products.services.moderation_redis import (
    clear_moderation_delivery_tracking,
    publish_new_product_to_moderation,
)

router = APIRouter()

UPLOAD_DIR = Path("static/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


#Тимофій
@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """GET /api/v1/categories — full list of marketplace categories."""
    result = await db.execute(select(Category).order_by(Category.id))
    return result.scalars().all()


#Настя
@router.get("/products/feed", response_model=FeedResponse)
async def product_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None),
    search: str | None = Query(None, description="Full-text search in product title"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id_optional),
):
    """GET /api/v1/products/feed — smart personalised feed with optional filters."""
    feed_items, total = await fetch_smart_feed(
        db,
        user_id=user_id,
        page=page,
        limit=limit,
        category_id=category_id,
        search=search,
        min_price=min_price,
        max_price=max_price,
    )
    return FeedResponse(feed_items=feed_items, total=total)

#Марта
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
            redis_conn = await get_redis()
            await clear_moderation_delivery_tracking(redis_conn, product_id)
            return {"ok": True}
    except Exception as ex:
        print(ex)
        await db.rollback()
        return {"ok": False, 'error': str(ex)}


#Марта
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
            seller.ban_reason = "Listing rejected by moderation (3-day posting restriction)"

        # 5. Збереження
        await db.commit()

        redis_conn = await get_redis()
        await clear_moderation_delivery_tracking(redis_conn, product_id)

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


#Марта
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


#Матвій
async def moderation_wrapper(product_id, title, price, image_urls, seller_id):
    redis_conn = await get_redis()
    await publish_new_product_to_moderation(
        redis=redis_conn,
        product_id=product_id,
        title=title,
        price=price,
        image_urls=image_urls,
        seller_id=str(seller_id),
    )


_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


#Женя Ліщук
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
    _ban: None = Depends(verify_user_not_banned),
    _rl: None = Depends(rate_limit(max_requests=20, window_seconds=3600)),
):
    """
    POST /api/v1/products — create a new listing (multipart/form-data).

    Ban guard: verify_user_not_banned runs before this handler.  It reuses
    the User object already fetched by get_current_user (zero extra DB query).
    Only PENDING products are created here; approval happens via the bot.
    """
    new_product = Product(
        seller_id=user_id,
        title=title,
        description=description,
        price=price,
        category_id=category_id,
        status="PENDING"
    )
    db.add(new_product)
    await db.flush()

    image_urls = []

    for file in images:
        # Validate MIME type
        if file.content_type not in _ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported image type '{file.content_type}'. Allowed: JPEG, PNG, WebP.",
            )

        content = await file.read()

        # Validate file size
        if len(content) > _MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Image '{file.filename}' exceeds 5 MB limit.",
            )

        file_ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
        safe_filename = f"{new_product.id}_{uuid.uuid4().hex}{file_ext}"
        file_path = UPLOAD_DIR / safe_filename

        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(content)

        relate_path = str(f"{UPLOAD_DIR}/{safe_filename}")
        image_urls.append(relate_path)

        new_image = ProductImage(
            product_id=new_product.id,
            image_url=relate_path,
        )
        db.add(new_image)
    
    try:
        await db.commit()
        await db.refresh(new_product)
    except Exception as ex:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Помилка збереження даних")

    background_tasks.add_task(moderation_wrapper, new_product.id, title, float(price), image_urls, user_id)
    
    return ProductCreatedResponse(id=new_product.id, status=new_product.status)


#Настя
@router.get("/products_list/likes", response_model=ProductsListLikeResponse)
async def products_like_list(
    user_id: uuid.UUID = Depends(get_current_user_id), 
    db: AsyncSession = Depends(get_db)
):
    # 1. Запит до БД: тягнемо Wishlist -> Product -> Seller
    stmt = (
        select(Wishlist)
        .where(Wishlist.user_id == user_id)
        .options(
            selectinload(Wishlist.product).options(
                joinedload(Product.seller),
                selectinload(Product.images),
            )
        )
    )
    
    result = await db.execute(stmt)
    # Отримуємо всі об'єкти Wishlist
    wishlist_items = result.scalars().all()

    products_out = []
    for item in wishlist_items:
        p = item.product
        
        # Створюємо SellerOut
        seller_info = SellerOut(
            id=p.seller.id,
            full_name=f"{p.seller.first_name} {p.seller.last_name or ''}".strip(),
            avatar_url=p.seller.avatar_url
        )

        # Створюємо ProductDetailResponse
        product_detail = ProductDetailResponse(
            id=p.id,
            title=p.title,
            description=p.description,
            price=float(p.price),
            seller=seller_info,
            status=p.status,
            images=[img.image_url for img in (p.images or [])],
        )

        # Додаємо у фінальний список згідно з твоєю структурою ProductsListLike
        products_out.append(
            ProductsListLike(
                product=product_detail,
                is_like=True
            )
        )

    return ProductsListLikeResponse(products=products_out)


#Настя
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

    check_query = select(Wishlist).where(
        Wishlist.user_id == user_id,
        Wishlist.product_id == product_id
    )
    result = await db.execute(check_query)
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        is_liked = False
    else:
        product_obj = await db.get(Product, product_id)
        if not product_obj:
            raise HTTPException(status_code=404, detail="Product not found")

        new_wish = Wishlist(user_id=user_id, product_id=product_id)
        db.add(new_wish)
        is_liked = True
    try:
        await db.commit()
        return LikeResponse(is_liked=is_liked)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
