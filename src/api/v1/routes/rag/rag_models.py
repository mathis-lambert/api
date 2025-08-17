from typing import Dict, List

from pydantic import BaseModel


class RagEncodeRequest(BaseModel):
    chunks: List[str]
    model: str = "mistral-embed"
    provider: str = "mistral"


class RagEncodeResponse(BaseModel):
    collection_name: str
    success: bool


class RagRetrieveRequest(BaseModel):
    query: str
    model: str = "mistral-embed"
    limit: int = 5
    provider: str = "mistral"


class RetrieveResult(BaseModel):
    score: float
    payload: Dict


class RagRetrieveResponse(BaseModel):
    collection_name: str
    results: List[RetrieveResult]
    success: bool
