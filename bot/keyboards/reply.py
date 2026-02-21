from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def location_keyboard(lang: str):
    text = {
        "ru": "📍 Отправить геолокацию",
        "kz": "📍 Геолокация жіберу"
    }

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text[lang], request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
