"""
Пакет лише для SQLAdmin (веб-адмінка БД).
REST-модерація винесена в apps.moderation.
"""

from apps.admin.admin_panel import mount_sqladmin

__all__ = ["mount_sqladmin"]
