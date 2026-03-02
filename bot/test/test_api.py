import asyncio
from bot.utils.api_utils import check_user_id_api

async def main():
    print("🔍 Тестирование API для проверки ID")
    user_id = input("Введите ID для проверки: ")

    # Проверяем ID через API
    result = await check_user_id_api(user_id)

    if result:
        print(f"✅ ID {user_id} найден через API!")
    else:
        print(f"❌ ID {user_id} не найден через API!")

# Запуск асинхронной функции
if __name__ == "__main__":
    asyncio.run(main())
