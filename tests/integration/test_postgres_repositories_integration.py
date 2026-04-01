import os
import pytest
import pytest_asyncio

from app.db import close_pool, create_pool
from app.repositories.items import ItemRepository
from app.repositories.moderation_results import ModerationResultRepository
from app.repositories.users import UserRepository

pytestmark = pytest.mark.integration


SCHEMA_SQL = """
DROP TABLE IF EXISTS moderation_results;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    seller_id BIGINT PRIMARY KEY,
    is_verified_seller BOOLEAN NOT NULL
);

CREATE TABLE items (
    item_id BIGINT PRIMARY KEY,
    seller_id BIGINT NOT NULL REFERENCES users(seller_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category INTEGER NOT NULL CHECK (category > 0),
    images_qty INTEGER NOT NULL CHECK (images_qty >= 0),
    is_closed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE moderation_results (
    id SERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed')),
    is_violation BOOLEAN NULL,
    probability FLOAT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP NULL
);
"""


@pytest_asyncio.fixture
async def pool(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/moderation_test"),
    )
    pool = await create_pool()
    await pool.execute(SCHEMA_SQL)
    yield pool
    await close_pool(pool)


@pytest.mark.asyncio
async def test_postgres_repositories_create_and_get(pool):
    user_repo = UserRepository(pool)
    item_repo = ItemRepository(pool)

    await user_repo.create(1, False)
    await item_repo.create(
        item_id=1001,
        seller_id=1,
        name="Phone",
        description="Desc",
        category=5,
        images_qty=2,
    )

    user = await user_repo.get_by_seller_id(1)
    item = await item_repo.get_by_item_id(1001)

    assert user == {"seller_id": 1, "is_verified_seller": False}
    assert item["item_id"] == 1001
    assert item["is_closed"] is False


@pytest.mark.asyncio
async def test_close_and_delete_removes_item_and_results(pool):
    user_repo = UserRepository(pool)
    item_repo = ItemRepository(pool)
    moderation_repo = ModerationResultRepository(pool)

    await user_repo.create(2, True)
    await item_repo.create(
        item_id=2001,
        seller_id=2,
        name="Laptop",
        description="Nice laptop",
        category=10,
        images_qty=3,
    )
    task = await moderation_repo.create_pending(2001)

    task_ids = await moderation_repo.list_task_ids_by_item_id(2001)
    assert task_ids == [task["id"]]

    closed = await item_repo.close_and_delete(2001)
    assert closed is True

    item = await item_repo.get_by_item_id(2001)
    task_after = await moderation_repo.get_by_id(task["id"])

    assert item is None
    assert task_after is None
