from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from services.api import register_owner
from services.language import get_user_language


router = Router()


# ===============================
# FSM состояния регистрации
# ===============================
class OwnerRegistration(StatesGroup):
    phone = State()
    station_name = State()
    location = State()


# ===============================
# Кнопка отправки геолокации
# ===============================
def location_keyboard(lang: str):
    if lang == "kz":
        text = "📍 Геолокация жіберу"
    else:
        text = "📍 Отправить геолокацию"

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text, request_location=True)]
        ],
        resize_keyboard=True
    )


# ===============================
# Старт регистрации
# ===============================
@router.message(F.text.contains("АГЗС") | F.text.contains("заправ"))
async def start_owner_registration(message: Message, state: FSMContext):

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("📱 Байланыс нөміріңізді енгізіңіз")
    else:
        await message.answer("📱 Введите контактный номер")

    await state.set_state(OwnerRegistration.phone)


# ===============================
# Телефон
# ===============================
@router.message(OwnerRegistration.phone)
async def get_phone(message: Message, state: FSMContext):

    await state.update_data(phone=message.text)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("⛽ Бекет атауын енгізіңіз")
    else:
        await message.answer("⛽ Введите название станции")

    await state.set_state(OwnerRegistration.station_name)


# ===============================
# Название станции
# ===============================
@router.message(OwnerRegistration.station_name)
async def get_station_name(message: Message, state: FSMContext):

    await state.update_data(station_name=message.text)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer(
            "📍 Геолокацияны жіберіңіз",
            reply_markup=location_keyboard(lang)
        )
    else:
        await message.answer(
            "📍 Отправьте геолокацию",
            reply_markup=location_keyboard(lang)
        )

    await state.set_state(OwnerRegistration.location)


# ===============================
# Геолокация + отправка в backend
# ===============================
@router.message(OwnerRegistration.location, F.location)
async def get_location(message: Message, state: FSMContext):

    data = await state.get_data()

    payload = {
        "telegram_id": message.from_user.id,
        "phone": data["phone"],
        "station_name": data["station_name"],
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
    }

    result = await register_owner(payload)

    lang = get_user_language(message.from_user.id)

    if result:
        if lang == "kz":
            await message.answer("✅ Өтінім жіберілді. Модерациядан кейін хабарлаймыз")
        else:
            await message.answer("✅ Заявка отправлена. После модерации мы свяжемся с вами")
    else:
        if lang == "kz":
            await message.answer("❌ Қате. Кейінірек қайталаңыз")
        else:
            await message.answer("❌ Ошибка. Попробуйте позже")

    await state.clear()