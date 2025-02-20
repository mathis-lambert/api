from api.v1.services import MistralAIService
from fastapi import APIRouter, Depends, Path

from .models_models import GetModelResponse, ListModelsResponse

router = APIRouter()


@router.get(
    "/{model_id}",
    response_model=GetModelResponse,
    tags=["models"],
    summary="Retrieve a specific model",
)
async def read_model(
    model_id: str = Path(..., description="The ID of the model to retrieve"),
    mistralai_service: MistralAIService = Depends(),
):
    return {"model": await mistralai_service.check_model(model_id)}


@router.get(
    "/", response_model=ListModelsResponse, tags=["models"], summary="List all models"
)
async def list_models(mistralai_service: MistralAIService = Depends()):
    models = await mistralai_service.list_models()
    return {"models": models}
