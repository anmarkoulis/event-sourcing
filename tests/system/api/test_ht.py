from fastapi.testclient import TestClient

from event_sourcing.main import app

client = TestClient(app)


def test_read_main() -> None:
    response = client.get("/ht/")
    assert response.status_code == 200
