from typing import List, Optional

from pydantic import BaseModel


class Model(BaseModel):
    id: str
    object: str = "model"
    owned_by: Optional[str] = None


class ListModelsResponse(BaseModel):
    object: str = "list"
    data: List[Model]
