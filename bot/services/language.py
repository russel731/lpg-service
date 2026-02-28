# временное хранение языка в памяти
user_languages = {}

async def set_user_language(telegram_id: int, language: str):
    user_languages[telegram_id] = language


async def get_user_language(telegram_id: int) -> str:
    return user_languages.get(telegram_id, "ru")