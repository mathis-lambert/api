from mistralai.models import RetrieveModelV1ModelsModelIDGetResponseRetrieveModelV1ModelsModelIDGet, ModelList
from pydantic import BaseModel


class GetModelResponse(BaseModel):
    model: RetrieveModelV1ModelsModelIDGetResponseRetrieveModelV1ModelsModelIDGet


class ListModelsResponse(BaseModel):
    models: ModelList
