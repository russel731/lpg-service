import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN

# routers
from handlers.start import router as start_router
from handlers.main_menu import router as main_menu_router
from handlers.owner_registration import router as owner_router


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # порядок очень важен
    dp.include_router(start_router)
    dp.include_router(main_menu_router)
    dp.include_router(owner_router)

    # запуск
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())