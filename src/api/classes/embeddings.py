from api.utils import CustomLogger, InferenceUtils
from api.providers import ProviderRegistry

logger = CustomLogger.get_logger(__name__)


class Embeddings:
    def __init__(self, provider_registry: ProviderRegistry, inference_utils: InferenceUtils):
        self.provider_registry = provider_registry
        self.inference_utils = inference_utils

    def _get_provider(self, model: str):
        provider = self.provider_registry.get_by_model_prefix(model)
        if provider is None:
            provider = self.provider_registry.get("mistral")
        if provider is None:
            raise ValueError("Aucun provider compatible trouvé pour ce modèle d'embedding")
        return provider

    async def generate_embeddings(
        self,
        model: str,
        inputs: list[str],
        job_id: str,
        output_format: str = "dict",
    ):
        provider = self._get_provider(model)
        response = await provider.create_embeddings(model=model, inputs=inputs)
        data = response.get("data", None)

        if not data:
            raise ValueError("Invalid response from provider API")

        if output_format == "points":
            return self.inference_utils.embedding_to_points(inputs, data)
        elif output_format == "tuple":
            return self.inference_utils.embedding_to_tuple(inputs, data)

        return self.inference_utils.format_embeddings_openai(inputs, data, model)
