import asyncio

import pytest

from api.classes.text_generation import TextGeneration
from api.providers.registry import ProviderRegistry
from api.utils import InferenceUtils


class DummyProvider:
    name = "mistral"

    async def chat_complete(self, **kwargs):
        return InferenceUtils.chat_openai_response(model=kwargs["model"], content="hello")

    async def chat_stream(self, **kwargs):  # pragma: no cover - trivial
        yield "a", None
        yield "b", "stop"


def build_registry():
    reg = ProviderRegistry()
    reg.register(DummyProvider())
    return reg


@pytest.mark.asyncio
async def test_complete_returns_openai_like_response():
    tg = TextGeneration(build_registry(), InferenceUtils())
    resp = await tg.complete(
        model="mistral-small",
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
    tg = TextGeneration(build_registry(), InferenceUtils())
    gen = tg.generate_stream_response(
        model="mistral-small",
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


