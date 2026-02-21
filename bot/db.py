import asyncpg
import os


DATABASE_URL = os.getenv("DATABASE_URL")

pool = None


async def get_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool


# ---------- USER ----------
async def get_user(telegram_id: int):
    pool = await get_pool()
    return await pool.fetchrow(
        "SELECT * FROM users WHERE telegram_id=$1",
        telegram_id
    )


async def create_user(telegram_id: int, language: str):
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO users (telegram_id, language)
        VALUES ($1, $2)
        """,
        telegram_id, language
    )


async def update_user_language(telegram_id: int, language: str):
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE users SET language=$1 WHERE telegram_id=$2
        """,
        language, telegram_id
    )


async def update_user_role(telegram_id: int, role: str):
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE users SET role=$1 WHERE telegram_id=$2
        """,
        role, telegram_id
    )