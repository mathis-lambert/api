from fastapi.testclient import TestClient


def test_chat_completions_non_stream(client: TestClient):
    payload = {
        "model": "mistral-small",
        "messages": [{"role": "user", "content": "Bonjour"}],
        "stream": False,
    }
    r = client.post("/v1/chat/completions", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"


def test_chat_completions_stream_sse(client: TestClient):
    payload = {
        "model": "mistral-small",
        "messages": [{"role": "user", "content": "Bonjour"}],
        "stream": True,
    }
    with client.stream("POST", "/v1/chat/completions", json=payload) as r:
        assert r.status_code == 200
        # read a few lines from the stream
        first_chunk = next(r.iter_lines())
        assert isinstance(first_chunk, (bytes, str))


