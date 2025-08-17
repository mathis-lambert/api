from pydantic import BaseModel


class GetModelResponse(BaseModel):
    model: dict


class ListModelsResponse(BaseModel):
    models: list
