from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from json.decoder import JSONDecodeError
from typing import AsyncGenerator, Tuple

from anthropic import AsyncAnthropic
from fastapi import HTTPException
from mistralai import Mistral
from openai import AsyncOpenAI

from api.utils import CustomLogger

logger = CustomLogger.get_logger(__name__)


class AIProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> str:
        pass

    @abstractmethod
    async def stream(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> AsyncGenerator[Tuple[str, str | None], None]:
        pass

    @abstractmethod
    async def check_model(self, model: str):
        pass

    @abstractmethod
    async def list_models(self):
        pass

    @abstractmethod
    async def generate_embeddings(self, inputs: list[str], model: str):
        pass


class MistralAIProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")
        self.client = Mistral(api_key=self.api_key)

    async def complete(self, model, messages, temperature, max_tokens, top_p):
        response = await self.client.chat.complete_async(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return response.choices[0].message.content

    async def stream(self, model, messages, temperature, max_tokens, top_p):
        response = await self.client.chat.stream_async(
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
            model = await self.client.models.retrieve_async(model_id=model)
            if model is None:
                raise HTTPException(status_code=404, detail="Model not found")
            return model
        except Exception as e:
            if "status 404" in str(e).lower():
                raise HTTPException(status_code=404, detail="Model not found") from e
            logger.error(f"An error occurred while checking model : {e}")
            raise HTTPException(status_code=503, detail="Service unavailable") from e

    async def list_models(self):
        return await self.client.models.list_async()

    async def generate_embeddings(
        self, inputs: list[str], model: str = "mistral-embed"
    ):
        try:
            response = await self.client.embeddings.create_async(
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


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def complete(self, model, messages, temperature, max_tokens, top_p):
        resp = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return resp.choices[0].message.content

    async def stream(self, model, messages, temperature, max_tokens, top_p):
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content, chunk.choices[0].finish_reason

    async def check_model(self, model):
        try:
            return await self.client.models.retrieve(model)
        except Exception as e:
            logger.error(f"OpenAI model check failed: {e}")
            raise HTTPException(status_code=404, detail="Model not found") from e

    async def list_models(self):
        return await self.client.models.list()

    async def generate_embeddings(
        self, inputs: list[str], model: str = "text-embedding-3-small"
    ):
        try:
            resp = await self.client.embeddings.create(model=model, input=inputs)
            return json.loads(resp.model_dump_json())
        except Exception as e:
            logger.error(f"OpenAI embeddings error: {e}")
            raise ConnectionError(f"OpenAI embeddings error: {e}") from e


class AnthropicProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def complete(self, model, messages, temperature, max_tokens, top_p):
        resp = await self.client.messages.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return resp.content[0].text if resp.content else ""

    async def stream(self, model, messages, temperature, max_tokens, top_p):
        stream = await self.client.messages.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True,
        )
        async for event in stream:
            if event.type == "content_block_delta" and event.delta.text:
                yield event.delta.text, None

    async def check_model(self, model):
        try:
            return await self.client.models.retrieve(model)
        except Exception as e:
            logger.error(f"Anthropic model check failed: {e}")
            raise HTTPException(status_code=404, detail="Model not found") from e

    async def list_models(self):
        return await self.client.models.list()

    async def generate_embeddings(
        self, inputs: list[str], model: str = "claude-3-sonnet-20240229"
    ):
        try:
            resp = await self.client.embeddings.create(model=model, input=inputs)
            return json.loads(resp.model_dump_json())
        except Exception as e:
            logger.error(f"Anthropic embeddings error: {e}")
            raise ConnectionError(f"Anthropic embeddings error: {e}") from e


def get_provider(name: str) -> AIProvider:
    normalized = name.lower()
    if normalized in {"mistral", "mistralai"}:
        return MistralAIProvider()
    if normalized == "openai":
        return OpenAIProvider()
    if normalized == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"Unknown provider: {name}")
