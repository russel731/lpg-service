from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from states.owner import OwnerRegistration

router = Router()


# 📌 Начало регистрации
@router.message(F.text.in_(["➕ Добавить АГЗС", "➕ Газ станция қосу"]))
async def add_station(message: Message, state: FSMContext):
    lang = "kz" if "қосу" in message.text else "ru"

    await state.update_data(lang=lang)

    if lang == "kz":
        await message.answer("Телефон нөміріңізді енгізіңіз:")
    else:
        await message.answer("Введите контактный номер:")

    await state.set_state(OwnerRegistration.phone)


# 📌 Телефон
@router.message(OwnerRegistration.phone)
async def owner_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)

    data = await state.get_data()
    lang = data["lang"]

    if lang == "kz":
        await message.answer("Газ станция атауын енгізіңіз:")
    else:
        await message.answer("Введите название станции:")

    await state.set_state(OwnerRegistration.station_name)


# 📌 Название станции
@router.message(OwnerRegistration.station_name)
async def owner_station(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    data = await state.get_data()
    lang = data["lang"]

    if lang == "kz":
        text = "Станция геолокациясын жіберіңіз"
    else:
        text = "Отправьте геолокацию станции"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Геолокация", request_location=True)]],
        resize_keyboard=True,
    )

    await message.answer(text, reply_markup=keyboard)

    await state.set_state(OwnerRegistration.location)


# 📌 Геолокация
@router.message(OwnerRegistration.location, F.location)
async def owner_location(message: Message, state: FSMContext):
    data = await state.get_data()

    lat = message.location.latitude
    lon = message.location.longitude

    # Пока просто показываем
    await message.answer(
        f"Заявка отправлена на модерацию.\n\n"
        f"Телефон: {data['phone']}\n"
        f"Станция: {data['name']}\n"
        f"Координаты: {lat}, {lon}"
    )

    await state.clear()