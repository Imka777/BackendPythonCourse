from fastapi.testclient import TestClient
from app.main import app
from app.repositories.items import ItemRepository
from app.repositories.moderation_results import ModerationResultRepository


class FakeCache:
    def __init__(self):
        self.deleted_items = []
        self.deleted_tasks = []

    async def delete_item_prediction(self, item_id: int):
        self.deleted_items.append(item_id)

    async def delete_task_results(self, task_ids):
        self.deleted_tasks.extend(task_ids)


def test_close_item_deletes_postgres_and_redis(monkeypatch):
    async def fake_get_by_item_id(self, item_id: int):
        return {
            "item_id": item_id,
            "seller_id": 1,
            "name": "Phone",
            "description": "Desc",
            "category": 5,
            "images_qty": 1,
            "is_closed": False,
        }

    async def fake_list_task_ids_by_item_id(self, item_id: int):
        return [10, 11]

    async def fake_close_and_delete(self, item_id: int):
        return True

    monkeypatch.setattr(ItemRepository, "get_by_item_id", fake_get_by_item_id)
    monkeypatch.setattr(ModerationResultRepository, "list_task_ids_by_item_id", fake_list_task_ids_by_item_id)
    monkeypatch.setattr(ItemRepository, "close_and_delete", fake_close_and_delete)

    cache = FakeCache()

    with TestClient(app) as client:
        client.app.state.db_pool = object()
        client.app.state.prediction_cache = cache

        response = client.post("/close", json={"item_id": 1001})

        assert response.status_code == 200
        assert response.json() == {
            "item_id": 1001,
            "status": "closed",
            "message": "Item was closed and removed from storages",
        }
        assert cache.deleted_items == [1001]
        assert cache.deleted_tasks == [10, 11]
