from fastapi.testclient import TestClient

from event_sourcing.main import app


def test_root() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
