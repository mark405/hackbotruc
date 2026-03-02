from aiogram import Router, types, F

router = Router()

@router.message(F.text == "/help")
async def help_handler(message: types.Message):
    await message.answer("Это бот CasinoHack. Введите /start для запуска.")
