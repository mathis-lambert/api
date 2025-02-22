from api.utils import CustomLogger, InferenceUtils

logger = CustomLogger.get_logger(__name__)


class Embeddings:
    def __init__(self, mistralai_service, inference_utils: InferenceUtils):
        self.mistralai_service = mistralai_service
        self.inference_utils = inference_utils

    async def generate_embeddings(
        self,
        model: str,
        inputs: list[str],
        job_id: str,
        encoding_format: str = "float",
        output_format: str = "dict",
    ):
        response = await self.mistralai_service.generate_embeddings(
            inputs=inputs,
            model=model,
            encoding_format=encoding_format,
        )
        data = response.get("data", None)

        if not data:
            raise ValueError("Invalid response from Mistral API")

        if output_format == "points":
            return self.inference_utils.embedding_to_points(inputs, data)
        elif output_format == "tuple":
            return self.inference_utils.embedding_to_tuple(inputs, data)

        return self.inference_utils.format_embeddings(inputs, data, job_id)
