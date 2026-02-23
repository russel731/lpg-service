from db import async_session
from user import User


async def set_user_language(telegram_id: int, language: str):
    async with async_session() as session:
        user = await session.get(User, telegram_id)

        if not user:
            user = User(telegram_id=telegram_id, language=language)
            session.add(user)
        else:
            user.language = language

        await session.commit()


async def get_user_language(telegram_id: int) -> str:
    async with async_session() as session:
        user = await session.get(User, telegram_id)

        if user and user.language:
            return user.language

    return "ru"