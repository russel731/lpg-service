from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from services.language import get_user_language
from states.owner_registration import OwnerRegistration


router = Router()


# 👤 Имя владельца
@router.message(OwnerRegistration.name)
async def owner_name(message: Message, state: FSMContext):

    await state.update_data(name=message.text)

    lang = get_user_language(message.from_user.id)

    # Кнопка телефона
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Отправить телефон", request_contact=True)]
        ],
        resize_keyboard=True
    )

    if lang == "kz":
        await message.answer(
            "Телефоныңызды жіберіңіз",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "Отправьте ваш телефон",
            reply_markup=keyboard
        )

    await state.set_state(OwnerRegistration.phone)


# 📞 Телефон
@router.message(OwnerRegistration.phone)
async def owner_phone(message: Message, state: FSMContext):

    if not message.contact:
        await message.answer("Пожалуйста, отправьте номер через кнопку")
        return

    data = await state.get_data()

    phone = message.contact.phone_number
    name = data["name"]

    # Пока просто вывод (проверка)
    await message.answer(
        f"✅ Заявка принята\n\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}"
    )

    await state.clear()