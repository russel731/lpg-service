import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.start import router as start_router
from handlers.main_menu import router as menu_router
from handlers.find_gas import router as find_router   # 🔥 ВАЖНО

from config import BOT_TOKEN


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Роутеры
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(find_router)   # 🔥 ВАЖНО

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())