from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Клавиатура выбора языка
def language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇰🇿 Қазақша")],
            [KeyboardButton(text="🇷🇺 Русский")]
        ],
        resize_keyboard=True
    )


# Получение языка пользователя
async def get_user_language(user_id: int) -> str:
    """
    Временная заглушка.
    Позже подключим БД.
    """
    # Пока по умолчанию казахский
    return "kz"