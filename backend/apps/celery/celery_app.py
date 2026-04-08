import asyncio
import sys
import os
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import delete

# Піднімаємося на два рівні вгору, щоб дістатися до папки backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from common.database import AsyncSessionLocal
from apps.users.models import BanList

# Створюємо екземпляр Celery
celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Налаштування часового поясу (важливо для crontab)
celery_app.conf.timezone = 'Europe/Kyiv' # Або UTC
celery_app.conf.broker_connection_retry_on_startup = True

async def delete_expired_bans_logic():
    """Асинхронна логіка видалення"""
    print(f"[{datetime.now()}] Starting ban cleanup process...")
    async with AsyncSessionLocal() as session:
        try:
            # Обчислюємо межу: все, що було до "зараз мінус 3 дні"
            threshold_date = datetime.now() - timedelta(days=3)
            
            # Створюємо запит на видалення
            stmt = delete(BanList).where(BanList.start_ban_date <= threshold_date)
            
            result = await session.execute(stmt)
            await session.commit()
            print(f"[{datetime.now()}] Deleted {result.rowcount} expired bans.")
        except Exception as e:
            await session.rollback()
            print(f"[{datetime.now()}] Error during ban cleanup: {e}")
            raise e

@celery_app.task(name="check_and_remove_bans")
def check_and_remove_bans():
    """
    Синхронна обгортка для Celery.
    Використовуємо новий event loop, щоб уникнути конфліктів.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Якщо ми в середовищі, де loop вже запущено
        asyncio.ensure_future(delete_expired_bans_logic())
    else:
        loop.run_until_complete(delete_expired_bans_logic())

# Налаштування розкладу
celery_app.conf.beat_schedule = {
    "remove-old-bans-daily": {
        "task": "check_and_remove_bans",
        "schedule": crontab(minute=1), # Кожну хвилину
        # Для тесту можна поставити: 'schedule': timedelta(seconds=30),
    },
}

#celery -A apps.celery.celery_app.celery_app worker --loglevel=info
#celery -A apps.celery.celery_app.celery_app beat --loglevel=info