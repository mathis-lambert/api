import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from api.classes.text_generation import TextGeneration
from api.classes.embeddings import Embeddings


class DummyProvider:
    def __init__(self):
        self.complete = AsyncMock(return_value="result")
        self.generate_embeddings = AsyncMock(
            return_value={"data": [{"object": "embedding", "embedding": [0.1, 0.2]}]}
        )
        self.check_model = AsyncMock()
        self.list_models = AsyncMock(return_value=["model1"])

    async def stream(self, *args, **kwargs):
        yield "chunk1", None
        yield "chunk2", "stop"


@pytest.mark.asyncio
async def test_text_generation_complete():
    provider = DummyProvider()
    tg = TextGeneration(provider, SimpleNamespace(format_response=lambda r, j: {"formatted": r, "job_id": j}))
    result = await tg.complete("model", [], 0.7, 10, 0.9, "job")
    assert result == {"formatted": "result", "job_id": "job"}
    provider.complete.assert_awaited_once()


@pytest.mark.asyncio
async def test_text_generation_stream():
    provider = DummyProvider()
    tg = TextGeneration(provider, SimpleNamespace())
    chunks = []
    async for c in tg.generate_stream_response("model", [], 0.7, 10, 0.9, "job"):
        chunks.append(c)
    assert chunks[-1]["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_embeddings_generate_embeddings_dict():
    provider = DummyProvider()
    embed = Embeddings(provider, SimpleNamespace(
        embedding_to_points=lambda i, d: "points",
        embedding_to_tuple=lambda i, d: ([0], [[0.1, 0.2]], [{}]),
        format_embeddings=lambda i, d, j: {"job_id": j, "embeddings": d},
    ))
    data = await embed.generate_embeddings("model", ["a"], "job")
    assert data["job_id"] == "job"
    provider.generate_embeddings.assert_awaited_once()


@pytest.mark.asyncio
async def test_embeddings_output_tuple():
    provider = DummyProvider()
    utils = SimpleNamespace(
        embedding_to_points=lambda i, d: "points",
        embedding_to_tuple=lambda i, d: ([0], [[0.1, 0.2]], [{}]),
        format_embeddings=lambda i, d, j: {"job_id": j, "embeddings": d},
    )
    embed = Embeddings(provider, utils)
    ids, vectors, payloads = await embed.generate_embeddings(
        "model", ["a"], "job", output_format="tuple"
    )
    assert ids == [0]
    assert vectors == [[0.1, 0.2]]
    assert payloads == [{}]
