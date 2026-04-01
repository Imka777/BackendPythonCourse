from fastapi.testclient import TestClient
from app.main import app


class FakeCache:
    async def get_task_result(self, task_id: int):
        return {
            "task_id": task_id,
            "status": "completed",
            "is_violation": False,
            "probability": 0.12,
            "error_message": None,
        }


def test_moderation_result_returns_cached_value():
    with TestClient(app) as client:
        client.app.state.prediction_cache = FakeCache()
        client.app.state.db_pool = None

        response = client.get("/moderation_result/15")

        assert response.status_code == 200
        assert response.json() == {
            "task_id": 15,
            "status": "completed",
            "is_violation": False,
            "probability": 0.12,
            "error_message": None,
        }
