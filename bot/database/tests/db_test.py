import asyncio
from bot.admin_panel.admin_utils import add_admin

async def main():
    await add_admin(123456789, 'superadmin')
    print("Админ добавлен")

asyncio.run(main())
