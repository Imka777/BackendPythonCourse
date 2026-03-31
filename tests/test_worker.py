import pytest

from app.repositories.items import ItemRepository
from app.repositories.moderation_results import ModerationResultRepository
from app.repositories.users import UserRepository
from app.workers.moderation_worker import process_message


class FakeModel:
    def __init__(self, prediction, probability):
        self.prediction = prediction
        self.probability = probability

    def predict(self, features):
        return [self.prediction]

    def predict_proba(self, features):
        return [[1 - self.probability, self.probability]]


class FakeKafkaClient:
    def __init__(self):
        self.dlq_messages = []

    async def send_to_dlq(self, original_message: dict, error: str, retry_count: int = 1):
        self.dlq_messages.append(
            {
                "original_message": original_message,
                "error": error,
                "retry_count": retry_count,
            }
        )


@pytest.mark.asyncio
async def test_worker_processes_message_success(monkeypatch):
    completed_calls = []

    async def fake_get_item(self, item_id: int):
        return {
            "item_id": item_id,
            "seller_id": 1,
            "name": "Phone",
            "description": "Short description",
            "category": 5,
            "images_qty": 0,
        }

    async def fake_get_user(self, seller_id: int):
        return {
            "seller_id": seller_id,
            "is_verified_seller": False,
        }

    async def fake_update_completed(self, task_id: int, is_violation: bool, probability: float):
        completed_calls.append(
            {
                "task_id": task_id,
                "is_violation": is_violation,
                "probability": probability,
            }
        )

    monkeypatch.setattr(ItemRepository, "get_by_item_id", fake_get_item)
    monkeypatch.setattr(UserRepository, "get_by_seller_id", fake_get_user)
    monkeypatch.setattr(ModerationResultRepository, "update_completed", fake_update_completed)

    model = FakeModel(prediction=1, probability=0.91)
    kafka_client = FakeKafkaClient()

    await process_message(
        {"task_id": 10, "item_id": 100},
        pool=object(),
        model=model,
        kafka_client=kafka_client,
    )

    assert completed_calls == [
        {
            "task_id": 10,
            "is_violation": True,
            "probability": 0.91,
        }
    ]
    assert kafka_client.dlq_messages == []


@pytest.mark.asyncio
async def test_worker_sends_to_dlq_on_error(monkeypatch):
    failed_calls = []

    async def fake_get_item(self, item_id: int):
        return None

    async def fake_update_failed(self, task_id: int, error_message: str):
        failed_calls.append(
            {
                "task_id": task_id,
                "error_message": error_message,
            }
        )

    monkeypatch.setattr(ItemRepository, "get_by_item_id", fake_get_item)
    monkeypatch.setattr(ModerationResultRepository, "update_failed", fake_update_failed)

    model = FakeModel(prediction=0, probability=0.05)
    kafka_client = FakeKafkaClient()

    await process_message(
        {"task_id": 11, "item_id": 999},
        pool=object(),
        model=model,
        kafka_client=kafka_client,
    )

    assert failed_calls[0]["task_id"] == 11
    assert "not found" in failed_calls[0]["error_message"]
    assert len(kafka_client.dlq_messages) == 1
    assert kafka_client.dlq_messages[0]["original_message"] == {"task_id": 11, "item_id": 999}
