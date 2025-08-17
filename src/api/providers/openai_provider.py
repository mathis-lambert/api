from __future__ import annotations

import os
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Tuple

from openai import AsyncOpenAI

from .base import ModelCard, Provider


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=api_key)

    async def list_models(self) -> List[ModelCard]:
        models = await self.client.models.list()
        return [ModelCard(id=m.id, provider=self.name) for m in models.data]

    async def get_model(self, model_id: str) -> ModelCard:
        m = await self.client.models.retrieve(model_id)
        return ModelCard(id=m.id, provider=self.name)

    async def chat_complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        top_p: float,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        # Ajoute les kwargs non nuls (provider-spécifiques)
        params.update({k: v for k, v in (kwargs or {}).items() if v is not None})
        response = await self.client.chat.completions.create(**params)
        # Retourne la réponse OpenAI originale (dict)
        return response.model_dump()

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        top_p: float,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True,
        }
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        params.update({k: v for k, v in (kwargs or {}).items() if v is not None})
        stream = await self.client.chat.completions.create(**params)
        async for event in stream:
            if event.choices:
                delta = event.choices[0].delta
                if delta and getattr(delta, "content", None):
                    yield delta.content, event.choices[0].finish_reason

    async def create_embeddings(self, model: str, inputs: Iterable[str]) -> Dict[str, Any]:
        response = await self.client.embeddings.create(model=model, input=list(inputs))
        return {"data": [{"object": "embedding", "embedding": d.embedding} for d in response.data]}


