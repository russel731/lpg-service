from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# ===== КНОПКА ТЕЛЕФОНА =====
def request_phone_keyboard(lang: str):
    if lang == "kz":
        text = "📱 Телефон жіберу"
    else:
        text = "📱 Отправить телефон"

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text, request_contact=True)]
        ],
        resize_keyboard=True
    )


# ===== КНОПКА ГЕОЛОКАЦИИ =====
def request_location_keyboard(lang: str):
    if lang == "kz":
        text = "📍 Геолокация жіберу"
    else:
        text = "📍 Отправить геолокацию"

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text, request_location=True)]
        ],
        resize_keyboard=True
    )