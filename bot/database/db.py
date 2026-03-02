from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from bot.config import DATABASE_URL
import asyncpg

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Базовый класс для моделей
Base = declarative_base()

# Фабрика сессий
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Инициализация базы данных (создание таблиц)
async def init_db():
    from bot.database.models import User, Admin, Referral  # убрал ReferralUser и ReferralLink
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Пул подключений через asyncpg (необязательный, но можно использовать)
async def get_pool():
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        return pool
    except Exception as e:
        print(f"Ошибка создания пула подключений: {e}")
        return None
