from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_info():
    r = client.get("/api/v1/info")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Datuvera"
    assert data["version"] == "0.1.0"
