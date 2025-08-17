from __future__ import annotations

import os
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Tuple

from anthropic import AsyncAnthropic

from .base import ModelCard, Provider


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = AsyncAnthropic(api_key=api_key)

    async def list_models(self) -> List[ModelCard]:
        # Anthropic n'expose pas toujours une liste complète des modèles par API
        # On retourne un sous-ensemble commun
        common = ["claude-3-5-sonnet-latest", "claude-3-opus-latest", "claude-3-haiku-latest"]
        return [ModelCard(id=m, provider=self.name) for m in common]

    async def get_model(self, model_id: str) -> ModelCard:
        return ModelCard(id=model_id, provider=self.name)

    async def chat_complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        # Anthropic utilise "messages" avec un format similaire mais avec system séparé
        system = None
        content_msgs = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                content_msgs.append({"role": m["role"], "content": m["content"]})

        response = await self.client.messages.create(
            model=model,
            system=system,
            messages=content_msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        # Réponse sous forme de blocs -> OpenAI-like
        text = ""
        for block in response.content:
            if getattr(block, "type", None) == "text":
                text += block.text
        import time, uuid
        now = int(time.time())
        result = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": now,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": getattr(response.usage, "input_tokens", 0) if getattr(response, "usage", None) else 0,
                "completion_tokens": getattr(response.usage, "output_tokens", 0) if getattr(response, "usage", None) else 0,
                "total_tokens": getattr(response.usage, "total_tokens", 0) if getattr(response, "usage", None) else 0,
                "prompt_tokens_details": {"cached_tokens": 0, "audio_tokens": 0},
                "completion_tokens_details": {
                    "reasoning_tokens": 0,
                    "audio_tokens": 0,
                    "accepted_prediction_tokens": 0,
                    "rejected_prediction_tokens": 0,
                },
            },
            "service_tier": "default",
        }
        return result

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        system = None
        content_msgs = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                content_msgs.append({"role": m["role"], "content": m["content"]})

        stream = await self.client.messages.create(
            model=model,
            system=system,
            messages=content_msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True,
        )
        async for event in stream:
            if hasattr(event, "type") and event.type == "content_block_delta":
                delta = getattr(event, "delta", None)
                if delta and getattr(delta, "type", None) == "text_delta":
                    yield delta.text, None

    async def create_embeddings(self, model: str, inputs: Iterable[str]) -> Dict[str, Any]:
        # Anthropic ne propose pas d'API embeddings publique standardisée à ce jour.
        # Placeholder pour permettre une interface uniforme. Soulève une erreur claire.
        raise NotImplementedError("Embeddings non disponibles pour Anthropic via API publique")


