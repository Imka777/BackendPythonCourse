import os
import asyncpg

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/moderation_db"


async def create_pool():
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    return await asyncpg.create_pool(database_url, min_size=1, max_size=5)


async def close_pool(pool):
    if pool is not None:
        await pool.close()
