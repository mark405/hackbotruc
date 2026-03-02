from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from bot.database.db import SessionLocal
from bot.database.models import User
from aiogram import types, Router
from aiogram.filters import Command

router = Router()

@router.message(Command("all_users"))
async def get_all_users(message: types.Message):
    async with SessionLocal() as session:
        try:
            result = await session.execute(select(User))
            users = result.scalars().all()
            if users:
                user_list = "\n".join([f"ID: {user.telegram_id}, Username: {user.username}" for user in users])
                await message.answer(f"Пользователи:\n{user_list}")
            else:
                await message.answer("Нет зарегистрированных пользователей.")
        except SQLAlchemyError:
            await message.answer("Ошибка получения пользователей.")
