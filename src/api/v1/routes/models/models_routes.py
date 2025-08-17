from fastapi import APIRouter, Depends, Path

from api.providers import ProviderRegistry
from api.v1.services.get_classes import get_provider_registry

from .models_models import ListModelsResponse, Model

router = APIRouter()


@router.get(
    "/{provider}/{model_id}",
    response_model=Model,
    summary="Retrieve a specific model",
)
async def read_model(
    provider: str = Path(..., description="The provider name (e.g., 'mistral', 'openai', 'anthropic', 'google')"),
    model_id: str = Path(..., description="The ID of the model to retrieve"),
    registry: ProviderRegistry = Depends(get_provider_registry),
):
    provider_client = registry.get(provider)
    if provider_client is None:
        return Model(id=model_id)
    m = await provider_client.get_model(model_id)
    return Model(id=m.id, owned_by=m.provider)


@router.get("/", response_model=ListModelsResponse, summary="List all models")
async def list_models(registry: ProviderRegistry = Depends(get_provider_registry)):
    aggregated: list[Model] = []
    for provider_name in ["mistral", "openai", "anthropic", "google"]:
        provider = registry.get(provider_name)
        if provider is None:
            continue
        try:
            ms = await provider.list_models()
            aggregated.extend(Model(id=m.id, owned_by=provider_name) for m in ms)
        except Exception:
            continue
    return {"object": "list", "data": aggregated}
