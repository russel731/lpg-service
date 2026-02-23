from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.owner_registration import OwnerRegistration
from services.language import get_user_language

router = Router()


# 🚀 Старт регистрации
@router.message(F.text.in_(["➕ Добавить заправку", "➕ Бекет қосу"]))
async def start_owner_registration(message: Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("👤 Атыңызды енгізіңіз")
    else:
        await message.answer("👤 Введите ваше имя")

    await state.set_state(OwnerRegistration.name)


# 👤 Имя
@router.message(OwnerRegistration.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("📱 Байланыс нөміріңізді енгізіңіз")
    else:
        await message.answer("📱 Введите контактный номер")

    await state.set_state(OwnerRegistration.phone)


# 📱 Телефон
@router.message(OwnerRegistration.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("⛽ Станция атауын енгізіңіз")
    else:
        await message.answer("⛽ Введите название станции")

    await state.set_state(OwnerRegistration.station_name)


# ⛽ Название станции
@router.message(OwnerRegistration.station_name)
async def get_station_name(message: Message, state: FSMContext):
    await state.update_data(station_name=message.text)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("📍 Геолокацияңызды жіберіңіз")
    else:
        await message.answer("📍 Отправьте геолокацию")

    await state.set_state(OwnerRegistration.location)


# 📍 Геолокация
@router.message(OwnerRegistration.location, F.location)
async def get_location(message: Message, state: FSMContext):
    data = await state.get_data()

    print("OWNER DATA:", data)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("✅ Сұраныс жіберілді")
    else:
        await message.answer("✅ Заявка отправлена")

    await state.clear()