from typing import List

from pydantic import BaseModel


class EmbeddingsRequest(BaseModel):
    chunks: List[str]
    model: str


class Embedding(BaseModel):
    index: int
    embedding: List[float]
    payload: dict
    object: str


class EmbeddingsResponse(BaseModel):
    embeddings: List[Embedding]
    job_id: str
