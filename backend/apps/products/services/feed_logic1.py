from datetime import datetime
from typing import List, Dict


def get_smart_feed(all_products: Dict, user_preferences: List):
    """Приймає продукти та вподобання юзера, сортує: спочатку уподобання(за часом), потім всі інші продукти"""
    priority_products = []
    other_products = []

    for product in all_products:
        if product['category_id'] in user_preferences:
            priority_products.append(product)
        else:
            other_products.append(product)

    priority_products.sort(key=lambda x: datetime.strptime(x['created_at'], '%Y-%m-%d'), reverse=True)
    other_products.sort(key=lambda x: datetime.strptime(x['created_at'], '%Y-%m-%d'), reverse=True)

    return priority_products + other_products