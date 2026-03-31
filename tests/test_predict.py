from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def valid_payload(**overrides):
    payload = {
        "seller_id": 1,
        "is_verified_seller": False,
        "item_id": 100,
        "name": "Ноутбук",
        "description": "Хорошее состояние",
        "category": 10,
        "images_qty": 1,
    }
    payload.update(overrides)
    return payload


def test_predict_positive_result():
    response = client.post(
        "/predict",
        json=valid_payload(is_verified_seller=False, images_qty=0),
    )

    assert response.status_code == 200
    assert response.json() is True


def test_predict_negative_result():
    response = client.post(
        "/predict",
        json=valid_payload(is_verified_seller=True, images_qty=0),
    )

    assert response.status_code == 200
    assert response.json() is False


def test_validation_missing_required_field():
    payload = valid_payload()
    payload.pop("seller_id")

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_validation_wrong_type():
    response = client.post(
        "/predict",
        json=valid_payload(images_qty="many"),
    )

    assert response.status_code == 422


def test_business_logic_error(monkeypatch):
    def mock_predict_violation(_payload):
        raise RuntimeError("Unexpected business error")

    monkeypatch.setattr(main, "predict_violation", mock_predict_violation)

    response = client.post("/predict", json=valid_payload())

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal prediction error"}
