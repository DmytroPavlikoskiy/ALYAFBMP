"""
Централізовані налаштування застосунку (pydantic-settings).
Значення зчитуються з змінних середовища та файлів .env
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Професійний клас налаштувань для FastAPI, Celery та Telegram-бота.
    У продакшені обов’язково задайте секрети через змінні середовища або .env (не комітьте секрети).
    """

    # --- Загальне ---
    PROJECT_NAME: str = Field(default="Marketplace MVP", description="Назва для OpenAPI / логів")
    DEBUG: bool = Field(default=False, description="Режим дебагу (детальніші логи SQL тощо)")

    # --- PostgreSQL (asyncpg через SQLAlchemy URL) ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:1111@127.0.0.1:5432/marketplace",
        description="Рядок підключення async (postgresql+asyncpg://...)",
    )

    # --- Redis (Celery, pub/sub модерації, кеш JWT бота) ---
    REDIS_URL: str = Field(
        default="redis://127.0.0.1:6379/0",
        description="URL Redis для async-клієнта та Celery broker",
    )

    # --- HTTP (Telegram-бот -> FastAPI; без слеша в кінці) ---
    API_BASE_URL: str = Field(
        default="http://127.0.0.1:8000",
        description="Базовий URL API для httpx у боті (scheme://host:port)",
    )

    # --- Telegram (бот модерації та клієнтський бот) ---
    BOT_TOKEN: str = Field(
        default="000000000:placeholder-replace-in-env",
        validation_alias=AliasChoices("BOT_TOKEN", "TG_BOT_TOKEN"),
        description="Токен BotFather; env може бути BOT_TOKEN або TG_BOT_TOKEN",
    )
    ADMIN_ID: int = Field(
        default=0,
        description="Telegram user id адміністратора (для розсилки карток модерації); 0 = не задано",
    )

    # --- JWT (REST API) ---
    JWT_SECRET: str = Field(
        default="dev-only-change-me-in-production",
        description="Секрет підпису access/refresh JWT",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Час життя refresh token, для перегенерації access_token"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Додатково (інтеграції) ---
    TG_CHANNEL_ID: str = Field(default="0", description="ID каналу Telegram (рядок)")
    BOT_SECRET: str = Field(
        default="dev-bot-secret",
        description="Секрет для викликів бот → internal API (заголовок X-Bot-Secret)",
    )

    # --- CORS ---
    CORS_ORIGINS: str = Field(
        default="*",
        description="Список origin через кому або * для розробки",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", ".env_dev"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Список дозволених origin для CORSMiddleware."""
        raw = self.CORS_ORIGINS.strip()
        if raw == "*":
            return ["*"]
        return [part.strip() for part in raw.split(",") if part.strip()]

    @property
    def sync_database_url(self) -> str:
        """
        Рядок підключення для sync-драйвера (SQLAdmin, скрипти).
        asyncpg замінюється на postgresql:// (очікується psycopg2 у середовищі).
        """
        url = self.DATABASE_URL
        if "postgresql+asyncpg://" in url:
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Кешований singleton налаштувань (зручно для тестів та імпортів)."""
    return Settings()


# Зворотна сумісність з існуючим кодом: `from config import settings`
settings = get_settings()
