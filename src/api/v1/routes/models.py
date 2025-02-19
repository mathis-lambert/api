from fastapi import APIRouter, Depends

from api.v1.services import MistralAIService

router = APIRouter()


@router.get("/{model_id}", tags=["models", "retrieve"], summary="Retrieve a specific model")
async def read_model(
        model_id: str,
        mistralai_service: MistralAIService = Depends()
):
    return {"model": await mistralai_service.check_model(model_id)}


@router.get('/', tags=["models", "list"], summary="List all models")
async def list_models(
        mistralai_service: MistralAIService = Depends()
):
    models = await mistralai_service.list_models()
    return {"models": models}
