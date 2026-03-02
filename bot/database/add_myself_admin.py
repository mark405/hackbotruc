import asyncio
from sqlalchemy.future import select
from bot.database.db import SessionLocal
from bot.database.models import Admin

# Список админов для добавления
ADMINS_TO_ADD = [
    (1067290024, "moonstrike2018"),
    (7096117141, "Traffgun_Albert"),
    (7124334923, "TraffGun_Andriy")
]

async def main():
    async with SessionLocal() as session:
        for telegram_id, username in ADMINS_TO_ADD:
            result = await session.execute(select(Admin).filter_by(telegram_id=telegram_id))
            existing_admin = result.scalars().first()

            if existing_admin:
                print(f"⚠️ Админ с ID {telegram_id} (@{existing_admin.username}) уже существует. Пропускаем.")
            else:
                admin = Admin(telegram_id=telegram_id, username=username)
                session.add(admin)
                await session.commit()
                print(f"✅ Админ {username} с ID {telegram_id} успешно добавлен!")

if __name__ == "__main__":
    asyncio.run(main())
