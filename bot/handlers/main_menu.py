from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
import requests

from keyboards.main_menu import main_menu_keyboard, location_keyboard
from services.language import get_user_language
from states.owner_registration import OwnerRegistration

router = Router()


# 🔎 Найти газ
@router.message(lambda message: message.text in ["🔎 Найти газ", "Газ табу"])
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
            text = "📍 Жақын газ бекеттері:\n\n"
        else:
            text = "📍 Ближайшие заправки:\n\n"

        for st in stations[:5]:
            text += f"⛽ {st['name']}\n"
            text += f"📏 {st['distance']} км\n\n"

        await message.answer(text)

    except Exception:
        if lang == "kz":
            await message.answer("Қате пайда болды")
        else:
            await message.answer("Ошибка поиска заправок")


# ➕ Добавить АГЗС
@router.message(lambda message: message.text in [
    "➕ Добавить АГЗС",
    "➕ АГЗС қосу",
    "➕ Добавить заправку"
])
async def start_owner_registration(message: Message, state: FSMContext):
    await state.set_state(OwnerRegistration.name)

    await message.answer(
        "Введите ваше имя (владельца станции):",
        reply_markup=ReplyKeyboardRemove()
    )


# 👤 Имя
@router.message(OwnerRegistration.name)
async def owner_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    await state.set_state(OwnerRegistration.phone)
    await message.answer("Введите ваш номер телефона:")


# 📞 Телефон
@router.message(OwnerRegistration.phone)
async def owner_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)

    await state.set_state(OwnerRegistration.station_name)
    await message.answer("Введите название вашей АГЗС:")


# 🏢 Название станции
@router.message(OwnerRegistration.station_name)
async def station_name(message: Message, state: FSMContext):
    await state.update_data(station_name=message.text)

    await state.set_state(OwnerRegistration.location)
    await message.answer("Отправьте геолокацию станции 📍")


# 📍 Геолокация станции
@router.message(OwnerRegistration.location)
async def station_location(message: Message, state: FSMContext):
    if not message.location:
        await message.answer("Пожалуйста, отправьте именно геолокацию 📍")
        return

    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude
    )

    await state.se