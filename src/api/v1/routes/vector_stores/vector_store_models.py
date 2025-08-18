from typing import List, Dict, Optional

from pydantic import BaseModel, Field


class VectorStore(BaseModel):
    id: str
    object: str = "vector_store"
    name: str
    created_at: int
    usage_bytes: int = 0


class CreateVectorStoreRequest(BaseModel):
    name: str = Field(..., description="Vector store name (Qdrant collection)")


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


class UpdateVectorStoreRequest(BaseModel):
    model: str = Field(default="text-embedding-3-large", description="Embedding model to use")
    chunks: List[str] = Field(..., description="List of text chunks to encode")
    metadata: Optional[List[Dict]] = Field(None, description="List of corresponding metadata")


class UpdateVectorStoreResponse(BaseModel):
    success: bool
    message: str
    chunks_added: int


class DeleteVectorStoreResponse(BaseModel):
    success: bool
    message: str
