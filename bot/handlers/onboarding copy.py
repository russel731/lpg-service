from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

from keyboards.language import language_keyboard
from keyboards.roles import roles_keyboard

router = Router()

# временное хранение языка
user_lang = {}


# 🚀 старт
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🌍 Выберите язык / Тілді таңдаңыз",
        reply_markup=language_keyboard()
    )


# 🚀 выбор языка
@router.callback_query(F.data.startswith("lang_"))
async def language_select(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_lang[callback.from_user.id] = lang

    text = "Рөліңізді таңдаңыз:" if lang == "kz" else "Выберите роль:"

    await callback.message.edit_text(
        text,
        reply_markup=roles_keyboard(lang)
    )
    await callback.answer()


# 🚀 выбор роли
@router.callback_query(F.data.startswith("role_"))
async def role_select(callback: CallbackQuery):
    lang = user_lang.get(callback.from_user.id, "ru")

    if lang == "kz":
        text = "📍 Жіберіңіз орналасқан жеріңізді"
        btn = "📍 Геолокация жіберу"
    else:
        text = "📍 Отправьте вашу геолокацию"
        btn = "📍 Отправить геолокацию"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn, request_location=True)]],
        resize_keyboard=True
    )

    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()