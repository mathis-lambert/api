from mistralai.models import (
    ModelList,
    RetrieveModelV1ModelsModelIDGetResponseRetrieveModelV1ModelsModelIDGet,
)
from pydantic import BaseModel


class GetModelResponse(BaseModel):
    model: RetrieveModelV1ModelsModelIDGetResponseRetrieveModelV1ModelsModelIDGet


class ListModelsResponse(BaseModel):
    models: ModelList
