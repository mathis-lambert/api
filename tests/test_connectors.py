import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.databases.mongo_db_connector import MongoDBConnector
from api.databases.qdrant_connector import QdrantConnector


class DummyLogger:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def test_mongo_serialize():
    connector = MongoDBConnector(DummyLogger())
    doc = {"_id": connector.object_id("64b8a3000000000000000000"), "value": 1}
    serialized = connector.serialize(doc)
    assert isinstance(serialized["_id"], str)


@pytest.mark.asyncio
async def test_qdrant_create_collection():
    with patch.dict(os.environ, {"QDRANT_API_KEY": "k", "QDRANT_URL": "u"}):
        with patch("api.databases.qdrant_connector.AsyncQdrantClient") as client_cls:
            client = MagicMock()
            client.create_collection = AsyncMock(return_value=True)
            client_cls.return_value = client
            qc = QdrantConnector(DummyLogger())
            await qc.create_collection("col")
            client.create_collection.assert_awaited()
