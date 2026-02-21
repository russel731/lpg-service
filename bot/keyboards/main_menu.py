from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Главное меню
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Найти газ")],
            [KeyboardButton(text="➕ Добавить АГЗС")]
        ],
        resize_keyboard=True
    )


# Кнопка геолокации (ЭТА ФУНКЦИЯ НУЖНА!)
def location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )