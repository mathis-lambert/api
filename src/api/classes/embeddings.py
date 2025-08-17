from api.utils import CustomLogger, InferenceUtils
from api.providers import ProviderRegistry

logger = CustomLogger.get_logger(__name__)


class Embeddings:
    def __init__(self, provider_registry: ProviderRegistry, inference_utils: InferenceUtils):
        self.provider_registry = provider_registry
        self.inference_utils = inference_utils

    def _resolve_provider_and_model(self, model: str):
        provider, normalized_model = self.provider_registry.resolve(model)
        if provider is None:
            provider = self.provider_registry.get("mistral")
        if provider is None:
            raise ValueError("Aucun provider compatible trouvé pour ce modèle d'embedding")
        return provider, normalized_model

    async def generate_embeddings(
        self,
        model: str,
        inputs: list[str],
        job_id: str,
        output_format: str = "dict",
    ):
        provider, normalized_model = self._resolve_provider_and_model(model)
        response = await provider.create_embeddings(model=normalized_model, inputs=inputs)
        data = response.get("data", None)

        if not data:
            raise ValueError("Invalid response from provider API")

        if output_format == "points":
            return self.inference_utils.embedding_to_points(inputs, data)
        elif output_format == "tuple":
            return self.inference_utils.embedding_to_tuple(inputs, data)

        return self.inference_utils.format_embeddings_openai(inputs, data, normalized_model)
