from fastapi.testclient import TestClient


def test_embeddings_ok(client: TestClient):
    payload = {"model": "mistral-embed", "input": ["a", "b"]}
    r = client.post("/v1/embeddings", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "list"
    assert len(body["data"]) == 2


def test_embeddings_validation_error(client: TestClient):
    # no input -> 400
    payload = {"model": "mistral-embed", "input": []}
    r = client.post("/v1/embeddings", json=payload)
    assert r.status_code == 400


