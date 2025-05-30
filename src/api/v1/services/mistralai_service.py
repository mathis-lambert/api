import json
import os
from json.decoder import JSONDecodeError
from typing import Tuple

from fastapi import HTTPException
from mistralai import Mistral

from api.utils import CustomLogger

logger = CustomLogger.get_logger(__name__)


class MistralAIService:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY", None)

        if self.api_key is None:
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

    async def stream(
        self, model, messages, temperature, max_tokens, top_p
    ) -> Tuple[str, str]:
        response = await self.mistral_client.chat.stream_async(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        async for chunk in response:
            if chunk.data.choices[0].delta.content is not None:
                yield (
                    chunk.data.choices[0].delta.content,
                    chunk.data.choices[0].finish_reason,
                )

    async def check_model(self, model):
        try:
            model = await self.mistral_client.models.retrieve_async(model_id=model)

            if model is None:
                raise HTTPException(status_code=404, detail="Model not found") from None

            return model
        except Exception as e:
            if "status 404" in str(e).lower():
                raise HTTPException(status_code=404, detail="Model not found") from e
            else:
                logger.error(f"An error occurred while checking model : {e}")
                raise HTTPException(
                    status_code=503, detail="Service unavailable"
                ) from e

    async def list_models(self):
        return await self.mistral_client.models.list_async()

    async def generate_embeddings(
        self,
        inputs: list[str],
        model: str = "mistral-embed",
    ):
        try:
            response = await self.mistral_client.embeddings.create_async(
                model=model, inputs=inputs
            )

            return json.loads(response.model_dump_json())

        except JSONDecodeError as e:
            logger.error(f"An error occurred while generating embeddings : {e}")
            raise ConnectionError(
                f"An error occurred while generating embeddings : {e}"
            ) from e

        except Exception as e:
            logger.error(f"An error occurred while generating embeddings : {e}")
            raise ConnectionError(
                f"An error occurred while generating embeddings : {e}"
            ) from e
