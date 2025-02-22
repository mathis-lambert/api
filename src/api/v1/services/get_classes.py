from fastapi import Depends

from api.classes import Embeddings, TextGeneration
from api.utils import InferenceUtils

from .get_databases import get_mongo_client, get_qdrant_client
from .mistralai_service import MistralAIService
from .rag_service import RagService


def get_embeddings(
    mistralai_service: MistralAIService = Depends(),
    inference_utils: InferenceUtils = Depends(),
) -> Embeddings:
    return Embeddings(mistralai_service, inference_utils)


def get_rag_service(
    embeddings: Embeddings = Depends(get_embeddings),
    qdrant_client=Depends(get_qdrant_client),
    mongo_client=Depends(get_mongo_client),
) -> RagService:
    return RagService(embeddings, qdrant_client, mongo_client)


def get_text_generation(
    mistralai_service: MistralAIService = Depends(),
    inference_utils: InferenceUtils = Depends(),
) -> TextGeneration:
    return TextGeneration(mistralai_service, inference_utils)


def get_mistral_service(
    mistralai_service: MistralAIService = Depends(),
) -> MistralAIService:
    return mistralai_service
