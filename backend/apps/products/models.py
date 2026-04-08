"""
Реекспорт ORM з `common.models` для зворотної сумісності з імпортами `apps.products.models`.
"""
from common.models import (
    Category,
    Order,
    Product,
    ProductImage,
    UserPreference,
    Wishlist,
)

# Старі назви класів у частині студентського коду
Products = Product
ProductImages = ProductImage

__all__ = [
    "Category",
    "Order",
    "Product",
    "Products",
    "ProductImage",
    "ProductImages",
    "UserPreference",
    "Wishlist",
]
