from fastapi import APIRouter, Path, Query

from api.providers import get_provider

from .models_models import GetModelResponse, ListModelsResponse

router = APIRouter()


@router.get(
    "/{model_id}",
    response_model=GetModelResponse,
    summary="Retrieve a specific model",
)
async def read_model(
    model_id: str = Path(..., description="The ID of the model to retrieve"),
    provider: str = Query("mistral", description="AI provider"),
):
    service = get_provider(provider)
    return {"model": await service.check_model(model_id)}


@router.get("/", response_model=ListModelsResponse, summary="List all models")
async def list_models(provider: str = Query("mistral", description="AI provider")):
    service = get_provider(provider)
    models = await service.list_models()
    return {"models": models}
