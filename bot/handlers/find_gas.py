from aiogram import Router, F
from aiogram.types import Message
import requests

from keyboards.main_menu import location_keyboard
from services.language import get_user_language

router = Router()


# 🔍 Найти газ
@router.message(F.text)
async def find_gas(message: Message):

    text = message.text.lower()
    lang = get_user_language(message.from_user.id)

    if "найти газ" in text or "газ табу" in text:

        if lang == "kz":
            await message.answer(
                "📍 Геолокацияңызды жіберіңіз",
                reply_markup=location_keyboard()
            )
        else:
            await message.answer(
                "📍 Отправьте свою геолокацию",
                reply_markup=location_keyboard()
            )


# 📍 Получение геолокации
@router.message(F.location)
async def location_received(message: Message):

    lang = get_user_language(message.from_user.id)

    lat = message.location.latitude
    lon = message.location.longitude

    try:
        response = requests.get(
            "http://backend:8000/stations/nearby",
            params={"lat": lat, "lon": lon},
            timeout=5
        )

        stations = response.json()

        if not stations:
            if lang == "kz":
                await message.answer("❌ Жақын жерде бекеттер жоқ")
            else:
                await message.answer("❌ Поблизости нет заправок")
            return

        text = "⛽ "

        if lang == "kz":
            text += "Жақын газ бекеттері:\n\n"
        else:
            text += "Ближайшие заправки:\n\n"

        for st in stations[:5]:
            text += f"📍 {st['name']}\n"
            text += f"{st['distance']} км\n\n"

        await message.answer(text)

    except Exception as e:
        print("ERROR:", e)

        if lang == "kz":
            await message.answer("Қате пайда болды")
        else:
            await message.answer("Ошибка поиска заправок")