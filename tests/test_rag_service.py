import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.v1.services.rag_service import RagService


class DummyEmbeddings:
    def __init__(self):
        self.generate_embeddings = AsyncMock(return_value=([0], [[0.1, 0.2]], [{}]))


@pytest.mark.asyncio
async def test_encode_to_collection():
    with patch.dict(os.environ, {"QDRANT_API_KEY": "k", "QDRANT_URL": "u"}):
        qdrant = MagicMock()
        qdrant.get_collection = AsyncMock(side_effect=[None, MagicMock(model_dump_json=lambda: "{}")])
        qdrant.create_collection = AsyncMock(return_value=True)
        qdrant.batch_upsert = AsyncMock()

        mongo = MagicMock()
        service = RagService(DummyEmbeddings(), qdrant, mongo)
        res = await service.encode_to_collection("col", ["text"], "model")
        qdrant.create_collection.assert_awaited()
        qdrant.batch_upsert.assert_awaited()
        assert res["collection_name"] == "col"


@pytest.mark.asyncio
async def test_retrieve_in_collection():
    with patch.dict(os.environ, {"QDRANT_API_KEY": "k", "QDRANT_URL": "u"}):
        qdrant = MagicMock()
        qdrant.search_in_collection = AsyncMock(return_value=[{"payload": {}, "score": 0.9}])
        embeddings = DummyEmbeddings()
        service = RagService(embeddings, qdrant, MagicMock())
        results = await service.retrieve_in_collection("col", "q", "model")
        embeddings.generate_embeddings.assert_awaited()
        qdrant.search_in_collection.assert_awaited_with(collection_name="col", query_vector=[0.1,0.2], limit=5)
        assert results[0]["score"] == 0.9
