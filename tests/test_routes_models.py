from fastapi.testclient import TestClient


def test_list_models(client: TestClient):
    r = client.get("/v1/models/")
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "list"
    assert isinstance(body["data"], list)
    # Should contain at least the dummy models
    assert any(m["owned_by"] in {"mistral", "openai", "anthropic", "google"} for m in body["data"]) 


def test_read_model(client: TestClient):
    r = client.get("/v1/models/mistral-test-001")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "mistral-test-001"


