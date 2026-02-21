from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from services.language import get_user_language

router = Router()


# FSM состояния регистрации владельца
class OwnerRegistration(StatesGroup):
    phone = State()
    station_name = State()
    location = State()


# Универсальный ловец кнопки (любой язык)
@router.message(F.text.contains("АГЗС") | F.text.contains("заправ"))
async def start_owner_registration(message: Message, state: FSMContext):

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("📱 Байланыс нөміріңізді енгізіңіз")
    else:
        await message.answer("📱 Введите контактный номер")

    await state.set_state(OwnerRegistration.phone)


# Телефон
@router.message(OwnerRegistration.phone)
async def get_phone(message: Message, state: FSMContext):

    await state.update_data(phone=message.text)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("⛽ Бекет атауын енгізіңіз")
    else:
        await message.answer("⛽ Введите название станции")

    await state.set_state(OwnerRegistration.station_name)


# Название
@router.message(OwnerRegistration.station_name)
async def get_station_name(message: Message, state: FSMContext):

    await state.update_data(station_name=message.text)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("📍 Геолокацияны жіберіңіз")
    else:
        await message.answer("📍 Отправьте геолокацию")

    await state.set_state(OwnerRegistration.location)


# Геолокация
@router.message(OwnerRegistration.location, F.location)
async def get_location(message: Message, state: FSMContext):

    data = await state.get_data()

    lat = message.location.latitude
    lon = message.location.longitude

    # 🔥 Пока просто подтверждение
    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("✅ Өтінім жіберілді. Модерациядан кейін хабарлаймыз")
    else:
        await message.answer("✅ Заявка отправлена. После модерации мы свяжемся с вами")

    await state.clear()