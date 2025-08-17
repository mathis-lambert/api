from typing import List

from pydantic import BaseModel, Field


class VectorStore(BaseModel):
    id: str
    object: str = "vector_store"
    name: str
    created_at: int
    usage_bytes: int = 0


class CreateVectorStoreRequest(BaseModel):
    name: str = Field(..., description="Nom du vector store (collection Qdrant)")


class CreateVectorStoreResponse(BaseModel):
    id: str
    object: str = "vector_store"
    name: str
    created_at: int
    usage_bytes: int = 0


class ListVectorStoresResponse(BaseModel):
    data: List[VectorStore]


class VectorStoreSearchRequest(BaseModel):
    query: str
    model: str
    limit: int = 5
