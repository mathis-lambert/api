import json

import httpx
import pytest

from api.classes.openrouter_proxy import OpenRouterProxy


@pytest.mark.asyncio
async def test_openrouter_proxy_non_stream():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            status_code=200,
            json={
                "id": "resp1",
                "object": "chat.completion",
                "created": 0,
                "model": body.get("model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                        "logprobs": None,
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(
        transport=transport, base_url="https://openrouter.ai/api/v1"
    )
    proxy = OpenRouterProxy(http_client=client)
    resp = await proxy.chat_completions(
        {
            "model": "openrouter/test-model",
            "messages": [{"role": "user", "content": "hi"}],
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "chat.completion"
    await client.aclose()


@pytest.mark.asyncio
async def test_openrouter_proxy_stream():
    def handler(_request: httpx.Request) -> httpx.Response:
        content = (
            b'data: {"id":"resp1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","content":"ok"}}]}\n\n'
            b"data: [DONE]\n\n"
        )
        return httpx.Response(
            status_code=200,
            headers={"content-type": "text/event-stream"},
            content=content,
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(
        transport=transport, base_url="https://openrouter.ai/api/v1"
    )
    proxy = OpenRouterProxy(http_client=client)
    async with proxy.stream_chat_completions(
        {"model": "openrouter/test-model", "messages": [], "stream": True}
    ) as resp:
        chunks = []
        async for chunk in resp.aiter_bytes():
            chunks.append(chunk)
    assert b"data:" in b"".join(chunks)
    await client.aclose()
