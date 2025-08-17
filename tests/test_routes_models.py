from fastapi.testclient import TestClient


def test_list_models(client: TestClient):
    r = client.get("/v1/models/")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("data"), list)
    # Sans provider registry, la liste peut être vide si OPENROUTER_API_KEY absent


def test_read_model(client: TestClient):
    r = client.get("/v1/models/some-model-id")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "some-model-id"
