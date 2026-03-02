from aiogram import types, Router
from bot.admin_panel.admin_utils import is_admin
from aiogram.filters import Command
router = Router()

@router.message(Command("admincheck"))

async def admin_check_command(message: types.Message):
    if await is_admin(message.from_user.id):
        await message.answer("Вы являетесь администратором.")
    else:
        await message.answer("У вас нет прав администратора.")
