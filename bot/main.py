import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN

# handlers
from handlers.start import router as start_router
from handlers.main_menu import router as menu_router
from handlers.find_gas import router as find_gas_router
from handlers.owner_registration import router as owner_router
from handlers.onboarding import router as onboarding_router


async def main():
    # Создание бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Диспетчер
    dp = Dispatcher()

    # Подключение обработчиков
    dp.include_router(start_router)
    dp.include_router(onboarding_router)
    dp.include_router(menu_router)
    dp.include_router(find_gas_router)
    dp.include_router(owner_router)

    # Запуск
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())