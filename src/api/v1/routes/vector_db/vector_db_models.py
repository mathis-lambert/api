from typing import List

from pydantic import BaseModel
from qdrant_client.models import CollectionInfo


class CollectionInfoResponse(BaseModel):
    name: str
    info: CollectionInfo


class CollectionsResponse(BaseModel):
    collections: List[CollectionInfoResponse]
