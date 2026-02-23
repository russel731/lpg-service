from aiogram import Router, F
from aiogram.types import Message
from keyboards.language import language_keyboard
from services.language import set_user_language

router = Router()


@router.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "🌍 Тілді таңдаңыз / Выберите язык",
        reply_markup=language_keyboard()
    )


# 🇰🇿 Казахский
@router.message(F.text == "🇰🇿 Қазақша")
async def set_kz(message: Message):
    await set_user_language(message.from_user.id, "kz")
    await message.answer("LPG сервисіне қош келдіңіз 🚗")


# 🇷🇺 Русский
@router.message(F.text == "🇷🇺 Русский")
async def set_ru(message: Message):
    await set_user_language(message.from_user.id, "ru")
    await message.answer("Добро пожаловать в LPG сервис 🚗")