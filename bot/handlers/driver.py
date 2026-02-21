from aiogram import Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
import aiohttp

router = Router()


def location_keyboard(lang: str):
    if lang == "kz":
        button = KeyboardButton(
            text="📍 Геолокация жіберу",
            request_location=True
        )
    else:
        button = KeyboardButton(
            text="📍 Отправить геолокацию",
            request_location=True
        )

    return ReplyKeyboardMarkup(
        keyboard=[[button]],
        resize_keyboard=True
    )


@router.message(F.text.in_(["🚗 Я водитель", "🚗 Мен жүргізушімін"]))
async def driver_selected(message: Message):

    lang = "kz" if "Мен" in message.text else "ru"

    if lang == "kz":
        text = "📍 Геолокацияңызды жіберіңіз"
    else:
        text = "📍 Отправьте вашу геолокацию"

    await message.answer(
        text,
        reply_markup=location_keyboard(lang)
    )


@router.message(F.location)
async def handle_location(message: Message):

    lat = message.location.latitude
    lon = message.location.longitude

    lang = "kz" if message.from_user.language_code == "kk" else "ru"

    if lang == "kz":
        await message.answer("🔍 Жақын АГЗС ізделуде...")
    else:
        await message.answer("🔍 Ищу ближайшие АГЗС...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://backend:8000/stations/nearby?lat={lat}&lon={lon}"
            ) as response:

                stations = await response.json()

        if not stations:
            if lang == "kz":
                await message.answer("❌ Жақын жерде АГЗС табылмады")
            else:
                await message.answer("❌ Поблизости АГЗС не найдено")
            return

        for station in stations:

            name = station.get("name", "АЗС")
            status = station.get("status", "unknown")

            if status == "available":
                status_text = "🟢 Газ бар" if lang == "kz" else "🟢 Газ есть"
            elif status == "low":
                status_text = "🟡 Газ аз" if lang == "kz" else "🟡 Мало газа"
            else:
                status_text = "🔴 Газ жоқ" if lang == "kz" else "🔴 Нет газа"

            text = (
                f"━━━━━━━━━━━━━━\n"
                f"⛽ {name}\n"
                f"{status_text}\n"
                f"━━━━━━━━━━━━━━"
            )

            await message.answer(text)

    except Exception:
        if lang == "kz":
            await message.answer("❌ Серверге қосылу мүмкін болмады")
        else:
            await message.answer("❌ Не удалось связаться с сервером")