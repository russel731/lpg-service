# bot/api.py

import aiohttp

# URL backend внутри Docker-сети
BASE_URL = "http://backend:8000"


async def create_owner(data: dict):
    """
    Отправка данных владельца в backend FastAPI
    """

    # 🔍 Лог отправляемых данных
    print("🚀 Отправка данных в backend:", data)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/owners/", json=data) as response:

                # читаем ответ текстом (для логов)
                text = await response.text()

                print("✅ Ответ backend:", text)
                print("📊 Статус:", response.status)

                # если backend вернул ошибку
                if response.status != 200:
                    return {
                        "status": "error",
                        "message": text
                    }

                return await response.json()

    except Exception as e:
        print("❌ Ошибка запроса к backend:", e)
        return {
            "status": "error",
            "message": str(e)
        }