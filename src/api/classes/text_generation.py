from __future__ import annotations

import datetime
import os
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional

from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
    Choice,
    ChoiceDelta,
)
from openai.types.chat import ChatCompletionMessageParam


class TextGeneration:
    def __init__(self, openrouter_client: Optional[AsyncOpenAI] = None):
        self._client: AsyncOpenAI = openrouter_client or self._build_openrouter_client()

    def _build_openrouter_client(self) -> Optional[AsyncOpenAI]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return None
        base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        # Recommended headers by OpenRouter
        default_headers = {}
        site = os.environ.get("OPENROUTER_SITE_URL")
        app_name = os.environ.get("OPENROUTER_APP_NAME")
        if site:
            default_headers["HTTP-Referer"] = site
        if app_name:
            default_headers["X-Title"] = app_name
        return AsyncOpenAI(
            base_url=base_url, api_key=api_key, default_headers=default_headers
        )

    async def generate_stream_response(
        self,
        model: str,
        messages: Iterable[ChatCompletionMessageParam],
        job_id: str,
        **kwargs: Any,
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """
        Generate a streaming response for SSE via OpenRouter (OpenAI Chat Completions).
        Returns ChatCompletion objects.
        """
        if self._client is None:
            # Fallback offline for tests: two simple chunks
            yield ChatCompletionChunk(
                id=f"chatcmpl-{job_id}",
                object="chat.completion.chunk",
                created=int(datetime.now().timestamp()),
                model=model,
                choices=[Choice(index=0, delta=ChoiceDelta(content="a"))],
            )
            return

        # Use the OpenAI-compatible OpenRouter API
        stream = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            yield chunk

    async def complete(
        self,
        model: str,
        messages: Iterable[ChatCompletionMessageParam],
        job_id: str,
        **kwargs: Any,
    ) -> ChatCompletion:
        """Generate a non-streaming OpenAI Chat Completions response via OpenRouter."""
        if self._client is None:
            # Offline fallback for tests
            def _get(field: str, obj: Any, default: str = "") -> Any:
                # Support both dict-like and Pydantic models
                if isinstance(obj, dict):
                    return obj.get(field, default)
                try:
                    return getattr(obj, field)
                except Exception:
                    return default

            content = "".join(
                _get("content", m, "")
                for m in messages
                if _get("role", m, "") == "user"
            )
            return {
                "id": f"chatcmpl-{job_id}",
                "object": "chat.completion",
                "created": 0,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content or "ok"},
                        "logprobs": None,
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
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

        resp = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs,
        )
        return resp
