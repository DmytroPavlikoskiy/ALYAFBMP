"""
Веб-інтерфейс SQLAdmin для перегляду/редагування таблиць у БД.
Підключається лише в FastAPI (main.py); бот сюди не імпортується.

Студенти: додайте ModelView для Product, Notification тощо за зразком UserAdmin нижче.
"""
from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqladmin import Admin, ModelView

from common.models import User
from config import settings

# ---------------------------------------------------------------------------
# Робочий приклад: одна модель (User)
# ---------------------------------------------------------------------------


class UserAdmin(ModelView, model=User):
    name = "Користувач"
    name_plural = "Користувачі"
    icon = "fa fa-user"
    column_list = ["id", "email", "first_name", "role", "created_at"]
    column_searchable_list = ["email", "first_name"]
    can_delete = False
    form_columns = [
        "email",
        "first_name",
        "last_name",
        "phone",
        "role",
        "tg_chat_id",
        "banned_until",
        "ban_reason",
    ]


# ---------------------------------------------------------------------------
# ПСЕВДОКОД ДЛЯ СТУДЕНТІВ (не підключати, доки не реалізуєте)
# ---------------------------------------------------------------------------
#
# from common.models import Product
#
# class ProductAdmin(ModelView, model=Product):
#     """
#     1. column_list: id, title, price, status, seller_id, category_id, created_at
#     2. column_filters: status (PENDING / APPROVE / …)
#     3. form_columns: title, description, price, status
#     4. can_create / can_delete — за політикою курсу
#     """
#     ...
#
# class BanOrModerationView(ModelView, model=User):
#     """
#     Варіант «Bans»: фільтрувати користувачів з banned_until.is_not(None) через
#     custom list query або окрему таблицю, якщо з’явиться в міграціях.
#     """
#     ...
#
# У функції mount_sqladmin нижче після add_view(UserAdmin):
#     admin.add_view(ProductAdmin)
# ---------------------------------------------------------------------------


def _create_sync_engine():
    """Окремий sync-двигун для SQLAdmin (asyncpg не потрібен)."""
    return create_engine(
        settings.sync_database_url,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )


def mount_sqladmin(app: FastAPI) -> Admin:
    """
    Монтує SQLAdmin (типово URL: /admin).
    Не імпортуйте цей модуль з apps.bot.*
    """
    engine = _create_sync_engine()
    admin = Admin(
        app,
        engine,
        title=f"{settings.PROJECT_NAME} — SQLAdmin",
        base_url="/admin",
    )
    admin.add_view(UserAdmin)
    return admin
