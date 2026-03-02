from aiogram import types, Router
from aiogram.filters import Command
from bot.admin_panel.admin_utils import is_admin, add_admin

router = Router()

@router.message(Command("add_admin"))
async def add_admin_command(message: types.Message):
    if await is_admin(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) < 3:
                await message.answer("Используйте команду так: /add_admin <telegram_id> <username>")
                return
            
            telegram_id = int(parts[1])
            username = parts[2]

            await add_admin(telegram_id, username)
            await message.answer(f"Админ {username} с ID {telegram_id} успешно добавлен.")
        except ValueError:
            await message.answer("ID должен быть числом.")
    else:
        await message.answer("У вас нет прав администратора.")
