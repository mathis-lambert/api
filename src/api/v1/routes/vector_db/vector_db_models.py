from typing import Any, Dict, List

from pydantic import BaseModel
from qdrant_client.models import CollectionInfo


class CollectionInfoResponse(BaseModel):
    name: str
    info: CollectionInfo


class CollectionsResponse(BaseModel):
    collections: List[CollectionInfoResponse]


class VectorData(BaseModel):
    id: int
    vector: List[float]
    payload: Dict[str, Any] = {}


class QueryVector(BaseModel):
    vector: List[float]
    top: int = 5
