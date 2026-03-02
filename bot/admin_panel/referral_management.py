import asyncpg
from aiogram import types, Router
from aiogram.filters import Command
from bot.database.db import get_pool

router = Router()

@router.message(Command("referrals"))
async def get_all_referrals(message: types.Message):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetch('SELECT * FROM referral_links')
            if result:
                referral_list = "\n".join([f"ID: {ref['id']}, Link: {ref['link']}" for ref in result])
                await message.answer(f"Реферальные ссылки:\n{referral_list}")
            else:
                await message.answer("Нет реферальных ссылок.")
    except Exception as e:
        await message.answer(f"Ошибка получения ссылок: {str(e)}")
