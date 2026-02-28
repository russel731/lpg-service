import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")
BACKEND_URL = os.getenv("BACKEND_URL")
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/lpg"

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env")