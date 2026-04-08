"""
Точка входу FastAPI.

Запуск з каталогу backend:
  uvicorn main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apps.admin.admin_panel import mount_sqladmin
from apps.auth.router import router as auth_router
from apps.communication.router import router as communication_router
from apps.moderation.router import router as moderation_router
from apps.orders.router import router as orders_router
from apps.products.router import router as products_router
from apps.users.router import router as users_router
from common.redis_client import close_redis, init_redis
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Старт: Redis PING.
    Каталоги static/ створюються до app.mount (нижче).
    Завершення: закриття Redis.
    """
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_root = Path(__file__).resolve().parent / "static"
static_root.mkdir(parents=True, exist_ok=True)
(static_root / "products").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

mount_sqladmin(app)

api_prefix = "/api/v1"
app.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{api_prefix}/users", tags=["users"])
app.include_router(products_router, prefix=api_prefix, tags=["products"])
app.include_router(orders_router, prefix=f"{api_prefix}/orders", tags=["orders"])
app.include_router(moderation_router, prefix=f"{api_prefix}/moderation", tags=["moderation"])
app.include_router(communication_router, prefix=api_prefix, tags=["communication"])


@app.get("/health")
async def health():
    """Перевірка доступності процесу (без звернення до БД)."""
    return {"status": "ok", "project": settings.PROJECT_NAME, "debug": settings.DEBUG}
