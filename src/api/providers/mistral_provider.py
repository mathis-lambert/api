from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Tuple

from mistralai import Mistral

from .base import ModelCard, Provider


class MistralProvider(Provider):
    name = "mistral"

    def __init__(self):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")
        self.client = Mistral(api_key=api_key)

    async def list_models(self) -> List[ModelCard]:
        models = await self.client.models.list_async()
        return [ModelCard(id=m.id, provider=self.name) for m in models.data]

    async def get_model(self, model_id: str) -> ModelCard:
        m = await self.client.models.retrieve_async(model_id=model_id)
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
        params.update({k: v for k, v in (kwargs or {}).items() if v is not None})
        response = await self.client.chat.complete_async(**params)
        # Normaliser en OpenAI chat.completion
        choice = response.choices[0]
        message = getattr(choice, "message", None)
        tool_calls = getattr(message, "tool_calls", None) if message else None
        finish_reason = getattr(choice, "finish_reason", None)
        content = (message.content if message else "") or None
        # tool_calls Mistral -> OpenAI-like dict
        tc = None
        if tool_calls:
            tc = [
                {
                    "id": getattr(c, "id", "call_"),
                    "type": getattr(c, "type", "function"),
                    "function": {
                        "name": getattr(getattr(c, "function", None), "name", ""),
                        "arguments": getattr(getattr(c, "function", None), "arguments", "{}"),
                    },
                }
                for c in tool_calls
            ]
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
                    "message": {
                        "role": "assistant",
                        "content": content,
                        **({"tool_calls": tc} if tc else {}),
                    },
                    "logprobs": None,
                    "finish_reason": finish_reason or ("tool_calls" if tc else "stop"),
                }
            ],
            "usage": {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) if getattr(response, "usage", None) else 0,
                "completion_tokens": getattr(response.usage, "completion_tokens", 0) if getattr(response, "usage", None) else 0,
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
        }
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        params.update({k: v for k, v in (kwargs or {}).items() if v is not None})
        stream = await self.client.chat.stream_async(**params)
        async for chunk in stream:
            if chunk.data.choices[0].delta.content is not None:
                yield chunk.data.choices[0].delta.content, chunk.data.choices[0].finish_reason

    async def create_embeddings(self, model: str, inputs: Iterable[str]) -> Dict[str, Any]:
        response = await self.client.embeddings.create_async(model=model, inputs=list(inputs))
        return json.loads(response.model_dump_json())


