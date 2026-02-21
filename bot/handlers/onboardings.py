from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from keyboards.main_menu import main_menu_keyboard
from services.language import get_user_language
from states.owner_registration import OwnerRegistration
from config import ADMIN_TELEGRAM_ID

router = Router()


# ➕ Добавить заправку
@router.message(lambda message: message.text in ["➕ Добавить заправку", "➕ Жанармай құю станциясын қосу"])
async def add_station(message: Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("Атыңызды енгізіңіз", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Введите ваше имя", reply_markup=ReplyKeyboardRemove())

    await state.set_state(OwnerRegistration.name)


# 👤 Имя
@router.message(OwnerRegistration.name)
async def owner_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    lang = get_user_language(message.from_user.id)

    if lang == "kz":
        await message.answer("Телефон нөміріңізді енгізіңіз")
    else:
        await message.answer("Введите номер телефона")

    await state.set_state(OwnerRegistration.phone)


# 📞 Телефон
@router.message(OwnerRegistration.phone)
async def owner_phone(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    name = data["name"]
    phone = message.text

    lang = get_user_language(message.from_user.id)

    # уведомление админу
    text = (
        f"📢 Новая заявка на добавление АГЗС\n\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Telegram ID: {message.from_user.id}"
    )

    if ADMIN_TELEGRAM_ID:
        await bot.send_message(int(ADMIN_TELEGRAM_ID), text)

    if lang == "kz":
        await message.answer(
            "✅ Өтініш модерацияға жіберілді",
            reply_markup=main_menu_keyboard()
        )
    else:
        await message.answer(
            "✅ Заявка отправлена на модерацию",
            reply_markup=main_menu_keyboard()
        )

    await state.clear()