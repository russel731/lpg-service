import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL")

def save_user(telegram_id: str, role: str, language: str):
    response = requests.post(
        f"{BACKEND_URL}/users/",
        params={
            "telegram_id": telegram_id,
            "role": role,
            "language": language
        },
        timeout=5
    )
    return response.json()