from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def driver_menu(lang: str):
    if lang == "kz":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📍 LPG табу")],
                [KeyboardButton(text="⭐ Таңдаулылар")],
                [KeyboardButton(text="⚙️ Баптаулар")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📍 Найти LPG")],
                [KeyboardButton(text="⭐ Избранные")],
                [KeyboardButton(text="⚙️ Настройки")]
            ],
            resize_keyboard=True
        )


def owner_menu(lang: str):
    if lang == "kz":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="➕ Станция қосу")],
                [KeyboardButton(text="📊 Менің станцияларым")],
                [KeyboardButton(text="⚙️ Баптаулар")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="➕ Добавить станцию")],
                [KeyboardButton(text="📊 Мои станции")],
                [KeyboardButton(text="⚙️ Настройки")]
            ],
            resize_keyboard=True
        )