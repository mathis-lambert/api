from fastapi import APIRouter, Depends, Path

from api.classes import Models as ModelsClient
from api.v1.services.get_classes import get_models

from .models_models import ListModelsResponse, ModelDTO

router = APIRouter()


@router.get(
    "/{author}/{model}/endpoints",
    response_model=ModelDTO,
    summary="Retrieve a specific model",
)
async def read_model(
    author: str = Path(..., description="The author of the model to retrieve"),
    model: str = Path(..., description="The ID of the model to retrieve"),
    models_client: ModelsClient = Depends(get_models),
):
    data = await models_client.read_model(author, model)
    return ModelDTO(**data)


@router.get("/", response_model=ListModelsResponse, summary="List all models")
async def list_models(models_client: ModelsClient = Depends(get_models)):
    data = await models_client.list_models()
    # Try to normalize items according to the DTO (if needed)
    items = data.get("data", []) if isinstance(data, dict) else []
    normalized: list[ModelDTO] = []
    for m in items:
        if not isinstance(m, dict):
            continue
        # Ensure id is present
        if "id" not in m and "slug" in m:
            m = {**m, "id": m.get("slug")}
        # Optionally map some common fields coming from OpenRouter
        if "name" not in m and "description" in m:
            m = {**m, "name": m.get("description")}
        normalized.append(m)  # Pydantic will validate according to ModelDTO
    return {"data": normalized}
