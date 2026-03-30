import time
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo, MenuButtonWebApp
)

BOT_TOKEN = "8482373207:AAGmeRGPBpiikO5mzxWuTJcVxsKDTTVc1CY"
API_URL = "https://nonconversationally-vestibular-pia.ngrok-free.dev"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_lang = {}

T = {
    'kz': {
        'welcome': (
            "⛽ *АГЗС Мониторинг*\n"
            "Қазақстанның газ бекеттерінің нақты уақыттағы картасы\n\n"
            "🟢 Газ бар бекеттерді табу\n"
            "🟡 Газ біткенде ескерту\n"
            "🔴 Газ жоқ болса баламасын іздеу\n"
            "🔔 Газ пайда болғанда хабарлау\n"
            "📍 Жақын бекетті автоматты табу\n"
            "👤 Иелерге — статусты басқару\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "🗺 *Картаны ашу* — төмендегі батырма\n"
            "⛽ *Мәзір* — сол жақ төменде"
        ),
        'btn': "🗺 Картаны ашу"
    },
    'ru': {
        'welcome': (
            "⛽ *АГЗС Мониторинг*\n"
            "Карта газовых заправок Казахстана в реальном времени\n\n"
            "🟢 Находить станции где есть газ\n"
            "🟡 Узнавать когда газ заканчивается\n"
            "🔴 Искать альтернативу если газа нет\n"
            "🔔 Получать уведомление когда газ появится\n"
            "📍 Автоматически находить ближайшую\n"
            "👤 Владельцам — управлять статусом\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "🗺 *Открыть карту* — кнопка внизу\n"
            "⛽ *Меню* — слева внизу"
        ),
        'btn': "🗺 Открыть карту"
    }
}

def get_text(user_id, key):
    lang = user_lang.get(user_id, 'ru')
    return T[lang].get(key, T['ru'].get(key, key))

def get_main_keyboard(user_id):
    lang = user_lang.get(user_id, 'ru')
    url = f"{API_URL}/miniapp_map?lang={lang}&v={int(time.time())}"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text(user_id, 'btn'), web_app=WebAppInfo(url=url))]],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    print(f"▶️ /start от {user_id}")

    try:
        await bot.set_chat_menu_button(
            chat_id=user_id,
            menu_button=MenuButtonWebApp(
                text="⛽ Меню",
                web_app=WebAppInfo(url=f"{API_URL}/miniapp")
            )
        )
    except Exception as e:
        print(f"MenuButton: {e}")

    await message.answer(
        "⛽ *АГЗС Мониторинг*\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "🌐 Тілді таңдаңыз\n"
        "🌐 Выберите язык",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]])
    )

@dp.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    selected_lang = callback.data.split("_")[1]
    user_lang[user_id] = selected_lang
    print(f"🌐 Язык: {selected_lang} для {user_id}")
    
    try: await callback.message.delete()
    except: pass

    await callback.bot.send_message(
        chat_id=user_id,
        text=get_text(user_id, 'welcome'),
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id)
    )
    await callback.answer()

async def main():
    print("🤖 АГЗС Мониторинг Бот")
    print(f"🔗 API: {API_URL}")
    print("✅ Запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
