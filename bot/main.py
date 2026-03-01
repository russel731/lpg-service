import os
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8482373207:AAGmeRGPBpiikO5mzxWuTJcVxsKDTTVc1CY")
API_URL = os.getenv("API_URL", "http://localhost:8000")
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://nonconversationally-vestibular-pia.ngrok-free.dev/miniapp")

logging.basicConfig(level=logging.INFO)

LANG_CHOICE, PHONE, PASSWORD = range(3)

user_tokens: dict[int, str] = {}
user_station: dict[int, dict] = {}
user_lang: dict[int, str] = {}

texts = {
    "kz": {
        "welcome": "👋 Сәлем! АГЗС мониторинг ботына қош келдіңіз!",
        "enter_phone": "📞 Телефон нөміріңізді енгізіңіз:",
        "enter_password": "🔒 Құпия сөзді енгізіңіз:",
        "login_success": "✅ Кіру сәтті!\n📍 Сіздің станцияңыз: *{name}*",
        "login_error": "❌ Қате логин немесе пароль. Қайта көріңіз.",
        "not_approved": "⏳ Сіздің аккаунтыңыз әлі бекітілмеген.\nАдминистраторды күтіңіз.",
        "login_btn": "🔑 Кіру",
        "status_updated": "{emoji} Статус жаңартылды!\n📍 {name}",
        "logout": "👋 Сау болыңыз!",
        "no_station": "❌ Станция табылмады.",
        "not_logged": "❌ Алдымен кіріңіз!",
        "welcome_back": "👋 Қош келдіңіз!\n📍 Сіздің станцияңыз: *{name}*\n\nСтатусты таңдаңыз:",
        "btn_green": "🟢 Газ бар",
        "btn_yellow": "🟡 Газ аз",
        "btn_red": "🔴 Газ жоқ",
        "btn_status": "📊 Статус",
        "btn_logout": "🚪 Шығу",
        "open_app": "⛽ Қолданбаны ашу",
    },
    "ru": {
        "welcome": "👋 Привет! Добро пожаловать в бот мониторинга АГЗС!",
        "enter_phone": "📞 Введите номер телефона:",
        "enter_password": "🔒 Введите пароль:",
        "login_success": "✅ Вход выполнен!\n📍 Ваша станция: *{name}*",
        "login_error": "❌ Неверный логин или пароль. Попробуйте снова.",
        "not_approved": "⏳ Ваш аккаунт ещё не одобрен.\nОжидайте администратора.",
        "login_btn": "🔑 Войти",
        "status_updated": "{emoji} Статус обновлён!\n📍 {name}",
        "logout": "👋 До свидания!",
        "no_station": "❌ Станция не найдена.",
        "not_logged": "❌ Сначала войдите!",
        "welcome_back": "👋 Добро пожаловать!\n📍 Ваша станция: *{name}*\n\nВыберите статус:",
        "btn_green": "🟢 Газ есть",
        "btn_yellow": "🟡 Газ мало",
        "btn_red": "🔴 Газа нет",
        "btn_status": "📊 Статус",
        "btn_logout": "🚪 Выйти",
        "open_app": "⛽ Открыть приложение",
    }
}

def t(user_id: int, key: str, **kwargs):
    lang = user_lang.get(user_id, "kz")
    text = texts[lang].get(key, key)
    return text.format(**kwargs) if kwargs else text

def main_keyboard(user_id: int):
    lang = user_lang.get(user_id, "kz")
    tx = texts[lang]
    return ReplyKeyboardMarkup([
        [tx["btn_green"], tx["btn_yellow"]],
        [tx["btn_red"], tx["btn_status"]],
        [tx["btn_logout"]]
    ], resize_keyboard=True)

def login_keyboard(user_id: int):
    return ReplyKeyboardMarkup([[t(user_id, "login_btn")]], resize_keyboard=True)

def lang_keyboard():
    return ReplyKeyboardMarkup([["🇰🇿 Қазақша", "🇷🇺 Русский"]], resize_keyboard=True)

def webapp_keyboard(user_id: int):
    lang = user_lang.get(user_id, "kz")
    label = texts[lang]["open_app"]
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(label, web_app=WebAppInfo(url=MINI_APP_URL))
    ]])

async def get_my_station(station_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/stations")
        stations = r.json()
        return next((s for s in stations if s["id"] == station_id), None)

async def update_status(token: str, station_id: int, status: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_URL}/stations/{station_id}/update",
            json={"status": status},
            headers={"Authorization": f"Bearer {token}"}
        )
        return r.status_code == 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonWebApp(
            text="⛽ АГЗС",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    )

    await update.message.reply_text(
        "🌐 Тілді таңдаңыз / Выберите язык:",
        reply_markup=lang_keyboard()
    )
    return LANG_CHOICE

async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    lang = "kz" if "Қазақша" in text else "ru"
    user_lang[user_id] = lang

    await update.message.reply_text(
        t(user_id, "welcome"),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🚀 Открыть / Ашу",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]])
    )
    return ConversationHandler.END

async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        t(user_id, "enter_phone"),
        reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    user_id = update.effective_user.id
    await update.message.reply_text(t(user_id, "enter_password"))
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data.get("phone")
    password = update.message.text
    user_id = update.effective_user.id

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{API_URL}/auth/login",
                data={"username": phone, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if r.status_code == 200:
                data = r.json()
                token = data["access_token"]
                user_tokens[user_id] = token

                me = await client.get(
                    f"{API_URL}/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                me_data = me.json()
                station_id = me_data.get("station_id")

                if station_id:
                    station = await get_my_station(station_id)
                    user_station[user_id] = station

                name = user_station.get(user_id, {}).get("name", "—")
                await update.message.reply_text(
                    t(user_id, "login_success", name=name),
                    parse_mode="Markdown",
                    reply_markup=main_keyboard(user_id)
                )
                await update.message.reply_text(
                    t(user_id, "open_app") + ":",
                    reply_markup=webapp_keyboard(user_id)
                )
            elif r.status_code == 403:
                await update.message.reply_text(
                    t(user_id, "not_approved"),
                    reply_markup=login_keyboard(user_id)
                )
            else:
                await update.message.reply_text(
                    t(user_id, "login_error"),
                    reply_markup=login_keyboard(user_id)
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")

    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_tokens:
        await update.message.reply_text(
            t(user_id, "not_logged"),
            reply_markup=login_keyboard(user_id)
        )
        return

    token = user_tokens[user_id]
    station = user_station.get(user_id)

    if not station:
        await update.message.reply_text(t(user_id, "no_station"))
        return

    lang = user_lang.get(user_id, "kz")
    tx = texts[lang]
    status_map = {
        tx["btn_green"]: "green",
        tx["btn_yellow"]: "yellow",
        tx["btn_red"]: "red",
    }

    if text in status_map:
        status = status_map[text]
        success = await update_status(token, station["id"], status)
        if success:
            emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[status]
            await update.message.reply_text(
                t(user_id, "status_updated", emoji=emoji, name=station["name"]),
                reply_markup=main_keyboard(user_id)
            )

    elif text == tx["btn_status"]:
        s = await get_my_station(station["id"])
        if s:
            emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(s["status"], "🟣")
            await update.message.reply_text(
                f"📍 *{s['name']}*\n{emoji} {s['status']}\n🕐 {s['lastUpdated'][:16]}",
                parse_mode="Markdown",
                reply_markup=main_keyboard(user_id)
            )

    elif text == tx["btn_logout"]:
        user_tokens.pop(user_id, None)
        user_station.pop(user_id, None)
        await update.message.reply_text(
            t(user_id, "logout"),
            reply_markup=lang_keyboard()
        )
        user_lang.pop(user_id, None)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("🔑 Кіру|🔑 Войти"), login_start),
        ],
        states={
            LANG_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_lang)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()