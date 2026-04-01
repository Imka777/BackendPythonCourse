import os
import redis.asyncio as redis

DEFAULT_REDIS_URL = "redis://localhost:6379/0"


async def create_redis():
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    client = redis.from_url(redis_url, decode_responses=True)
    await client.ping()
    return client


async def close_redis(client):
    if client is not None:
        await client.aclose()
