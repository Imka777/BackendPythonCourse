from fastapi.testclient import TestClient

from app.main import app
from app.repositories.items import ItemRepository
from app.repositories.moderation_results import ModerationResultRepository


class FakeKafkaProducer:
    def __init__(self):
        self.sent_messages = []
        self.dlq_messages = []

    async def send_moderation_request(self, item_id: int, task_id: int):
        message = {"item_id": item_id, "task_id": task_id}
        self.sent_messages.append(message)
        return message

    async def send_to_dlq(self, original_message: dict, error: str, retry_count: int = 1):
        message = {
            "original_message": original_message,
            "error": error,
            "retry_count": retry_count,
        }
        self.dlq_messages.append(message)
        return message


def test_async_predict_creates_task(monkeypatch):
    async def fake_get_item(self, item_id: int):
        return {
            "item_id": item_id,
            "seller_id": 1,
            "name": "Phone",
            "description": "Good phone",
            "category": 10,
            "images_qty": 2,
        }

    async def fake_create_pending(self, item_id: int):
        return {
            "id": 123,
            "item_id": item_id,
            "status": "pending",
            "is_violation": None,
            "probability": None,
            "error_message": None,
            "created_at": None,
            "processed_at": None,
        }

    monkeypatch.setattr(ItemRepository, "get_by_item_id", fake_get_item)
    monkeypatch.setattr(ModerationResultRepository, "create_pending", fake_create_pending)

    fake_kafka = FakeKafkaProducer()

    with TestClient(app) as client:
        client.app.state.db_pool = object()
        client.app.state.kafka_producer = fake_kafka

        response = client.post("/async_predict", json={"item_id": 100})

        assert response.status_code == 202
        assert response.json() == {
            "task_id": 123,
            "status": "pending",
            "message": "Moderation request accepted",
        }
        assert fake_kafka.sent_messages == [{"item_id": 100, "task_id": 123}]


def test_moderation_result_returns_status(monkeypatch):
    async def fake_get_by_id(self, task_id: int):
        return {
            "id": task_id,
            "item_id": 10289,
            "status": "completed",
            "is_violation": True,
            "probability": 0.87,
            "error_message": None,
            "created_at": None,
            "processed_at": None,
        }

    monkeypatch.setattr(ModerationResultRepository, "get_by_id", fake_get_by_id)

    with TestClient(app) as client:
        client.app.state.db_pool = object()
        client.app.state.prediction_cache = None

        response = client.get("/moderation_result/123")

        assert response.status_code == 200
        assert response.json() == {
            "task_id": 123,
            "status": "completed",
            "is_violation": True,
            "probability": 0.87,
            "error_message": None,
        }
