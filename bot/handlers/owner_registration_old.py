from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.owner_registration import OwnerRegistration
from keyboards.owner import request_phone_keyboard, request_location_keyboard
from services.owner_registration import register_owner
from keyboards.language import get_user_language


router = Router()


# ===== ШАГ 1. Старт регистрации =====
@router.message(
    F.text.contains("Бекет") |
    F.text.contains("Добавить") |
    F.text.contains("Регистрация")
)
async def start_registration(message: Message, state: FSMContext):
    lang = await get_user_language(message.from_user.id)

    await state.set_state(OwnerRegistration.phone)

    if lang == "kz":
        text = "📱 Байланыс нөміріңізді жіберіңіз"
    else:
        text = "📱 Введите контактный номер"

    await message.answer(text, reply_markup=request_phone_keyboard(lang))


# ===== ШАГ 2. Телефон =====
@router.message(OwnerRegistration.phone)
async def get_phone(message: Message, state: FSMContext):
    lang = await get_user_language(message.from_user.id)

    phone = None

    # поддержка кнопки контакта
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    if not phone:
        if lang == "kz":
            text = "❌ Нөмірді дұрыс енгізіңіз"
        else:
            text = "❌ Введите корректный номер"
        await message.answer(text)
        return

    await state.update_data(phone=phone)
    await state.set_state(OwnerRegistration.station_name)

    if lang == "kz":
        text = "⛽ Станция атауын енгізіңіз"
    else:
        text = "⛽ Введите название станции"

    await message.answer(text)


# ===== ШАГ 3. Название станции =====
@router.message(OwnerRegistration.station_name)
async def get_station(message: Message, state: FSMContext):
    lang = await get_user_language(message.from_user.id)

    await state.update_data(station=message.text)
    await state.set_state(OwnerRegistration.location)

    if lang == "kz":
        text = "📍 Геолокацияны жіберіңіз"
    else:
        text = "📍 Отправьте геолокацию"

    await message.answer(text, reply_markup=request_location_keyboard(lang))


# ===== ШАГ 4. Геолокация =====
@router.message(OwnerRegistration.location, F.location)
async def get_location(message: Message, state: FSMContext):
    lang = await get_user_language(message.from_user.id)

    data = await state.get_data()

    payload = {
        "telegram_id": message.from_user.id,
        "phone": data["phone"],
        "station_name": data["station"],
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
    }

    result = await register_owner(payload)

    if result:
        if lang == "kz":
            text = "✅ Өтінім қабылданды. Модерациядан кейін байланысамыз"
        else:
            text = "✅ Заявка отправлена. После модерации мы свяжемся"
    else:
        if lang == "kz":
            text = "❌ Қате орын алды"
        else:
            text = "❌ Ошибка регистрации"

    await message.answer(text)
    await state.clear()