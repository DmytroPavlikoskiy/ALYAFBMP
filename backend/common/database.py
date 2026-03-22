from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

# 1. Створюємо асинхронний двигун (Engine)
# Future=True дозволяє використовувати синтаксис SQLAlchemy 2.0
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Логування SQL запитів у консоль (тільки в дебаг режимі)
    future=True
)

# 2. Фабрика сесій
# expire_on_commit=False потрібно для асинхронної роботи
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3. Базовий клас для всіх моделей (Групи будуть наслідуватися від нього)
class Base(DeclarativeBase):
    pass

# 4. Depends метод для FastAPI роутерів
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()