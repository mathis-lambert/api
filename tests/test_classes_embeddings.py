import pytest

from api.classes.embeddings import Embeddings
from api.providers.registry import ProviderRegistry
from api.utils import InferenceUtils


class DummyProvider:
    name = "mistral"

    async def create_embeddings(self, model, inputs):
        return {"data": [{"object": "embedding", "embedding": [0.1, 0.2, 0.3]} for _ in inputs]}


def build_registry():
    reg = ProviderRegistry()
    reg.register(DummyProvider())
    return reg


@pytest.mark.asyncio
async def test_generate_embeddings_default_format():
    e = Embeddings(build_registry(), InferenceUtils())
    out = await e.generate_embeddings(model="mistral-embed", inputs=["abc"], job_id="jid")
    assert out["object"] == "list"
    assert len(out["data"]) == 1


@pytest.mark.asyncio
async def test_generate_embeddings_tuple_format():
    e = Embeddings(build_registry(), InferenceUtils())
    ids, vectors, payloads = await e.generate_embeddings(
        model="mistral-embed", inputs=["abc"], job_id="jid", output_format="tuple"
    )
    assert ids == [0]
    assert len(vectors[0]) == 3
    assert payloads[0]["source_text"] == "abc"


