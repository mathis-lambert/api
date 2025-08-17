from fastapi.testclient import TestClient


def test_vector_store_crud_and_search(client: TestClient):
    # Create
    r = client.post("/v1/vector_stores", json={"name": "vs1"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "vs1"

    # List
    r = client.get("/v1/vector_stores")
    assert r.status_code == 200
    data = r.json()["data"]
    assert any(vs["id"] == "vs1" for vs in data)

    # Get
    r = client.get("/v1/vector_stores/vs1")
    assert r.status_code == 200
    assert r.json()["id"] == "vs1"

    # Search -> empty list (fake qdrant)
    r = client.post(
        "/v1/vector_stores/vs1/search",
        json={"query": "hello", "model": "mistral-embed", "limit": 5},
    )
    assert r.status_code == 200
    assert r.json()["object"] == "list"
    assert r.json()["data"] == []
