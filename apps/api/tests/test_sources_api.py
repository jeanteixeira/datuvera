from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SOURCE_PAYLOAD = {
    "name": "demo-api-src",
    "type": "postgresql",
    "host": "datuvera-demo-db",
    "port": 5432,
    "database": "demo",
    "username": "demo",
    "password": "demo",
}


def test_create_source_and_no_password_in_response():
    # create
    r = client.post("/api/v1/sources", json=SOURCE_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == SOURCE_PAYLOAD["name"]
    assert "password" not in data
    src_id = data["id"]

    # get list
    r2 = client.get("/api/v1/sources")
    assert r2.status_code == 200
    lst = r2.json()
    assert any(item["id"] == src_id for item in lst)

    # get by id
    r3 = client.get(f"/api/v1/sources/{src_id}")
    assert r3.status_code == 200
    got = r3.json()
    assert got["id"] == src_id
    assert "password" not in got

    # test connection
    r4 = client.post(f"/api/v1/sources/{src_id}/test")
    assert r4.status_code == 200
    res = r4.json()
    assert res.get("success") is True
