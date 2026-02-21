from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove

router = Router()


# 🚗 Водитель
@router.message(F.text.contains("Жүргізуші"))
async def driver_selected(message: Message):
    await message.answer(
        "📍 Жіберіңіз орналасқан жеріңізді",
        reply_markup=ReplyKeyboardRemove()
    )


# ⛽ АГЗС
@router.message(F.text.contains("АГЗС"))
async def station_selected(message: Message):
    await message.answer(
        "📍 Жіберіңіз орналасқан жеріңізді",
        reply_markup=ReplyKeyboardRemove()
    )