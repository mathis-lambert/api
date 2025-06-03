from api.providers import AIProvider
from api.utils import CustomLogger, InferenceUtils

logger = CustomLogger.get_logger(__name__)


class Embeddings:
    def __init__(self, provider: AIProvider, inference_utils: InferenceUtils):
        self.provider = provider
        self.inference_utils = inference_utils

    async def generate_embeddings(
        self,
        model: str,
        inputs: list[str],
        job_id: str,
        output_format: str = "dict",
    ):
        response = await self.provider.generate_embeddings(
            inputs=inputs,
            model=model,
        )
        data = response.get("data", None)

        if not data:
            raise ValueError("Invalid response from AI provider")

        if output_format == "points":
            return self.inference_utils.embedding_to_points(inputs, data)
        elif output_format == "tuple":
            return self.inference_utils.embedding_to_tuple(inputs, data)

        return self.inference_utils.format_embeddings(inputs, data, job_id)
