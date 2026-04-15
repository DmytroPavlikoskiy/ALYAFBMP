"""
Точка входу FastAPI.

Запуск з каталогу backend:
  uvicorn main:app --reload
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

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


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request and response for tracing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(parents=False, exist_ok=True)

_cors_origins = settings.cors_origins_list
# allow_credentials=True is incompatible with wildcard origins per the CORS spec.
# When origins is ["*"] (dev default), disable credentials so browsers won't reject responses.
_allow_credentials = "*" not in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
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
