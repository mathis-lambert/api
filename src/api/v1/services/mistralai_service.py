import os

from mistralai import Mistral

from api.utils import CustomLogger

logger = CustomLogger.get_logger(__name__)


class MistralAIService:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY", None)

        if self.api_key == "":
            raise ValueError("MISTRAL_API_KEY environment variable is not set")

        self.mistral_client = Mistral(api_key=self.api_key)

    async def complete(self, model, messages, temperature, max_tokens, top_p):
        response = await self.mistral_client.chat.complete_async(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return response.choices[0].message.content

    async def stream(self, model, messages, temperature, max_tokens, top_p):
        response = await self.mistral_client.chat.stream_async(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        async for chunk in response:
            if chunk.data.choices[0].delta.content is not None:
                yield chunk.data.choices[0].delta.content

    async def check_model(self, model):
        try:
            model = await self.mistral_client.models.retrieve_async(model_id=model)

            if model is None:
                raise ValueError(f"Model {model} not found")

            return model
        except Exception as e:
            logger.error(f"An error occurred while checking model : {e}")
            raise ConnectionError(f"An error occurred while checking model : {e}") from e

    async def list_models(self):
        return await self.mistral_client.models.list_async()
