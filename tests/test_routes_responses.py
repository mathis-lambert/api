from fastapi.testclient import TestClient


def test_responses_non_stream(client: TestClient):
    payload = {
        "model": "openai/gpt-4.1-mini",
        "input": "Hello!",
        "stream": False,
    }
    r = client.post("/v1/responses", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "response"
    logs = client.app.mongodb_client._collections.get("llm_requests", [])
    assert logs
    record = logs[-1]
    assert record["operation"] == "responses"
    assert record["status_code"] == 200
    assert record["usage"]["total_tokens"] == 2


def test_responses_stream(client: TestClient):
    payload = {
        "model": "openai/gpt-4.1-mini",
        "input": "Hello!",
        "stream": True,
    }
    with client.stream("POST", "/v1/responses", json=payload) as r:
        assert r.status_code == 200
        list(r.iter_lines())
    logs = client.app.mongodb_client._collections.get("llm_requests", [])
    assert logs
    record = logs[-1]
    assert record["operation"] == "responses"
    assert record["status_code"] == 200
    assert record["usage"] is None
