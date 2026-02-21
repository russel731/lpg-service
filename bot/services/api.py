import httpx
import logging

# URL backend внутри Docker
BACKEND_URL = "http://backend:8000"

logger = logging.getLogger(__name__)

# 🚀 Регистрация владельца станции
async def register_owner(data: dict):
    try:
        logger.info(f"Sending data to backend: {data}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/owners/",
                json=data,
                timeout=10,
            )

        logger.info(f"Backend response: {response.status_code}")
        response.raise_for_status()

        return response.json()

    except Exception as e:
        logger.exception("API ERROR")
        return None