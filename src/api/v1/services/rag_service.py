import json
from typing import Dict, List

from api.classes import Embeddings
from api.databases import MongoDBConnector, QdrantConnector
from api.utils import CustomLogger

logger = CustomLogger.get_logger(__name__)


class RagService:
    def __init__(
        self,
        embeddings: Embeddings,
        qdrant_client: QdrantConnector,
        mongo_client: MongoDBConnector,
    ):
        self.embeddings = embeddings
        self.qdrant_client = qdrant_client
        self.mongo_client = mongo_client

    async def encode_to_collection(
        self,
        collection_name: str,
        chunks: list[str],
        model: str,
        encoding_format: str = "float",
        job_id: str | None = None,
    ):
        if not await self.qdrant_client.get_collection(collection_name):
            await self.qdrant_client.create_collection(collection_name=collection_name)
            logger.info(f"Collection {collection_name} created with")

        ids, vectors, payloads = await self.embeddings.generate_embeddings(
            model=model,
            inputs=chunks,
            job_id=job_id,
            encoding_format=encoding_format,
            output_format="tuple",
        )
        await self.qdrant_client.batch_upsert(
            collection_name=collection_name,
            indexes=ids,
            vectors=vectors,
            payloads=payloads,
        )
        collection_info = await self.qdrant_client.get_collection(collection_name)
        return {
            "collection_name": collection_name,
            "info": json.loads(collection_info.model_dump_json()),
        }

    async def retrieve_in_collection(
        self,
        collection_name: str,
        query: str,
        model: str,
        limit: int = 5,
        job_id: str | None = None,
    ) -> List[Dict]:
        ids, vectors, payloads = await self.embeddings.generate_embeddings(
            model=model,
            inputs=[query],
            job_id=job_id,
            encoding_format="float",
            output_format="tuple",
        )
        results = await self.qdrant_client.search_in_collection(
            collection_name=collection_name,
            query_vector=vectors[0],
            limit=limit,
        )
        return results
