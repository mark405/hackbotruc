from bot.database.db import SessionLocal
from bot.database.models import Admin, Referral
from sqlalchemy.future import select

# Проверка, является ли пользователь админом
async def is_admin(telegram_id: int) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(select(Admin).filter_by(telegram_id=telegram_id))
        return result.scalars().first() is not None

# Добавление нового администратора
async def add_admin(telegram_id: int, username: str):
    async with SessionLocal() as session:
        session.add(Admin(telegram_id=telegram_id, username=username))
        await session.commit()

# Удаление администратора
async def remove_admin(telegram_id: int):
    async with SessionLocal() as session:
        admin = await session.scalar(select(Admin).filter_by(telegram_id=telegram_id))
        if admin:
            await session.delete(admin)
            await session.commit()

# Получение списка всех админов
async def list_admins():
    async with SessionLocal() as session:
        result = await session.execute(select(Admin))
        return result.scalars().all()

# Добавление реферальной ссылки (вебмастера)
async def add_referral(tag: str, link: str, admin_id: int):
    async with SessionLocal() as session:
        session.add(Referral(tag=tag, link=link, admin_id=admin_id))
        await session.commit()

# Удаление реферальной ссылки по ID
async def remove_ref_link(referral_id: int):
    async with SessionLocal() as session:
        referral = await session.get(Referral, referral_id)
        if referral:
            await session.delete(referral)
            await session.commit()

# Получение списка всех рефералов (вебмастеров)
async def list_ref_links():
    async with SessionLocal() as session:
        result = await session.execute(select(Referral))
        return result.scalars().all()

# Получение конкретного реферала по тегу
async def get_referral_by_tag(tag: str):
    async with SessionLocal() as session:
        result = await session.execute(select(Referral).filter_by(tag=tag))
        return result.scalars().first()
