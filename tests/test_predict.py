from fastapi.testclient import TestClient

from main import app


class FakeModel:
    def __init__(self, prediction, probability):
        self.prediction = prediction
        self.probability = probability

    def predict(self, features):
        return [self.prediction]

    def predict_proba(self, features):
        return [[1 - self.probability, self.probability]]


def valid_payload(**overrides):
    payload = {
        "seller_id": 1,
        "is_verified_seller": False,
        "item_id": 100,
        "name": "Ноутбук",
        "description": "Отличное состояние",
        "category": 10,
        "images_qty": 2,
    }
    payload.update(overrides)
    return payload


def test_predict_success():
    with TestClient(app) as client:
        response = client.post("/predict", json=valid_payload())
        
        assert response.status_code == 200
        assert isinstance(response.json()["is_violation"], bool)
        assert isinstance(response.json()["probability"], float)


def test_predict_success_true():
    with TestClient(app) as client:
        client.app.state.model = FakeModel(prediction=1, probability=0.91)

        response = client.post("/predict", json=valid_payload())

        assert response.status_code == 200
        data = response.json()
        assert data["is_violation"] is True
        assert data["probability"] == 0.91


def test_predict_success_false():
    with TestClient(app) as client:
        client.app.state.model = FakeModel(prediction=0, probability=0.08)

        response = client.post("/predict", json=valid_payload())

        assert response.status_code == 200
        data = response.json()
        assert data["is_violation"] is False
        assert data["probability"] == 0.08


def test_predict_validation_error_wrong_type():
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json=valid_payload(images_qty="many")
        )

        assert response.status_code == 422


def test_predict_model_unavailable():
    with TestClient(app) as client:
        client.app.state.model = None

        response = client.post("/predict", json=valid_payload())

        assert response.status_code == 503
        assert response.json() == {"detail": "Model is not available"}
