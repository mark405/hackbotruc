import requests
import logging
from bot.config import API_KEY, BASE_URL, TEST_MODE

async def check_user_id_api(user_id):
    try:
        if TEST_MODE and len(user_id) <= 6:
            # Тестовый режим - проверка по локальному файлу
            try:
                with open("bot/database/valid_ids.txt", "r", encoding="utf-8") as f:
                    valid_ids = f.read().splitlines()
                if user_id in valid_ids:
                    logging.info(f"✅ Тестовый ID {user_id} найден в локальном файле.")
                    return True
                else:
                    logging.warning(f"❌ Тестовый ID {user_id} не найден в локальном файле.")
                    return False
            except FileNotFoundError:
                logging.error("❗ Файл с тестовыми ID не найден.")
                return False
        else:
            # Проверка через API
            headers = {
                "X-AUTH-API-KEY": API_KEY,
                "Content-Type": "application/json"
            }
            params = {
                "sub1": user_id
            }
            response = requests.get(BASE_URL, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if any(str(user_id) == str(item.get("sub1", "")) for item in data):
                    logging.info(f"✅ Реальный ID {user_id} найден через API.")
                    return True
                else:
                    logging.warning(f"❌ Реальный ID {user_id} не найден через API.")
                    return False
            else:
                logging.error(f"❗ Ошибка API: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logging.error(f"❗ Ошибка при запросе к API: {str(e)}")
        return False
