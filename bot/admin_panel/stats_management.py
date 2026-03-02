import asyncpg
from aiogram import types, Router
from aiogram.filters import Command
from bot.database.db import get_pool

router = Router()

@router.message(Command("stats"))
async def get_all_stats(message: types.Message):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetch('SELECT * FROM referral_stats')
            if result:
                stats_list = "\n".join([f"ID: {stat['id']}, Clicks: {stat['click_count']}, Registrations: {stat['registration_count']}" for stat in result])
                await message.answer(f"Статистика реферальных ссылок:\n{stats_list}")
            else:
                await message.answer("Нет статистики на данный момент.")
    except Exception as e:
        await message.answer(f"Ошибка получения статистики: {str(e)}")
