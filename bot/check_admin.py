import sys
import os
import asyncio

# Добавляем корневую папку в путь поиска модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.admin_panel.admin_utils import is_admin

async def check_admin():
    telegram_id = int(input("Введите ID администратора: "))
    result = await is_admin(telegram_id)
    print("Админ:", result)

asyncio.run(check_admin())
