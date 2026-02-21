from aiogram import Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

router = Router()


def role_keyboard(lang: str):
    if lang == "kz":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚗 Мен жүргізушімін")],
                [KeyboardButton(text="⛽ Мен АГЗС (LPG) иесімін")]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚗 Я водитель")],
                [KeyboardButton(text="⛽ Я владелец АГЗС (LPG)")]
            ],
            resize_keyboard=True
        )

    return keyboard


@router.message(F.text.in_(["🇰🇿 Қазақша", "🇷🇺 Русский"]))
async def language_selected(message: Message):

    if "Қазақша" in message.text:
        lang = "kz"
        text = "LPG сервисіне қош келдіңіз 🚗\n\nРөліңізді таңдаңыз:"
    else:
        lang = "ru"
        text = "Добро пожаловать в сервис LPG 🚗\n\nВыберите роль:"

    await message.answer(
        text,
        reply_markup=role_keyboard(lang)
    )