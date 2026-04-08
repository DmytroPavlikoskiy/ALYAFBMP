"""
Застарілий модуль: логіка перенесена в `apps.products.services.feed`.
Залишено для зворотної сумісності зі старими гілками студентів.
"""
from apps.products.services.feed import fetch_smart_feed

__all__ = ["fetch_smart_feed"]
