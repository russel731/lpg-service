from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def request_location_keyboard(lang: str):
    """
    Клавиатура запроса геолокации
    """

    if lang == "kz":
        text = "📍 Геолокацияны жіберу"
    else:
        text = "📍 Отправить геолокацию"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text, request_location=True)]
        ],
        resize_keyboard=True
    )

    return keyboard