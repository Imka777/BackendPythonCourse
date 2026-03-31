import os
import pytest
import pytest_asyncio

from db import close_pool, create_pool
from repositories.items import ItemRepository
from repositories.users import UserRepository


TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/moderation_test"
)


CREATE_SCHEMA_SQL = """
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
    images_qty INTEGER NOT NULL CHECK (images_qty >= 0)
);
"""

DROP_SCHEMA_SQL = """
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;
"""


@pytest_asyncio.fixture
async def pool(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    pool = await create_pool()

    await pool.execute(CREATE_SCHEMA_SQL)
    yield pool
    await pool.execute(DROP_SCHEMA_SQL)

    await close_pool(pool)


@pytest.mark.asyncio
async def test_create_user_and_item(pool):
    user_repo = UserRepository(pool)
    item_repo = ItemRepository(pool)

    user = await user_repo.create(seller_id=1, is_verified_seller=True)
    item = await item_repo.create(
        item_id=100,
        seller_id=1,
        name="Телефон",
        description="Описание телефона",
        category=10,
        images_qty=3,
    )

    saved_user = await user_repo.get_by_seller_id(1)
    saved_item = await item_repo.get_by_item_id(100)

    assert user["seller_id"] == 1
    assert user["is_verified_seller"] is True

    assert item["item_id"] == 100
    assert item["seller_id"] == 1

    assert saved_user == {
        "seller_id": 1,
        "is_verified_seller": True,
    }

    assert saved_item["item_id"] == 100
    assert saved_item["seller_id"] == 1
    assert saved_item["name"] == "Телефон"
    assert saved_item["description"] == "Описание телефона"
    assert saved_item["category"] == 10
    assert saved_item["images_qty"] == 3
