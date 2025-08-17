from fastapi.testclient import TestClient


def test_root_ok(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    assert "Welcome" in r.json()["message"]


def test_health_ok(client: TestClient):
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
