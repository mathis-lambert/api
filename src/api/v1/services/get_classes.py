from fastapi import Depends

from api.classes import Embeddings, TextGeneration
from api.providers import get_provider
from api.utils import InferenceUtils

from .get_databases import get_mongo_client, get_qdrant_client
from .rag_service import RagService


def get_embeddings(
    provider: str = "mistral",
    inference_utils: InferenceUtils = Depends(),
) -> Embeddings:
    return Embeddings(get_provider(provider), inference_utils)


def get_rag_service(
    embeddings: Embeddings = Depends(get_embeddings),
    qdrant_client=Depends(get_qdrant_client),
    mongo_client=Depends(get_mongo_client),
) -> RagService:
    return RagService(embeddings, qdrant_client, mongo_client)


def get_text_generation(
    provider: str = "mistral",
    inference_utils: InferenceUtils = Depends(),
) -> TextGeneration:
    return TextGeneration(get_provider(provider), inference_utils)


def get_mistral_service():
    return get_provider("mistral")
