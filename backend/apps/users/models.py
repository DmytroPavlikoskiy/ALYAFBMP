"""
ORM для користувача: реекспорт з `common.models` (єдине джерело таблиць).
"""
from common.models import User

__all__ = ["User"]
