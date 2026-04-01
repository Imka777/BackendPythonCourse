from fastapi.testclient import TestClient

import app.main as main
from app.main import app
from app.repositories.items import ItemRepository
from app.repositories.users import UserRepository


class FakeModel:
    def __init__(self, prediction, probability):
        self.prediction = prediction
        self.probability = probability

    def predict(self, features):
        return [self.prediction]

    def predict_proba(self, features):
        return [[1 - self.probability, self.probability]]


async def fake_create_pool():
    return object()


async def fake_close_pool(_pool):
    return None


def test_simple_predict_success_true(monkeypatch):
    async def fake_get_item(self, item_id: int):
        return {
            "item_id": item_id,
            "seller_id": 1,
            "name": "Телефон",
            "description": "Короткое описание",
            "category": 5,
            "images_qty": 0,
        }

    async def fake_get_user(self, seller_id: int):
        return {
            "seller_id": seller_id,
            "is_verified_seller": False,
        }

    monkeypatch.setattr(main, "create_pool", fake_create_pool)
    monkeypatch.setattr(main, "close_pool", fake_close_pool)
    monkeypatch.setattr(ItemRepository, "get_by_item_id", fake_get_item)
    monkeypatch.setattr(UserRepository, "get_by_seller_id", fake_get_user)

    with TestClient(app) as client:
        client.app.state.model = FakeModel(prediction=1, probability=0.93)

        response = client.get("/simple_predict", params={"item_id": 10541})

        assert response.status_code == 200
        data = response.json()
        assert data["is_violation"] is True
        assert data["probability"] == 0.93


def test_simple_predict_success_false(monkeypatch):
    async def fake_get_item(self, item_id: int):
        return {
            "item_id": item_id,
            "seller_id": 2,
            "name": "Ноутбук",
            "description": "Большое хорошее описание",
            "category": 20,
            "images_qty": 5,
        }

    async def fake_get_user(self, seller_id: int):
        return {
            "seller_id": seller_id,
            "is_verified_seller": True,
        }

    monkeypatch.setattr(main, "create_pool", fake_create_pool)
    monkeypatch.setattr(main, "close_pool", fake_close_pool)
    monkeypatch.setattr(ItemRepository, "get_by_item_id", fake_get_item)
    monkeypatch.setattr(UserRepository, "get_by_seller_id", fake_get_user)

    with TestClient(app) as client:
        client.app.state.model = FakeModel(prediction=0, probability=0.07)

        response = client.get("/simple_predict", params={"item_id": 10542})

        assert response.status_code == 200
        data = response.json()
        assert data["is_violation"] is False
        assert data["probability"] == 0.07


def test_simple_predict_validation_error(monkeypatch):
    monkeypatch.setattr(main, "create_pool", fake_create_pool)
    monkeypatch.setattr(main, "close_pool", fake_close_pool)

    with TestClient(app) as client:
        response = client.get("/simple_predict", params={"item_id": "abc"})
        assert response.status_code == 422


def test_simple_predict_real():
    with TestClient(app) as client:
        response = client.get("/simple_predict?item_id=1001")  # в бд есть такой айтем

        assert response.status_code == 200
        data = response.json()
        assert "is_violation" in data
        assert "probability" in data


def test_simple_predict_real_not_found():
    with TestClient(app) as client:
        response = client.get("/simple_predict?item_id=99999999")  # в бд нет такого айтема
        assert response.status_code == 404