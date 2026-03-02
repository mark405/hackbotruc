from aiogram import types, Router
from bot.admin_panel.admin_utils import is_admin, remove_admin
from aiogram.filters import Command

router = Router()

@router.message(Command("remove_admin"))
async def remove_admin_command(message: types.Message):
    if await is_admin(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) < 2:
                await message.answer("Используйте команду так: /remove_admin <telegram_id>")
                return
            
            telegram_id = int(parts[1])

            await remove_admin(telegram_id)
            await message.answer(f"Админ с ID {telegram_id} успешно удалён.")
        except ValueError:
            await message.answer("ID должен быть числом.")
    else:
        await message.answer("У вас нет прав администратора.")
