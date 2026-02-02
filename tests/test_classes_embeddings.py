import pytest

from api.classes.embeddings import Embeddings


@pytest.mark.asyncio
async def test_generate_embeddings_default_format():
    e = Embeddings()
    out = await e.generate_embeddings(
        model="text-embedding-3-small", inputs=["abc"], job_id="jid"
    )
    assert out["object"] == "list"
    assert len(out["data"]) == 1


@pytest.mark.asyncio
async def test_generate_embeddings_tuple_format():
    e = Embeddings()
    ids, vectors, payloads = await e.generate_embeddings(
        model="text-embedding-3-small",
        inputs=["abc"],
        job_id="jid",
        output_format="tuple",
    )
    assert ids == [0]
    assert len(vectors[0]) == 3
    assert payloads[0]["source_text"] == "abc"
