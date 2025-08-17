from fastapi import Depends

from api.classes import Embeddings, TextGeneration
from api.utils import InferenceUtils
from api.providers import ProviderRegistry
from api.providers.mistral_provider import MistralProvider
from api.providers.openai_provider import OpenAIProvider

from .get_databases import get_mongo_client, get_qdrant_client


def _build_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    # Chaque provider peut lever une erreur si la clé API n'est pas définie.
    # On capture pour permettre au système de fonctionner même si certains providers sont absents.
    try:
        registry.register(MistralProvider())
    except Exception:
        pass
    try:
        registry.register(OpenAIProvider())
    except Exception:
        pass
    return registry


def get_provider_registry() -> ProviderRegistry:
    return _build_provider_registry()


def get_embeddings(
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
    inference_utils: InferenceUtils = Depends(),
) -> Embeddings:
    return Embeddings(provider_registry, inference_utils)


# RAG supprimé au profit de /vector_stores/{id}/search


def get_text_generation(
    provider_registry: ProviderRegistry = Depends(get_provider_registry),
    inference_utils: InferenceUtils = Depends(),
) -> TextGeneration:
    return TextGeneration(provider_registry, inference_utils)
