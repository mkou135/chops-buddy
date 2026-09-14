from fastapi.testclient import TestClient

from chops_buddy.api.main import app


def test_health_reports_commit() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["commit"], str)
