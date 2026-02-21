from aiogram import Router, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()


# 🌍 Кнопки выбора языка
def language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇰🇿 Қазақша"), KeyboardButton(text="🇷🇺 Русский")]
        ],
        resize_keyboard=True
    )


# 📍 Главное меню
def main_menu(lang: str):
    if lang == "kk":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Газ табу")],
                [KeyboardButton(text="➕ Бекет қосу")],
                [KeyboardButton(text="🌐 Тілді өзгерту")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Найти газ")],
                [KeyboardButton(text="➕ Добавить заправку")],
                [KeyboardButton(text="🌐 Сменить язык")]
            ],
            resize_keyboard=True
        )


# 🚀 Старт
@router.message(lambda m: m.text == "/start")
async def start(message: types.Message):
    await message.answer(
        "🌍 Тілді таңдаңыз / Выберите язык",
        reply_markup=language_keyboard()
    )


# 🇷🇺 Русский
@router.message(lambda m: m.text == "🇷🇺 Русский")
async def set_russian(message: types.Message):
    await message.answer(
        "Добро пожаловать в LPG сервис 🚗",
        reply_markup=main_menu("ru")
    )


# 🇰🇿 Қазақша
@router.message(lambda m: m.text == "🇰🇿 Қазақша")
async def set_kazakh(message: types.Message):
    await message.answer(
        "LPG сервисіне қош келдіңіз 🚗",
        reply_markup=main_menu("kk")
    )