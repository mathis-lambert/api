import pytest
from api.classes.text_generation import TextGeneration


@pytest.mark.asyncio
async def test_complete_returns_openai_like_response():
    tg = TextGeneration()
    resp = await tg.complete(
        model="openrouter/test-model",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.1,
        max_tokens=10,
        top_p=0.9,
        job_id="jid",
    )
    assert resp["object"] == "chat.completion"
    assert resp["choices"][0]["message"]["role"] == "assistant"


@pytest.mark.asyncio
async def test_generate_stream_response_yields_chunks():
    tg = TextGeneration()
    gen = tg.generate_stream_response(
        model="openrouter/test-model",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.1,
        max_tokens=10,
        top_p=0.9,
        job_id="jid",
    )
    chunks = []
    async for c in gen:
        chunks.append(c)
    assert len(chunks) >= 2
    assert "chunk" in chunks[0]
