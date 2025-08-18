import time
import uuid
from typing import List

from api.classes import Embeddings
from api.databases import MongoDBConnector, QdrantConnector
from api.v1.security import (
    ensure_valid_api_key_or_token,
    get_current_user_with_api_key_or_token,
)
from api.v1.services import get_embeddings, get_mongo_client, get_qdrant_client
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from .vector_store_models import (
    CreateVectorStoreRequest,
    CreateVectorStoreResponse,
    DeleteVectorStoreResponse,
    ListVectorStoresResponse,
    UpdateVectorStoreRequest,
    UpdateVectorStoreResponse,
    VectorStore,
    VectorStoreSearchRequest,
)

router = APIRouter(dependencies=[Depends(ensure_valid_api_key_or_token)])


def _collection_to_vector_store(name: str, info) -> VectorStore:
    return VectorStore(
        id=name,
        name=name,
        created_at=int(time.time()),
        usage_bytes=0,
    )


@router.post("", response_model=CreateVectorStoreResponse)
async def create_vector_store(
    body: CreateVectorStoreRequest,
    qdrant: QdrantConnector = Depends(get_qdrant_client),
    mongo: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user_with_api_key_or_token),
):
    # Check logical existence on MongoDB
    existing = await mongo.find_one(
        "vector_db_collections",
        {"name": body.name, "user_id": ObjectId(user["_id"])},
    )
    if existing:
        raise HTTPException(status_code=400, detail="Vector store already exists")

    # Create the Qdrant collection and save in MongoDB
    await qdrant.create_collection(collection_name=body.name)
    await mongo.insert_one(
        "vector_db_collections",
        {"name": body.name, "user_id": ObjectId(user["_id"])},
    )
    info = await qdrant.get_collection(body.name)
    vs = _collection_to_vector_store(body.name, info)
    return vs.model_dump()


@router.get("", response_model=ListVectorStoresResponse)
async def list_vector_stores(
    qdrant: QdrantConnector = Depends(get_qdrant_client),
    mongo: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user_with_api_key_or_token),
):
    user_collections = await mongo.find_many(
        "vector_db_collections",
        {"user_id": ObjectId(user["_id"])},
    )
    data: List[VectorStore] = []
    for c in user_collections:
        info = await qdrant.get_collection(c["name"])
        data.append(_collection_to_vector_store(c["name"], info))
    return {"data": data}


@router.get("/{vector_store_id}", response_model=VectorStore)
async def get_vector_store(
    vector_store_id: str,
    qdrant: QdrantConnector = Depends(get_qdrant_client),
    mongo: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user_with_api_key_or_token),
):
    one = await mongo.find_one(
        "vector_db_collections",
        {"name": vector_store_id, "user_id": ObjectId(user["_id"])},
    )
    if not one:
        raise HTTPException(status_code=404, detail="Vector store not found")
    info = await qdrant.get_collection(vector_store_id)
    return _collection_to_vector_store(vector_store_id, info)


@router.post("/{vector_store_id}/search")
async def search_vector_store(
    vector_store_id: str,
    body: VectorStoreSearchRequest,
    qdrant: QdrantConnector = Depends(get_qdrant_client),
    mongo: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user_with_api_key_or_token),
    embeddings: Embeddings = Depends(get_embeddings),
):
    # Ownership check
    one = await mongo.find_one(
        "vector_db_collections",
        {"name": vector_store_id, "user_id": ObjectId(user["_id"])},
    )
    if not one:
        raise HTTPException(status_code=404, detail="Vector store not found")

    ids, vectors, payloads = await embeddings.generate_embeddings(
        model=body.model,
        inputs=[body.query],
        job_id="",
        output_format="tuple",
    )
    results = await qdrant.search_in_collection(
        collection_name=vector_store_id,
        query_vector=vectors[0],
        limit=body.limit,
    )
    return {"object": "list", "data": results}


@router.put("/{vector_store_id}", response_model=UpdateVectorStoreResponse)
async def update_vector_store(
    vector_store_id: str,
    body: UpdateVectorStoreRequest,
    qdrant: QdrantConnector = Depends(get_qdrant_client),
    mongo: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user_with_api_key_or_token),
    embeddings: Embeddings = Depends(get_embeddings),
):
    # Ownership check
    one = await mongo.find_one(
        "vector_db_collections",
        {"name": vector_store_id, "user_id": ObjectId(user["_id"])},
    )
    if not one:
        raise HTTPException(status_code=404, detail="Vector store not found")

    # Validation de l'entrée
    if not body.chunks:
        raise HTTPException(status_code=400, detail="No input provided")
    
    if len(body.chunks) != len(body.metadata):
        raise HTTPException(status_code=400, detail="Number of chunks must match number of metadata entries")

    job_id: str = str(uuid.uuid4())

    # Generate embeddings for chunks
    ids, vectors, payloads = await embeddings.generate_embeddings(
        model=body.model,
        inputs=body.chunks,
        job_id=job_id,
        output_format="tuple",
    )

    # Add vectors to Qdrant collection
    await qdrant.add_vectors_to_collection(
        collection_name=vector_store_id,
        vectors=vectors,
        payloads=body.metadata,
        ids=ids,
    )

    # Log event to mongodb
    await mongo.log_event(
        user["_id"], job_id, "encode", {
            "collection_name": vector_store_id,
            "model": body.model,
            "chunks_count": len(body.chunks)
        }
    )

    return UpdateVectorStoreResponse(
        success=True,
        message=f"{len(body.chunks)} chunks added to vector store {vector_store_id}",
        chunks_added=len(body.chunks)
    )


@router.delete("/{vector_store_id}", response_model=DeleteVectorStoreResponse)
async def delete_vector_store(
    vector_store_id: str,
    qdrant: QdrantConnector = Depends(get_qdrant_client),
    mongo: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user_with_api_key_or_token),
):
    # Ownership check
    one = await mongo.find_one(
        "vector_db_collections",
        {"name": vector_store_id, "user_id": ObjectId(user["_id"])},
    )
    if not one:
        raise HTTPException(status_code=404, detail="Vector store not found")

    # Delete collection from Qdrant
    await qdrant.delete_collection(collection_name=vector_store_id)
    
    # Delete from MongoDB
    await mongo.delete_one(
        "vector_db_collections",
        {"name": vector_store_id, "user_id": ObjectId(user["_id"])},
    )

    return DeleteVectorStoreResponse(
        success=True,
        message=f"Vector store {vector_store_id} successfully deleted"
    )
