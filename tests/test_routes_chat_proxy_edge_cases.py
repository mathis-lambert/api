import asyncio
import json

import httpx
from fastapi.testclient import TestClient

from api.classes import OpenRouterProxy
from api.v1.services.get_classes import (
    get_openrouter_proxy as _get_openrouter_proxy_dep,
)


def _override_proxy(client: TestClient, handler):
    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(
        transport=transport, base_url="https://openrouter.ai/api/v1"
    )
    proxy = OpenRouterProxy(http_client=async_client)
    client.app.dependency_overrides[_get_openrouter_proxy_dep] = lambda: proxy
    return proxy


def _clear_override(client: TestClient, proxy: OpenRouterProxy):
    client.app.dependency_overrides.pop(_get_openrouter_proxy_dep, None)
    if getattr(proxy, "_client", None) is not None:
        asyncio.run(proxy._client.aclose())


def test_chat_completions_stream_without_usage_logs_null(client: TestClient):
    def handler(request: httpx.Request) -> httpx.Response:
        json.loads(request.content.decode("utf-8"))
        content = b'data: {"id":"resp1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","content":"hi"}}]}\n\n'
        return httpx.Response(
            status_code=200,
            headers={"content-type": "text/event-stream"},
            content=content,
        )

    proxy = _override_proxy(client, handler)
    try:
        payload = {
            "model": "mistral-small",
            "messages": [{"role": "user", "content": "Bonjour"}],
            "stream": True,
        }
        with client.stream("POST", "/v1/chat/completions", json=payload) as r:
            assert r.status_code == 200
            list(r.iter_lines())
        logs = client.app.mongodb_client._collections.get("llm_requests", [])
        assert logs
        record = logs[-1]
        assert record["usage"] is None
    finally:
        _clear_override(client, proxy)


def test_chat_completions_upstream_error_pass_through(client: TestClient):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            json={"error": {"message": "bad key", "type": "invalid_request_error"}},
        )

    proxy = _override_proxy(client, handler)
    try:
        payload = {
            "model": "mistral-small",
            "messages": [{"role": "user", "content": "Bonjour"}],
            "stream": False,
        }
        r = client.post("/v1/chat/completions", json=payload)
        assert r.status_code == 401
        body = r.json()
        assert body["error"]["message"] == "bad key"
        logs = client.app.mongodb_client._collections.get("llm_requests", [])
        assert logs
        record = logs[-1]
        assert record["status_code"] == 401
        assert record["error"]["message"] == "bad key"
    finally:
        _clear_override(client, proxy)
