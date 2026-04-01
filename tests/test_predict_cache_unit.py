from fastapi.testclient import TestClient
from app.main import app


class FakeCache:
    def __init__(self, item_value=None):
        self.item_value = item_value
        self.set_calls = []

    async def get_item_prediction(self, item_id: int):
        return self.item_value

    async def set_item_prediction(self, item_id: int, value: dict):
        self.set_calls.append((item_id, value))


def test_predict_returns_cached_value_without_model():
    cache = FakeCache(item_value={"is_violation": True, "probability": 0.99})

    with TestClient(app) as client:
        client.app.state.prediction_cache = cache
        client.app.state.model = None

        response = client.post(
            "/predict",
            json={
                "seller_id": 1,
                "is_verified_seller": False,
                "item_id": 100,
                "name": "Телефон",
                "description": "Описание",
                "category": 5,
                "images_qty": 1,
            },
        )

        assert response.status_code == 200
        assert response.json() == {"is_violation": True, "probability": 0.99}
