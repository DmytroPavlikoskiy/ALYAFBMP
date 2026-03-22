import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # --- Основні налаштування ---
    PROJECT_NAME: str = "Marketplace MVP"
    DEBUG: bool = False
    
    # --- Налаштування Бази Даних ---
    # Приклад: postgresql+asyncpg://user:password@localhost:5432/db_name
    DATABASE_URL: str = Field(alias="DATABASE_URL")
    
    # --- Налаштування JWT (Група 1) ---
    JWT_SECRET: str = Field(alias="JWT_SECRET")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # --- Налаштування Telegram (Група 5) ---
    TG_BOT_TOKEN: str = Field(alias="TG_BOT_TOKEN")
    TG_CHANNEL_ID: str = Field(alias="TG_CHANNEL_ID")
    
    # --- Налаштування Redis для Celery (Група 6) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # Автоматичне зчитування з .env файлу
    model_config = SettingsConfigDict(env_file=".env_dev", extra="ignore")

# Створюємо екземпляр налаштувань для використання в усьому проекті
settings = Settings()