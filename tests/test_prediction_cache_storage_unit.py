import os
import pytest
from app.clients.redis import close_redis, create_redis
from app.storages.prediction_cache import PredictionCacheStorage

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_prediction_cache_roundtrip(monkeypatch):
    monkeypatch.setenv("REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    client = await create_redis()
    storage = PredictionCacheStorage(client, ttl_seconds=300)

    await storage.set_item_prediction(5001, {"is_violation": True, "probability": 0.91})
    value = await storage.get_item_prediction(5001)

    assert value == {"is_violation": True, "probability": 0.91}

    await storage.delete_item_prediction(5001)
    deleted = await storage.get_item_prediction(5001)

    assert deleted is None

    await close_redis(client)


@pytest.mark.asyncio
async def test_task_cache_roundtrip(monkeypatch):
    monkeypatch.setenv("REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    client = await create_redis()
    storage = PredictionCacheStorage(client, ttl_seconds=300)

    payload = {
        "task_id": 77,
        "status": "completed",
        "is_violation": False,
        "probability": 0.22,
        "error_message": None,
    }

    await storage.set_task_result(77, payload)
    value = await storage.get_task_result(77)

    assert value == payload

    await storage.delete_task_result(77)
    deleted = await storage.get_task_result(77)

    assert deleted is None

    await close_redis(client)
