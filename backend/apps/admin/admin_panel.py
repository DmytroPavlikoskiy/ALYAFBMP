"""
Веб-інтерфейс SQLAdmin для перегляду/редагування таблиць у БД.
Підключається лише в FastAPI (main.py); бот сюди не імпортується.
"""
from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqladmin import Admin, ModelView

from common.models import (
    Category,
    Chat,
    Message,
    Notification,
    Order,
    Product,
    ProductImage,
    User,
    UserPreference,
    Wishlist,
)
from config import settings

# ---------------------------------------------------------------------------
# Користувачі
# ---------------------------------------------------------------------------


class UserAdmin(ModelView, model=User):
    name = "Користувач"
    name_plural = "Користувачі"
    icon = "fa fa-user"
    column_list = [
        "id",
        "email",
        "first_name",
        "role",
        "is_banned",
        "banned_until",
        "created_at",
    ]
    column_searchable_list = ["email", "first_name", "last_name"]
    column_sortable_list = ["email", "created_at", "banned_until"]
    can_delete = False
    # password_hash навмисно не в формі — зміна пароля через API / окремий скрипт
    form_columns = [
        "email",
        "first_name",
        "last_name",
        "phone",
        "role",
        "avatar_url",
        "tg_chat_id",
        "banned_until",
        "ban_reason",
        "is_banned",
    ]


# ---------------------------------------------------------------------------
# Каталог і товари
# ---------------------------------------------------------------------------


class CategoryAdmin(ModelView, model=Category):
    name = "Категорія"
    name_plural = "Категорії"
    icon = "fa fa-tags"
    column_list = ["id", "name", "icon_url"]
    column_searchable_list = ["name"]
    form_columns = ["name", "icon_url"]


class ProductAdmin(ModelView, model=Product):
    name = "Товар"
    name_plural = "Товари"
    icon = "fa fa-box"
    column_list = [
        "id",
        "title",
        "price",
        "status",
        "seller_id",
        "category_id",
        "created_at",
        "updated_at",
    ]
    column_searchable_list = ["title"]
    column_sortable_list = ["id", "price", "created_at", "status"]
    column_filters = ["status"]
    form_columns = [
        "title",
        "description",
        "price",
        "status",
        "seller_id",
        "category_id",
    ]
    can_create = True
    can_delete = True


class ProductImageAdmin(ModelView, model=ProductImage):
    name = "Зображення товару"
    name_plural = "Зображення товарів"
    icon = "fa fa-image"
    column_list = ["id", "product_id", "image_url"]
    column_searchable_list = ["image_url"]
    form_columns = ["product_id", "image_url"]


# ---------------------------------------------------------------------------
# Профіль і взаємодія
# ---------------------------------------------------------------------------


class UserPreferenceAdmin(ModelView, model=UserPreference):
    name = "Уподобання (категорії)"
    name_plural = "Уподобання користувачів"
    icon = "fa fa-heart"
    column_list = ["user_id", "category_id"]
    form_columns = ["user_id", "category_id"]
    can_delete = True


class WishlistAdmin(ModelView, model=Wishlist):
    name = "Вибране"
    name_plural = "Вибране"
    icon = "fa fa-star"
    column_list = ["user_id", "product_id"]
    form_columns = ["user_id", "product_id"]


class OrderAdmin(ModelView, model=Order):
    name = "Замовлення"
    name_plural = "Замовлення"
    icon = "fa fa-shopping-cart"
    column_list = ["id", "buyer_id", "product_id", "status", "created_at"]
    column_sortable_list = ["id", "created_at", "status"]
    column_filters = ["status"]
    form_columns = ["buyer_id", "product_id", "status"]
    can_delete = False


class NotificationAdmin(ModelView, model=Notification):
    name = "Сповіщення"
    name_plural = "Сповіщення"
    icon = "fa fa-bell"
    column_list = ["id", "user_id", "type", "is_read", "created_at"]
    column_sortable_list = ["id", "created_at", "is_read"]
    column_filters = ["type", "is_read"]
    form_columns = ["user_id", "text_notification", "type", "is_read"]
    column_searchable_list = ["text_notification"]


class ChatAdmin(ModelView, model=Chat):
    name = "Чат"
    name_plural = "Чати"
    icon = "fa fa-comments"
    column_list = ["id", "product_id", "buyer_id", "seller_id", "created_at"]
    column_sortable_list = ["created_at"]
    form_columns = ["product_id", "buyer_id", "seller_id"]


class MessageAdmin(ModelView, model=Message):
    name = "Повідомлення"
    name_plural = "Повідомлення"
    icon = "fa fa-comment"
    column_list = ["id", "chat_id", "sender_id", "sent_at"]
    column_sortable_list = ["id", "sent_at"]
    form_columns = ["chat_id", "sender_id", "text_msg"]
    column_searchable_list = ["text_msg"]


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
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(ProductImageAdmin)
    admin.add_view(UserPreferenceAdmin)
    admin.add_view(WishlistAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(NotificationAdmin)
    admin.add_view(ChatAdmin)
    admin.add_view(MessageAdmin)

    return admin
