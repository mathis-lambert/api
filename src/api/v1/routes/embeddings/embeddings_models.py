from typing import List, Optional

from pydantic import BaseModel


class EmbeddingsRequest(BaseModel):
    input: List[str]
    model: str


class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingsUsage(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingsResponse(BaseModel):
    id: str
    object: str = "list"
    model: str
    data: List[EmbeddingData]
    usage: EmbeddingsUsage
