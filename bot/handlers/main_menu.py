from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import requests

from keyboards.main_menu import main_menu_keyboard, location_keyboard
from services.language import get_user_language
from states.owner_registration import OwnerRegistration


router = Router()


# 🔍 Найти газ
@router.message(lambda message: message.text and ("Найти газ" in message.text or "Газ табу" in message.text))
async def find_gas(message: Message):

    lang = get_user_language(message.from_user.id)

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
@router.message(lambda msg: msg.location is not None)
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

        if lang == "kz":
            text = "⛽ Жақын газ бекеттері:\n\n"
        else:
            text = "⛽ Ближайшие заправки:\n\n"

        for st in stations[:5]:
            text += f"📍 {st['name']}\n"
            text += f"{st['distance']} км\n\n"

        await message.answer(text)

    except Exception:
        if lang == "kz":
            await message.answer("Қате пайда болды")
        else:
            await message.answer("Ошибка поиска заправок")


# ➕ Добавить заправку (универсально, без проблем с emoji)
@router.message(lambda message: message.text and "Добавить" in message.text)
async def add_station(message: Message, state: FSMContext):

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("Атыңызды енгізіңіз")
    else:
        await message.answer("Введите ваше имя")

    await state.set_state(OwnerRegistration.name)