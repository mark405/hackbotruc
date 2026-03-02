from bot.database.db import Base, engine
from bot.database.models import User, Admin, Referral, ReferralLink, ReferralInvite
import asyncio

async def init_db():
    print("⚙️ Проверка и создание таблиц, если они отсутствуют...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База данных готова.")

if __name__ == "__main__":
    asyncio.run(init_db())
